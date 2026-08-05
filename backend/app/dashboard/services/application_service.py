# backend/app/dashboard/services/application_service.py
# Application Service Layer gathering dashboard metrics and logging new application events

import uuid
from typing import List, Optional
from backend.app.dashboard.repository.application_repository import ApplicationRepository
from backend.app.resume.repository.resume_repository import ResumeRepository
from backend.app.resume.repository.optimization_repository import ResumeOptimizationRepository
from backend.app.email.repository.email_repository import EmailRepository
from backend.app.jobs.repository.job_repository import JobRepository
from backend.app.dashboard.models.application_model import JobApplicationModel
from backend.app.shared.exceptions import NotFoundException, ValidationException, BusinessRuleException

class ApplicationManagementService:
    def __init__(
        self,
        app_repo: ApplicationRepository,
        resume_repo: ResumeRepository,
        opt_repo: ResumeOptimizationRepository,
        email_repo: EmailRepository,
        job_repo: JobRepository
    ):
        self.app_repo = app_repo
        self.resume_repo = resume_repo
        self.opt_repo = opt_repo
        self.email_repo = email_repo
        self.job_repo = job_repo

    async def get_dashboard_statistics(self, user_id: uuid.UUID) -> dict:
        """Gather aggregate summary counters and recent activity logs for dashboard widget cards."""
        # 1. Total and Today's application counts
        total_apps, apps_today = await self.app_repo.get_summary_stats(user_id)

        # 2. Active drafts count
        drafts = await self.email_repo.list_drafts(user_id)
        drafts_count = len(drafts)

        # 3. Recent applications (limit to 5)
        all_apps = await self.app_repo.list_applications(user_id)
        recent_apps = all_apps[:5]

        # 4. Total tailored resume versions
        versions = await self.resume_repo.list_user_versions(user_id)
        resumes_count = len(versions)

        # 5. Total sent emails history
        history = await self.email_repo.list_history(user_id)
        emails_count = len(history)

        return {
            "total_applications": total_apps,
            "applications_today": apps_today,
            "active_drafts_count": drafts_count,
            "recent_applications": recent_apps,
            "recent_resumes_count": resumes_count,
            "recent_emails_count": emails_count
        }

    async def log_new_application(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        resume_opt_id: uuid.UUID,
        email_history_id: Optional[uuid.UUID] = None
    ) -> JobApplicationModel:
        """Register a new job application event linking parsing, optimization, & email contexts."""
        # Validate references exist
        job = await self.job_repo.get_by_id(job_id)
        if not job or job.user_id != user_id:
            raise NotFoundException("Parsed job posting not found.", "JOB_NOT_FOUND")

        opt = await self.opt_repo.get_by_id(resume_opt_id)
        if not opt or opt.user_id != user_id:
            raise NotFoundException("Resume optimization not found.", "OPTIMIZATION_NOT_FOUND")

        app_model = JobApplicationModel(
            id=uuid.uuid4(),
            user_id=user_id,
            job_id=job_id,
            resume_id=opt.resume_id,
            resume_version_id=opt.id,
            email_history_id=email_history_id,
            company_name=job.parsed_data.company_name,
            job_title=job.parsed_data.job_title,
            job_url=job.source.source_url,
            recruiter_email=job.parsed_data.recruiter_email
        )

        return await self.app_repo.create_application(app_model)

    async def search_user_applications(
        self,
        user_id: uuid.UUID,
        query: str,
        company_filter: Optional[str] = None,
        role_filter: Optional[str] = None
    ) -> List[JobApplicationModel]:
        """Search and filter through user applications."""
        return await self.app_repo.search_applications(
            user_id=user_id,
            query=query,
            company_filter=company_filter,
            role_filter=role_filter
        )

    async def get_application_details(self, user_id: uuid.UUID, app_id: uuid.UUID) -> JobApplicationModel:
        """Retrieve details for a specific application entry."""
        db_app = await self.app_repo.get_by_id(app_id)
        if not db_app or db_app.user_id != user_id:
            raise NotFoundException("Job application record not found.", "APPLICATION_NOT_FOUND")
        return db_app

    async def delete_user_application(self, user_id: uuid.UUID, app_id: uuid.UUID) -> None:
        """Remove application tracking log."""
        db_app = await self.app_repo.get_by_id(app_id)
        if not db_app or db_app.user_id != user_id:
            raise NotFoundException("Job application record not found.", "APPLICATION_NOT_FOUND")
        await self.app_repo.delete_application(db_app)
