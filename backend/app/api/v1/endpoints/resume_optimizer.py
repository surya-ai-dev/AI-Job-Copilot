"""Resume Optimizer API endpoints exposing optimization triggers and telemetry."""



import uuid

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.future import select



from backend.app.database.session import get_async_db

from backend.app.auth.api.routes import get_current_active_user

from backend.app.auth.schemas.auth_schema import UserResponse

from backend.app.ai.services.resume_optimizer_service import ResumeOptimizerService

from backend.app.ai.repository.optimization_repository import OptimizationRepository

from backend.app.ai.models.optimization_model import OptimizationRunModel

from backend.app.ai.schemas.resume_optimizer_schema import (

    ResumeOptimizationRequest,

    ResumeOptimizationResponse

)



router = APIRouter(prefix="/resume", tags=["Resume Optimization Pipeline"])





def get_optimizer_service(db: AsyncSession = Depends(get_async_db)) -> ResumeOptimizerService:

    """Dependency injection helper returning initialized ResumeOptimizerService."""

    return ResumeOptimizerService(db)





@router.post("/optimize", status_code=status.HTTP_201_CREATED)

async def optimize_resume(

    payload: ResumeOptimizationRequest,

    current_user: UserResponse = Depends(get_current_active_user),

    service: ResumeOptimizerService = Depends(get_optimizer_service),

    db: AsyncSession = Depends(get_async_db)

):

    """Triggers the autonomous optimization loop to tailor the active resume profile for a job."""

    try:

        if payload.job_analysis_id is not None:

            # Backward compatibility path: use old optimization service

            from backend.app.resume.repository.optimization_repository import ResumeOptimizationRepository as OldOptimizationRepository

            from backend.app.resume.repository.resume_repository import ResumeRepository as OldResumeRepository

            from backend.app.jobs.repository.analysis_repository import JobAnalysisRepository as OldJobAnalysisRepository

            from backend.app.resume.services.optimization_service import ResumeOptimizationService as OldOptimizationService

            import os



            opt_repo = OldOptimizationRepository(db)

            resume_repo = OldResumeRepository(db)

            analysis_repo = OldJobAnalysisRepository(db)

            storage_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "storage")



            old_service = OldOptimizationService(opt_repo, resume_repo, analysis_repo, storage_path=storage_path)

            res = await old_service.optimize_resume(current_user.id, payload.job_analysis_id)

            return res



        return await service.optimize_resume(uuid.UUID(str(current_user.id)), payload)

    except ValueError as exc:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    except Exception as exc:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))





@router.get("/optimization/{id}", response_model=ResumeOptimizationResponse)

async def get_optimization_details(

    id: uuid.UUID,

    current_user: UserResponse = Depends(get_current_active_user),

    db: AsyncSession = Depends(get_async_db)

):

    """Fetches details and scores of a specific optimization run."""

    repo = OptimizationRepository(db)

    run = await repo.get_run(id)

    if not run:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization run not found.")



    # Map model properties to response schema

    # Retrieve iteration details

    iterations = await repo.get_iterations_by_run(run.id)

    history = await repo.get_history_by_run(run.id)



    # Construct schema structure

    # (Since iterations and history are database model entities, map them)

    # We can map manually or return a custom dictionary matching schema fields

    return {

        "run_id": f"opt-{run.id}",

        "candidate_profile_id": 1,

        "job_profile_id": 2,

        "status": run.status,

        "initial_score": float(run.initial_score),

        "final_score": float(run.final_score) if run.final_score is not None else 0.0,

        "score_improvement": float(run.final_score - run.initial_score) if run.final_score is not None else 0.0,

        "changes": [],

        "history": {

            "run_id": f"opt-{run.id}",

            "initial_score": float(run.initial_score),

            "final_score": float(run.final_score) if run.final_score is not None else 0.0,

            "total_iterations": history.total_iterations if history else 0,

            "status": run.status,

            "iterations": [

                {

                    "iteration_number": it.iteration_number,

                    "pre_score": float(it.pre_score),

                    "post_score": float(it.post_score),

                    "planning_tasks": it.planning_tasks or [],

                    "critic_feedback": [],

                    "validation_errors": [],

                    "decision": it.status,

                    "is_rolled_back": it.status == "REJECTED"

                }

                for it in iterations

            ],

            "created_at": run.created_at.isoformat() + "Z",

            "completed_at": run.completed_at.isoformat() + "Z" if run.completed_at else None

        }

    }





@router.get("/history/{candidate}", response_model=List[ResumeOptimizationResponse])

async def get_candidate_optimization_history(

    candidate: uuid.UUID,

    current_user: UserResponse = Depends(get_current_active_user),

    db: AsyncSession = Depends(get_async_db)

):

    """Lists all optimization runs executed for a specific candidate profile."""

    result = await db.execute(

        select(OptimizationRunModel).where(OptimizationRunModel.candidate_profile_id == candidate)

    )

    runs = result.scalars().all()



    response_list = []

    repo = OptimizationRepository(db)

    for run in runs:

        iterations = await repo.get_iterations_by_run(run.id)

        response_list.append({

            "run_id": f"opt-{run.id}",

            "candidate_profile_id": 1,

            "job_profile_id": 2,

            "status": run.status,

            "initial_score": float(run.initial_score),

            "final_score": float(run.final_score) if run.final_score is not None else 0.0,

            "score_improvement": float(run.final_score - run.initial_score) if run.final_score is not None else 0.0,

            "changes": [],

            "history": {

                "run_id": f"opt-{run.id}",

                "initial_score": float(run.initial_score),

                "final_score": float(run.final_score) if run.final_score is not None else 0.0,

                "total_iterations": len(iterations),

                "status": run.status,

                "iterations": [],

                "created_at": run.created_at.isoformat() + "Z",

                "completed_at": run.completed_at.isoformat() + "Z" if run.completed_at else None

            }

        })

    return response_list





@router.get("/best/{candidate}")

async def get_best_optimized_resume(

    candidate: uuid.UUID,

    current_user: UserResponse = Depends(get_current_active_user),

    db: AsyncSession = Depends(get_async_db)

):

    """Retrieves the details of the best performing optimized resume version for a candidate profile."""

    result = await db.execute(

        select(OptimizationRunModel)

        .where(OptimizationRunModel.candidate_profile_id == candidate)

        .order_by(OptimizationRunModel.final_score.desc())

    )

    best_run = result.scalars().first()

    if not best_run:

        raise HTTPException(

            status_code=status.HTTP_404_NOT_FOUND,

            detail="No optimization runs found for this candidate profile."

        )



    return {

        "run_id": f"opt-{best_run.id}",

        "best_score": float(best_run.final_score) if best_run.final_score is not None else 0.0,

        "completed_at": best_run.completed_at

    }





@router.delete("/optimization/{id}", status_code=status.HTTP_200_OK)

async def delete_optimization_run(

    id: uuid.UUID,

    current_user: UserResponse = Depends(get_current_active_user),

    db: AsyncSession = Depends(get_async_db)

):

    """Deletes an optimization run and cascade deletes associated checkpoints."""

    repo = OptimizationRepository(db)

    run = await repo.get_run(id)

    if not run:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization run not found.")



    await db.delete(run)

    await db.flush()

    return {"detail": "Optimization run record successfully deleted."}
