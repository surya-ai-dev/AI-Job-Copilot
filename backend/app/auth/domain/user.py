# backend/app/auth/domain/user.py
# Pure python Domain entities representing User & Profile contexts with UUID support

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import re
import uuid
from backend.app.shared.exceptions import ValidationException

@dataclass
class UserProfile:
    first_name: str
    last_name: str

    def validate(self) -> None:
        """Validate profile details."""
        if not self.first_name.strip():
            raise ValidationException("First name cannot be empty.")
        if not self.last_name.strip():
            raise ValidationException("Last name cannot be empty.")


@dataclass
class User:
    email: str
    hashed_password: str
    first_name: str
    last_name: str
    id: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """Enforces domain validation rules for email and password structures."""
        # Simple email syntax verification
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, self.email):
            raise ValidationException(f"Invalid email structure: {self.email}")
            
        if not self.first_name.strip():
            raise ValidationException("First name must not be blank.")
        if not self.last_name.strip():
            raise ValidationException("Last name must not be blank.")

    def update_profile(self, profile: UserProfile) -> None:
        """Update user profile metrics."""
        profile.validate()
        self.first_name = profile.first_name
        self.last_name = profile.last_name
        self.updated_at = datetime.utcnow()
