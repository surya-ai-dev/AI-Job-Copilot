# backend/app/resume/repository/resume_repository.py
# Database access operations encapsulating SQLAlchemy transactions for resumes & versions

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime
from typing import Optional, List
from backend.app.resume.models.resume_model import ResumeModel, ResumeVersionModel
from backend.app.resume.domain.resume import Resume, ResumeVersion

class ResumeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_resume(self, resume: Resume) -> ResumeModel:
        """Create new database master resume entry."""
        db_resume = ResumeModel(
            id=resume.id or uuid.uuid4(),
            user_id=resume.user_id,
            file_path=resume.file_path,
            file_name=resume.metadata.file_name,
            file_size=resume.metadata.file_size,
            content_type=resume.metadata.content_type,
            status=resume.status,
            parsed_skills=resume.metadata.parsed_skills,
            experience_years=resume.metadata.parsed_experience_years,
            created_at=resume.created_at,
            updated_at=resume.updated_at
        )
        self.db.add(db_resume)
        await self.db.flush()
        return db_resume

    async def get_active_by_user(self, user_id: uuid.UUID) -> Optional[ResumeModel]:
        """Fetch the active master resume for a user."""
        result = await self.db.execute(
            select(ResumeModel).where(ResumeModel.user_id == user_id, ResumeModel.status == "active")
        )
        return result.scalars().first()

    async def get_by_id(self, resume_id: uuid.UUID) -> Optional[ResumeModel]:
        """Fetch resume details by ID."""
        result = await self.db.execute(select(ResumeModel).where(ResumeModel.id == resume_id))
        return result.scalars().first()

    async def update_status(self, db_resume: ResumeModel, status: str) -> ResumeModel:
        """Update resume status (e.g. replaced, deleted)."""
        db_resume.status = status
        db_resume.updated_at = datetime.utcnow()
        await self.db.flush()
        return db_resume

    async def create_version(self, version: ResumeVersion) -> ResumeVersionModel:
        """Save a new resume version metadata record."""
        db_version = ResumeVersionModel(
            id=version.id or uuid.uuid4(),
            resume_id=version.resume_id,
            user_id=version.user_id,
            version_number=version.version_number,
            file_path=version.file_path,
            optimized_for_company=version.optimized_for_company,
            optimized_for_role=version.optimized_for_role,
            created_at=version.created_at
        )
        self.db.add(db_version)
        await self.db.flush()
        return db_version

    async def list_versions(self, user_id: uuid.UUID) -> List[ResumeVersionModel]:
        """List all resume versions for a user."""
        result = await self.db.execute(
            select(ResumeVersionModel)
            .where(ResumeVersionModel.user_id == user_id)
            .order_by(ResumeVersionModel.version_number.desc())
        )
        return result.scalars().all()

    async def get_latest_version_number(self, user_id: uuid.UUID) -> int:
        """Query the latest version number for a user to support auto-incrementing."""
        result = await self.db.execute(
            select(func.max(ResumeVersionModel.version_number)).where(RefreshTokenModel := ResumeVersionModel.user_id == user_id)
        )
        max_val = result.scalar()
        return max_val if max_val is not None else 0
