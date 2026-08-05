# backend/app/jobs/domain/analysis.py
# Pure python Domain entities representing JobAnalysis and extracted properties with UUID support

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid
from backend.app.shared.exceptions import ValidationException

@dataclass
class Skill:
    name: str
    category: str # Programming Languages, Frameworks, Databases, Cloud, AI/ML, DevOps, Testing, Tools, Soft Skills, Domain Knowledge
    importance: str # Mandatory, Preferred, Optional, Good to Have, Unknown

    def validate(self) -> None:
        """Validate skill attributes."""
        if not self.name.strip():
            raise ValidationException("Skill name must not be blank.")
        valid_categories = [
            "Programming Languages", "Frameworks", "Databases", "Cloud", 
            "AI/ML", "DevOps", "Testing", "Tools", "Soft Skills", "Domain Knowledge"
        ]
        if self.category not in valid_categories:
            raise ValidationException(f"Unsupported skill category: {self.category}")
        valid_importances = ["Mandatory", "Preferred", "Optional", "Good to Have", "Unknown"]
        if self.importance not in valid_importances:
            raise ValidationException(f"Unsupported skill importance: {self.importance}")


@dataclass
class ATSKeyword:
    word: str
    category: str # Technical, Role, Industry, Action Verbs, Certification

    def validate(self) -> None:
        """Validate keyword details."""
        if not self.word.strip():
            raise ValidationException("ATS Keyword must not be blank.")
        valid_categories = ["Technical", "Role", "Industry", "Action Verbs", "Certification"]
        if self.category not in valid_categories:
            raise ValidationException(f"Unsupported keyword category: {self.category}")


@dataclass
class JobMetadata:
    seniority: str # Fresher, 0-2 Years, 2-5 Years, 5-8 Years, Senior, Lead, Principal
    employment_type: str # Full-Time, Part-Time, Contract, Internship, Unknown
    education_requirements: Optional[str] = None
    certifications: List[str] = field(default_factory=list)


@dataclass
class JobAnalysis:
    job_id: uuid.UUID
    user_id: uuid.UUID
    metadata: JobMetadata
    skills: List[Skill]
    ats_keywords: List[ATSKeyword]
    responsibilities: List[str]
    qualifications: List[str]
    confidence_score: float = 1.0
    llm_provider: str = "gemini"
    prompt_version: str = "1.0.0"
    processing_time_ms: int = 0
    id: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """Enforces domain constraints for job analysis structures."""
        if self.confidence_score < 0.0 or self.confidence_score > 1.0:
            raise ValidationException("Confidence score must be between 0.0 and 1.0.")
        for skill in self.skills:
            skill.validate()
        for kw in self.ats_keywords:
            kw.validate()
        if not self.skills:
            raise ValidationException("Parsed analysis must extract at least one skill.")
