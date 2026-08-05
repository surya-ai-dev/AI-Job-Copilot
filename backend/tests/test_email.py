# backend/tests/test_email.py
# API Integration tests verifying email generation from parsing targets, drafts updates, and OAuth callbacks

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from backend.app.email.models.email_model import EmailDraftModel
from backend.tests.helpers import get_auth_headers
from backend.tests.constants import TEST_EMAIL, MOCK_USER_ID, MOCK_DRAFT_ID, MOCK_ANALYSIS_ID, MOCK_OPTIMIZATION_ID

@pytest.mark.asyncio
async def test_generate_email_success(async_client: AsyncClient, mock_user_record):
    """Test standard outreach email generation passes using mock parsed components."""
    from backend.app.jobs.models.analysis_model import JobAnalysisModel
    from backend.app.resume.models.optimization_model import ResumeOptimizationModel
    from unittest.mock import MagicMock

    headers = get_auth_headers(TEST_EMAIL)
    payload = {
        "job_analysis_id": str(MOCK_ANALYSIS_ID),
        "resume_optimization_id": str(MOCK_OPTIMIZATION_ID)
    }

    mock_analysis_repo = MagicMock()
    mock_analysis_repo.get_by_id = AsyncMock(return_value=JobAnalysisModel(
        id=MOCK_ANALYSIS_ID,
        user_id=MOCK_USER_ID,
        metadata_json={"company_name": "Google", "job_title": "Software Engineer", "recruiter_email": "recruiter@google.com"}
    ))

    mock_opt_repo = MagicMock()
    mock_opt_repo.get_by_id = AsyncMock(return_value=ResumeOptimizationModel(
        id=MOCK_OPTIMIZATION_ID,
        user_id=MOCK_USER_ID,
        optimized_file_path="/app/storage/optimized/dummy.pdf"
    ))

    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.email.api.routes.JobAnalysisRepository", return_value=mock_analysis_repo), \
         patch("backend.app.email.api.routes.ResumeOptimizationRepository", return_value=mock_opt_repo), \
         patch("backend.app.email.services.email_service.EmailOutreachService.generate_outreach_email", new_callable=AsyncMock) as mock_service_generate:
        
        mock_user_get.return_value = mock_user_record
        mock_service_generate.return_value = EmailDraftModel(
            id=MOCK_DRAFT_ID,
            user_id=MOCK_USER_ID,
            recipient_email="recruiter@hiring.com",
            recipient_name="John Doe",
            subject="Application for Python Developer - Surya Charan",
            body="Hello John, I am writing to express my interest...",
            attachment_path=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # response = await async_client.post("/api/v1/email/generate", json=payload, headers=headers)
        response = await async_client.post("/api/v1/email/generate", json=payload, headers=headers)

        print(response.status_code)
        print(response.json())

        assert response.status_code == 201
                
        # Verify status is 201 Created
        # assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(MOCK_DRAFT_ID)
        assert data["recipient_email"] == "recruiter@hiring.com"
        assert data["subject"] == "Application for Python Developer - Surya Charan"
