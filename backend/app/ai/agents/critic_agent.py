"""Critic Agent for the Autonomous Resume Optimizer Engine."""

import logging
import re
from enum import Enum
from typing import List
from pydantic import BaseModel, Field, field_validator
from backend.app.ai.schemas.candidate_profile_schema import CandidateProfile

logger = logging.getLogger(__name__)

CRITIC_SYSTEM_PROMPT = """You are a Senior Recruiter and Editorial Critic.
Review the rewritten candidate profile for stylistic flow, clarity, tone, and formatting consistency.
Ensure descriptions are written in active voice, lead with impact, and contain no awkward sentence transitions.
Do not verify facts; focus entirely on style, readability, and vocabulary.
Return the results strictly as JSON.
"""


class CriticStatus(str, Enum):
    """Outcomes from the Critic Agent."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AwkwardPhrase(BaseModel):
    """An identified styling deficit and its suggestion."""
    original_text: str = Field(..., description="The identified awkward text segment.")
    suggestion: str = Field(..., description="Proposed replacement text.")


class CriticReport(BaseModel):
    """The structured evaluation output from the Critic Agent."""
    status: CriticStatus = Field(
        ...,
        description="Style evaluation outcome (APPROVED/REJECTED)."
    )
    comments: List[str] = Field(
        default_factory=list,
        description="General feedback comments regarding tone, grammar, and ATS format."
    )
    awkward_phrases: List[AwkwardPhrase] = Field(
        default_factory=list,
        description="Detailed list of phrasing improvements."
    )


class CriticAgent:
    """Agent responsible for checking writing style, active voice, and formatting."""

    def review(self, candidate: CandidateProfile, job_profile_data: dict) -> CriticReport:
        """Reviews candidate profile and returns style audit reports with approval state."""
        logger.info("Executing critic agent review.")
        comments: List[str] = []
        awkward_phrases: List[AwkwardPhrase] = []

        # 1. Check professional summary readability
        summary = candidate.professional_summary or ""
        if len(summary.split()) > 120:
            comments.append("Professional summary is too long (exceeds 120 words). Limit to keep reader engaged.")
        elif len(summary.split()) < 15:
            comments.append("Professional summary is too brief. Expand to highlight key value propositions.")

        # 2. Check passive voice in work experience highlights and description
        passive_patterns = [
            (r"\bwas\s+responsible\s+for\b", "Led / Managed"),
            (r"\bhelped\s+with\b", "Collaborated on / Facilitated"),
            (r"\bassisted\s+in\b", "Contributed to / Supported"),
            (r"\bduties\s+included\b", "Directed / Orchestrated")
        ]

        for i, exp in enumerate(candidate.experience):
            desc = exp.description or ""
            for pattern, suggestion in passive_patterns:
                if re.search(pattern, desc, re.IGNORECASE):
                    match = re.search(pattern, desc, re.IGNORECASE).group(0)
                    awkward_phrases.append(
                        AwkwardPhrase(
                            original_text=f"Experience {i+1}: '{match}'",
                            suggestion=f"Use active verb like '{suggestion}'"
                        )
                    )

            for j, highlight in enumerate(exp.highlights):
                for pattern, suggestion in passive_patterns:
                    if re.search(pattern, highlight, re.IGNORECASE):
                        match = re.search(pattern, highlight, re.IGNORECASE).group(0)
                        awkward_phrases.append(
                            AwkwardPhrase(
                                original_text=f"Experience {i+1} Highlight {j+1}: '{match}'",
                                suggestion=f"Use active verb like '{suggestion}'"
                            )
                        )

        # 3. Check ATS Keyword density / compliance
        missing_skills = []
        candidate_skills_lower = {s.lower().strip() for s in candidate.skills}
        for skill in job_profile_data.get("required_skills", []):
            if skill.lower().strip() not in candidate_skills_lower:
                missing_skills.append(skill)

        if missing_skills:
            comments.append(f"ATS warning: Missing key required skills: {', '.join(missing_skills[:3])}.")

        # 4. Determine Approval / Rejection status
        # If there are severe styling problems (e.g. more than 3 awkward passive-voice phrases), reject the draft.
        if len(awkward_phrases) >= 3 or len(summary.split()) >= 150:
            status = CriticStatus.REJECTED
            comments.append("Stylistic rejection: Resume contains too many passive voice structures or layout issues.")
        else:
            status = CriticStatus.APPROVED
            logger.info("Draft approved for stylistic flow and active voice.")

        return CriticReport(
            status=status,
            comments=comments,
            awkward_phrases=awkward_phrases
        )
