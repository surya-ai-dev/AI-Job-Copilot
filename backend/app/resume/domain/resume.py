# backend/app/resume/domain/resume.py
# Pure python Domain entities representing Resume & Version contexts with UUID support

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid
from backend.app.shared.exceptions import ValidationException

@dataclass
class ResumeMetadata:
    file_name: str
    file_size: int
    content_type: str
    parsed_skills: list[str] = field(default_factory=list)
    parsed_experience_years: Optional[float] = None

    def validate(self) -> None:
        """Validate metadata details."""
        if not self.file_name.strip():
            raise ValidationException("File name must not be blank.")
        if self.file_size <= 0:
            raise ValidationException("File size must be positive.")
        if self.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            raise ValidationException("Unsupported file type format. Only PDF and DOCX are allowed.")


@dataclass
class Resume:
    user_id: uuid.UUID
    file_path: str
    metadata: ResumeMetadata
    id: Optional[uuid.UUID] = None
    status: str = "active" # active, replaced, deleted
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def validate(self) -> None:
        """Enforces domain constraints for resume structures."""
        self.metadata.validate()
        if not self.file_path.strip():
            raise ValidationException("File path must not be blank.")
        if self.status not in ["active", "replaced", "deleted"]:
            raise ValidationException("Invalid resume status code.")


@dataclass
class ResumeVersion:
    resume_id: uuid.UUID
    user_id: uuid.UUID
    version_number: int
    file_path: str
    optimized_for_company: str
    optimized_for_role: str
    id: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def validate(self) -> None:
        """Verify version specifications."""
        if self.version_number <= 0:
            raise ValidationException("Version number must be greater than zero.")
        if not self.file_path.strip():
            raise ValidationException("File path must not be blank.")
        if not self.optimized_for_company.strip():
            raise ValidationException("Optimization company target must not be blank.")
        if not self.optimized_for_role.strip():
            raise ValidationException("Optimization role target must not be blank.")
