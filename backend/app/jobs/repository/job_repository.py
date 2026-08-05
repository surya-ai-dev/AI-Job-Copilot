# backend/app/jobs/repository/job_repository.py
# Database access operations encapsulating SQLAlchemy transactions for parsed jobs

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from backend.app.jobs.models.job_model import JobModel
from backend.app.jobs.domain.job import Job

class JobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_job(self, job: Job) -> JobModel:
        """Create new database parsed job entry."""
        db_job = JobModel(
            id=job.id or uuid.uuid4(),
            user_id=job.user_id,
            source_type=job.source.source_type,
            source_url=job.source.source_url,
            company_name=job.parsed_data.company_name,
            job_title=job.parsed_data.job_title,
            description=job.parsed_data.description,
            recruiter_email=job.parsed_data.recruiter_email,
            location=job.parsed_data.location,
            raw_content=job.raw_content,
            created_at=job.created_at
        )
        self.db.add(db_job)
        await self.db.flush()
        return db_job

    async def get_by_id(self, job_id: uuid.UUID) -> Optional[JobModel]:
        """Fetch job details by ID."""
        result = await self.db.execute(select(JobModel).where(JobModel.id == job_id))
        return result.scalars().first()

    async def list_jobs(self, user_id: uuid.UUID) -> List[JobModel]:
        """List all parsed jobs for a user."""
        result = await self.db.execute(
            select(JobModel).where(JobModel.user_id == user_id).order_by(JobModel.created_at.desc())
        )
        return result.scalars().all()

    async def delete_job(self, db_job: JobModel) -> None:
        """Delete parsed job from database."""
        await self.db.delete(db_job)
        await self.db.flush()
