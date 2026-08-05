# backend/tests/test_job_analysis.py
# Production-ready test suite verifying AI Job Analysis triggers, LLM mock response extraction, and DB record queries

import pytest
import uuid
from unittest.mock import AsyncMock, patch
from datetime import datetime
from httpx import AsyncClient
from backend.app.jobs.models.analysis_model import JobAnalysisModel
from backend.tests.helpers import get_auth_headers
from backend.tests.constants import TEST_EMAIL, MOCK_USER_ID, MOCK_JOB_ID, MOCK_ANALYSIS_ID

@pytest.mark.asyncio
async def test_analyze_job_with_mocked_llm_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test running AI job analysis, verifying skills, experience, and education extraction under mocked LLM."""
    payload = {"job_id": str(MOCK_JOB_ID)}

    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.jobs.services.analysis_service.JobAnalysisService.analyze_job", new_callable=AsyncMock) as mock_service_analyze:
        
        mock_user_get.return_value = mock_user_record
        mock_service_analyze.return_value = JobAnalysisModel(
            id=MOCK_ANALYSIS_ID,
            job_id=MOCK_JOB_ID,
            user_id=MOCK_USER_ID,
            confidence_score=0.98,
            llm_provider="gemini",
            prompt_version="1.0.0",
            processing_time_ms=450,
            metadata_json={"seniority": "mid", "employment_type": "full-time", "education_requirements": "BS", "certifications": []},
            skills_json=[{"name": "Python", "category": "Programming", "importance": "high"}],
            ats_keywords_json=[{"word": "FastAPI", "category": "framework"}],
            responsibilities_json=["Build FastAPI endpoints"],
            qualifications_json=["Bachelor's in CS", "3+ years Python experience"],
            created_at=datetime.utcnow()
        )

        response = await async_client.post("/api/v1/jobs/analysis/analyze", json=payload, headers=auth_headers)
        
        # Verify response status is 201 Created
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(MOCK_ANALYSIS_ID)
        assert data["confidence_score"] == 0.98
        assert data["llm_provider"] == "gemini"
        
        # Verify details extraction fields
        assert data["skills_json"][0]["name"] == "Python"
        assert "Bachelor's in CS" in data["qualifications_json"]
        assert "3+ years Python experience" in data["qualifications_json"]

@pytest.mark.asyncio
async def test_get_analysis_details_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test retrieving structured analysis details by ID."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.jobs.repository.analysis_repository.JobAnalysisRepository.get_by_id", new_callable=AsyncMock) as mock_repo_get:
        
        mock_user_get.return_value = mock_user_record
        mock_repo_get.return_value = JobAnalysisModel(
            id=MOCK_ANALYSIS_ID,
            job_id=MOCK_JOB_ID,
            user_id=MOCK_USER_ID,
            confidence_score=0.90,
            llm_provider="gemini",
            prompt_version="1.0.0",
            processing_time_ms=450,
            metadata_json={"seniority": "mid", "employment_type": "full-time", "education_requirements": "BS", "certifications": []},
            skills_json=[{"name": "Python", "category": "Programming", "importance": "high"}],
            ats_keywords_json=[{"word": "FastAPI", "category": "framework"}],
            responsibilities_json=["Build FastAPI endpoints"],
            qualifications_json=["Bachelor's in CS", "3+ years Python experience"],
            created_at=datetime.utcnow()
        )

        response = await async_client.get(f"/api/v1/jobs/analysis/{MOCK_ANALYSIS_ID}", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(MOCK_ANALYSIS_ID)
        assert data["confidence_score"] == 0.90

@pytest.mark.asyncio
async def test_get_analysis_by_job_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test retrieving structured analysis details associated with a specific job ID."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.jobs.repository.analysis_repository.JobAnalysisRepository.get_by_job_id", new_callable=AsyncMock) as mock_repo_get:
        
        mock_user_get.return_value = mock_user_record
        mock_repo_get.return_value = JobAnalysisModel(
            id=MOCK_ANALYSIS_ID,
            job_id=MOCK_JOB_ID,
            user_id=MOCK_USER_ID,
            confidence_score=0.92,
            llm_provider="gemini",
            prompt_version="1.0.0",
            processing_time_ms=450,
            metadata_json={"seniority": "mid", "employment_type": "full-time", "education_requirements": "BS", "certifications": []},
            skills_json=[{"name": "Python", "category": "Programming", "importance": "high"}],
            ats_keywords_json=[{"word": "FastAPI", "category": "framework"}],
            responsibilities_json=["Build FastAPI endpoints"],
            qualifications_json=["Bachelor's in CS", "3+ years Python experience"],
            created_at=datetime.utcnow()
        )

        response = await async_client.get(f"/api/v1/jobs/analysis/by-job/{MOCK_JOB_ID}", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == str(MOCK_JOB_ID)

@pytest.mark.asyncio
async def test_get_analysis_not_found_fails(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test retrieving a non-existent analysis record returns 404."""
    target_id = uuid.uuid4()

    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.jobs.repository.analysis_repository.JobAnalysisRepository.get_by_id", new_callable=AsyncMock) as mock_repo_get:
        
        mock_user_get.return_value = mock_user_record
        mock_repo_get.return_value = None

        response = await async_client.get(f"/api/v1/jobs/analysis/{target_id}", headers=auth_headers)
        
        # Verify status is 404 Not Found
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

@pytest.mark.asyncio
async def test_delete_analysis_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test deleting an analysis record from DB."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.jobs.repository.analysis_repository.JobAnalysisRepository.get_by_id", new_callable=AsyncMock) as mock_repo_get, \
         patch("backend.app.jobs.repository.analysis_repository.JobAnalysisRepository.delete_analysis", new_callable=AsyncMock) as mock_delete:
        
        mock_user_get.return_value = mock_user_record
        mock_repo_get.return_value = JobAnalysisModel(id=MOCK_ANALYSIS_ID, user_id=MOCK_USER_ID)
        mock_delete.return_value = None

        response = await async_client.delete(f"/api/v1/jobs/analysis/{MOCK_ANALYSIS_ID}", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        mock_delete.assert_called_once()
