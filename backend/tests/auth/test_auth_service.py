# backend/tests/auth/test_auth_service.py
# Unit tests verifying authentication service operations with UUID support

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
import uuid
from backend.app.auth.services.auth_service import AuthService
from backend.app.auth.domain.user import User, UserProfile
from backend.app.shared.exceptions import AuthenticationException, NotFoundException
from backend.app.core import security

@pytest.mark.asyncio
async def test_register_user_success():
    # Arrange: Mock UserRepository with UUID
    user_uuid = uuid.uuid4()
    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(return_value=MagicMock(id=user_uuid, email="test@example.com"))

    auth_service = AuthService(mock_repo)
    user_reg = User(
        email="test@example.com",
        hashed_password=security.get_password_hash("password123"),
        first_name="Surya",
        last_name="Charan"
    )

    # Act: Register user
    db_user = await auth_service.register_user(user_reg)

    # Assert
    assert db_user.id == user_uuid
    assert db_user.email == "test@example.com"
    mock_repo.get_by_email.assert_called_once_with("test@example.com")
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_duplicate_email():
    # Arrange
    user_uuid = uuid.uuid4()
    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=MagicMock(id=user_uuid, email="test@example.com"))

    auth_service = AuthService(mock_repo)
    user_reg = User(
        email="test@example.com",
        hashed_password=security.get_password_hash("password123"),
        first_name="Surya",
        last_name="Charan"
    )

    # Act & Assert: Expect duplicate email registration failure exception
    with pytest.raises(AuthenticationException) as exc_info:
        await auth_service.register_user(user_reg)
        
    assert exc_info.value.code == "USER_ALREADY_EXISTS"
    mock_repo.create.assert_not_called()
