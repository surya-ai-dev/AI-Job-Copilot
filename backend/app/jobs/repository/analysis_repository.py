# backend/app/jobs/repository/analysis_repository.py
# Database access operations encapsulating SQLAlchemy transactions for job analysis results

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from backend.app.jobs.models.analysis_model import JobAnalysisModel
from backend.app.jobs.domain.analysis import JobAnalysis

class JobAnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_analysis(self, analysis: JobAnalysis) -> JobAnalysisModel:
        """Create new database job analysis entry."""
        db_analysis = JobAnalysisModel(
            id=analysis.id or uuid.uuid4(),
            job_id=analysis.job_id,
            user_id=analysis.user_id,
            confidence_score=analysis.confidence_score,
            llm_provider=analysis.llm_provider,
            prompt_version=analysis.prompt_version,
            processing_time_ms=analysis.processing_time_ms,
            # Map dataclass lists/objects to dictionaries/lists for JSON columns serialization
            metadata_json={
                "seniority": analysis.metadata.seniority,
                "employment_type": analysis.metadata.employment_type,
                "education_requirements": analysis.metadata.education_requirements,
                "certifications": analysis.metadata.certifications
            },
            skills_json=[
                {"name": s.name, "category": s.category, "importance": s.importance}
                for s in analysis.skills
            ],
            ats_keywords_json=[
                {"word": k.word, "category": k.category}
                for k in analysis.ats_keywords
            ],
            responsibilities_json=analysis.responsibilities,
            qualifications_json=analysis.qualifications,
            created_at=analysis.created_at
        )
        self.db.add(db_analysis)
        await self.db.flush()
        return db_analysis

    async def get_by_id(self, analysis_id: uuid.UUID) -> Optional[JobAnalysisModel]:
        """Fetch analysis details by ID."""
        result = await self.db.execute(select(JobAnalysisModel).where(JobAnalysisModel.id == analysis_id))
        return result.scalars().first()

    async def get_by_job_id(self, job_id: uuid.UUID) -> Optional[JobAnalysisModel]:
        """Fetch analysis details by job ID."""
        result = await self.db.execute(select(JobAnalysisModel).where(JobAnalysisModel.job_id == job_id))
        return result.scalars().first()

    async def list_analyses(self, user_id: uuid.UUID) -> List[JobAnalysisModel]:
        """List all parsed analyses for a user."""
        result = await self.db.execute(
            select(JobAnalysisModel).where(JobAnalysisModel.user_id == user_id).order_by(JobAnalysisModel.created_at.desc())
        )
        return result.scalars().all()

    async def delete_analysis(self, db_analysis: JobAnalysisModel) -> None:
        """Delete parsed analysis from database."""
        await self.db.delete(db_analysis)
        await self.db.flush()
