# backend/app/email/schemas/email_schema.py
# Pydantic schemas validating API request payloads & formatting email response models

import uuid
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class EmailGenerateRequest(BaseModel):
    job_analysis_id: uuid.UUID = Field(..., description="UUID reference to structured job details")
    resume_optimization_id: uuid.UUID = Field(..., description="UUID reference to tailored resume details")


class EmailDraftCreate(BaseModel):
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    attachment_path: Optional[str] = None


class EmailDraftUpdate(BaseModel):
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class EmailSendRequest(BaseModel):
    draft_id: uuid.UUID


class EmailDraftResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    subject: str
    body: str
    attachment_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailHistoryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    recipient_email: EmailStr
    subject: str
    body: str
    attachment_path: Optional[str] = None
    status: str
    sent_at: datetime

    class Config:
        from_attributes = True


class GmailTokenStatusResponse(BaseModel):
    connected: bool
    expires_at: Optional[datetime] = None
