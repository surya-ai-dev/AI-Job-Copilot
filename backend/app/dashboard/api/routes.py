# backend/app/dashboard/api/routes.py
# FastAPI routes exposing endpoints for dashboard summary counters, applications tracking, & searching

import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from backend.app.database.session import get_async_db
from backend.app.auth.api.routes import get_current_active_user
from backend.app.auth.schemas.auth_schema import UserResponse
from backend.app.dashboard.repository.application_repository import ApplicationRepository
from backend.app.resume.repository.resume_repository import ResumeRepository
from backend.app.resume.repository.optimization_repository import ResumeOptimizationRepository
from backend.app.email.repository.email_repository import EmailRepository
from backend.app.jobs.repository.job_repository import JobRepository
from backend.app.dashboard.services.application_service import ApplicationManagementService
from backend.app.dashboard.schemas.application_schema import (
    JobApplicationCreate,
    JobApplicationResponse,
    DashboardStatsResponse
)
from backend.app.shared.exceptions import BaseAppException

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Applications"])

def get_dashboard_service(db: AsyncSession = Depends(get_async_db)) -> ApplicationManagementService:
    """Dependency resolver returning initialized ApplicationManagementService instance."""
    app_repo = ApplicationRepository(db)
    resume_repo = ResumeRepository(db)
    opt_repo = ResumeOptimizationRepository(db)
    email_repo = EmailRepository(db)
    job_repo = JobRepository(db)
    return ApplicationManagementService(app_repo, resume_repo, opt_repo, email_repo, job_repo)


@router.get("/summary", response_model=DashboardStatsResponse)
async def get_summary(
    current_user: UserResponse = Depends(get_current_active_user),
    service: ApplicationManagementService = Depends(get_dashboard_service)
):
    """Fetch aggregate summary counters and recent applications details for dashboard widget cards."""
    return await service.get_dashboard_statistics(current_user.id)


@router.post("/applications", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
async def log_application(
    payload: JobApplicationCreate,
    current_user: UserResponse = Depends(get_current_active_user),
    service: ApplicationManagementService = Depends(get_dashboard_service)
):
    """Register a new job application event in database tracker logs."""
    try:
        return await service.log_new_application(
            user_id=current_user.id,
            job_id=payload.job_id,
            resume_opt_id=payload.resume_optimization_id,
            email_history_id=payload.email_history_id
        )
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get("/applications", response_model=List[JobApplicationResponse])
async def list_applications(
    current_user: UserResponse = Depends(get_current_active_user),
    service: ApplicationManagementService = Depends(get_dashboard_service)
):
    """List all application events logged by the current user."""
    return await service.app_repo.list_applications(current_user.id)


@router.get("/applications/search", response_model=List[JobApplicationResponse])
async def search_applications(
    query: str = Query("", description="Search term for company name, job role, or recruiter email"),
    company: Optional[str] = Query(None, description="Filter specifically by company name"),
    role: Optional[str] = Query(None, description="Filter specifically by job role"),
    current_user: UserResponse = Depends(get_current_active_user),
    service: ApplicationManagementService = Depends(get_dashboard_service)
):
    """Query, search, or filter logged application tracking entries."""
    return await service.search_user_applications(
        user_id=current_user.id,
        query=query,
        company_filter=company,
        role_filter=role
    )


@router.get("/applications/{id}", response_model=JobApplicationResponse)
async def get_application(
    id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    service: ApplicationManagementService = Depends(get_dashboard_service)
):
    """Retrieve details for a logged application entry by ID."""
    try:
        return await service.get_application_details(current_user.id, id)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/applications/{id}", status_code=status.HTTP_200_OK)
async def delete_application(
    id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    service: ApplicationManagementService = Depends(get_dashboard_service)
):
    """Delete an application tracking log entry from database."""
    try:
        await service.delete_user_application(current_user.id, id)
        return {"message": "Job application log removed successfully."}
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
