# backend/app/email/domain/email.py
# Pure python Domain entities representing EmailDraft, EmailHistory, & Attachment contexts with UUID support

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid
import re
from backend.app.shared.exceptions import ValidationException

@dataclass
class EmailRecipient:
    email: str
    name: Optional[str] = None

    def validate(self) -> None:
        """Validate recipient email format."""
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, self.email):
            raise ValidationException(f"Invalid recipient email format: {self.email}")


@dataclass
class EmailAttachment:
    file_path: str
    file_name: str
    file_size: int

    def validate(self) -> None:
        """Validate attachment attributes."""
        if not self.file_path.strip():
            raise ValidationException("Attachment file path cannot be blank.")
        if self.file_size <= 0:
            raise ValidationException("Attachment file size must be positive.")
        if self.file_size > 15 * 1024 * 1024: # 15MB Gmail limit
            raise ValidationException("Attachment file size exceeds Gmail limit of 15MB.")


@dataclass
class EmailDraft:
    user_id: uuid.UUID
    recipient: EmailRecipient
    subject: str
    body: str
    attachment: Optional[EmailAttachment] = None
    id: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """Enforces domain constraints for email drafts."""
        self.recipient.validate()
        if not self.subject.strip():
            raise ValidationException("Email subject cannot be empty.")
        if not self.body.strip():
            raise ValidationException("Email body cannot be empty.")
        if self.attachment:
            self.attachment.validate()


@dataclass
class EmailHistory:
    draft_id: uuid.UUID
    user_id: uuid.UUID
    recipient_email: str
    subject: str
    body: str
    attachment_path: Optional[str] = None
    status: str = "sent" # sent, failed
    sent_at: datetime = field(default_factory=datetime.utcnow)
    id: Optional[uuid.UUID] = None
