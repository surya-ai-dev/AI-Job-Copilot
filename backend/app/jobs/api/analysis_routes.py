# backend/app/jobs/api/analysis_routes.py
# FastAPI routes exposing endpoints for running AI analyses and retrieving structured job intelligence

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.app.database.session import get_async_db
from backend.app.auth.api.routes import get_current_active_user
from backend.app.auth.schemas.auth_schema import UserResponse
from backend.app.jobs.repository.job_repository import JobRepository
from backend.app.jobs.repository.analysis_repository import JobAnalysisRepository
from backend.app.jobs.services.analysis_service import JobAnalysisService
from backend.app.jobs.schemas.analysis_schema import (
    JobAnalysisRequest, 
    JobAnalysisResponse
)
from backend.app.shared.exceptions import BaseAppException

router = APIRouter(prefix="/jobs/analysis", tags=["AI Job Analysis"])

def get_analysis_service(db: AsyncSession = Depends(get_async_db)) -> JobAnalysisService:
    """Dependency resolver returning initialized JobAnalysisService instance."""
    analysis_repo = JobAnalysisRepository(db)
    job_repo = JobRepository(db)
    return JobAnalysisService(analysis_repo, job_repo)


@router.post("/analyze", response_model=JobAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_job(
    payload: JobAnalysisRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobAnalysisService = Depends(get_analysis_service)
):
    """Run AI analysis on a parsed job posting to extract structured requirements."""
    try:
        return await service.analyze_job(current_user.id, payload.job_id)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get("", response_model=List[JobAnalysisResponse])
async def list_analyses(
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobAnalysisService = Depends(get_analysis_service)
):
    """List all job analyses parsed by current authenticated user."""
    return await service.list_user_analyses(current_user.id)


@router.get("/{id}", response_model=JobAnalysisResponse)
async def get_analysis(
    id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobAnalysisService = Depends(get_analysis_service)
):
    """Retrieve details for a specific job analysis by ID."""
    try:
        return await service.get_analysis_details(current_user.id, id)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get("/by-job/{job_id}", response_model=JobAnalysisResponse)
async def get_analysis_by_job(
    job_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobAnalysisService = Depends(get_analysis_service)
):
    """Retrieve details for a job analysis by job ID."""
    try:
        return await service.get_analysis_by_job(current_user.id, job_id)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_analysis(
    id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    service: JobAnalysisService = Depends(get_analysis_service)
):
    """Delete a job analysis record from database logs."""
    try:
        await service.delete_user_analysis(current_user.id, id)
        return {"message": "Job analysis record deleted successfully."}
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
