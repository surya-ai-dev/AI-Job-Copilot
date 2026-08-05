# backend/tests/resume/test_optimization_service.py
# Unit tests verifying resume optimization loops and quality evaluations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from backend.app.resume.services.optimization_service import ResumeOptimizationService
from backend.app.shared.exceptions import NotFoundException

@pytest.mark.asyncio
async def test_optimize_resume_success():
    # Arrange

    user_id = uuid.uuid4()
    job_analysis_id = uuid.uuid4()

    # Optimization Repository
    mock_opt_repo = MagicMock()
    mock_opt_repo.create_optimization = AsyncMock(
        return_value=MagicMock(
            id=uuid.uuid4(),
            match_score=95,
            ats_score=92
        )
    )

    # Resume Repository
    mock_resume_repo = MagicMock()
    mock_resume_repo.get_active_by_user = AsyncMock(
        return_value=MagicMock(
            id=uuid.uuid4(),
            user_id=user_id,
            file_path="/mock/resume.docx",
            parsed_skills=[
                "Python",
                "FastAPI",
                "PostgreSQL"
            ]
        )
    )

    mock_resume_repo.get_latest_version_number = AsyncMock(return_value=1)
    mock_resume_repo.create_version = AsyncMock()

    # Job Analysis Repository
    mock_analysis_repo = MagicMock()
    mock_analysis_repo.get_by_id = AsyncMock(
        return_value=MagicMock(
            id=job_analysis_id,
            user_id=user_id,
            skills_json=[
                {
                    "name": "Python",
                    "category": "Programming Languages",
                    "importance": "Mandatory"
                },
                {
                    "name": "FastAPI",
                    "category": "Frameworks",
                    "importance": "Mandatory"
                }
            ],
            metadata_json={
                "company_name": "Google",
                "job_title": "Engineer"
            }
        )
    )

    # Service
    service = ResumeOptimizationService(
        mock_opt_repo,
        mock_resume_repo,
        mock_analysis_repo,
        storage_path="/mock_storage"
    )

    # Prevent actual file creation
    service._compile_optimized_resume_file = MagicMock(
        return_value="/mock_storage/user_Role_Company.pdf"
    )

    # Act
    db_opt = await service.optimize_resume(
        user_id,
        job_analysis_id
    )

    # Assert
    assert db_opt is not None

    mock_resume_repo.get_active_by_user.assert_called_once_with(user_id)
    mock_analysis_repo.get_by_id.assert_called_once_with(job_analysis_id)
    mock_opt_repo.create_optimization.assert_called_once()
    mock_resume_repo.create_version.assert_called_once()