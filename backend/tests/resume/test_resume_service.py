# backend/tests/resume/test_resume_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid

from backend.app.resume.services.resume_service import ResumeService
from backend.app.shared.exceptions import ValidationException


@pytest.mark.asyncio
async def test_upload_master_resume_success(tmp_path):
    # Arrange
    mock_repo = MagicMock()
    mock_repo.get_active_by_user = AsyncMock(return_value=None)
    mock_repo.create_resume = AsyncMock(
        return_value=MagicMock(
            id=uuid.uuid4(),
            file_name="resume.pdf"
        )
    )

    service = ResumeService(
        mock_repo,
        storage_path=str(tmp_path)
    )

    service._write_file_to_disk = AsyncMock()

    user_id = uuid.uuid4()

    db_resume = await service.upload_master_resume(
        user_id=user_id,
        file_name="resume.pdf",
        file_size=5000,
        content_type="application/pdf",
        file_content=b"PDF-mock-content"
    )

    assert db_resume is not None
    mock_repo.get_active_by_user.assert_called_once_with(user_id)
    service._write_file_to_disk.assert_called_once()
    mock_repo.create_resume.assert_called_once()


@pytest.mark.asyncio
async def test_upload_master_resume_size_exceeded(tmp_path):
    # Arrange
    mock_repo = MagicMock()

    service = ResumeService(
        mock_repo,
        storage_path=str(tmp_path)
    )

    with pytest.raises(ValidationException) as exc_info:
        await service.upload_master_resume(
            user_id=uuid.uuid4(),
            file_name="large.docx",
            file_size=15 * 1024 * 1024,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            file_content=b"content"
        )

    assert "exceeds maximum limit" in exc_info.value.message
    mock_repo.create_resume.assert_not_called()