# backend/tests/test_dashboard.py
# Production-ready test suite verifying dashboard stats aggregates, CRM logs, and application searches

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from backend.app.dashboard.models.application_model import JobApplicationModel
from backend.tests.helpers import get_auth_headers
from backend.tests.constants import TEST_EMAIL, MOCK_USER_ID, MOCK_APPLICATION_ID, MOCK_JOB_ID, MOCK_RESUME_ID, MOCK_OPTIMIZATION_ID

@pytest.mark.asyncio
async def test_get_dashboard_summary_stats(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test retrieving active dashboard aggregate metrics counts."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.dashboard.services.application_service.ApplicationManagementService.get_dashboard_statistics", new_callable=AsyncMock) as mock_stats:
        
        mock_user_get.return_value = mock_user_record
        mock_stats.return_value = {
            "total_applications": 25,
            "applications_today": 3,
            "active_drafts_count": 8,
            "recent_resumes_count": 4,
            "recent_emails_count": 12,
            "recent_applications": []
        }

        response = await async_client.get("/api/v1/dashboard/summary", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        
        # Verify correctness of stats counts
        assert data["total_applications"] == 25
        assert data["applications_today"] == 3
        assert data["active_drafts_count"] == 8
        assert data["recent_resumes_count"] == 4
        assert data["recent_emails_count"] == 12
        assert isinstance(data["recent_applications"], list)

@pytest.mark.asyncio
async def test_list_applications_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test retrieving all tracked applications."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.dashboard.repository.application_repository.ApplicationRepository.list_applications", new_callable=AsyncMock) as mock_list:
        
        mock_user_get.return_value = mock_user_record
        mock_list.return_value = [
            JobApplicationModel(
                id=MOCK_APPLICATION_ID,
                user_id=MOCK_USER_ID,
                job_id=MOCK_JOB_ID,
                resume_id=MOCK_RESUME_ID,
                resume_version_id=MOCK_OPTIMIZATION_ID,
                company_name="Amazon",
                job_title="DevOps Engineer",
                job_url="https://amazon.jobs/123",
                applied_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
        ]

        response = await async_client.get("/api/v1/dashboard/applications", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["company_name"] == "Amazon"
        assert data[0]["job_title"] == "DevOps Engineer"

@pytest.mark.asyncio
async def test_search_applications_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test searching applications history by keyword queries."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.dashboard.repository.application_repository.ApplicationRepository.search_applications", new_callable=AsyncMock) as mock_search:
        
        mock_user_get.return_value = mock_user_record
        mock_search.return_value = [
            JobApplicationModel(
                id=MOCK_APPLICATION_ID,
                user_id=MOCK_USER_ID,
                job_id=MOCK_JOB_ID,
                resume_id=MOCK_RESUME_ID,
                resume_version_id=MOCK_OPTIMIZATION_ID,
                company_name="Netflix",
                job_title="Senior Engineer",
                applied_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
        ]

        response = await async_client.get("/api/v1/dashboard/applications/search?query=Netflix", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["company_name"] == "Netflix"
