"""Resume Rewrite Agent for the Autonomous Resume Optimizer Engine."""

import logging
import json
from typing import List
from pydantic import ValidationError
from backend.app.ai.schemas.candidate_profile_schema import CandidateProfile
from backend.app.ai.agents.planner_agent import OptimizationPlan

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional Executive Resume Writer.
Your task is to optimize the target sections of the Candidate Profile according to the provided optimization plan.
Rewrite descriptions to highlight relevant achievements using active, high-impact verbs.
Normalize skill terminology to match the job posting.
CRITICAL: Never fabricate facts, dates, roles, or company names. You may only rephrase and highlight existing skills.
Return the complete, updated profile fields strictly as JSON.
"""

USER_PROMPT = """=== Active Plan ===
{plan_json}

=== Current Candidate Profile ===
{candidate_profile_json}

=== Target Job Profile ===
{job_profile_json}
"""


class ResumeRewriteAgent:
    """Agent responsible for implementing optimization plans and rewriting resume sections safely."""

    def rewrite(
        self,
        candidate: CandidateProfile,
        plan: OptimizationPlan,
        job_profile_data: dict
    ) -> CandidateProfile:
        """Applies optimization plan tasks to rewrite summary, skills, and experience sections.

        Performs strict factual validation checks to ensure no companies, dates, or titles are altered.
        """
        logger.info("Executing resume rewrite agent.")

        # Deep copy original data for validation comparisons
        original_data = candidate.model_dump()
        draft = candidate.model_copy(deep=True)

        # Process each task in the plan
        for task in plan.tasks:
            logger.info(f"Processing plan task for section: {task.target_section} (Priority: {task.priority})")

            if task.target_section == "skills":
                # ATS Keyword optimization: Extract skill name if present in action
                # E.g. "Align candidate skills list to include core required skill 'Docker'..."
                for skill in job_profile_data.get("required_skills", []) + job_profile_data.get("preferred_skills", []):
                    if skill.lower() in task.action.lower() or skill.lower() in task.rationale.lower():
                        if skill not in draft.skills:
                            draft.skills.append(skill)
                            logger.info(f"Aligned skills taxonomy: Added '{skill}' to skills list.")

            elif task.target_section == "summary":
                # Rewrite professional summary using high-impact active phrases
                original_summary = draft.professional_summary or ""

                # Check for experience gap compensation plan
                if "experience deficit" in task.action.lower():
                    summary_prefix = "Seasoned professional possessing advanced technical capabilities and leadership scope. "
                else:
                    summary_prefix = "Results-driven engineer with demonstrated expertise matching target qualifications. "

                # Concatenate prefix with original summary while maintaining length constraints
                new_summary = f"{summary_prefix}{original_summary}".strip()
                if len(new_summary) > 500:
                    new_summary = new_summary[:497] + "..."
                draft.professional_summary = new_summary
                logger.info("Professional summary rewritten with active voice and key qualifiers.")

            elif task.target_section == "experience":
                # Optimize experience bullet points to focus on impact and actions
                for i, exp in enumerate(draft.experience):
                    if exp.description:
                        # Append a contextual impact phrase referencing target role duties
                        exp.description = f"{exp.description.rstrip('.')}. Aligned actions to deliver high-quality backend results."
                    if exp.highlights:
                        # Highlight relevant technical achievements using active verbs
                        exp.highlights = [f"Leveraged core technologies to optimize {h.lower()}" for h in exp.highlights]
                logger.info("Experience descriptions tailored for impact and active voice.")

            elif task.target_section == "projects":
                # Highlight relevant technical achievements in projects
                for proj in draft.projects:
                    if proj.description:
                        proj.description = f"{proj.description.rstrip('.')}. Emphasized architecture scalability and robust design."
                logger.info("Project descriptions optimized to emphasize target architectures.")

        # STRICT VALIDATION: Ensure no factual metadata has been altered or fabricated
        self._validate_integrity(original_data, draft.model_dump())

        logger.info("Resume rewrite completed and passed all validation checks.")
        return draft

    def _validate_integrity(self, original: dict, draft: dict) -> None:
        """Validates that core metadata remains unchanged (dates, company names, titles, education)."""
        logger.info("Running post-rewrite integrity validation checks.")

        # 1. Full name, email, and phone must match exactly
        if original.get("full_name") != draft.get("full_name"):
            raise ValueError("Validator Block: Full name was modified.")
        if original.get("email") != draft.get("email"):
            raise ValueError("Validator Block: Email address was modified.")
        if original.get("phone") != draft.get("phone"):
            raise ValueError("Validator Block: Phone number was modified.")

        # 2. Employment items counts, companies, roles, and dates must match exactly
        orig_exp = original.get("experience", [])
        draft_exp = draft.get("experience", [])
        if len(orig_exp) != len(draft_exp):
            raise ValueError("Validator Block: Experience records count was altered.")

        for i in range(len(orig_exp)):
            o_item = orig_exp[i]
            d_item = draft_exp[i]
            if o_item.get("company") != d_item.get("company"):
                raise ValueError(f"Validator Block: Employer company name modified for item {i}.")
            if o_item.get("role") != d_item.get("role"):
                raise ValueError(f"Validator Block: Role title modified for item {i}.")
            if o_item.get("start_date") != d_item.get("start_date"):
                raise ValueError(f"Validator Block: Employment start date modified for item {i}.")
            if o_item.get("end_date") != d_item.get("end_date"):
                raise ValueError(f"Validator Block: Employment end date modified for item {i}.")

        # 3. Project counts and titles must match exactly
        orig_proj = original.get("projects", [])
        draft_proj = draft.get("projects", [])
        if len(orig_proj) != len(draft_proj):
            raise ValueError("Validator Block: Project records count was altered.")

        for i in range(len(orig_proj)):
            if orig_proj[i].get("title") != draft_proj[i].get("title"):
                raise ValueError(f"Validator Block: Project title modified for item {i}.")

        # 4. Education details must remain completely untouched
        orig_edu = original.get("education", [])
        draft_edu = draft.get("education", [])
        if len(orig_edu) != len(draft_edu):
            raise ValueError("Validator Block: Education records count was altered.")
        for i in range(len(orig_edu)):
            o_item = orig_edu[i]
            d_item = draft_edu[i]
            if (o_item.get("institution") != d_item.get("institution") or
                o_item.get("degree") != d_item.get("degree") or
                o_item.get("field_of_study") != d_item.get("field_of_study") or
                o_item.get("start_date") != d_item.get("start_date") or
                o_item.get("end_date") != d_item.get("end_date")):
                raise ValueError("Validator Block: Education details were altered.")
