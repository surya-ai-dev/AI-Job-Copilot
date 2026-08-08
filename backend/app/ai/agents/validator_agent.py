"""Validator Agent for the Autonomous Resume Optimizer Engine."""

import logging
import re
from enum import Enum
from typing import List, Set, Optional
from pydantic import BaseModel, Field
from backend.app.ai.schemas.candidate_profile_schema import CandidateProfile

logger = logging.getLogger(__name__)


class ValidationStatus(str, Enum):
    """Factual integrity validation status outcomes."""
    PASSED = "PASSED"
    FAILED = "FAILED"


class FactualViolation(BaseModel):
    """Represents a single factual containment discrepancy."""
    field: str = Field(
        ...,
        description="The field where violation was detected (e.g. experience, projects, education)."
    )
    description: str = Field(
        ...,
        description="Description of the fabricated or modified detail."
    )
    original_reference: str = Field(
        ...,
        description="Reference text in the original resume."
    )
    tailored_reference: str = Field(
        ...,
        description="Reference text in the tailored resume."
    )


class ValidationReport(BaseModel):
    """Structured report returned by the Validator Agent."""
    status: ValidationStatus = Field(
        ...,
        description="PASSED or FAILED validation result."
    )
    factual_violations: List[FactualViolation] = Field(
        default_factory=list,
        description="List of factual integrity violations."
    )


class ResumeValidatorAgent:
    """Agent responsible for checking structural, metadata, and semantic containment integrity."""

    def validate(
        self,
        original: CandidateProfile,
        tailored: CandidateProfile,
        job_skills: Optional[List[str]] = None
    ) -> ValidationReport:
        """Compares original ground truth resume against tailored version to detect fabrication."""
        logger.info("Executing resume validator agent fact-checking.")
        violations: List[FactualViolation] = []

        # 1. Structural count checks
        if len(tailored.experience) != len(original.experience):
            violations.append(
                FactualViolation(
                    field="experience",
                    description="Altered the number of employment history records.",
                    original_reference=f"{len(original.experience)} items",
                    tailored_reference=f"{len(tailored.experience)} items"
                )
            )

        if len(tailored.projects) != len(original.projects):
            violations.append(
                FactualViolation(
                    field="projects",
                    description="Altered the number of project records.",
                    original_reference=f"{len(original.projects)} items",
                    tailored_reference=f"{len(tailored.projects)} items"
                )
            )

        if len(tailored.education) != len(original.education):
            violations.append(
                FactualViolation(
                    field="education",
                    description="Altered the number of education records.",
                    original_reference=f"{len(original.education)} items",
                    tailored_reference=f"{len(tailored.education)} items"
                )
            )

        # Skip granular checks if counts are broken to avoid index errors
        if violations:
            return ValidationReport(status=ValidationStatus.FAILED, factual_violations=violations)

        # 2. Detailed metadata & date validation
        # Check experience records
        for i in range(len(original.experience)):
            o_exp = original.experience[i]
            t_exp = tailored.experience[i]

            if t_exp.company != o_exp.company:
                violations.append(
                    FactualViolation(
                        field="experience",
                        description=f"Fabricated/modified company name for item {i+1}.",
                        original_reference=o_exp.company or "None",
                        tailored_reference=t_exp.company or "None"
                    )
                )
            if t_exp.role != o_exp.role:
                violations.append(
                    FactualViolation(
                        field="experience",
                        description=f"Fabricated/modified job role title for item {i+1}.",
                        original_reference=o_exp.role or "None",
                        tailored_reference=t_exp.role or "None"
                    )
                )
            if t_exp.start_date != o_exp.start_date or t_exp.end_date != o_exp.end_date:
                violations.append(
                    FactualViolation(
                        field="experience",
                        description=f"Altered employment duration dates for item {i+1}.",
                        original_reference=f"{o_exp.start_date} to {o_exp.end_date}",
                        tailored_reference=f"{t_exp.start_date} to {t_exp.end_date}"
                    )
                )

        # Check projects records
        for i in range(len(original.projects)):
            o_proj = original.projects[i]
            t_proj = tailored.projects[i]
            if t_proj.title != o_proj.title:
                violations.append(
                    FactualViolation(
                        field="projects",
                        description=f"Modified project title for item {i+1}.",
                        original_reference=o_proj.title or "None",
                        tailored_reference=t_proj.title or "None"
                    )
                )

        # Check education records
        for i in range(len(original.education)):
            o_edu = original.education[i]
            t_edu = tailored.education[i]
            if (t_edu.institution != o_edu.institution or
                t_edu.degree != o_edu.degree or
                t_edu.field_of_study != o_edu.field_of_study or
                t_edu.start_date != o_edu.start_date or
                t_edu.end_date != o_edu.end_date):
                violations.append(
                    FactualViolation(
                        field="education",
                        description=f"Altered educational credentials for item {i+1}.",
                        original_reference=f"{o_edu.degree} in {o_edu.field_of_study} from {o_edu.institution}",
                        tailored_reference=f"{t_edu.degree} in {t_edu.field_of_study} from {t_edu.institution}"
                    )
                )

        # Check certifications (cannot add certifications)
        orig_certs_lower = {c.lower().strip() for c in original.certifications}
        for cert in tailored.certifications:
            if cert.lower().strip() not in orig_certs_lower:
                violations.append(
                    FactualViolation(
                        field="certifications",
                        description="Fabricated new certification credentials.",
                        original_reference="Not present",
                        tailored_reference=cert
                    )
                )

        # 3. Semantic containment and entity check (no fake skills/technologies in description text)
        # Extract all technology tokens from original profile to build a grounding vocabulary
        grounding_vocabulary = self._extract_tech_entities(original)
        if job_skills:
            for s in job_skills:
                grounding_vocabulary.add(s.lower().strip())

        for i, exp in enumerate(tailored.experience):
            desc = exp.description or ""
            # Extract technical words (e.g. capitalized strings / tools)
            tech_tokens = self._find_tech_tokens(desc)
            for token in tech_tokens:
                if token.lower() not in grounding_vocabulary:
                    # Fabricated experience: claiming familiarity with a tech not listed in original resume
                    violations.append(
                        FactualViolation(
                            field="experience",
                            description=f"Fabricated skill claim in experience {i+1}: Candidate profile contains no mention of '{token}'.",
                            original_reference="Not present",
                            tailored_reference=token
                        )
                    )

        status = ValidationStatus.FAILED if violations else ValidationStatus.PASSED
        logger.info(f"Factual validation complete. Result: {status.name}")
        return ValidationReport(status=status, factual_violations=violations)

    def _extract_tech_entities(self, profile: CandidateProfile) -> Set[str]:
        """Builds a set of allowed lower-case technology/skills terms from original profile."""
        entities = set()

        # Add listed skills
        for skill in profile.skills:
            entities.add(skill.lower().strip())

        # Add listed certifications
        for cert in profile.certifications:
            entities.update(t.lower() for t in self._find_tech_tokens(cert))

        # Add words from original experience descriptions
        for exp in profile.experience:
            entities.update(t.lower() for t in self._find_tech_tokens(exp.description or ""))
            for h in exp.highlights:
                entities.update(t.lower() for t in self._find_tech_tokens(h))

        # Add words from original project descriptions
        for proj in profile.projects:
            entities.update(t.lower() for t in self._find_tech_tokens(proj.description or ""))
            for h in proj.highlights:
                entities.update(t.lower() for t in self._find_tech_tokens(h))
            for tech in proj.technologies:
                entities.add(tech.lower().strip())

        return entities

    def _find_tech_tokens(self, text: str) -> Set[str]:
        """Helper to find potential technology tokens (words containing uppercase characters or specific tech patterns)."""
        tokens = set()
        words = re.findall(r"\b[A-Za-z0-9+#\-\.]+\b", text)
        for w in words:
            # Acronyms (e.g. AWS, REST, API, HTML, SQL)
            is_acronym = w.isupper() and len(w) > 1
            # Mixed case/camelCase/PascalCase (e.g. FastAPI, PostgreSQL, TypeScript, ReactJS, jQuery)
            is_mixed_case = any(c.islower() for c in w) and sum(1 for c in w if c.isupper()) > 1
            # Technical symbols (e.g. C++, C#, .NET)
            has_symbols = "+" in w or "#" in w or w.startswith(".")
            # Common tech tools and programming languages (case-insensitive)
            is_common_tech = w.lower() in {
                "fastapi", "postgres", "postgresql", "redis", "mongodb", "sql", "git", "docker",
                "python", "kubernetes", "aws", "gcp", "azure", "java", "ruby", "c", "c++", "c#",
                "typescript", "javascript", "html", "css", "pmp", "cissp", "csm"
            }

            if is_acronym or is_mixed_case or has_symbols or is_common_tech:
                tokens.add(w.strip(" .,"))
        return tokens
