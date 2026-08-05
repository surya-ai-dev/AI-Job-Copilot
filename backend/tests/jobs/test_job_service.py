# backend/tests/jobs/test_job_service.py
# Unit tests verifying job parser and ingestion service operations

import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from backend.app.jobs.services.job_service import JobService
from backend.app.shared.exceptions import ValidationException

@pytest.mark.asyncio
async def test_ingest_job_from_text_success():
    # Arrange: Mock Repository
    mock_repo = MagicMock()
    mock_repo.create_job = AsyncMock(return_value=MagicMock(id=uuid.uuid4(), company_name="Google"))

    service = JobService(mock_repo)
    user_id = uuid.uuid4()
    raw_text = "Company: Google\nRole: Engineer\nRequired skills: Python, SQL"

    # Act
    db_job = await service.ingest_job_from_text(user_id, raw_text)

    # Assert
    assert db_job is not None
    mock_repo.create_job.assert_called_once()


@pytest.mark.asyncio
async def test_ingest_job_from_text_empty():
    # Arrange
    mock_repo = MagicMock()
    service = JobService(mock_repo)

    # Act & Assert: Expect validation error on empty paste
    with pytest.raises(ValidationException) as exc_info:
        await service.ingest_job_from_text(uuid.uuid4(), "   ")
        
    assert "must not be empty" in exc_info.value.message
    mock_repo.create_job.assert_not_called()
