# backend/tests/jobs/test_analysis_api.py
# Integration tests verifying AI Job Analysis API endpoints

from fastapi.testclient import TestClient
import pytest
from backend.app.main import app

client = TestClient(app)

def test_analysis_routes_authentication_required():
    # Calling list analyses endpoint without JWT headers should return 401 Unauthorized
    response = client.get("/api/v1/jobs/analysis")
    assert response.status_code == 401


def test_analyze_job_authentication_required():
    # Calling analyze without JWT headers should return 401
    import uuid
    response = client.post("/api/v1/jobs/analysis/analyze", json={"job_id": str(uuid.uuid4())})
    assert response.status_code == 401
