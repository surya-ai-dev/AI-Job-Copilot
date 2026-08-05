# backend/tests/jobs/test_job_api.py
# Integration tests verifying job Ingestion API endpoints

from fastapi.testclient import TestClient
import pytest
from backend.app.main import app

client = TestClient(app)

def test_jobs_routes_authentication_required():
    # Calling list jobs endpoint without JWT headers should return 401 Unauthorized
    response = client.get("/api/v1/jobs")
    assert response.status_code == 401


def test_jobs_url_parse_authentication_required():
    # Calling parse URL without JWT headers should return 401 Unauthorized
    response = client.post("/api/v1/jobs/parse-url", json={"url": "https://linkedin.com"})
    assert response.status_code == 401
