# backend/tests/dashboard/test_application_service.py
# Unit tests verifying dashboard metrics compilation and search service operations

import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from backend.app.dashboard.services.application_service import ApplicationManagementService
from backend.app.shared.exceptions import NotFoundException

@pytest.mark.asyncio
async def test_get_dashboard_statistics_success():
    # Arrange: Mock Repositories
    mock_app_repo = MagicMock()
    mock_app_repo.get_summary_stats = AsyncMock(return_value=(10, 2))
    mock_app_repo.list_applications = AsyncMock(return_value=[])

    mock_resume_repo = MagicMock()
    mock_resume_repo.list_user_versions = AsyncMock(return_value=[])

    mock_opt_repo = MagicMock()
    mock_email_repo = MagicMock()
    mock_email_repo.list_drafts = AsyncMock(return_value=[])
    mock_email_repo.list_history = AsyncMock(return_value=[])

    mock_job_repo = MagicMock()

    service = ApplicationManagementService(
        mock_app_repo, mock_resume_repo, mock_opt_repo, mock_email_repo, mock_job_repo
    )
    user_id = uuid.uuid4()

    # Act
    stats = await service.get_dashboard_statistics(user_id)

    # Assert
    assert stats["total_applications"] == 10
    assert stats["applications_today"] == 2
    mock_app_repo.get_summary_stats.assert_called_once_with(user_id)
    mock_email_repo.list_drafts.assert_called_once_with(user_id)
