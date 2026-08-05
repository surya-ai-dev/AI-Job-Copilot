# backend/tests/email/test_email_api.py
# Integration tests verifying email outreach API endpoints

from fastapi.testclient import TestClient
import pytest
from backend.app.main import app

client = TestClient(app)

def test_email_routes_authentication_required():
    # Calling list drafts endpoint without JWT headers should return 401 Unauthorized
    response = client.get("/api/v1/email/drafts")
    assert response.status_code == 401


def test_generate_outreach_authentication_required():
    # Calling generate outreach without JWT headers should return 401
    import uuid
    payload = {
        "job_analysis_id": str(uuid.uuid4()),
        "resume_optimization_id": str(uuid.uuid4())
    }
    response = client.post("/api/v1/email/generate", json=payload)
    assert response.status_code == 401
