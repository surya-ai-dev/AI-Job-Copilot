# backend/tests/resume/test_resume_api.py
# Integration tests verifying resume management API endpoints

from fastapi.testclient import TestClient
import pytest
from backend.app.main import app

client = TestClient(app)

def test_resume_routes_authentication_required():
    # Calling details endpoint without JWT headers should return 401 Unauthorized
    response = client.get("/api/v1/resume")
    assert response.status_code == 401


def test_resume_upload_authentication_required():
    # Calling upload without JWT headers should return 401 Unauthorized
    response = client.post(
        "/api/v1/resume/upload", 
        files={"file": ("resume.pdf", b"content", "application/pdf")}
    )
    assert response.status_code == 401
