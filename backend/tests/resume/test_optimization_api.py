# backend/tests/resume/test_optimization_api.py
# Integration tests verifying AI Resume Optimization API endpoints

from fastapi.testclient import TestClient
import pytest
from backend.app.main import app

client = TestClient(app)

def test_optimization_routes_authentication_required():
    # Calling list optimizations history without JWT headers should return 401 Unauthorized
    response = client.get("/api/v1/resume/optimize/history")
    assert response.status_code == 401


def test_trigger_optimization_authentication_required():
    # Calling optimize post route without JWT headers should return 401
    import uuid
    response = client.post("/api/v1/resume/optimize", json={"job_analysis_id": str(uuid.uuid4())})
    assert response.status_code == 401
