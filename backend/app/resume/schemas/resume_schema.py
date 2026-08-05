# backend/app/resume/schemas/resume_schema.py
# Pydantic schemas validating API request payloads & formatting resume response models

import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class ResumeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    file_name: str
    file_size: int
    content_type: str
    status: str
    parsed_skills: List[str] = []
    experience_years: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeVersionResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    user_id: uuid.UUID
    version_number: int
    file_path: str
    optimized_for_company: str
    optimized_for_role: str
    created_at: datetime

    class Config:
        from_attributes = True


class VersionMetadataCreate(BaseModel):
    optimized_for_company: str = Field(..., min_length=1, max_length=255)
    optimized_for_role: str = Field(..., min_length=1, max_length=255)
