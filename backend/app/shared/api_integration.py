# backend/app/shared/api_integration.py
# FastAPI routes exposing unified outreach workflow pipelines orchestrator endpoints

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import uuid
from typing import Optional
from backend.app.database.session import get_async_db
from backend.app.auth.api.routes import get_current_active_user
from backend.app.auth.schemas.auth_schema import UserResponse

# Import services
from backend.app.jobs.repository.job_repository import JobRepository
from backend.app.jobs.services.job_service import JobService
from backend.app.jobs.repository.analysis_repository import JobAnalysisRepository
from backend.app.jobs.services.analysis_service import JobAnalysisService
from backend.app.resume.repository.resume_repository import ResumeRepository
from backend.app.resume.repository.optimization_repository import ResumeOptimizationRepository
from backend.app.resume.services.optimization_service import ResumeOptimizationService
from backend.app.email.repository.email_repository import EmailRepository
from backend.app.email.services.email_service import EmailOutreachService
from backend.app.dashboard.repository.application_repository import ApplicationRepository
from backend.app.dashboard.services.application_service import ApplicationManagementService

# Import orchestrator
from backend.app.shared.orchestrator import JobApplicationOrchestrator

router = APIRouter(prefix="/application", tags=["Workflow Integration Pipeline"])

class ApplyPipelineRequest(BaseModel):
    job_input: str = Field(..., description="Raw pasted job description text details")


class ApplyPipelineResponse(BaseModel):
    job_id: Optional[uuid.UUID] = None
    analysis_id: Optional[uuid.UUID] = None
    resume_optimization_id: Optional[uuid.UUID] = None
    email_draft_id: Optional[uuid.UUID] = None
    status: str
    error: Optional[str] = None


def get_orchestrator(db: AsyncSession = Depends(get_async_db)) -> JobApplicationOrchestrator:
    """Dependency resolver compiling full pipeline orchestrator with all modules."""
    job_repo = JobRepository(db)
    job_service = JobService(job_repo)
    
    analysis_repo = JobAnalysisRepository(db)
    analysis_service = JobAnalysisService(analysis_repo, job_repo)
    
    opt_repo = ResumeOptimizationRepository(db)
    resume_repo = ResumeRepository(db)
    opt_service = ResumeOptimizationService(opt_repo, resume_repo, analysis_repo, storage_path="/storage")
    
    email_repo = EmailRepository(db)
    email_service = EmailOutreachService(email_repo)
    
    app_repo = ApplicationRepository(db)
    app_service = ApplicationManagementService(app_repo, resume_repo, opt_repo, email_repo, job_repo)
    
    return JobApplicationOrchestrator(
        job_service=job_service,
        analysis_service=analysis_service,
        opt_service=opt_service,
        email_service=email_service,
        app_service=app_service
    )


@router.post("/apply", response_model=ApplyPipelineResponse, status_code=status.HTTP_200_OK)
async def trigger_apply_pipeline(
    payload: ApplyPipelineRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    orchestrator: JobApplicationOrchestrator = Depends(get_orchestrator)
):
    """Run the complete end-to-end job ingestion, analysis, and optimization pipeline in one click."""
    result_state = await orchestrator.execute_pipeline(current_user.id, payload.job_input)
    
    if result_state.status == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow failed at step {result_state.current_step}: {result_state.error_state}"
        )
        
    return ApplyPipelineResponse(
        job_id=result_state.job_id,
        analysis_id=result_state.analysis_id,
        resume_optimization_id=result_state.optimization_id,
        email_draft_id=result_state.draft_id,
        status=result_state.status,
        error=result_state.error_state
    )
