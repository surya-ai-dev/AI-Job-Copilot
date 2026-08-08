"""Optimization Repository for managing database CRUD operations for AI Optimization runs."""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.ai.models.optimization_model import (
    OptimizationRunModel,
    OptimizationIterationModel,
    OptimizationChangesModel,
    OptimizationHistoryModel
)


class OptimizationRepository:
    """Encapsulates transactional database CRUD operations for Optimization entities using SQLAlchemy Async."""

    def __init__(self, db: AsyncSession):
        """Initializes the repository with an AsyncSession reference."""
        self.db = db

    # ==========================================
    # OptimizationRun CRUD
    # ==========================================

    async def create_run(
        self,
        candidate_profile_id: uuid.UUID,
        job_profile_id: uuid.UUID,
        initial_score: float
    ) -> OptimizationRunModel:
        """Saves a new optimization run session record."""
        run = OptimizationRunModel(
            id=uuid.uuid4(),
            candidate_profile_id=candidate_profile_id,
            job_profile_id=job_profile_id,
            initial_score=initial_score,
            status="RUNNING",
            created_at=datetime.utcnow()
        )
        self.db.add(run)
        await self.db.flush()
        return run

    async def get_run(self, run_id: uuid.UUID) -> Optional[OptimizationRunModel]:
        """Retrieves an optimization run record by ID."""
        result = await self.db.execute(
            select(OptimizationRunModel).where(OptimizationRunModel.id == run_id)
        )
        return result.scalars().first()

    async def update_run_completion(
        self,
        run_id: uuid.UUID,
        final_score: float,
        status: str
    ) -> Optional[OptimizationRunModel]:
        """Updates run completion score, status, and timestamp."""
        run = await self.get_run(run_id)
        if run:
            run.final_score = final_score
            run.status = status
            run.completed_at = datetime.utcnow()
            await self.db.flush()
        return run

    # ==========================================
    # OptimizationIteration CRUD
    # ==========================================

    async def create_iteration(
        self,
        run_id: uuid.UUID,
        iteration_number: int,
        pre_score: float,
        post_score: float,
        planning_tasks: List[str],
        status: str
    ) -> OptimizationIterationModel:
        """Saves a new iteration loop checkpoint."""
        iteration = OptimizationIterationModel(
            id=uuid.uuid4(),
            run_id=run_id,
            iteration_number=iteration_number,
            pre_score=pre_score,
            post_score=post_score,
            planning_tasks=planning_tasks,
            status=status,
            created_at=datetime.utcnow()
        )
        self.db.add(iteration)
        await self.db.flush()
        return iteration

    async def get_iterations_by_run(self, run_id: uuid.UUID) -> List[OptimizationIterationModel]:
        """Retrieves all iteration checkpoints associated with a run."""
        result = await self.db.execute(
            select(OptimizationIterationModel)
            .where(OptimizationIterationModel.run_id == run_id)
            .order_by(OptimizationIterationModel.iteration_number.asc())
        )
        return list(result.scalars().all())

    # ==========================================
    # OptimizationChanges CRUD
    # ==========================================

    async def create_changes(
        self,
        iteration_id: uuid.UUID,
        modified_sections: dict
    ) -> OptimizationChangesModel:
        """Saves section changes associated with an iteration."""
        changes = OptimizationChangesModel(
            id=uuid.uuid4(),
            iteration_id=iteration_id,
            modified_sections=modified_sections,
            created_at=datetime.utcnow()
        )
        self.db.add(changes)
        await self.db.flush()
        return changes

    async def get_changes_by_iteration(self, iteration_id: uuid.UUID) -> Optional[OptimizationChangesModel]:
        """Retrieves section changes linked to an iteration ID."""
        result = await self.db.execute(
            select(OptimizationChangesModel).where(OptimizationChangesModel.iteration_id == iteration_id)
        )
        return result.scalars().first()

    # ==========================================
    # OptimizationHistory CRUD
    # ==========================================

    async def create_history(
        self,
        run_id: uuid.UUID,
        total_iterations: int,
        optimization_log: List[dict]
    ) -> OptimizationHistoryModel:
        """Saves aggregate run history log metadata."""
        history = OptimizationHistoryModel(
            id=uuid.uuid4(),
            run_id=run_id,
            total_iterations=total_iterations,
            optimization_log=optimization_log,
            created_at=datetime.utcnow()
        )
        self.db.add(history)
        await self.db.flush()
        return history

    async def get_history_by_run(self, run_id: uuid.UUID) -> Optional[OptimizationHistoryModel]:
        """Retrieves history metadata linked to a run ID."""
        result = await self.db.execute(
            select(OptimizationHistoryModel).where(OptimizationHistoryModel.run_id == run_id)
        )
        return result.scalars().first()
