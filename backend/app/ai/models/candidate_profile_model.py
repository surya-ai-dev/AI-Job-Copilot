"""SQLAlchemy Database Model for the Candidate Profile entity."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from backend.app.database.session import Base

class CandidateProfileModel(Base):
    """SQLAlchemy model representing a candidate's structured profile (active resume memory)."""
    
    __tablename__ = "candidate_profiles"

    # UUID Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    
    # Foreign Keys referencing users and resumes
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)

    # Core Candidate Metadata
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(512), nullable=True)
    github_url = Column(String(512), nullable=True)
    professional_summary = Column(String, nullable=True)

    # Parsed structured segments stored as JSON
    skills_json = Column(JSON, default=list, nullable=False)
    experience_json = Column(JSON, default=list, nullable=False)
    projects_json = Column(JSON, default=list, nullable=False)
    education_json = Column(JSON, default=list, nullable=False)
    certifications_json = Column(JSON, default=list, nullable=False)

    # Active status tracking (Only one profile can be active per user)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Audits
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
