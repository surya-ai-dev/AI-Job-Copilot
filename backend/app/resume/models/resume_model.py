# backend/app/resume/models/resume_model.py
# SQLAlchemy Database Models mapping to PostgreSQL tables for resumes & versions

import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database.session import Base

class ResumeModel(Base):
    __tablename__ = "resumes"

    # UUID Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    status = Column(String(50), default="active", nullable=False) # active, replaced, deleted
    
    # Parsed Skill sets Metadata
    parsed_skills = Column(JSON, default=list, nullable=False)
    experience_years = Column(Integer, nullable=True)

    # Audits
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    versions = relationship("ResumeVersionModel", back_populates="resume", cascade="all, delete-orphan")


class ResumeVersionModel(Base):
    __tablename__ = "resume_versions"

    # UUID Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(512), nullable=False)
    
    # Tailoring targets
    optimized_for_company = Column(String(255), nullable=False)
    optimized_for_role = Column(String(255), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    resume = relationship("ResumeModel", back_populates="versions")
