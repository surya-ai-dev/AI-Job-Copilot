# backend/app/dashboard/domain/application.py
# Pure python Domain entities representing JobApplication & Dashboard metrics with UUID support

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid
from backend.app.shared.exceptions import ValidationException

@dataclass
class ResumeRecord:
    resume_id: uuid.UUID
    version_number: int
    file_name: str
    file_size: int


@dataclass
class EmailRecord:
    email_history_id: Optional[uuid.UUID]
    recipient_email: str
    subject: str
    sent_at: Optional[datetime] = None


@dataclass
class ApplicationMetadata:
    job_url: Optional[str] = None
    recruiter_email: Optional[str] = None
    applied_date: datetime = field(default_factory=datetime.utcnow)


@dataclass
class JobApplication:
    job_id: uuid.UUID
    user_id: uuid.UUID
    company_name: str
    job_title: str
    resume_info: ResumeRecord
    email_info: Optional[EmailRecord] = None
    metadata: ApplicationMetadata = field(default_factory=ApplicationMetadata)
    id: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """Enforces domain constraints for job applications."""
        if not self.company_name.strip():
            raise ValidationException("Company name must not be blank.")
        if not self.job_title.strip():
            raise ValidationException("Job title must not be blank.")


@dataclass
class DashboardSummary:
    total_applications: int
    applications_today: int
    active_drafts_count: int
    recent_applications: List[JobApplication] = field(default_factory=list)
