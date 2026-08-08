"""Planner Agent for the Autonomous Resume Optimizer Engine."""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class GapAnalysis(BaseModel):
    """Structured inputs representing the candidate profile gaps."""
    missing_required_skills: List[str] = Field(
        default_factory=list,
        description="Core required skills missing from the candidate profile."
    )
    missing_preferred_skills: List[str] = Field(
        default_factory=list,
        description="Nice-to-have preferred skills missing from the candidate profile."
    )
    experience_years_deficit: float = Field(
        default=0.0,
        description="Difference between job experience requirement and candidate's total years."
    )
    education_mismatch: Optional[str] = Field(
        default=None,
        description="Description of educational major or degree level mismatches."
    )

    @field_validator("experience_years_deficit")
    @classmethod
    def validate_deficit(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError("Experience years deficit cannot be negative")
        return v


class OptimizationTask(BaseModel):
    """A single planned optimization task."""
    priority: int = Field(
        ...,
        description="Priority sequence order (1 being highest)."
    )
    target_section: str = Field(
        ...,
        description="Target profile section: 'skills', 'summary', 'experience', or 'projects'."
    )
    action: str = Field(
        ...,
        description="Factual, compliance-safe instruction for rewriting."
    )
    rationale: str = Field(
        ...,
        description="Underlying motivation or gap explaining the task."
    )

    @field_validator("target_section")
    @classmethod
    def validate_section(cls, v: str) -> str:
        allowed = {"skills", "summary", "experience", "projects"}
        if v not in allowed:
            raise ValueError(f"target_section must be one of {allowed}")
        return v


class OptimizationPlan(BaseModel):
    """A prioritized list of targeted optimization tasks."""
    tasks: List[OptimizationTask] = Field(
        default_factory=list,
        description="List of tasks sequenced for this iteration."
    )


class PlannerAgent:
    """Agent responsible for analyzing gaps and formulating a prioritized, compliance-safe plan."""

    def generate_plan(self, gaps: GapAnalysis) -> OptimizationPlan:
        """Generates a prioritized OptimizationPlan from a GapAnalysis.

        Guarantees that at most 3 tasks are scheduled and instructions do not invent facts.
        """
        logger.info("Generating optimization plan based on gap analysis.")
        tasks: List[OptimizationTask] = []
        priority_counter = 1

        # 1. Prioritize core required skills (max 3)
        for skill in gaps.missing_required_skills:
            if len(tasks) >= 3:
                break
            tasks.append(
                OptimizationTask(
                    priority=priority_counter,
                    target_section="skills",
                    action=(
                        f"Align candidate skills list to include core required skill '{skill}' "
                        f"only if candidate has related background, or highlight experience with "
                        f"'{skill}' in project descriptions."
                    ),
                    rationale=f"Core required skill '{skill}' was identified as missing from candidate profile."
                )
            )
            priority_counter += 1

        # 2. Prioritize experience years deficit
        if len(tasks) < 3 and gaps.experience_years_deficit > 0.0:
            tasks.append(
                OptimizationTask(
                    priority=priority_counter,
                    target_section="summary",
                    action=(
                        f"Emphasize depth, leadership scope, and project scaling in the professional summary "
                        f"to address the identified {gaps.experience_years_deficit}-year experience deficit."
                    ),
                    rationale="Job posting requires more years of experience than the candidate's profile explicitly totals."
                )
            )
            priority_counter += 1

        # 3. Prioritize preferred skills
        for skill in gaps.missing_preferred_skills:
            if len(tasks) >= 3:
                break
            tasks.append(
                OptimizationTask(
                    priority=priority_counter,
                    target_section="skills",
                    action=f"Highlight candidate familiarity with nice-to-have preferred skill '{skill}' if applicable.",
                    rationale=f"Nice-to-have preferred skill '{skill}' was identified as missing."
                )
            )
            priority_counter += 1

        # 4. Prioritize education mismatch
        if len(tasks) < 3 and gaps.education_mismatch:
            tasks.append(
                OptimizationTask(
                    priority=priority_counter,
                    target_section="summary",
                    action=(
                        f"Tailor professional summary context to frame candidate achievements in alignment "
                        f"with educational requirements: '{gaps.education_mismatch}'."
                    ),
                    rationale="Candidate's listed degree rank or major does not match job's target qualifications."
                )
            )
            priority_counter += 1

        plan = OptimizationPlan(tasks=tasks)
        logger.info(f"Optimization plan generated successfully with {len(plan.tasks)} tasks.")
        return plan
