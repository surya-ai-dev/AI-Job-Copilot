# backend/tests/test_users.py
# API Integration tests verifying active user profiles queries and profile changes validation

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from backend.app.auth.models.user_model import UserModel
from backend.tests.helpers import get_auth_headers
from backend.tests.constants import TEST_EMAIL, TEST_FIRST_NAME, TEST_LAST_NAME

@pytest.mark.asyncio
async def test_get_current_user_profile(async_client: AsyncClient, mock_user_record):
    """Test retrieving active user profile metrics."""
    headers = get_auth_headers(TEST_EMAIL)

    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user_record

        response = await async_client.get("/api/v1/users/me", headers=headers)
        
        # Verify response status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        assert data["first_name"] == TEST_FIRST_NAME

@pytest.mark.asyncio
async def test_update_profile_validation_error(async_client: AsyncClient, mock_user_record):
    """Test updating user profiles fails on invalid data payload."""
    headers = get_auth_headers(TEST_EMAIL)
    payload = {"first_name": "", "last_name": ""}

    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_user_record

        response = await async_client.put("/api/v1/users/me", json=payload, headers=headers)
        
        # Verify status is 422 Unprocessable Entity
        assert response.status_code == 422
