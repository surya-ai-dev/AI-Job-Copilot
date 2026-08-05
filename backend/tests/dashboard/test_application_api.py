# backend/tests/dashboard/test_application_api.py
# Integration tests verifying dashboard and applications tracking API endpoints

from fastapi.testclient import TestClient
import pytest
from backend.app.main import app

client = TestClient(app)

def test_dashboard_summary_authentication_required():
    # Calling dashboard stats summary without JWT headers should return 401 Unauthorized
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 401


def test_list_applications_authentication_required():
    # Calling applications list without JWT headers should return 401
    response = client.get("/api/v1/dashboard/applications")
    assert response.status_code == 401
