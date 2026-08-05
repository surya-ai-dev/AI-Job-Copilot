# backend/tests/helpers.py
# Helper utility methods for generating token headers, mock file uploads, and payload structures

from datetime import datetime, timedelta
from typing import Dict
from jose import jwt
from backend.app.core.config import settings

def create_mock_jwt(subject: str, token_type: str = "access") -> str:
    """Generate a mock signed JWT token for test requests authorization."""
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = {
        "exp": expire,
        "sub": subject,
        "type": token_type
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def get_auth_headers(email: str) -> Dict[str, str]:
    """Return authorization header dict with a signed mock token."""
    token = create_mock_jwt(email)
    return {"Authorization": f"Bearer {token}"}

def generate_mock_pdf_content() -> bytes:
    """Return mock binary content representing a PDF file upload."""
    return b"%PDF-1.4 %mock pdf data content for testing upload files"
