# backend/app/email/api/routes.py
# FastAPI routes exposing endpoints for generating outreach email drafts, updating drafts, & sending messages

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.app.database.session import get_async_db
from backend.app.auth.api.routes import get_current_active_user
from backend.app.auth.schemas.auth_schema import UserResponse
from backend.app.email.repository.email_repository import EmailRepository
from backend.app.email.services.email_service import EmailOutreachService
from backend.app.jobs.repository.analysis_repository import JobAnalysisRepository
from backend.app.resume.repository.optimization_repository import ResumeOptimizationRepository
from backend.app.email.schemas.email_schema import (
    EmailGenerateRequest,
    EmailDraftUpdate,
    EmailSendRequest,
    EmailDraftResponse,
    EmailHistoryResponse,
    GmailTokenStatusResponse
)
from backend.app.shared.exceptions import BaseAppException

router = APIRouter(prefix="/email", tags=["Email Outreach Management"])

def get_email_service(db: AsyncSession = Depends(get_async_db)) -> EmailOutreachService:
    """Dependency resolver returning initialized EmailOutreachService instance."""
    repo = EmailRepository(db)
    return EmailOutreachService(repo)


@router.post("/generate", response_model=EmailDraftResponse, status_code=status.HTTP_201_CREATED)
async def generate_outreach(
    payload: EmailGenerateRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
    service: EmailOutreachService = Depends(get_email_service)
):
    """Generate personalized recruiter outreach email draft based on job analysis and resume details."""
    try:
        # Load references to extract company, role and file paths
        analysis_repo = JobAnalysisRepository(db)
        opt_repo = ResumeOptimizationRepository(db)
        
        analysis = await analysis_repo.get_by_id(payload.job_analysis_id)
        opt = await opt_repo.get_by_id(payload.resume_optimization_id)
        
        if not analysis or analysis.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Job analysis details not found.")
        if not opt or opt.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Resume optimization details not found.")

        # Load linked JobModel to retrieve company_name, job_title, and recruiter_email
        from backend.app.jobs.models.job_model import JobModel
        from sqlalchemy.future import select
        job_query = await db.execute(select(JobModel).where(JobModel.id == analysis.job_id))
        job = job_query.scalars().first()

        company = job.company_name if job else analysis.metadata_json.get("company_name", "TargetCompany")
        role = job.job_title if job else analysis.metadata_json.get("job_title", "TargetRole")
        recruiter_email = (job.recruiter_email or analysis.metadata_json.get("recruiter_email")) if job else analysis.metadata_json.get("recruiter_email")

        return await service.generate_outreach_email(
            user_id=current_user.id,
            job_analysis_company=company,
            job_analysis_role=role,
            optimized_resume_path=opt.optimized_file_path,
            recruiter_email=recruiter_email
        )
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.put("/draft/{id}", response_model=EmailDraftResponse)
async def update_draft(
    id: uuid.UUID,
    payload: EmailDraftUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    service: EmailOutreachService = Depends(get_email_service)
):
    """Update active email draft details in workspace."""
    try:
        return await service.save_draft_update(
            user_id=current_user.id,
            draft_id=id,
            recipient_email=payload.recipient_email,
            recipient_name=payload.recipient_name,
            subject=payload.subject,
            body=payload.body
        )
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post("/send", response_model=EmailHistoryResponse)
async def send_email(
    payload: EmailSendRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    service: EmailOutreachService = Depends(get_email_service)
):
    """Deliver outreach email via Gmail API, requiring explicit user confirmation."""
    try:
        return await service.send_outreach_email(current_user.id, payload.draft_id)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get("/drafts", response_model=List[EmailDraftResponse])
async def list_drafts(
    current_user: UserResponse = Depends(get_current_active_user),
    service: EmailOutreachService = Depends(get_email_service)
):
    """List active email drafts in workspace."""
    return await service.list_user_drafts(current_user.id)


@router.delete("/draft/{id}", status_code=status.HTTP_200_OK)
async def delete_draft(
    id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    service: EmailOutreachService = Depends(get_email_service)
):
    """Delete an email draft from database logs."""
    try:
        await service.delete_user_draft(current_user.id, id)
        return {"message": "Draft deleted successfully."}
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get("/history", response_model=List[EmailHistoryResponse])
async def list_history(
    current_user: UserResponse = Depends(get_current_active_user),
    service: EmailOutreachService = Depends(get_email_service)
):
    """List sent email history logs."""
    return await service.list_user_email_history(current_user.id)


@router.get("/oauth/status", response_model=GmailTokenStatusResponse)
async def oauth_status(
    current_user: UserResponse = Depends(get_current_active_user),
    service: EmailOutreachService = Depends(get_email_service)
):
    """Check user's Gmail authorization session status."""
    return await service.get_gmail_connection_status(current_user.id)


@router.post("/oauth/callback", status_code=status.HTTP_200_OK)
async def oauth_callback(
    access_token: str,
    expires_in: int,
    refresh_token: str = None,
    current_user: UserResponse = Depends(get_current_active_user),
    service: EmailOutreachService = Depends(get_email_service)
):
    """Mocks Google OAuth callback to register Gmail credentials tokens."""
    try:
        await service.save_gmail_oauth_callback(
            user_id=current_user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in_seconds=expires_in
        )
        return {"message": "Gmail tokens saved successfully."}
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
