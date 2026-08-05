# backend/app/jobs/models/analysis_model.py
# SQLAlchemy Database Models mapping to PostgreSQL tables for job analysis results

import uuid
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from backend.app.database.session import Base

class JobAnalysisModel(Base):
    __tablename__ = "job_analyses"

    # UUID Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Audit metrics
    confidence_score = Column(Float, default=1.0, nullable=False)
    llm_provider = Column(String(50), default="gemini", nullable=False)
    prompt_version = Column(String(20), default="1.0.0", nullable=False)
    processing_time_ms = Column(Integer, default=0, nullable=False)
    
    # Structured JSON data payload fields
    metadata_json = Column(JSON, nullable=False) # holds seniority, employment_type, education, certifications
    skills_json = Column(JSON, nullable=False) # holds list of skills (name, category, importance)
    ats_keywords_json = Column(JSON, nullable=False) # holds list of keywords (word, category)
    responsibilities_json = Column(JSON, nullable=False) # holds list of strings
    qualifications_json = Column(JSON, nullable=False) # holds list of strings

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
