# backend/app/auth/domain/token.py
# Pure python Domain entities representing Token and JWT schemas with UUID support

from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class Token:
    access_token: str
    token_type: str = "bearer"


@dataclass
class RefreshTokenDetails:
    token: str
    user_id: uuid.UUID
    expires_at: datetime
    is_revoked: bool = False

    def is_expired(self) -> bool:
        """Check token expiration status."""
        return datetime.utcnow() > self.expires_at
