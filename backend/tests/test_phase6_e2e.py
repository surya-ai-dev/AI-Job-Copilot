"""Complete End-to-End Tests for Phase 6 Autonomous Resume Optimizer Engine."""



import uuid

import pytest

from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.future import select



from backend.app.ai.services.candidate_profile_storage_service import CandidateProfileStorageService

from backend.app.ai.schemas.candidate_profile_schema import (

    CandidateProfile,

    ExperienceItem,

    EducationItem

)

from backend.app.jobs.models.job_model import JobModel

from backend.app.jobs.models.analysis_model import JobAnalysisModel

from backend.app.ai.models.optimization_model import (

    OptimizationRunModel,

    OptimizationIterationModel,

    OptimizationChangesModel,

    OptimizationHistoryModel

)

from backend.app.ai.repository.optimization_repository import OptimizationRepository





@pytest.mark.asyncio

async def test_phase6_complete_end_to_end_flow(

    async_client: AsyncClient,

    auth_headers,

    db_session: AsyncSession,

    seed_users_and_resumes

):

    """End-to-End test representing the full user journey of resume optimization.



    Scenario: Ingest/Upload Profile -> Ingest Job Requirements -> Run Multi-Agent Loop

    -> Factual Validation -> Persist check -> Fetch telemetry API -> Deletion cascade.

    """

    user_id = seed_users_and_resumes["user_a"]

    resume_id = seed_users_and_resumes["resume_a1"]



    # ----------------------------------------------------

    # Step 1: Resume Upload / Ingest Candidate Profile

    # ----------------------------------------------------

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

    db_cand = await profile_storage.store_candidate_profile(user_id, resume_id, candidate_profile)

    await db_session.commit()



    # ----------------------------------------------------

    # Step 2: Job Ingest / Parse Job Requirements

    # ----------------------------------------------------

    job_id = uuid.uuid4()

    db_job = JobModel(

        id=job_id,

        user_id=user_id,

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

        user_id=user_id,

        metadata_json={"experience_required": "3 years", "education_requirements": "BS"},

        skills_json=[{"name": "Python", "importance": "high"}, {"name": "FastAPI", "importance": "high"}],

        ats_keywords_json=[],

        responsibilities_json=[],

        qualifications_json=[]

    )

    db_session.add(db_analysis)

    await db_session.commit()



    # Expire session to load new values cleanly

    db_session.expire_all()



    # ----------------------------------------------------

    # Step 3: Run Multi-Agent Optimization Loop API

    # ----------------------------------------------------

    payload = {

        "candidate_profile_id": 1, # Not queried as service fetches current active profile

        "job_profile_id": str(job_id),

        "tone": "Bold",

        "focus_skills": []

    }



    response = await async_client.post(

        "/api/v1/resume/optimize",

        json=payload,

        headers=auth_headers

    )

    assert response.status_code == 201, f"POST /resume/optimize failed: {response.text}"

    response_data = response.json()

    run_id_str = response_data["run_id"]

    assert run_id_str.startswith("opt-")

    run_id = uuid.UUID(run_id_str.removeprefix("opt-"))



    # ----------------------------------------------------

    # Step 4: Verification - Score Improves & Target Reached

    # ----------------------------------------------------

    assert response_data["status"] == "SUCCESS"

    assert response_data["final_score"] > response_data["initial_score"]

    assert response_data["score_improvement"] > 0.0



    # ----------------------------------------------------

    # Step 5: Verification - Factual Validation (No Hallucination)

    # ----------------------------------------------------

    # Load optimization history run to verify database logging

    repo = OptimizationRepository(db_session)

    db_run = await repo.get_run(run_id)

    assert db_run is not None

    assert db_run.status == "SUCCESS"



    # Query latest iteration to check decisions

    iterations = await repo.get_iterations_by_run(run_id)

    assert len(iterations) > 0

    assert iterations[0].status == "ACCEPTED"  # Safe rewords accepted



    # Check database persistence for history logs

    db_history = await repo.get_history_by_run(run_id)

    assert db_history is not None

    assert db_history.total_iterations == len(iterations)



    # ----------------------------------------------------

    # Step 6: Verification - API telemetry retrieval

    # ----------------------------------------------------

    # GET details

    get_response = await async_client.get(

        f"/api/v1/resume/optimization/{run_id}",

        headers=auth_headers

    )

    assert get_response.status_code == 200

    details = get_response.json()

    assert details["run_id"] == run_id_str

    assert details["status"] == "SUCCESS"



    # GET history list

    history_response = await async_client.get(

        f"/api/v1/resume/history/{db_cand.id}",

        headers=auth_headers

    )

    assert history_response.status_code == 200

    history_list = history_response.json()

    assert len(history_list) >= 1



    # GET best resume metadata

    best_response = await async_client.get(

        f"/api/v1/resume/best/{db_cand.id}",

        headers=auth_headers

    )

    assert best_response.status_code == 200

    best_data = best_response.json()

    assert best_data["run_id"] == run_id_str



    # ----------------------------------------------------

    # Step 7: Verification - Deletion & Cascades

    # ----------------------------------------------------

    delete_response = await async_client.delete(

        f"/api/v1/resume/optimization/{run_id}",

        headers=auth_headers

    )

    assert delete_response.status_code == 200



    # Assert cascade deletes

    db_session.expire_all()

    assert await repo.get_run(run_id) is None

    assert len(await repo.get_iterations_by_run(run_id)) == 0

    assert await repo.get_history_by_run(run_id) is None
