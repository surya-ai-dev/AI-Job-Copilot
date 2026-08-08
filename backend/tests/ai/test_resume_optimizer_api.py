"""API Endpoint Tests for the Resume Optimizer router."""



import uuid

import pytest

from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession



from backend.app.ai.services.candidate_profile_storage_service import CandidateProfileStorageService

from backend.app.ai.schemas.candidate_profile_schema import (

    CandidateProfile,

    ExperienceItem,

    EducationItem

)

from backend.app.jobs.models.job_model import JobModel

from backend.app.jobs.models.analysis_model import JobAnalysisModel

from backend.app.ai.repository.optimization_repository import OptimizationRepository





@pytest.fixture

async def seed_data(db_session: AsyncSession, seed_users_and_resumes):

    """Seed helper returning user, candidate profile, and job model details."""

    user_a = seed_users_and_resumes["user_a"]

    resume_a1 = seed_users_and_resumes["resume_a1"]



    # 1. Seed Active Candidate Profile

    profile_storage = CandidateProfileStorageService(db_session)

    candidate_profile = CandidateProfile(

        full_name="Alice Smith",

        skills=["Python"],

        professional_summary="Junior developer.",

        experience=[

            ExperienceItem(

                company="Tech Corp",

                role="Dev",

                start_date="2020",

                end_date="2022",

                description="Designed Python APIs."

            )

        ],

        education=[

            EducationItem(institution="State Uni", degree="BS")

        ]

    )

    db_cand = await profile_storage.store_candidate_profile(user_a, resume_a1, candidate_profile)

    await db_session.commit()



    # 2. Seed Job posting and parsed requirements analysis

    job_id = uuid.uuid4()

    db_job = JobModel(

        id=job_id,

        user_id=user_a,

        source_type="text",

        company_name="Acme Systems",

        job_title="Python Developer",

        description="Wants Python and FastAPI.",

        raw_content="Wants Python and FastAPI."

    )

    db_session.add(db_job)



    db_analysis = JobAnalysisModel(

        id=uuid.uuid4(),

        job_id=job_id,

        user_id=user_a,

        metadata_json={"experience_required": "3 years", "education_requirements": "BS"},

        skills_json=[{"name": "Python", "importance": "high"}, {"name": "FastAPI", "importance": "high"}],

        ats_keywords_json=[],

        responsibilities_json=[],

        qualifications_json=[]

    )

    db_session.add(db_analysis)

    await db_session.commit()



    # Expire to reload

    db_session.expire_all()



    return {

        "user_id": user_a,

        "candidate_profile_id": db_cand.id,

        "job_profile_id": job_id

    }





@pytest.mark.asyncio

async def test_api_optimize_resume_flow(async_client: AsyncClient, auth_headers, seed_data):

    """Test POST /api/v1/resume/optimize endpoint."""

    payload = {

        "candidate_profile_id": 1,  # Irrelevant parameter during load because service queries current active

        "job_profile_id": str(seed_data["job_profile_id"]),

        "tone": "Professional",

        "focus_skills": []

    }



    response = await async_client.post(

        "/api/v1/resume/optimize",

        json=payload,

        headers=auth_headers

    )

    assert response.status_code == 201

    data = response.json()

    assert data["run_id"] is not None

    assert data["status"] == "SUCCESS"

    assert data["final_score"] > data["initial_score"]





@pytest.mark.asyncio

async def test_api_get_optimization_details(async_client: AsyncClient, auth_headers, db_session: AsyncSession, seed_data):

    """Test GET /api/v1/resume/optimization/{id} endpoint."""

    repo = OptimizationRepository(db_session)

    run = await repo.create_run(seed_data["candidate_profile_id"], seed_data["job_profile_id"], 72.0)

    await repo.create_iteration(run.id, 1, 72.0, 75.0, ["Tasks"], "ACCEPTED")

    await db_session.commit()



    response = await async_client.get(

        f"/api/v1/resume/optimization/{run.id}",

        headers=auth_headers

    )

    assert response.status_code == 200

    data = response.json()

    assert data["run_id"] == f"opt-{run.id}"

    assert data["initial_score"] == 72.0





@pytest.mark.asyncio

async def test_api_get_optimization_details_not_found(async_client: AsyncClient, auth_headers):

    """Test GET /api/v1/resume/optimization/{id} returns 404 for missing records."""

    random_id = uuid.uuid4()

    response = await async_client.get(

        f"/api/v1/resume/optimization/{random_id}",

        headers=auth_headers

    )

    assert response.status_code == 404

    assert "Optimization run not found" in response.json()["detail"]





@pytest.mark.asyncio

async def test_api_get_history_and_best_resume(async_client: AsyncClient, auth_headers, db_session: AsyncSession, seed_data):

    """Test history and best resume endpoints."""

    repo = OptimizationRepository(db_session)

    # Seed a couple of runs

    run1 = await repo.create_run(seed_data["candidate_profile_id"], seed_data["job_profile_id"], 70.0)

    await repo.update_run_completion(run1.id, 75.0, "SUCCESS")



    run2 = await repo.create_run(seed_data["candidate_profile_id"], seed_data["job_profile_id"], 70.0)

    await repo.update_run_completion(run2.id, 88.0, "SUCCESS")

    await db_session.commit()



    # 1. Test GET /api/v1/resume/history/{candidate}

    response_history = await async_client.get(

        f"/api/v1/resume/history/{seed_data['candidate_profile_id']}",

        headers=auth_headers

    )

    assert response_history.status_code == 200

    history_data = response_history.json()

    assert len(history_data) == 2



    # 2. Test GET /api/v1/resume/best/{candidate}

    response_best = await async_client.get(

        f"/api/v1/resume/best/{seed_data['candidate_profile_id']}",

        headers=auth_headers

    )

    assert response_best.status_code == 200

    best_data = response_best.json()

    assert best_data["run_id"] == f"opt-{run2.id}"  # Max score is 88.0 (run2)

    assert best_data["best_score"] == 88.0





@pytest.mark.asyncio

async def test_api_delete_optimization_run(async_client: AsyncClient, auth_headers, db_session: AsyncSession, seed_data):

    """Test DELETE /api/v1/resume/optimization/{id} endpoint."""

    repo = OptimizationRepository(db_session)

    run = await repo.create_run(seed_data["candidate_profile_id"], seed_data["job_profile_id"], 72.0)

    await db_session.commit()



    response = await async_client.delete(

        f"/api/v1/resume/optimization/{run.id}",

        headers=auth_headers

    )

    assert response.status_code == 200

    assert "successfully deleted" in response.json()["detail"]



    # Verify deleted from DB

    db_session.expire_all()

    deleted_run = await repo.get_run(run.id)

    assert deleted_run is None
