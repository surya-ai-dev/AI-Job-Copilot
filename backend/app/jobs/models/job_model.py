# backend/app/jobs/models/job_model.py
# SQLAlchemy Database Models mapping to PostgreSQL tables for jobs context

import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from backend.app.database.session import Base

class JobModel(Base):
    __tablename__ = "jobs"

    # UUID Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Source metadata
    source_type = Column(String(50), nullable=False) # url, text, pdf, image, email, whatsapp
    source_url = Column(String(512), nullable=True)
    
    # Parsed Content fields
    company_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    recruiter_email = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Raw ingested payload
    raw_content = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
