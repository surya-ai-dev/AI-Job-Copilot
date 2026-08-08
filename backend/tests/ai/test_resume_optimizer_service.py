"""Integration tests for the Resume Optimizer Service."""



import uuid

import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.future import select



from backend.app.ai.services.resume_optimizer_service import ResumeOptimizerService

from backend.app.ai.services.candidate_profile_storage_service import CandidateProfileStorageService

from backend.app.ai.models.candidate_profile_model import CandidateProfileModel

from backend.app.ai.schemas.candidate_profile_schema import (

    CandidateProfile,

    ExperienceItem,

    EducationItem

)

from backend.app.jobs.models.job_model import JobModel

from backend.app.jobs.models.analysis_model import JobAnalysisModel

from backend.app.ai.schemas.resume_optimizer_schema import (

    ResumeOptimizationRequest,

    OptimizationRunStatus

)





@pytest.mark.asyncio

async def test_integration_resume_optimizer_service_flow(db_session: AsyncSession, seed_users_and_resumes):

    """Verify end-to-end service loading, execution of optimization, and DB persistence."""

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

    await profile_storage.store_candidate_profile(user_a, resume_a1, candidate_profile)

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



    # Expire to reload updated records

    db_session.expire_all()



    # 3. Instantiate and run ResumeOptimizerService

    service = ResumeOptimizerService(db_session)

    request = ResumeOptimizationRequest(

        candidate_profile_id=1,  # Irrelevant parameter during load because service queries current active

        job_profile_id=job_id,

        tone="Professional"

    )



    response = await service.optimize_resume(user_a, request)



    # 4. Verify loop controller was run and response is populated

    assert response.status == OptimizationRunStatus.SUCCESS

    assert response.initial_score < response.final_score

    assert response.score_improvement > 0.0

    assert len(response.changes) > 0



    # 5. Verify database persistence: Check that a new tailored (inactive) profile was created

    # Query database for all profiles of the user

    query = await db_session.execute(

        select(CandidateProfileModel)

        .where(CandidateProfileModel.user_id == user_a)

        .order_by(CandidateProfileModel.created_at.desc())

    )

    profiles = query.scalars().all()



    # We should have 2 profiles (1 active from step 1, and 1 inactive version created by optimizer)

    assert len(profiles) == 2

    assert profiles[0].is_active is False  # Latest profile (inactive version)

    assert profiles[1].is_active is True   # Original profile (still active master)

    assert "FastAPI" in profiles[0].skills_json





@pytest.mark.asyncio

async def test_integration_resume_optimizer_invalid_job_id(db_session: AsyncSession, seed_users_and_resumes):

    """Verify service raises value error if requested job ID does not exist."""

    user_a = seed_users_and_resumes["user_a"]

    resume_a1 = seed_users_and_resumes["resume_a1"]



    profile_storage = CandidateProfileStorageService(db_session)

    candidate_profile = CandidateProfile(full_name="Alice Smith", skills=["Python"])

    await profile_storage.store_candidate_profile(user_a, resume_a1, candidate_profile)

    await db_session.commit()



    service = ResumeOptimizerService(db_session)

    request = ResumeOptimizationRequest(

        candidate_profile_id=1,

        job_profile_id=uuid.uuid4(),  # Random missing ID

        tone="Professional"

    )



    with pytest.raises(ValueError) as exc_info:

        await service.optimize_resume(user_a, request)

    assert "Job not found" in str(exc_info.value)
