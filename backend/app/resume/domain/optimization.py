# backend/app/resume/domain/optimization.py
# Pure python Domain entities representing ResumeMatch, ATSScore, & Optimization contexts with UUID support

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid
from backend.app.shared.exceptions import ValidationException

@dataclass
class ATSScore:
    score: int # 0 to 100
    explanation: str
    keyword_coverage_percent: int
    readability_index: float

    def validate(self) -> None:
        """Validate ATS score metrics."""
        if self.score < 0 or self.score > 100:
            raise ValidationException("ATS Score must be between 0 and 100.")
        if self.keyword_coverage_percent < 0 or self.keyword_coverage_percent > 100:
            raise ValidationException("Keyword coverage must be between 0 and 100.")


@dataclass
class OptimizationRecommendation:
    section: str # summary, skills, experience_bullets
    change_type: str # addition, rephrase, reorder
    description: str
    original_text: Optional[str] = None
    suggested_text: Optional[str] = None


@dataclass
class ResumeEvaluation:
    grammar_issues: List[str] = field(default_factory=list)
    readability_score: float = 70.0 # Flesch-Kincaid mock score
    keyword_coverage: int = 0
    formatting_is_valid: bool = True
    ats_compatibility_checked: bool = True


@dataclass
class ResumeMatch:
    resume_id: uuid.UUID
    job_analysis_id: uuid.UUID
    match_score: int # 0 to 100
    skills_match_score: int
    experience_match_score: int
    gap_skills: List[str] = field(default_factory=list)

    def validate(self) -> None:
        """Validate matching metrics."""
        if self.match_score < 0 or self.match_score > 100:
            raise ValidationException("Match score must be between 0 and 100.")


@dataclass
class ResumeOptimization:
    resume_id: uuid.UUID
    job_analysis_id: uuid.UUID
    user_id: uuid.UUID
    match_details: ResumeMatch
    ats_evaluation: ATSScore
    recommendations: List[OptimizationRecommendation]
    optimized_summary: str
    optimized_skills: List[str]
    optimized_file_path: str
    id: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """Enforces domain constraints for optimization models structures."""
        self.match_details.validate()
        self.ats_evaluation.validate()
        if not self.optimized_summary.strip():
            raise ValidationException("Optimized summary must not be empty.")
        if not self.optimized_skills:
            raise ValidationException("Optimized skills list must not be empty.")
        if not self.optimized_file_path.strip():
            raise ValidationException("Optimized file path must not be empty.")
