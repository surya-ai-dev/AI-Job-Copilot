# backend/app/email/models/email_model.py
# SQLAlchemy Database Models mapping to PostgreSQL tables for email drafts, history & OAuth credentials

import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from backend.app.database.session import Base

class EmailDraftModel(Base):
    __tablename__ = "email_drafts"

    # UUID Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    recipient_email = Column(String(255), nullable=False)
    recipient_name = Column(String(100), nullable=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    attachment_path = Column(String(512), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class EmailHistoryModel(Base):
    __tablename__ = "email_histories"

    # UUID Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    attachment_path = Column(String(512), nullable=True)
    
    status = Column(String(50), default="sent", nullable=False) # sent, failed
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class GmailTokenModel(Base):
    __tablename__ = "gmail_oauth_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    access_token = Column(String(1024), nullable=False)
    refresh_token = Column(String(1024), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
