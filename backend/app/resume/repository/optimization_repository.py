# backend/app/resume/repository/optimization_repository.py
# Database access operations encapsulating SQLAlchemy transactions for resume optimization results

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from backend.app.resume.models.optimization_model import ResumeOptimizationModel
from backend.app.resume.domain.optimization import ResumeOptimization

class ResumeOptimizationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_optimization(self, opt: ResumeOptimization) -> ResumeOptimizationModel:
        """Create new database resume optimization entry."""
        db_opt = ResumeOptimizationModel(
            id=opt.id or uuid.uuid4(),
            resume_id=opt.resume_id,
            job_analysis_id=opt.job_analysis_id,
            user_id=opt.user_id,
            match_score=opt.match_details.match_score,
            ats_score=opt.ats_evaluation.score,
            optimized_file_path=opt.optimized_file_path,
            match_details_json={
                "resume_id": str(opt.match_details.resume_id),
                "job_analysis_id": str(opt.match_details.job_analysis_id),
                "match_score": opt.match_details.match_score,
                "skills_match_score": opt.match_details.skills_match_score,
                "experience_match_score": opt.match_details.experience_match_score,
                "gap_skills": opt.match_details.gap_skills
            },
            ats_evaluation_json={
                "score": opt.ats_evaluation.score,
                "explanation": opt.ats_evaluation.explanation,
                "keyword_coverage_percent": opt.ats_evaluation.keyword_coverage_percent,
                "readability_index": opt.ats_evaluation.readability_index
            },
            recommendations_json=[
                {
                    "section": r.section,
                    "change_type": r.change_type,
                    "description": r.description,
                    "original_text": r.original_text,
                    "suggested_text": r.suggested_text
                }
                for r in opt.recommendations
            ],
            optimized_summary=opt.optimized_summary,
            optimized_skills_json=opt.optimized_skills,
            created_at=opt.created_at
        )
        self.db.add(db_opt)
        await self.db.flush()
        return db_opt

    async def get_by_id(self, opt_id: uuid.UUID) -> Optional[ResumeOptimizationModel]:
        """Fetch optimization details by ID."""
        result = await self.db.execute(select(ResumeOptimizationModel).where(ResumeOptimizationModel.id == opt_id))
        return result.scalars().first()

    async def list_optimizations(self, user_id: uuid.UUID) -> List[ResumeOptimizationModel]:
        """List all optimizations for a user."""
        result = await self.db.execute(
            select(ResumeOptimizationModel).where(ResumeOptimizationModel.user_id == user_id).order_by(ResumeOptimizationModel.created_at.desc())
        )
        return result.scalars().all()

    async def delete_optimization(self, db_opt: ResumeOptimizationModel) -> None:
        """Delete optimization record from database."""
        await self.db.delete(db_opt)
        await self.db.flush()
