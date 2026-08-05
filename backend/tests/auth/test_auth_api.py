# backend/tests/auth/test_auth_api.py
# Integration tests verifying authentication API endpoints

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import pytest
from backend.app.main import app

client = TestClient(app)

def test_api_health_check():
    response = client.get("/health/api")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_register_validation_failure():
    # Attempt register with short password
    payload = {
        "email": "invalid-email",
        "password": "short",
        "first_name": "",
        "last_name": "Charan"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    # FastAPI returns 422 for pydantic schema validation failures
    assert response.status_code == 422
