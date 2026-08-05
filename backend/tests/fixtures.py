# backend/tests/fixtures.py
# Pytest modular reusable fixtures for SQLAlchemy database sessions, mock repositories, and server boundaries

import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.auth.models.user_model import UserModel
from backend.tests.constants import TEST_EMAIL, TEST_FIRST_NAME, TEST_LAST_NAME, MOCK_USER_ID

@pytest.fixture
def mock_db_session() -> MagicMock:
    """Fixture yielding a mocked SQLAlchemy AsyncSession database connection."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session

@pytest.fixture
def mock_user_record() -> UserModel:
    """Fixture returning a mock database UserModel instance."""
    from datetime import datetime
    return UserModel(
        id=MOCK_USER_ID,
        email=TEST_EMAIL,
        hashed_password="$bcrypt$v=2$r=12$mockhashvalueplaceholderpassword",
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        is_deleted=False,
        created_at=datetime.utcnow()
    )
