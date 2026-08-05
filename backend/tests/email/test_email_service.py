# backend/tests/email/test_email_service.py
# Unit tests verifying email outreach service operations

import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from datetime import datetime, timedelta
from backend.app.email.services.email_service import EmailOutreachService
from backend.app.shared.exceptions import ValidationException, AuthenticationException

@pytest.mark.asyncio
async def test_generate_outreach_email_success():
    # Arrange: Mock Repository
    mock_repo = MagicMock()
    mock_repo.create_draft = AsyncMock(
        return_value=MagicMock(id=uuid.uuid4(), subject="Application")
    )

    service = EmailOutreachService(mock_repo)
    user_id = uuid.uuid4()

    # Act
    db_draft = await service.generate_outreach_email(
        user_id=user_id,
        job_analysis_company="Google",
        job_analysis_role="Engineer",
        optimized_resume_path="/mock/resume.pdf"
    )

    # Assert
    assert db_draft is not None
    mock_repo.create_draft.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_disconnected_gmail():
    # Arrange
    mock_repo = MagicMock()

    user_id = uuid.uuid4()
    draft_id = uuid.uuid4()

    mock_draft = MagicMock()
    mock_draft.user_id = user_id

    mock_repo.get_draft = AsyncMock(return_value=mock_draft)
    mock_repo.get_gmail_token = AsyncMock(return_value=None)

    service = EmailOutreachService(mock_repo)

    # Act + Assert
    with pytest.raises(AuthenticationException) as exc_info:
        await service.send_outreach_email(user_id, draft_id)

    assert exc_info.value.code == "GMAIL_NOT_CONNECTED"

    mock_repo.create_history.assert_not_called()