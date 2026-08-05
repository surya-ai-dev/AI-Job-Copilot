# backend/app/dashboard/schemas/application_schema.py
# Pydantic schemas validating API request payloads & formatting dashboard response models

import uuid
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

class JobApplicationCreate(BaseModel):
    job_id: uuid.UUID = Field(..., description="UUID reference to raw parsed job posting")
    resume_optimization_id: uuid.UUID = Field(..., description="UUID reference to optimized resume version details")
    email_history_id: Optional[uuid.UUID] = Field(None, description="Optional UUID reference to sent outreach email")
    applied_at: datetime = Field(default_factory=datetime.utcnow)


class JobApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    resume_id: uuid.UUID
    resume_version_id: uuid.UUID
    email_history_id: Optional[uuid.UUID] = None
    company_name: str
    job_title: str
    job_url: Optional[str] = None
    recruiter_email: Optional[str] = None
    applied_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardStatsResponse(BaseModel):
    total_applications: int
    applications_today: int
    active_drafts_count: int
    recent_applications: List[JobApplicationResponse]
    recent_resumes_count: int
    recent_emails_count: int
