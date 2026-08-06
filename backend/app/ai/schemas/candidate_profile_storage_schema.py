"""Pydantic Schemas for the Candidate Profile Storage module."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.ai.schemas.candidate_profile_schema import (
    CandidateProfile,
    ExperienceItem,
    ProjectItem,
    EducationItem
)
from backend.app.ai.models.candidate_profile_model import CandidateProfileModel

class CandidateProfileStorageCreate(BaseModel):
    """Pydantic schema representing the request payload to store a new Candidate Profile."""
    user_id: uuid.UUID = Field(..., description="ID of the user this profile belongs to.")
    resume_id: uuid.UUID = Field(..., description="ID of the resume source file.")
    profile_data: CandidateProfile = Field(..., description="The structured candidate profile data extracted from the resume.")


class CandidateProfileStorageResponse(BaseModel):
    """Pydantic schema representing the candidate profile response retrieved from storage."""
    id: uuid.UUID
    user_id: uuid.UUID
    resume_id: uuid.UUID
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    professional_summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, model: CandidateProfileModel) -> "CandidateProfileStorageResponse":
        """Maps an ORM database model representation into this structured schema.

        Args:
            model (CandidateProfileModel): Persistence database model instance.

        Returns:
            CandidateProfileStorageResponse: Structured response model.
        """
        return cls(
            id=model.id,
            user_id=model.user_id,
            resume_id=model.resume_id,
            full_name=model.full_name,
            email=model.email,
            phone=model.phone,
            linkedin_url=model.linkedin_url,
            github_url=model.github_url,
            professional_summary=model.professional_summary,
            skills=model.skills_json,
            experience=[ExperienceItem(**item) for item in model.experience_json],
            projects=[ProjectItem(**item) for item in model.projects_json],
            education=[EducationItem(**item) for item in model.education_json],
            certifications=model.certifications_json,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
