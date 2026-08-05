# backend/app/jobs/domain/job.py
# Pure python Domain entities representing Job, ParsedJob, & JobSource contexts with UUID support

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid
import re
from backend.app.shared.exceptions import ValidationException

@dataclass
class JobSource:
    source_type: str # url, text, pdf, image, email, whatsapp
    source_url: Optional[str] = None

    def validate(self) -> None:
        """Validate job source credentials."""
        valid_types = ["url", "text", "pdf", "image", "email", "whatsapp"]
        if self.source_type not in valid_types:
            raise ValidationException(f"Unsupported job source type: {self.source_type}")
        if self.source_type == "url" and not self.source_url:
            raise ValidationException("Source URL is required when source type is 'url'.")
        if self.source_url:
            url_regex = r"^https?://[\w\.-]+\.\w+.*$"
            if not re.match(url_regex, self.source_url):
                raise ValidationException(f"Malformed source URL: {self.source_url}")


@dataclass
class ParsedJob:
    company_name: str
    job_title: str
    description: str
    recruiter_email: Optional[str] = None
    location: Optional[str] = None

    def validate(self) -> None:
        """Validate parsed content parameters."""
        if not self.company_name.strip():
            raise ValidationException("Parsed company name cannot be blank.")
        if not self.job_title.strip():
            raise ValidationException("Parsed job title cannot be blank.")
        if not self.description.strip():
            raise ValidationException("Parsed job description cannot be blank.")
        if self.recruiter_email:
            email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            if not re.match(email_regex, self.recruiter_email):
                raise ValidationException(f"Malformed recruiter email: {self.recruiter_email}")


@dataclass
class Job:
    user_id: uuid.UUID
    source: JobSource
    parsed_data: ParsedJob
    raw_content: str
    id: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """Enforces domain constraints for job models structures."""
        self.source.validate()
        self.parsed_data.validate()
        if not self.raw_content.strip():
            raise ValidationException("Raw job content cannot be empty.")
