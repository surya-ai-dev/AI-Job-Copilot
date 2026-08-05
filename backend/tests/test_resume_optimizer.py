# backend/tests/test_resume_optimizer.py
# Production-ready test suite verifying AI resume optimization iterations, score calculations, report generation, and downloads

import pytest
import uuid
from unittest.mock import AsyncMock, patch, mock_open
from datetime import datetime
from httpx import AsyncClient
from backend.app.resume.models.optimization_model import ResumeOptimizationModel
from backend.tests.helpers import get_auth_headers
from backend.tests.constants import TEST_EMAIL, MOCK_USER_ID, MOCK_RESUME_ID, MOCK_ANALYSIS_ID, MOCK_OPTIMIZATION_ID

@pytest.mark.asyncio
async def test_optimize_resume_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test triggering AI resume optimization logic returns matched indicators."""
    headers = get_auth_headers(TEST_EMAIL)
    payload = {"job_analysis_id": str(MOCK_ANALYSIS_ID)}

    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.resume.services.optimization_service.ResumeOptimizationService.optimize_resume", new_callable=AsyncMock) as mock_service_optimize:
        
        mock_user_get.return_value = mock_user_record
        mock_service_optimize.return_value = ResumeOptimizationModel(
            id=MOCK_OPTIMIZATION_ID,
            resume_id=MOCK_RESUME_ID,
            job_analysis_id=MOCK_ANALYSIS_ID,
            user_id=MOCK_USER_ID,
            match_score=85,
            ats_score=90,
            optimized_file_path="/app/storage/optimized/dummy.pdf",
            match_details_json={"resume_id": MOCK_RESUME_ID, "job_analysis_id": MOCK_ANALYSIS_ID, "match_score": 85, "skills_match_score": 85, "experience_match_score": 90, "gap_skills": []},
            ats_evaluation_json={"score": 90, "explanation": "Good keyword coverage.", "keyword_coverage_percent": 85, "readability_index": 7.5},
            recommendations_json=[],
            optimized_summary="Experienced Python engineer specializing in FastAPI and Docker deployments.",
            optimized_skills_json=["Python", "FastAPI", "Docker", "PostgreSQL"],
            created_at=datetime.utcnow()
        )

        response = await async_client.post("/api/v1/resume/optimize", json=payload, headers=headers)
        
        # Verify status is 201 Created
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(MOCK_OPTIMIZATION_ID)
        assert data["match_score"] == 85
        assert data["ats_score"] == 90

@pytest.mark.asyncio
async def test_get_optimization_details_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test retrieving optimization record by ID."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.resume.repository.optimization_repository.ResumeOptimizationRepository.get_by_id", new_callable=AsyncMock) as mock_repo_get:
        
        mock_user_get.return_value = mock_user_record
        mock_repo_get.return_value = ResumeOptimizationModel(
            id=MOCK_OPTIMIZATION_ID,
            resume_id=MOCK_RESUME_ID,
            job_analysis_id=MOCK_ANALYSIS_ID,
            user_id=MOCK_USER_ID,
            match_score=88,
            ats_score=90,
            optimized_file_path="/app/storage/optimized/dummy.pdf",
            match_details_json={"resume_id": MOCK_RESUME_ID, "job_analysis_id": MOCK_ANALYSIS_ID, "match_score": 88, "skills_match_score": 88, "experience_match_score": 90, "gap_skills": []},
            ats_evaluation_json={"score": 90, "explanation": "Good keyword coverage.", "keyword_coverage_percent": 85, "readability_index": 7.5},
            recommendations_json=[],
            optimized_summary="Expert Python developer summary",
            optimized_skills_json=["Python", "FastAPI"],
            created_at=datetime.utcnow()
        )

        response = await async_client.get(f"/api/v1/resume/optimize/{MOCK_OPTIMIZATION_ID}", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(MOCK_OPTIMIZATION_ID)
        assert data["match_score"] == 88

@pytest.mark.asyncio
async def test_list_optimizations_history_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test retrieving previous optimizations history list."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.resume.repository.optimization_repository.ResumeOptimizationRepository.list_optimizations", new_callable=AsyncMock) as mock_list:
        
        mock_user_get.return_value = mock_user_record
        mock_list.return_value = [
            ResumeOptimizationModel(
                id=MOCK_OPTIMIZATION_ID,
                resume_id=MOCK_RESUME_ID,
                job_analysis_id=MOCK_ANALYSIS_ID,
                user_id=MOCK_USER_ID,
                match_score=82,
                ats_score=90,
                optimized_file_path="/app/storage/optimized/dummy.pdf",
                match_details_json={"resume_id": MOCK_RESUME_ID, "job_analysis_id": MOCK_ANALYSIS_ID, "match_score": 82, "skills_match_score": 82, "experience_match_score": 90, "gap_skills": []},
                ats_evaluation_json={"score": 90, "explanation": "Good keyword coverage.", "keyword_coverage_percent": 85, "readability_index": 7.5},
                recommendations_json=[],
                optimized_summary="Expert Python developer summary",
                optimized_skills_json=["Python", "FastAPI"],
                created_at=datetime.utcnow()
            )
        ]

        response = await async_client.get("/api/v1/resume/optimize/history", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["match_score"] == 82

@pytest.mark.asyncio
async def test_generate_optimization_report_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test generating a structured optimization audit report."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.resume.services.optimization_service.ResumeOptimizationService.get_optimization_report", new_callable=AsyncMock) as mock_report:
        
        mock_user_get.return_value = mock_user_record
        mock_report.return_value = {
            "match_score": 85,
            "ats_score": 90,
            "ats_evaluation": {"score": 90, "missing_keywords": ["Kubernetes"], "formatting_issues": []},
            "recommendations": []
        }

        response = await async_client.get(f"/api/v1/resume/optimize/report/{MOCK_OPTIMIZATION_ID}", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert data["match_score"] == 85
        assert data["ats_evaluation"]["missing_keywords"] == ["Kubernetes"]

@pytest.mark.asyncio
async def test_download_optimized_resume_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test downloading the generated optimized PDF resume."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.resume.services.optimization_service.ResumeOptimizationService.download_optimized_resume", new_callable=AsyncMock) as mock_download, \
         patch("backend.app.resume.api.optimization_routes.FileResponse") as mock_fileresponse:
        
        mock_user_get.return_value = mock_user_record
        mock_download.return_value = ("/app/storage/optimized/dummy.pdf", "optimized_resume.pdf")

        # Fake response mock
        mock_fileresponse.return_value = b"%PDF mock optimized content%"

        response = await async_client.get(f"/api/v1/resume/optimize/download/{MOCK_OPTIMIZATION_ID}", headers=auth_headers)
        
        # Verify status is 200 OK
        assert response.status_code == 200
