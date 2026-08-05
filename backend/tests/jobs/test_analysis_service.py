# backend/tests/jobs/test_analysis_service.py
# Unit tests verifying job analysis engine and semantic parser operations

import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from backend.app.jobs.services.analysis_service import JobAnalysisService
from backend.app.shared.exceptions import NotFoundException

@pytest.mark.asyncio
async def test_analyze_job_success():
    # Arrange

    user_id = uuid.uuid4()
    job_id = uuid.uuid4()

    mock_job_repo = MagicMock()
    mock_job_repo.get_by_id = AsyncMock(
        return_value=MagicMock(
            id=job_id,
            user_id=user_id,
            description="We need a Python developer with FastAPI experience. Senior level."
        )
    )

    mock_analysis_repo = MagicMock()
    mock_analysis_repo.get_by_job_id = AsyncMock(return_value=None)
    mock_analysis_repo.create_analysis = AsyncMock(
        return_value=MagicMock(
            id=uuid.uuid4(),
            confidence_score=0.95
        )
    )

    service = JobAnalysisService(mock_analysis_repo, mock_job_repo)

    # Act
    db_analysis = await service.analyze_job(user_id, job_id)

    # Assert
    assert db_analysis is not None
    mock_job_repo.get_by_id.assert_called_once_with(job_id)
    mock_analysis_repo.create_analysis.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_job_not_found():
    # Arrange
    mock_job_repo = MagicMock()
    mock_job_repo.get_by_id = AsyncMock(return_value=None)
    mock_analysis_repo = MagicMock()

    service = JobAnalysisService(mock_analysis_repo, mock_job_repo)

    # Act & Assert: Expect not found exception
    with pytest.raises(NotFoundException) as exc_info:
        await service.analyze_job(uuid.uuid4(), uuid.uuid4())
        
    assert exc_info.value.code == "JOB_NOT_FOUND"
    mock_analysis_repo.create_analysis.assert_not_called()
