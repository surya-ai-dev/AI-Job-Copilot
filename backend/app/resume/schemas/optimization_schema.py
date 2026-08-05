# backend/app/resume/schemas/optimization_schema.py
# Pydantic schemas validating API request payloads & formatting resume optimization response models

import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class ResumeOptimizeRequest(BaseModel):
    job_analysis_id: uuid.UUID = Field(..., description="UUID primary key referencing the structured job analysis")


class RecommendationSchema(BaseModel):
    section: str
    change_type: str
    description: str
    original_text: Optional[str] = None
    suggested_text: Optional[str] = None


class ATSScoreSchema(BaseModel):
    score: int
    explanation: str
    keyword_coverage_percent: int
    readability_index: float


class MatchDetailsSchema(BaseModel):
    resume_id: uuid.UUID
    job_analysis_id: uuid.UUID
    match_score: int
    skills_match_score: int
    experience_match_score: int
    gap_skills: List[str] = []


class ResumeOptimizationResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    job_analysis_id: uuid.UUID
    user_id: uuid.UUID
    match_score: int
    ats_score: int
    optimized_summary: str
    optimized_skills: List[str] = Field(..., alias="optimized_skills_json")
    match_details: MatchDetailsSchema = Field(..., alias="match_details_json")
    ats_evaluation: ATSScoreSchema = Field(..., alias="ats_evaluation_json")
    recommendations: List[RecommendationSchema] = Field(..., alias="recommendations_json")
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
