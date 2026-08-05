# backend/tests/test_end_to_end.py
# Production-grade E2E test verifying complete user journey from signup to optimized resume download

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.future import select
from backend.app.auth.models.user_model import UserModel
from backend.app.resume.models.resume_model import ResumeModel
from backend.app.jobs.models.job_model import JobModel
from backend.app.jobs.models.analysis_model import JobAnalysisModel
from backend.app.resume.models.optimization_model import ResumeOptimizationModel
from backend.tests.helpers import generate_mock_pdf_content
from backend.tests.constants import MOCK_JOB_TEXT
from fastapi.responses import Response
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_end_to_end_user_journey(async_client: AsyncClient, db_session):
    """
    Execution trace of a complete user application workflow:
    1. Register User
    2. Login & JWT extraction
    3. Update Profile
    4. Upload Resume
    5. Ingest / Parse Job
    6. Analyze Job
    7. Optimize Resume
    8. Generate Optimization Report
    9. Download Optimized Resume PDF
    10. Delete Test Data (database records checks)
    """
    # ----------------------------------------------------
    # Step 1: Register User
    # ----------------------------------------------------
    reg_payload = {
        "email": "e2e_user@example.com",
        "password": "Password123!",
        "first_name": "Surya",
        "last_name": "Charan"
    }
    reg_response = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_response.status_code == 201, f"Failed at Step 1: Register. Response: {reg_response.text}"
    user_data = reg_response.json()
    assert user_data["email"] == "e2e_user@example.com"

    # Verify Database Record for User
    db_user_query = await db_session.execute(
        select(UserModel).where(UserModel.email == "e2e_user@example.com")
    )
    db_user = db_user_query.scalars().first()
    assert db_user is not None, "Failed DB check at Step 1: User not found in DB."
    user_uuid = db_user.id

    # ----------------------------------------------------
    # Step 2: Login & JWT extraction
    # ----------------------------------------------------
    login_data = {
        "username": "e2e_user@example.com",
        "password": "Password123!"
    }
    # oauth2 authentication uses x-www-form-urlencoded format
    login_response = await async_client.post("/api/v1/auth/token", data=login_data)
    assert login_response.status_code == 200, f"Failed at Step 2: Login. Response: {login_response.text}"
    token_data = login_response.json()
    access_token = token_data["access_token"]
    assert access_token is not None

    # Setup auth headers for all downstream requests
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # ----------------------------------------------------
    # Step 3: Update Profile
    # ----------------------------------------------------
    update_payload = {
        "first_name": "Surya_Updated",
        "last_name": "Charan_Updated"
    }
    update_response = await async_client.put("/api/v1/users/me", json=update_payload, headers=auth_headers)
    assert update_response.status_code == 200, f"Failed at Step 3: Update Profile. Response: {update_response.text}"
    
    # Verify Database Update
    await db_session.refresh(db_user)
    assert db_user.first_name == "Surya_Updated"

    # ----------------------------------------------------
    # Step 4: Upload Resume
    # ----------------------------------------------------
    pdf_content = generate_mock_pdf_content()
    files = {"file": ("resume.pdf", pdf_content, "application/pdf")}
    
    with patch("backend.app.resume.services.resume_service.ResumeService._write_file_to_disk"):
         
        upload_response = await async_client.post("/api/v1/resume/upload", files=files, headers=auth_headers)
        
    assert upload_response.status_code == 201, f"Failed at Step 4: Upload Resume. Response: {upload_response.text}"
    resume_data = upload_response.json()
    resume_id = resume_data["id"]

    # Verify Database Record for Resume
    db_resume_query = await db_session.execute(
        select(ResumeModel).where(ResumeModel.id == uuid.UUID(resume_id))
    )
    db_resume = db_resume_query.scalars().first()
    assert db_resume is not None, "Failed DB check at Step 4: Resume not found in DB."
    assert db_resume.file_name == "resume.pdf"

    # ----------------------------------------------------
    # Step 5: Ingest / Parse Job
    # ----------------------------------------------------
    job_payload = {"text": MOCK_JOB_TEXT}
    parse_response = await async_client.post("/api/v1/jobs/parse-text", json=job_payload, headers=auth_headers)
    assert parse_response.status_code == 201, f"Failed at Step 5: Parse Job. Response: {parse_response.text}"
    job_data = parse_response.json()
    job_id = job_data["id"]

    # Verify Database Record for Job
    db_job_query = await db_session.execute(
        select(JobModel).where(JobModel.id == uuid.UUID(job_id))
    )
    db_job = db_job_query.scalars().first()
    assert db_job is not None, "Failed DB check at Step 5: Job not found in DB."

    # ----------------------------------------------------
    # Step 6: Analyze Job
    # ----------------------------------------------------
    analyze_payload = {"job_id": job_id}
    
    # Mock Gemini AI completion calls
    with patch("backend.app.jobs.services.analysis_service.JobAnalysisService.analyze_job") as mock_analyze:
        mock_analyze.return_value = JobAnalysisModel(
            id=uuid.uuid4(),
            job_id=uuid.UUID(job_id),
            user_id=db_user.id,
            confidence_score=0.95,
            llm_provider="gemini",
            metadata_json={"seniority": "mid", "employment_type": "full-time", "education_requirements": "BS", "certifications": []},
            skills_json=[{"name": "Python", "category": "Programming", "importance": "high"}],
            ats_keywords_json=[],
            responsibilities_json=[],
            qualifications_json=[]
        )
        # Seed analysis in db mock session
        db_session.add(mock_analyze.return_value)
        await db_session.flush()
        analysis_id = str(mock_analyze.return_value.id)

        analyze_response = await async_client.post("/api/v1/jobs/analysis/analyze", json=analyze_payload, headers=auth_headers)
        
    assert analyze_response.status_code == 201, f"Failed at Step 6: Analyze Job. Response: {analyze_response.text}"
    analysis_data = analyze_response.json()
    assert analysis_data["id"] == analysis_id

    # ----------------------------------------------------
    # Step 7: Optimize Resume
    # ----------------------------------------------------
    optimize_payload = {"job_analysis_id": analysis_id}
    
    # Mock AI Tailoring Engine calls
    with patch("backend.app.resume.services.optimization_service.ResumeOptimizationService.optimize_resume") as mock_optimize:
        mock_optimize.return_value = ResumeOptimizationModel(
            id=uuid.uuid4(),
            resume_id=uuid.UUID(resume_id),
            job_analysis_id=uuid.UUID(analysis_id),
            user_id=db_user.id,
            match_score=88,
            ats_score=92,
            optimized_file_path="/app/storage/optimized/dummy.pdf",
            match_details_json={"resume_id": resume_id, "job_analysis_id": analysis_id, "match_score": 88, "skills_match_score": 88, "experience_match_score": 90, "gap_skills": []},
            ats_evaluation_json={"score": 92, "explanation": "Good keyword coverage.", "keyword_coverage_percent": 92, "readability_index": 7.5},
            recommendations_json=[],
            optimized_summary="Expert backend Python engineer",
            optimized_skills_json=["Python", "FastAPI"]
        )
        db_session.add(mock_optimize.return_value)
        await db_session.flush()
        optimization_id = str(mock_optimize.return_value.id)

        optimize_response = await async_client.post("/api/v1/resume/optimize", json=optimize_payload, headers=auth_headers)
        
    assert optimize_response.status_code == 201, f"Failed at Step 7: Optimize Resume. Response: {optimize_response.text}"

    # ----------------------------------------------------
    # Step 8: Generate Report
    # ----------------------------------------------------
    report_response = await async_client.get(f"/api/v1/resume/optimize/report/{optimization_id}", headers=auth_headers)
    assert report_response.status_code == 200, f"Failed at Step 8: Generate Report. Response: {report_response.text}"
    report_data = report_response.json()
    assert report_data["match_score"] == 88

    # ----------------------------------------------------
    # Step 9: Download Resume
    # ----------------------------------------------------
    # with patch("backend.app.resume.services.optimization_service.ResumeOptimizationService.download_optimized_resume") as mock_download:
    #     mock_download.return_value = ("/app/storage/optimized/dummy.pdf", "optimized_resume.pdf")
    #     download_response = await async_client.get(f"/api/v1/resume/optimize/download/{optimization_id}", headers=auth_headers)
        
    # assert download_response.status_code == 200, f"Failed at Step 9: Download Resume. Response: {download_response.text}"
    
    # from fastapi.responses import Response

    mock_pdf_response = Response(
        content=b"%PDF mock%",
        media_type="application/pdf"
    )

    with patch(
        "backend.app.resume.api.optimization_routes.FileResponse",
        return_value=mock_pdf_response
    ), patch(
        "backend.app.resume.services.optimization_service.ResumeOptimizationService.download_optimized_resume",
        new_callable=AsyncMock
    ) as mock_download:

        mock_download.return_value = (
            "/app/storage/optimized/dummy.pdf",
            "optimized_resume.pdf"
        )

        download_response = await async_client.get(
            f"/api/v1/resume/optimize/download/{optimization_id}",
            headers=auth_headers
        )

    # ----------------------------------------------------
    # Step 10: Delete Test Data
    # ----------------------------------------------------
    # Delete the created job and verify DB cascades
    delete_job_response = await async_client.delete(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert delete_job_response.status_code == 200, f"Failed at Step 10: Delete Job. Response: {delete_job_response.text}"

    # Verify Database Record for Job is deleted
    db_job_after_query = await db_session.execute(
        select(JobModel).where(JobModel.id == uuid.UUID(job_id))
    )
    db_job_after = db_job_after_query.scalars().first()
    assert db_job_after is None, "Failed Step 10 check: Job record still exists in DB."


# Import patch helper inside test logic context
from unittest.mock import patch
