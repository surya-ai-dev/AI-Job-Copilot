# backend/tests/test_jobs.py
# Production-ready test suite verifying job descriptions parsing, retrieval, deletions, and listing behaviors

import pytest
import uuid
from unittest.mock import AsyncMock, patch
from datetime import datetime
from httpx import AsyncClient
from backend.app.jobs.models.job_model import JobModel
from backend.tests.constants import TEST_EMAIL, MOCK_USER_ID, MOCK_JOB_ID, MOCK_JOB_TEXT

@pytest.mark.asyncio
async def test_parse_job_text_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test parsing pasted plain-text job description successfully."""
    payload = {"text": MOCK_JOB_TEXT}

    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.jobs.repository.job_repository.JobRepository.create_job", new_callable=AsyncMock) as mock_create:
        
        mock_user_get.return_value = mock_user_record
        mock_create.return_value = JobModel(
            id=MOCK_JOB_ID,
            user_id=MOCK_USER_ID,
            source_type="text",
            company_name="Google",
            job_title="Python Engineer",
            description=MOCK_JOB_TEXT,
            raw_content=MOCK_JOB_TEXT,
            created_at=datetime.utcnow()
        )

        response = await async_client.post("/api/v1/jobs/parse-text", json=payload, headers=auth_headers)
        
        # Verify response status is 201 Created
        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == "Google"
        assert data["job_title"] == "Python Engineer"
        assert data["description"] == MOCK_JOB_TEXT

@pytest.mark.asyncio
async def test_parse_job_invalid_payload_fails(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test job parsing fails on invalid body payloads."""
    payload = {"invalid_key": "some text content"}

    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get:
        mock_user_get.return_value = mock_user_record

        response = await async_client.post("/api/v1/jobs/parse-text", json=payload, headers=auth_headers)
        
        # Verify status is 422 Unprocessable Entity for schema validation failures
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_job_details_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test retrieving parsed job posting details by ID."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.jobs.repository.job_repository.JobRepository.get_by_id", new_callable=AsyncMock) as mock_job_get:
        
        mock_user_get.return_value = mock_user_record
        mock_job_get.return_value = JobModel(
            id=MOCK_JOB_ID,
            user_id=MOCK_USER_ID,
            source_type="text",
            company_name="Meta",
            job_title="Software Architect",
            description="Requirements analysis details",
            raw_content="Requirements analysis details",
            created_at=datetime.utcnow()
        )

        response = await async_client.get(f"/api/v1/jobs/{MOCK_JOB_ID}", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == "Meta"
        assert data["job_title"] == "Software Architect"

@pytest.mark.asyncio
async def test_get_job_details_not_found(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test retrieving job details returns 404 when the ID is missing."""
    target_id = uuid.uuid4()
    
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.jobs.repository.job_repository.JobRepository.get_by_id", new_callable=AsyncMock) as mock_job_get:
        
        mock_user_get.return_value = mock_user_record
        mock_job_get.return_value = None

        response = await async_client.get(f"/api/v1/jobs/{target_id}", headers=auth_headers)
        
        # Verify status is 404 Not Found
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

@pytest.mark.asyncio
async def test_list_user_jobs_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test listing all job postings parsed by the user."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.jobs.repository.job_repository.JobRepository.list_jobs", new_callable=AsyncMock) as mock_list:
        
        mock_user_get.return_value = mock_user_record
        mock_list.return_value = [
            JobModel(
                id=MOCK_JOB_ID,
                user_id=MOCK_USER_ID,
                source_type="text",
                company_name="Apple",
                job_title="iOS Developer",
                description="Swift development details",
                raw_content="Swift development details",
                created_at=datetime.utcnow()
            )
        ]

        response = await async_client.get("/api/v1/jobs", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["company_name"] == "Apple"

@pytest.mark.asyncio
async def test_delete_job_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test deleting a parsed job description from logs."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.jobs.repository.job_repository.JobRepository.get_by_id", new_callable=AsyncMock) as mock_job_get, \
         patch("backend.app.jobs.repository.job_repository.JobRepository.delete_job", new_callable=AsyncMock) as mock_delete:
        
        mock_user_get.return_value = mock_user_record
        mock_job_get.return_value = JobModel(id=MOCK_JOB_ID, user_id=MOCK_USER_ID)
        mock_delete.return_value = None

        response = await async_client.delete(f"/api/v1/jobs/{MOCK_JOB_ID}", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        mock_delete.assert_called_once()
