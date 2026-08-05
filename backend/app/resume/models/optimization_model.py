# backend/app/resume/models/optimization_model.py
# SQLAlchemy Database Models mapping to PostgreSQL tables for resume optimization results

import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from backend.app.database.session import Base

class ResumeOptimizationModel(Base):
    __tablename__ = "resume_optimizations"

    # UUID Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_analysis_id = Column(UUID(as_uuid=True), ForeignKey("job_analyses.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Simple search index properties
    match_score = Column(Integer, nullable=False)
    ats_score = Column(Integer, nullable=False)
    optimized_file_path = Column(String(512), nullable=False)
    
    # Structured JSON data payload fields
    match_details_json = Column(JSON, nullable=False) # holds skills/exp match scores and gap details
    ats_evaluation_json = Column(JSON, nullable=False) # holds score, keyword coverage, and readability metrics
    recommendations_json = Column(JSON, nullable=False) # holds list of recommendations
    optimized_summary = Column(String(1000), nullable=False)
    optimized_skills_json = Column(JSON, nullable=False) # holds list of strings

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
