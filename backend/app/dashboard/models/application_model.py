# backend/app/dashboard/models/application_model.py
# SQLAlchemy Database Models mapping to PostgreSQL tables for job applications log

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from backend.app.database.session import Base

class JobApplicationModel(Base):
    __tablename__ = "applications"

    # UUID Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Context references
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    resume_version_id = Column(UUID(as_uuid=True), nullable=False)
    email_history_id = Column(UUID(as_uuid=True), ForeignKey("email_histories.id", ondelete="SET NULL"), nullable=True)

    # Ingestion logs cache
    company_name = Column(String(255), index=True, nullable=False)
    job_title = Column(String(255), index=True, nullable=False)
    job_url = Column(String(512), nullable=True)
    recruiter_email = Column(String(255), nullable=True)
    
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
