"""Unit and integration tests for the Optimization Repository."""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.repository.optimization_repository import OptimizationRepository
from backend.app.ai.models.candidate_profile_model import CandidateProfileModel
from backend.app.jobs.models.job_model import JobModel


@pytest.mark.asyncio
async def test_optimization_repository_crud_operations(db_session: AsyncSession, seed_users_and_resumes):
    """Verify CRUD creation, retrieval, and updates across all optimization database entities."""
    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # 1. Seed CandidateProfileModel
    candidate_id = uuid.uuid4()
    db_profile = CandidateProfileModel(
        id=candidate_id,
        user_id=user_a,
        resume_id=resume_a1,
        full_name="Alice Smith",
        skills_json=[],
        experience_json=[],
        projects_json=[],
        education_json=[],
        certifications_json=[],
        is_active=True
    )
    db_session.add(db_profile)

    # 2. Seed JobModel
    job_id = uuid.uuid4()
    db_job = JobModel(
        id=job_id,
        user_id=user_a,
        source_type="text",
        company_name="Acme Inc",
        job_title="Dev",
        description="Wants Dev",
        raw_content="Wants Dev"
    )
    db_session.add(db_job)
    await db_session.commit()

    # Expire to reload seeded records
    db_session.expire_all()

    # 3. Instantiate repository
    repository = OptimizationRepository(db_session)

    # ==========================================
    # Test OptimizationRun CRUD
    # ==========================================
    run = await repository.create_run(candidate_id, job_id, 75.0)
    assert run.id is not None
    assert run.initial_score == 75.0
    assert run.status == "RUNNING"
    await db_session.commit()

    db_session.expire_all()
    fetched_run = await repository.get_run(run.id)
    assert fetched_run is not None
    assert fetched_run.id == run.id

    updated_run = await repository.update_run_completion(run.id, 88.0, "SUCCESS")
    assert updated_run.final_score == 88.0
    assert updated_run.status == "SUCCESS"
    assert updated_run.completed_at is not None
    await db_session.commit()

    # ==========================================
    # Test OptimizationIteration CRUD
    # ==========================================
    db_session.expire_all()
    iteration = await repository.create_iteration(
        run_id=run.id,
        iteration_number=1,
        pre_score=75.0,
        post_score=80.0,
        planning_tasks=["Align summary"],
        status="ACCEPTED"
    )
    assert iteration.id is not None
    assert iteration.iteration_number == 1
    await db_session.commit()

    db_session.expire_all()
    iters = await repository.get_iterations_by_run(run.id)
    assert len(iters) == 1
    assert iters[0].id == iteration.id

    # ==========================================
    # Test OptimizationChanges CRUD
    # ==========================================
    changes = await repository.create_changes(iteration.id, {"summary": "tailored summary"})
    assert changes.id is not None
    assert changes.modified_sections == {"summary": "tailored summary"}
    await db_session.commit()

    db_session.expire_all()
    fetched_changes = await repository.get_changes_by_iteration(iteration.id)
    assert fetched_changes is not None
    assert fetched_changes.id == changes.id

    # ==========================================
    # Test OptimizationHistory CRUD
    # ==========================================
    history = await repository.create_history(run.id, 1, [{"step": 1, "score": 80.0}])
    assert history.id is not None
    assert history.total_iterations == 1
    await db_session.commit()

    db_session.expire_all()
    fetched_history = await repository.get_history_by_run(run.id)
    assert fetched_history is not None
    assert fetched_history.id == history.id
