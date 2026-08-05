# backend/tests/test_auth.py
# Production-ready test suite verifying registration, oauth2 token login, verification, and logout scenarios

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from httpx import AsyncClient
from backend.app.auth.models.user_model import UserModel, RefreshTokenModel
from backend.tests.constants import TEST_EMAIL, TEST_PASSWORD, TEST_FIRST_NAME, TEST_LAST_NAME, MOCK_USER_ID

@pytest.mark.asyncio
async def test_register_user_success(async_client: AsyncClient):
    """Test registering a new user succeeds with valid credentials."""
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "first_name": TEST_FIRST_NAME,
        "last_name": TEST_LAST_NAME
    }

    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(return_value=UserModel(
        id=MOCK_USER_ID,
        email=TEST_EMAIL,
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        created_at=datetime.utcnow()
    ))

    with patch("backend.app.auth.api.routes.UserRepository", return_value=mock_repo):
        response = await async_client.post("/api/v1/auth/register", json=payload)
        
        # Verify response status is 201 Created
        assert response.status_code == 201
        data = response.json()
        # Verify returned JSON fields match payload
        assert data["email"] == TEST_EMAIL
        assert data["first_name"] == TEST_FIRST_NAME
        assert data["last_name"] == TEST_LAST_NAME

@pytest.mark.asyncio
async def test_register_user_duplicate_email_fails(async_client: AsyncClient):
    """Test registering an existing email fails validation checks."""
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "first_name": TEST_FIRST_NAME,
        "last_name": TEST_LAST_NAME
    }

    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=UserModel(
        id=MOCK_USER_ID,
        email=TEST_EMAIL,
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        created_at=datetime.utcnow()
    ))

    with patch("backend.app.auth.api.routes.UserRepository", return_value=mock_repo):
        response = await async_client.post("/api/v1/auth/register", json=payload)
        
        # Verify status is 400 Bad Request
        assert response.status_code == 400
        data = response.json()
        # Verify error message detail
        assert "already registered" in data["detail"]

@pytest.mark.asyncio
async def test_login_oauth2_success(async_client: AsyncClient, test_user):
    """Test user can retrieve valid access & refresh tokens on correct login credentials."""
    login_data = {
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD
    }

    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=UserModel(
        id=MOCK_USER_ID,
        email=TEST_EMAIL,
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        hashed_password="hashed_pw_placeholder",
        is_deleted=False,
        created_at=datetime.utcnow()
    ))
    mock_repo.save_refresh_token = AsyncMock()

    with patch("backend.app.auth.api.routes.UserRepository", return_value=mock_repo), \
         patch("backend.app.core.security.verify_password", return_value=True):
        
        response = await async_client.post("/api/v1/auth/token", data=login_data)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        # Verify token payloads are returned
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_oauth2_invalid_credentials_fails(async_client: AsyncClient):
    """Test login fails when user input password verification fails."""
    login_data = {
        "username": TEST_EMAIL,
        "password": "wrong_password"
    }

    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=UserModel(
        id=MOCK_USER_ID,
        email=TEST_EMAIL,
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        hashed_password="hashed",
        created_at=datetime.utcnow()
    ))

    with patch("backend.app.auth.api.routes.UserRepository", return_value=mock_repo), \
         patch("backend.app.core.security.verify_password", return_value=False):
        
        response = await async_client.post("/api/v1/auth/token", data=login_data)
        
        # Verify status is 401 Unauthorized
        assert response.status_code == 401
        data = response.json()
        assert "Invalid email or password" in data["detail"]

@pytest.mark.asyncio
async def test_unauthorized_request_profile_fails(async_client: AsyncClient):
    """Test requests without access token headers are blocked."""
    response = await async_client.get("/api/v1/users/me")
    
    # Verify status is 401 Unauthorized
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_jwt_verification_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test request passes with active authorization header tokens."""
    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=mock_user_record)

    with patch("backend.app.auth.api.routes.UserRepository", return_value=mock_repo):
        response = await async_client.get("/api/v1/users/me", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL

@pytest.mark.asyncio
async def test_expired_jwt_token_fails(async_client: AsyncClient):
    """Test expired or forged authorization signatures are blocked."""
    headers = {"Authorization": "Bearer invalid.expired.token.signature"}
    response = await async_client.get("/api/v1/users/me", headers=headers)
    
    # Verify status is 401 Unauthorized
    assert response.status_code == 401
    data = response.json()
    assert "Signature verification failed" in data["detail"]

@pytest.mark.asyncio
async def test_refresh_token_success(async_client: AsyncClient):
    """Test generating a new access token using a valid refresh token."""
    payload = {"refresh_token": "valid_refresh_token"}

    mock_repo = MagicMock()
    mock_repo.get_refresh_token = AsyncMock(return_value=RefreshTokenModel(
        token="valid_refresh_token",
        user_id=MOCK_USER_ID,
        is_revoked=False,
        expires_at=datetime.utcnow()
    ))

    with patch("backend.app.core.security.verify_token", return_value=TEST_EMAIL), \
         patch("backend.app.auth.api.routes.UserRepository", return_value=mock_repo):
        
        # Patch expires_at checking logic bypass
        with patch("backend.app.auth.services.auth_service.datetime") as mock_date:
            mock_date.utcnow.return_value = datetime.min
            
            response = await async_client.post("/api/v1/auth/refresh", json=payload)
            
            # Verify status is 200 OK
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data

@pytest.mark.asyncio
async def test_logout_user_success(async_client: AsyncClient):
    """Test revoking a refresh token on user logout."""
    payload = {"refresh_token": "token_to_revoke"}

    mock_repo = MagicMock()
    mock_repo.get_refresh_token = AsyncMock(return_value=RefreshTokenModel(token="token_to_revoke"))
    mock_repo.revoke_refresh_token = AsyncMock(return_value=None)
    
    with patch("backend.app.auth.api.routes.UserRepository", return_value=mock_repo):
        response = await async_client.post("/api/v1/auth/logout", json=payload)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert "Logged out successfully" in data["message"]
        mock_repo.revoke_refresh_token.assert_called_once()
