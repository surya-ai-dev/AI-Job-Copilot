# backend/app/shared/orchestrator.py
# Application Orchestrator Graph implementation connecting job parsing, analysis, tailoring and drafts

import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from backend.app.jobs.services.job_service import JobService
from backend.app.jobs.services.analysis_service import JobAnalysisService
from backend.app.resume.services.optimization_service import ResumeOptimizationService
from backend.app.email.services.email_service import EmailOutreachService
from backend.app.dashboard.services.application_service import ApplicationManagementService
from backend.app.shared.exceptions import BaseAppException
from backend.app.shared.events import (
    dispatcher, 
    JobParsedEvent, 
    JobAnalyzedEvent, 
    ResumeOptimizedEvent, 
    EmailGeneratedEvent
)

class WorkflowState:
    def __init__(self, user_id: uuid.UUID, job_input: str):
        self.user_id = user_id
        self.job_input = job_input
        self.job_id: Optional[uuid.UUID] = None
        self.analysis_id: Optional[uuid.UUID] = None
        self.optimization_id: Optional[uuid.UUID] = None
        self.draft_id: Optional[uuid.UUID] = None
        
        # Execution metrics
        self.current_step = "START"
        self.error_state: Optional[str] = None
        self.retry_count = 0
        self.status = "PENDING"


class JobApplicationOrchestrator:
    def __init__(
        self,
        job_service: JobService,
        analysis_service: JobAnalysisService,
        opt_service: ResumeOptimizationService,
        email_service: EmailOutreachService,
        app_service: ApplicationManagementService
    ):
        self.job_service = job_service
        self.analysis_service = analysis_service
        self.opt_service = opt_service
        self.email_service = email_service
        self.app_service = app_service

    async def execute_pipeline(self, user_id: uuid.UUID, job_input: str) -> WorkflowState:
        """Run the end-to-end job ingestion, understanding, matching, and optimization pipeline."""
        state = WorkflowState(user_id, job_input)
        
        try:
            # 1. Parse Job Input
            state.current_step = "JOB_PARSING"
            db_job = await self._run_with_retry(
                self.job_service.ingest_job_from_text, state, user_id, job_input
            )
            state.job_id = db_job.id
            
            # Dispatch event
            dispatcher.dispatch(JobParsedEvent(
                event_id=uuid.uuid4(),
                timestamp=datetime.utcnow(),
                event_name="JobParsed",
                user_id=user_id,
                job_id=db_job.id,
                company_name=db_job.company_name,
                job_title=db_job.job_title
            ))

            # 2. Analyze Job Requirements
            state.current_step = "AI_UNDERSTANDING"
            db_analysis = await self._run_with_retry(
                self.analysis_service.analyze_job, state, user_id, state.job_id
            )
            state.analysis_id = db_analysis.id
            
            dispatcher.dispatch(JobAnalyzedEvent(
                event_id=uuid.uuid4(),
                timestamp=datetime.utcnow(),
                event_name="JobAnalyzed",
                user_id=user_id,
                job_id=state.job_id,
                analysis_id=db_analysis.id
            ))

            # 3. Match & Optimize Resume
            state.current_step = "RESUME_OPTIMIZATION"
            db_opt = await self._run_with_retry(
                self.opt_service.optimize_resume, state, user_id, state.analysis_id
            )
            state.optimization_id = db_opt.id
            
            dispatcher.dispatch(ResumeOptimizedEvent(
                event_id=uuid.uuid4(),
                timestamp=datetime.utcnow(),
                event_name="ResumeOptimized",
                user_id=user_id,
                resume_id=db_opt.resume_id,
                optimization_id=db_opt.id,
                match_score=db_opt.match_score
            ))

            # 4. Generate Outreach Email Draft
            state.current_step = "EMAIL_GENERATION"
            # Extract details from models to populate
            company = db_job.company_name
            role = db_job.job_title
            recruiter_email = db_job.recruiter_email

            import re
            email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            if recruiter_email and re.match(email_regex, str(recruiter_email).strip()):
                db_draft = await self._run_with_retry(
                    self.email_service.generate_outreach_email,
                    state,
                    user_id,
                    company,
                    role,
                    db_opt.optimized_file_path,
                    recruiter_email
                )
                state.draft_id = db_draft.id

                dispatcher.dispatch(EmailGeneratedEvent(
                    event_id=uuid.uuid4(),
                    timestamp=datetime.utcnow(),
                    event_name="EmailGenerated",
                    user_id=user_id,
                    draft_id=db_draft.id,
                    recipient_email=db_draft.recipient_email
                ))
                state.current_step = "HUMAN_REVIEW_WAITING"
            else:
                state.current_step = "NO_EMAIL_WORKFLOW_STOPPED"

            state.status = "SUCCESS"

        except Exception as e:
            state.error_state = str(e)
            state.status = "FAILED"
            print(f"Workflow pipeline failed at step {state.current_step}: {e}")

        return state

    async def _run_with_retry(self, func, state: WorkflowState, *args, **kwargs):
        """Helper to invoke service tasks supporting retry capabilities."""
        max_retries = 3
        while True:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                state.retry_count += 1
                if state.retry_count > max_retries:
                    raise e
                print(f"Retrying step {state.current_step} after error: {e}. Retry: {state.retry_count}")
