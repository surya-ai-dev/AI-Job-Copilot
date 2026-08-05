# backend/app/jobs/api/routes.py
# FastAPI routes exposing endpoints for scraping URLs, pasting text, parsing PDFs & screenshots ingestion

import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.app.database.session import get_async_db
from backend.app.auth.api.routes import get_current_active_user
from backend.app.auth.schemas.auth_schema import UserResponse
from backend.app.jobs.repository.job_repository import JobRepository
from backend.app.jobs.services.job_service import JobService
from backend.app.jobs.schemas.job_schema import (
    JobUrlParseRequest, 
    JobTextParseRequest, 
    JobEmailParseRequest, 
    JobWhatsAppParseRequest, 
    JobResponse
)
from backend.app.shared.exceptions import BaseAppException

router = APIRouter(prefix="/jobs", tags=["Job Ingestion"])

def get_job_service(db: AsyncSession = Depends(get_async_db)) -> JobService:
    """Dependency resolver returning initialized JobService instance."""
    repo = JobRepository(db)
    return JobService(repo)


@router.post("/parse-url", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def parse_url(
    payload: JobUrlParseRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobService = Depends(get_job_service)
):
    """Scrape and parse job posting from a target URL."""
    try:
        return await service.ingest_job_from_url(current_user.id, payload.url)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post("/parse-text", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def parse_text(
    payload: JobTextParseRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobService = Depends(get_job_service)
):
    """Parse pasted plain text job description."""
    try:
        return await service.ingest_job_from_text(current_user.id, payload.text)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post("/parse-pdf", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def parse_pdf(
    file: UploadFile = File(..., description="PDF job description document"),
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobService = Depends(get_job_service)
):
    """Extract and parse job description from a PDF file."""
    try:
        content = await file.read()
        return await service.ingest_job_from_pdf(current_user.id, file.filename, content)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post("/parse-image", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def parse_image(
    file: UploadFile = File(..., description="Job posting screenshot image"),
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobService = Depends(get_job_service)
):
    """Ingest job details from image screenshots using OCR extraction."""
    try:
        content = await file.read()
        return await service.ingest_job_from_image(current_user.id, file.filename, content)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post("/parse-email", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def parse_email(
    payload: JobEmailParseRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobService = Depends(get_job_service)
):
    """Parse recruiter outreach email text details."""
    try:
        return await service.ingest_job_from_email(current_user.id, payload.subject, payload.body)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post("/parse-whatsapp", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def parse_whatsapp(
    payload: JobWhatsAppParseRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobService = Depends(get_job_service)
):
    """Parse job referral text details pasted from WhatsApp."""
    try:
        return await service.ingest_job_from_whatsapp(current_user.id, payload.message)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get("/{id}", response_model=JobResponse)
async def get_job(
    id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobService = Depends(get_job_service)
):
    """Retrieve details for a previously parsed job posting."""
    try:
        return await service.get_job_details(current_user.id, id)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobService = Depends(get_job_service)
):
    """List all job postings parsed by current authenticated user."""
    return await service.list_user_jobs(current_user.id)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_job(
    id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobService = Depends(get_job_service)
):
    """Delete a parsed job posting from database logs."""
    try:
        await service.delete_user_job(current_user.id, id)
        return {"message": "Job posting record deleted successfully."}
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
