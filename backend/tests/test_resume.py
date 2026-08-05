# backend/tests/test_resume.py
# Production-ready test suite verifying resume uploads, limits checking, downloads, and deletions

import pytest
from unittest.mock import AsyncMock, patch, mock_open
from datetime import datetime
from httpx import AsyncClient
from backend.app.resume.models.resume_model import ResumeModel
from backend.tests.helpers import generate_mock_pdf_content
from backend.tests.constants import TEST_EMAIL, MOCK_USER_ID, MOCK_RESUME_ID

@pytest.mark.asyncio
async def test_upload_resume_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test uploading a valid PDF resume file successfully."""
    pdf_content = generate_mock_pdf_content()

    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.resume.repository.resume_repository.ResumeRepository.get_active_by_user", new_callable=AsyncMock) as mock_resume_get, \
         patch("backend.app.resume.services.resume_service.ResumeService._write_file_to_disk"), \
         patch("backend.app.resume.repository.resume_repository.ResumeRepository.create_resume", new_callable=AsyncMock) as mock_create:
        
        mock_user_get.return_value = mock_user_record
        mock_resume_get.return_value = None
        mock_create.return_value = ResumeModel(
            id=MOCK_RESUME_ID,
            user_id=MOCK_USER_ID,
            file_path="/app/storage/resumes/dummy.pdf",
            file_name="resume.pdf",
            file_size=len(pdf_content),
            content_type="application/pdf",
            status="active",
            parsed_skills=["Python", "FastAPI"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        files = {"file": ("resume.pdf", pdf_content, "application/pdf")}
        response = await async_client.post("/api/v1/resume/upload", files=files, headers=auth_headers)
        
        # Verify response status is 201 Created
        assert response.status_code == 201
        data = response.json()
        assert data["file_name"] == "resume.pdf"
        assert data["content_type"] == "application/pdf"
        assert "Python" in data["parsed_skills"]

@pytest.mark.asyncio
async def test_upload_resume_unsupported_extension_fails(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test uploading an unsupported extension (e.g. .txt) throws a 400 validation error."""
    text_content = b"Some plain text description content that is not a PDF/docx"

    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get:
        mock_user_get.return_value = mock_user_record

        files = {"file": ("resume.txt", text_content, "text/plain")}
        response = await async_client.post("/api/v1/resume/upload", files=files, headers=auth_headers)
        
        # Verify response status is 400 Bad Request
        assert response.status_code == 400
        data = response.json()
        assert "Only PDF and DOCX" in data["detail"]

@pytest.mark.asyncio
async def test_upload_resume_too_large_fails(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test uploading a file larger than the 10MB size limit fails validation."""
    # Create mock content representing a 11MB file (11 * 1024 * 1024 bytes)
    large_content = b"0" * (11 * 1024 * 1024)

    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get:
        mock_user_get.return_value = mock_user_record

        files = {"file": ("large_resume.pdf", large_content, "application/pdf")}
        response = await async_client.post("/api/v1/resume/upload", files=files, headers=auth_headers)
        
        # Verify response status is 400 Bad Request
        assert response.status_code == 400
        data = response.json()
        assert "exceeds maximum limit" in data["detail"]

@pytest.mark.asyncio
async def test_get_active_resume_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test retrieving active master resume details."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.resume.repository.resume_repository.ResumeRepository.get_active_by_user", new_callable=AsyncMock) as mock_resume_get:
        
        mock_user_get.return_value = mock_user_record
        mock_resume_get.return_value = ResumeModel(
            id=MOCK_RESUME_ID,
            user_id=MOCK_USER_ID,
            file_path="/app/storage/resumes/dummy.pdf",
            file_name="resume.pdf",
            file_size=1024,
            content_type="application/pdf",
            status="active",
            parsed_skills=["React", "Python"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        response = await async_client.get("/api/v1/resume", headers=auth_headers)
        
        # Verify response status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert data["file_name"] == "resume.pdf"
        assert "React" in data["parsed_skills"]

@pytest.mark.asyncio
async def test_get_active_resume_not_found(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test retrieving resume details fails if no master resume exists."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.resume.repository.resume_repository.ResumeRepository.get_active_by_user", new_callable=AsyncMock) as mock_resume_get:
        
        mock_user_get.return_value = mock_user_record
        mock_resume_get.return_value = None

        response = await async_client.get("/api/v1/resume", headers=auth_headers)
        
        # Verify response status is 404 Not Found
        assert response.status_code == 404
        data = response.json()
        assert "No active master resume" in data["detail"]

@pytest.mark.asyncio
async def test_download_active_resume_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test downloading the binary file of the active master resume."""
    from fastapi.responses import Response
    mock_response = Response(content=b"%PDF mock binary data%", media_type="application/pdf")

    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.resume.repository.resume_repository.ResumeRepository.get_active_by_user", new_callable=AsyncMock) as mock_resume_get, \
         patch("backend.app.resume.services.resume_service.os.path.exists", return_value=True), \
         patch("backend.app.resume.api.routes.FileResponse", return_value=mock_response):
        
        mock_user_get.return_value = mock_user_record
        mock_resume_get.return_value = ResumeModel(
            id=MOCK_RESUME_ID,
            file_name="resume.pdf",
            file_path="/app/storage/resumes/dummy.pdf",
            content_type="application/pdf"
        )

        response = await async_client.get("/api/v1/resume/download", headers=auth_headers)
        
        # Verify response status is 200 OK
        assert response.status_code == 200
        # Verify response content type header is pdf
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == b"%PDF mock binary data%"

@pytest.mark.asyncio
async def test_delete_resume_success(async_client: AsyncClient, auth_headers, mock_user_record):
    """Test deleting the active master resume record."""
    with patch("backend.app.auth.repository.user_repository.UserRepository.get_by_email", new_callable=AsyncMock) as mock_user_get, \
         patch("backend.app.resume.repository.resume_repository.ResumeRepository.get_active_by_user", new_callable=AsyncMock) as mock_resume_get, \
         patch("backend.app.resume.repository.resume_repository.ResumeRepository.update_status", new_callable=AsyncMock) as mock_delete, \
         patch("backend.app.resume.services.resume_service.os.remove"):
        
        mock_user_get.return_value = mock_user_record
        mock_resume_get.return_value = ResumeModel(id=MOCK_RESUME_ID, file_path="/app/storage/resumes/dummy.pdf")
        mock_delete.return_value = None

        response = await async_client.delete("/api/v1/resume", headers=auth_headers)
        
        # Verify response status is 200 OK
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        mock_delete.assert_called_once()
