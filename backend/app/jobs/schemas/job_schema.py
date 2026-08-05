# backend/app/jobs/schemas/job_schema.py
# Pydantic schemas validating API request payloads & formatting job response models

import uuid
from pydantic import BaseModel, HttpUrl, EmailStr, Field
from datetime import datetime
from typing import Optional

class JobUrlParseRequest(BaseModel):
    url: str = Field(..., description="LinkedIn or Career Page URL to scrape")


class JobTextParseRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Raw job description plain text")


class JobEmailParseRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class JobWhatsAppParseRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Raw whatsapp message payload text")


class JobResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    source_type: str
    source_url: Optional[str] = None
    company_name: str
    job_title: str
    description: str
    recruiter_email: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
