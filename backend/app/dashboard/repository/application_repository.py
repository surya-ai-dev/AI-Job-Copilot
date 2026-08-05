# backend/app/dashboard/repository/application_repository.py
# Database access operations encapsulating SQLAlchemy transactions for job applications tracking

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from datetime import datetime, date
from typing import Optional, List
from backend.app.dashboard.models.application_model import JobApplicationModel

class ApplicationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_application(self, app_model: JobApplicationModel) -> JobApplicationModel:
        """Create new database job application entry."""
        self.db.add(app_model)
        await self.db.flush()
        return app_model

    async def get_by_id(self, app_id: uuid.UUID) -> Optional[JobApplicationModel]:
        """Fetch application details by ID."""
        result = await self.db.execute(select(JobApplicationModel).where(JobApplicationModel.id == app_id))
        return result.scalars().first()

    async def list_applications(self, user_id: uuid.UUID) -> List[JobApplicationModel]:
        """List all applications logged by the user."""
        result = await self.db.execute(
            select(JobApplicationModel).where(JobApplicationModel.user_id == user_id).order_by(JobApplicationModel.applied_at.desc())
        )
        return result.scalars().all()

    async def search_applications(
        self, 
        user_id: uuid.UUID, 
        query: str, 
        company_filter: Optional[str] = None, 
        role_filter: Optional[str] = None
    ) -> List[JobApplicationModel]:
        """Search applications matching search string or category filters."""
        stmt = select(JobApplicationModel).where(JobApplicationModel.user_id == user_id)
        
        if query.strip():
            like_pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    JobApplicationModel.company_name.ilike(like_pattern),
                    JobApplicationModel.job_title.ilike(like_pattern),
                    JobApplicationModel.recruiter_email.ilike(like_pattern)
                )
            )

        if company_filter:
            stmt = stmt.where(JobApplicationModel.company_name == company_filter)
        if role_filter:
            stmt = stmt.where(JobApplicationModel.job_title == role_filter)

        stmt = stmt.order_by(JobApplicationModel.applied_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_application(self, db_app: JobApplicationModel) -> None:
        """Remove application record from database logs."""
        await self.db.delete(db_app)
        await self.db.flush()

    async def get_summary_stats(self, user_id: uuid.UUID) -> tuple:
        """Aggregate total count of applications and count logged today."""
        # Total
        total_stmt = select(func.count(JobApplicationModel.id)).where(JobApplicationModel.user_id == user_id)
        total_result = await self.db.execute(total_stmt)
        total_count = total_result.scalar() or 0

        # Today
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_stmt = select(func.count(JobApplicationModel.id)).where(
            JobApplicationModel.user_id == user_id,
            JobApplicationModel.applied_at >= today_start
        )
        today_result = await self.db.execute(today_stmt)
        today_count = today_result.scalar() or 0

        return total_count, today_count
