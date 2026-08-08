"""SQLAlchemy database models for Optimization tracking."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.database.session import Base


class OptimizationRunModel(Base):
    """SQLAlchemy model representing a full multi-agent optimization run session."""

    __tablename__ = "resume_optimization_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    candidate_profile_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    job_profile_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    initial_score = Column(Numeric(5, 2), nullable=False)
    final_score = Column(Numeric(5, 2), nullable=True)
    status = Column(String(50), default="RUNNING", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    iterations = relationship("OptimizationIterationModel", backref="run", cascade="all, delete-orphan")
    history = relationship("OptimizationHistoryModel", backref="run", cascade="all, delete-orphan", uselist=False)


class OptimizationIterationModel(Base):
    """SQLAlchemy model representing a single loop iteration cycle."""

    __tablename__ = "optimization_iterations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    run_id = Column(UUID(as_uuid=True), ForeignKey("resume_optimization_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    iteration_number = Column(Integer, nullable=False)
    pre_score = Column(Numeric(5, 2), nullable=False)
    post_score = Column(Numeric(5, 2), nullable=False)
    planning_tasks = Column(JSON, default=list, nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class OptimizationChangesModel(Base):
    """SQLAlchemy model representing granular diff updates inside an iteration."""

    __tablename__ = "optimization_changes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    iteration_id = Column(UUID(as_uuid=True), ForeignKey("optimization_iterations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    modified_sections = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class OptimizationHistoryModel(Base):
    """SQLAlchemy model representing aggregated execution history logs for auditing."""

    __tablename__ = "optimization_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    run_id = Column(UUID(as_uuid=True), ForeignKey("resume_optimization_runs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    total_iterations = Column(Integer, nullable=False)
    optimization_log = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
