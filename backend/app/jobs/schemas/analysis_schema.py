# backend/app/jobs/schemas/analysis_schema.py
# Pydantic schemas validating API request payloads & formatting job analysis response models

import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class JobAnalysisRequest(BaseModel):
    job_id: uuid.UUID = Field(..., description="UUID primary key referencing the parsed job posting")


class SkillSchema(BaseModel):
    name: str
    category: str
    importance: str


class ATSKeywordSchema(BaseModel):
    word: str
    category: str


class JobMetadataSchema(BaseModel):
    seniority: str
    employment_type: str
    education_requirements: Optional[str] = None
    certifications: List[str] = []


class JobAnalysisResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    user_id: uuid.UUID
    confidence_score: float
    llm_provider: str
    prompt_version: str
    processing_time_ms: int
    metadata: JobMetadataSchema = Field(..., alias="metadata_json")
    skills: List[SkillSchema] = Field(..., alias="skills_json")
    ats_keywords: List[ATSKeywordSchema] = Field(..., alias="ats_keywords_json")
    responsibilities: List[str] = Field(..., alias="responsibilities_json")
    qualifications: List[str] = Field(..., alias="qualifications_json")
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
