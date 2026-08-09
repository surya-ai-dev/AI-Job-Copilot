"""Integration and E2E tests for Phase 7 JD recruiter email draft generation & human approval workflow."""

import uuid
import pytest
import os
import shutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.ai.services.resume_optimizer_service import ResumeOptimizerService
from backend.app.ai.services.candidate_profile_storage_service import CandidateProfileStorageService
from backend.app.ai.schemas.candidate_profile_schema import CandidateProfile, ExperienceItem, EducationItem
from backend.app.ai.schemas.resume_optimizer_schema import ResumeOptimizationRequest
from backend.app.jobs.models.job_model import JobModel
from backend.app.jobs.models.analysis_model import JobAnalysisModel
from backend.app.email.models.email_model import EmailDraftModel, EmailHistoryModel
from backend.app.email.services.email_service import EmailOutreachService
from backend.app.email.repository.email_repository import EmailRepository
from backend.app.resume.models.resume_model import ResumeModel


@pytest.mark.asyncio
async def test_phase7_email_workflow_valid_email(db_session: AsyncSession, seed_users_and_resumes):
    """Verify that a personalized email draft is generated when the JD contains a valid recruiter email."""
    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # 1. Seed Candidate Profile
    profile_storage = CandidateProfileStorageService(db_session)
    candidate_profile = CandidateProfile(
        full_name="Alice Smith",
        skills=["Python", "FastAPI"],
        professional_summary="Backend Engineer.",
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

    # 2. Seed Job with valid recruiter email
    job_id = uuid.uuid4()
    db_job = JobModel(
        id=job_id,
        user_id=user_a,
        source_type="text",
        company_name="Acme Corporation",
        job_title="Senior Python Developer",
        description="We are looking for a Python Developer. Send applications to recruiter@acme.com",
        recruiter_email="recruiter@acme.com",
        raw_content="Acme JD text"
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

    # 3. Optimize resume
    service = ResumeOptimizerService(db_session)
    request = ResumeOptimizationRequest(
        candidate_profile_id=1,
        job_profile_id=job_id,
        tone="Professional"
    )
    response = await service.optimize_resume(user_a, request)

    # 4. Assert response contains the email draft ID
    assert response.email_draft_id is not None

    # 5. Verify draft database entry
    draft_query = await db_session.execute(
        select(EmailDraftModel).where(EmailDraftModel.id == response.email_draft_id)
    )
    draft = draft_query.scalars().first()
    assert draft is not None
    assert draft.recipient_email == "recruiter@acme.com"
    assert draft.recipient_name == "Acme Corporation"
    assert "Acme Corporation" in draft.subject
    assert "Alice Smith" in draft.body
    assert "Python" in draft.body
    assert draft.attachment_path is not None
    assert os.path.exists(draft.attachment_path)


@pytest.mark.asyncio
async def test_phase7_email_workflow_no_valid_email(db_session: AsyncSession, seed_users_and_resumes):
    """Verify that NO email draft is generated when the JD has NO valid recruiter email."""
    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # 1. Seed Candidate Profile
    profile_storage = CandidateProfileStorageService(db_session)
    candidate_profile = CandidateProfile(
        full_name="Alice Smith",
        skills=["Python"],
        professional_summary="Backend Engineer.",
        experience=[],
        education=[]
    )
    await profile_storage.store_candidate_profile(user_a, resume_a1, candidate_profile)
    await db_session.commit()

    # 2. Seed Job with NO recruiter email
    job_id = uuid.uuid4()
    db_job = JobModel(
        id=job_id,
        user_id=user_a,
        source_type="text",
        company_name="No Email Corp",
        job_title="Developer",
        description="We are looking for a Developer. Apply online.",
        recruiter_email=None,
        raw_content="No email JD text"
    )
    db_session.add(db_job)

    db_analysis = JobAnalysisModel(
        id=uuid.uuid4(),
        job_id=job_id,
        user_id=user_a,
        metadata_json={},
        skills_json=[{"name": "Python", "importance": "high"}],
        ats_keywords_json=[],
        responsibilities_json=[],
        qualifications_json=[]
    )
    db_session.add(db_analysis)
    await db_session.commit()

    # Expire to reload updated records
    db_session.expire_all()

    # 3. Optimize resume
    service = ResumeOptimizerService(db_session)
    request = ResumeOptimizationRequest(
        candidate_profile_id=1,
        job_profile_id=job_id,
        tone="Professional"
    )
    response = await service.optimize_resume(user_a, request)

    # 4. Assert response contains NO email draft ID
    assert response.email_draft_id is None


@pytest.mark.asyncio
async def test_phase7_email_workflow_invalid_format_email(db_session: AsyncSession, seed_users_and_resumes):
    """Verify that NO email draft is generated when the JD has an invalid recruiter email format."""
    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # 1. Seed Candidate Profile
    profile_storage = CandidateProfileStorageService(db_session)
    candidate_profile = CandidateProfile(
        full_name="Alice Smith",
        skills=["Python"],
        professional_summary="Backend Engineer.",
        experience=[],
        education=[]
    )
    await profile_storage.store_candidate_profile(user_a, resume_a1, candidate_profile)
    await db_session.commit()

    # 2. Seed Job with invalid format recruiter email
    job_id = uuid.uuid4()
    db_job = JobModel(
        id=job_id,
        user_id=user_a,
        source_type="text",
        company_name="Bad Email Corp",
        job_title="Developer",
        description="We are looking for a Developer.",
        recruiter_email="not-an-email",
        raw_content="Bad email JD text"
    )
    db_session.add(db_job)

    db_analysis = JobAnalysisModel(
        id=uuid.uuid4(),
        job_id=job_id,
        user_id=user_a,
        metadata_json={},
        skills_json=[{"name": "Python", "importance": "high"}],
        ats_keywords_json=[],
        responsibilities_json=[],
        qualifications_json=[]
    )
    db_session.add(db_analysis)
    await db_session.commit()

    # Expire to reload updated records
    db_session.expire_all()

    # 3. Optimize resume
    service = ResumeOptimizerService(db_session)
    request = ResumeOptimizationRequest(
        candidate_profile_id=1,
        job_profile_id=job_id,
        tone="Professional"
    )
    response = await service.optimize_resume(user_a, request)

    # 4. Assert response contains NO email draft ID
    assert response.email_draft_id is None


@pytest.mark.asyncio
async def test_phase7_email_review_approve_send(db_session: AsyncSession, seed_users_and_resumes):
    """Verify the human review approval workflow where user edits, reviews, and approves/sends the draft email."""
    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # 1. Seed Candidate Profile
    profile_storage = CandidateProfileStorageService(db_session)
    candidate_profile = CandidateProfile(
        full_name="Alice Smith",
        skills=["Python"],
        professional_summary="Backend Engineer.",
        experience=[],
        education=[]
    )
    await profile_storage.store_candidate_profile(user_a, resume_a1, candidate_profile)
    await db_session.commit()

    # 2. Seed Job with valid recruiter email
    job_id = uuid.uuid4()
    db_job = JobModel(
        id=job_id,
        user_id=user_a,
        source_type="text",
        company_name="Acme Corp",
        job_title="Developer",
        description="We are looking for a Developer.",
        recruiter_email="hiring@acme.com",
        raw_content="JD text"
    )
    db_session.add(db_job)

    db_analysis = JobAnalysisModel(
        id=uuid.uuid4(),
        job_id=job_id,
        user_id=user_a,
        metadata_json={},
        skills_json=[{"name": "Python", "importance": "high"}],
        ats_keywords_json=[],
        responsibilities_json=[],
        qualifications_json=[]
    )
    db_session.add(db_analysis)
    await db_session.commit()

    # Expire to reload updated records
    db_session.expire_all()

    # 3. Optimize resume to generate the email draft
    optimizer_service = ResumeOptimizerService(db_session)
    request = ResumeOptimizationRequest(
        candidate_profile_id=1,
        job_profile_id=job_id,
        tone="Professional"
    )
    response = await optimizer_service.optimize_resume(user_a, request)
    assert response.email_draft_id is not None
    draft_id = response.email_draft_id

    # 4. Instantiate Email Outreach Service & Repository
    email_repo = EmailRepository(db_session)
    email_service = EmailOutreachService(email_repo)

    # Mock Gmail connection status to bypass send restriction
    from datetime import datetime, timedelta
    from backend.app.email.models.email_model import GmailTokenModel
    token = GmailTokenModel(
        id=uuid.uuid4(),
        user_id=user_a,
        access_token="mock_access",
        refresh_token="mock_refresh",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db_session.add(token)
    await db_session.commit()

    # 5. USER EDITS/REVIEWS the draft
    updated_subject = "Updated Application Subject"
    updated_body = "Updated application body."
    draft = await email_service.save_draft_update(
        user_id=user_a,
        draft_id=draft_id,
        recipient_email="recruiter@acme.com",
        recipient_name="Acme Recruiter",
        subject=updated_subject,
        body=updated_body
    )
    assert draft.subject == updated_subject
    assert draft.body == updated_body

    # 6. USER APPROVES AND SENDS
    history = await email_service.send_outreach_email(user_a, draft_id)
    assert history.status == "sent"
    assert history.subject == updated_subject
    assert history.body == updated_body
    assert history.recipient_email == "recruiter@acme.com"

    # 7. Check database states: draft is deleted and history is stored
    db_session.expire_all()

    # Draft should be deleted
    draft_check = await email_repo.get_draft(draft_id)
    assert draft_check is None

    # History list should contain the record
    history_list = await email_service.list_user_email_history(user_a)
    assert len(history_list) == 1
    assert history_list[0].id == history.id


@pytest.mark.asyncio
async def test_phase7_email_routes_generate_valid(
    async_client,
    auth_headers,
    db_session: AsyncSession,
    seed_users_and_resumes
):
    """Verify endpoint POST /api/v1/email/generate generates a personalized draft when valid email is found."""
    user_id = seed_users_and_resumes["user_a"]
    resume_id = seed_users_and_resumes["resume_a1"]

    # Seed Candidate Profile
    profile_storage = CandidateProfileStorageService(db_session)
    candidate_profile = CandidateProfile(
        full_name="Alice Smith",
        skills=["Python"],
        professional_summary="Backend Engineer.",
        experience=[],
        education=[]
    )
    await profile_storage.store_candidate_profile(user_id, resume_id, candidate_profile)
    await db_session.commit()

    # Seed Job and Analysis
    job_id = uuid.uuid4()
    db_job = JobModel(
        id=job_id,
        user_id=user_id,
        source_type="text",
        company_name="Acme Corp",
        job_title="Developer",
        description="We are looking for a Developer. Contact recruiter@acme.com",
        recruiter_email="recruiter@acme.com",
        raw_content="JD text"
    )
    db_session.add(db_job)

    db_analysis = JobAnalysisModel(
        id=uuid.uuid4(),
        job_id=job_id,
        user_id=user_id,
        metadata_json={},
        skills_json=[{"name": "Python", "importance": "high"}],
        ats_keywords_json=[],
        responsibilities_json=[],
        qualifications_json=[]
    )
    db_session.add(db_analysis)

    # Seed an old optimization record representing the optimized resume
    from backend.app.resume.models.optimization_model import ResumeOptimizationModel
    opt_id = uuid.uuid4()
    db_opt = ResumeOptimizationModel(
        id=opt_id,
        resume_id=resume_id,
        job_analysis_id=db_analysis.id,
        user_id=user_id,
        match_score=85,
        ats_score=90,
        optimized_file_path="/storage/test_resume.pdf",
        match_details_json={},
        ats_evaluation_json={},
        recommendations_json=[],
        optimized_summary="Tailored Summary",
        optimized_skills_json=["Python"]
    )
    db_session.add(db_opt)
    await db_session.commit()

    # Expire to reload updated records
    db_session.expire_all()

    # POST to /api/v1/email/generate
    payload = {
        "job_analysis_id": str(db_analysis.id),
        "resume_optimization_id": str(opt_id)
    }

    response = await async_client.post(
        "/api/v1/email/generate",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["recipient_email"] == "recruiter@acme.com"
    assert "Alice Smith" in res_data["body"]


@pytest.mark.asyncio
async def test_phase7_email_routes_generate_invalid(
    async_client,
    auth_headers,
    db_session: AsyncSession,
    seed_users_and_resumes
):
    """Verify endpoint POST /api/v1/email/generate fails with 400 when no valid email is found in job details."""
    user_id = seed_users_and_resumes["user_a"]
    resume_id = seed_users_and_resumes["resume_a1"]

    # Seed Candidate Profile
    profile_storage = CandidateProfileStorageService(db_session)
    candidate_profile = CandidateProfile(
        full_name="Alice Smith",
        skills=["Python"],
        professional_summary="Backend Engineer.",
        experience=[],
        education=[]
    )
    await profile_storage.store_candidate_profile(user_id, resume_id, candidate_profile)
    await db_session.commit()

    # Seed Job with no email
    job_id = uuid.uuid4()
    db_job = JobModel(
        id=job_id,
        user_id=user_id,
        source_type="text",
        company_name="Acme Corp",
        job_title="Developer",
        description="We are looking for a Developer.",
        recruiter_email=None,
        raw_content="JD text"
    )
    db_session.add(db_job)

    db_analysis = JobAnalysisModel(
        id=uuid.uuid4(),
        job_id=job_id,
        user_id=user_id,
        metadata_json={},
        skills_json=[{"name": "Python", "importance": "high"}],
        ats_keywords_json=[],
        responsibilities_json=[],
        qualifications_json=[]
    )
    db_session.add(db_analysis)

    # Seed an old optimization record representing the optimized resume
    from backend.app.resume.models.optimization_model import ResumeOptimizationModel
    opt_id = uuid.uuid4()
    db_opt = ResumeOptimizationModel(
        id=opt_id,
        resume_id=resume_id,
        job_analysis_id=db_analysis.id,
        user_id=user_id,
        match_score=85,
        ats_score=90,
        optimized_file_path="/storage/test_resume.pdf",
        match_details_json={},
        ats_evaluation_json={},
        recommendations_json=[],
        optimized_summary="Tailored Summary",
        optimized_skills_json=["Python"]
    )
    db_session.add(db_opt)
    await db_session.commit()

    # Expire to reload updated records
    db_session.expire_all()

    # POST to /api/v1/email/generate
    payload = {
        "job_analysis_id": str(db_analysis.id),
        "resume_optimization_id": str(opt_id)
    }

    response = await async_client.post(
        "/api/v1/email/generate",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "No valid recruiter/application email found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_phase7_email_workflow_missing_optimized_file(db_session: AsyncSession, seed_users_and_resumes):
    """Verify that if the optimized resume attachment is physically missing, sending fails safely."""
    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # Seed Candidate Profile
    profile_storage = CandidateProfileStorageService(db_session)
    candidate_profile = CandidateProfile(
        full_name="Alice Smith",
        skills=["Python"],
        professional_summary="Backend Engineer.",
        experience=[],
        education=[]
    )
    await profile_storage.store_candidate_profile(user_a, resume_a1, candidate_profile)
    await db_session.commit()

    # Seed Job
    job_id = uuid.uuid4()
    db_job = JobModel(
        id=job_id,
        user_id=user_a,
        source_type="text",
        company_name="Acme Corp",
        job_title="Developer",
        description="Contact recruiter@acme.com",
        recruiter_email="recruiter@acme.com",
        raw_content="JD text"
    )
    db_session.add(db_job)

    db_analysis = JobAnalysisModel(
        id=uuid.uuid4(),
        job_id=job_id,
        user_id=user_a,
        metadata_json={},
        skills_json=[{"name": "Python", "importance": "high"}],
        ats_keywords_json=[],
        responsibilities_json=[],
        qualifications_json=[]
    )
    db_session.add(db_analysis)
    await db_session.commit()

    # Optimize to create draft
    optimizer_service = ResumeOptimizerService(db_session)
    request = ResumeOptimizationRequest(
        candidate_profile_id=1,
        job_profile_id=job_id,
        tone="Professional"
    )
    response = await optimizer_service.optimize_resume(user_a, request)
    draft_id = response.email_draft_id

    # Mock Gmail connection status to bypass send restriction
    from datetime import datetime, timedelta
    from backend.app.email.models.email_model import GmailTokenModel
    token = GmailTokenModel(
        id=uuid.uuid4(),
        user_id=user_a,
        access_token="mock_access",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db_session.add(token)
    await db_session.commit()

    # Expire to reload updated records
    db_session.expire_all()

    email_repo = EmailRepository(db_session)
    email_service = EmailOutreachService(email_repo)

    draft = await email_repo.get_draft(draft_id)
    assert draft is not None

    # Physically delete the attachment file
    if draft.attachment_path and os.path.exists(draft.attachment_path):
        os.remove(draft.attachment_path)

    # Attempt to send and assert safe failure
    from backend.app.shared.exceptions import NotFoundException
    with pytest.raises(NotFoundException) as exc_info:
        await email_service.send_outreach_email(user_a, draft_id)
    assert exc_info.value.code == "ATTACHMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_phase7_email_workflow_reject_draft(db_session: AsyncSession, seed_users_and_resumes):
    """Verify that a draft can be cancelled/rejected (deleted)."""
    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # Seed Candidate Profile
    profile_storage = CandidateProfileStorageService(db_session)
    candidate_profile = CandidateProfile(full_name="Alice Smith", skills=["Python"])
    await profile_storage.store_candidate_profile(user_a, resume_a1, candidate_profile)
    await db_session.commit()

    # Seed Job
    job_id = uuid.uuid4()
    db_job = JobModel(
        id=job_id,
        user_id=user_a,
        source_type="text",
        company_name="Acme Corp",
        job_title="Developer",
        description="Contact recruiter@acme.com",
        recruiter_email="recruiter@acme.com",
        raw_content="JD text"
    )
    db_session.add(db_job)

    db_analysis = JobAnalysisModel(
        id=uuid.uuid4(),
        job_id=job_id,
        user_id=user_a,
        metadata_json={},
        skills_json=[{"name": "Python", "importance": "high"}],
        ats_keywords_json=[],
        responsibilities_json=[],
        qualifications_json=[]
    )
    db_session.add(db_analysis)
    await db_session.commit()

    optimizer_service = ResumeOptimizerService(db_session)
    request = ResumeOptimizationRequest(
        candidate_profile_id=1,
        job_profile_id=job_id,
        tone="Professional"
    )
    response = await optimizer_service.optimize_resume(user_a, request)
    draft_id = response.email_draft_id

    # Expire to reload updated records
    db_session.expire_all()

    email_repo = EmailRepository(db_session)
    email_service = EmailOutreachService(email_repo)

    # Reject / Delete the draft
    await email_service.delete_user_draft(user_a, draft_id)

    # Confirm it's gone
    db_session.expire_all()
    draft = await email_repo.get_draft(draft_id)
    assert draft is None


@pytest.mark.asyncio
async def test_phase7_email_workflow_cannot_send_twice(db_session: AsyncSession, seed_users_and_resumes):
    """Verify that a draft cannot be approved/sent twice."""
    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # Seed Candidate Profile
    profile_storage = CandidateProfileStorageService(db_session)
    candidate_profile = CandidateProfile(full_name="Alice Smith", skills=["Python"])
    await profile_storage.store_candidate_profile(user_a, resume_a1, candidate_profile)
    await db_session.commit()

    # Seed Job
    job_id = uuid.uuid4()
    db_job = JobModel(
        id=job_id,
        user_id=user_a,
        source_type="text",
        company_name="Acme Corp",
        job_title="Developer",
        description="Contact recruiter@acme.com",
        recruiter_email="recruiter@acme.com",
        raw_content="JD text"
    )
    db_session.add(db_job)

    db_analysis = JobAnalysisModel(
        id=uuid.uuid4(),
        job_id=job_id,
        user_id=user_a,
        metadata_json={},
        skills_json=[{"name": "Python", "importance": "high"}],
        ats_keywords_json=[],
        responsibilities_json=[],
        qualifications_json=[]
    )
    db_session.add(db_analysis)
    await db_session.commit()

    optimizer_service = ResumeOptimizerService(db_session)
    request = ResumeOptimizationRequest(
        candidate_profile_id=1,
        job_profile_id=job_id,
        tone="Professional"
    )
    response = await optimizer_service.optimize_resume(user_a, request)
    draft_id = response.email_draft_id

    # Mock Gmail connection status to bypass send restriction
    from datetime import datetime, timedelta
    from backend.app.email.models.email_model import GmailTokenModel
    token = GmailTokenModel(
        id=uuid.uuid4(),
        user_id=user_a,
        access_token="mock_access",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db_session.add(token)
    await db_session.commit()

    # Expire to reload updated records
    db_session.expire_all()

    email_repo = EmailRepository(db_session)
    email_service = EmailOutreachService(email_repo)

    # 1st Send succeeds
    await email_service.send_outreach_email(user_a, draft_id)

    # 2nd Send fails
    from backend.app.shared.exceptions import NotFoundException
    with pytest.raises(NotFoundException) as exc_info:
        await email_service.send_outreach_email(user_a, draft_id)
    assert exc_info.value.code == "DRAFT_NOT_FOUND"


@pytest.mark.asyncio
async def test_phase7_email_workflow_user_isolation(db_session: AsyncSession, seed_users_and_resumes):
    """Verify that a user cannot access or modify another user's draft."""
    user_a = seed_users_and_resumes["user_a"]
    user_b = seed_users_and_resumes["user_b"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # Seed Candidate Profile
    profile_storage = CandidateProfileStorageService(db_session)
    candidate_profile = CandidateProfile(full_name="Alice Smith", skills=["Python"])
    await profile_storage.store_candidate_profile(user_a, resume_a1, candidate_profile)
    await db_session.commit()

    # Seed Job
    job_id = uuid.uuid4()
    db_job = JobModel(
        id=job_id,
        user_id=user_a,
        source_type="text",
        company_name="Acme Corp",
        job_title="Developer",
        description="Contact recruiter@acme.com",
        recruiter_email="recruiter@acme.com",
        raw_content="JD text"
    )
    db_session.add(db_job)

    db_analysis = JobAnalysisModel(
        id=uuid.uuid4(),
        job_id=job_id,
        user_id=user_a,
        metadata_json={},
        skills_json=[{"name": "Python", "importance": "high"}],
        ats_keywords_json=[],
        responsibilities_json=[],
        qualifications_json=[]
    )
    db_session.add(db_analysis)
    await db_session.commit()

    optimizer_service = ResumeOptimizerService(db_session)
    request = ResumeOptimizationRequest(
        candidate_profile_id=1,
        job_profile_id=job_id,
        tone="Professional"
    )
    response = await optimizer_service.optimize_resume(user_a, request)
    draft_id = response.email_draft_id

    # Expire to reload updated records
    db_session.expire_all()

    email_repo = EmailRepository(db_session)
    email_service = EmailOutreachService(email_repo)

    from backend.app.shared.exceptions import NotFoundException

    # User B tries to update User A's draft -> fails
    with pytest.raises(NotFoundException) as exc_info:
        await email_service.save_draft_update(
            user_id=user_b,
            draft_id=draft_id,
            recipient_email="another@recruiter.com",
            recipient_name="Another Recruiter",
            subject="Hack Subject",
            body="Hack Body"
        )
    assert exc_info.value.code == "DRAFT_NOT_FOUND"

    # User B tries to delete User A's draft -> fails
    with pytest.raises(NotFoundException) as exc_info:
        await email_service.delete_user_draft(user_b, draft_id)
    assert exc_info.value.code == "DRAFT_NOT_FOUND"

    # User B tries to send User A's draft -> fails
    with pytest.raises(NotFoundException) as exc_info:
        await email_service.send_outreach_email(user_b, draft_id)
    assert exc_info.value.code == "DRAFT_NOT_FOUND"


@pytest.mark.asyncio
async def test_phase7_email_workflow_invalid_updates(db_session: AsyncSession, seed_users_and_resumes):
    """Verify that updating a draft with empty fields or invalid emails is rejected."""
    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # Seed Candidate Profile
    profile_storage = CandidateProfileStorageService(db_session)
    candidate_profile = CandidateProfile(full_name="Alice Smith", skills=["Python"])
    await profile_storage.store_candidate_profile(user_a, resume_a1, candidate_profile)
    await db_session.commit()

    # Seed Job
    job_id = uuid.uuid4()
    db_job = JobModel(
        id=job_id,
        user_id=user_a,
        source_type="text",
        company_name="Acme Corp",
        job_title="Developer",
        description="Contact recruiter@acme.com",
        recruiter_email="recruiter@acme.com",
        raw_content="JD text"
    )
    db_session.add(db_job)

    db_analysis = JobAnalysisModel(
        id=uuid.uuid4(),
        job_id=job_id,
        user_id=user_a,
        metadata_json={},
        skills_json=[{"name": "Python", "importance": "high"}],
        ats_keywords_json=[],
        responsibilities_json=[],
        qualifications_json=[]
    )
    db_session.add(db_analysis)
    await db_session.commit()

    optimizer_service = ResumeOptimizerService(db_session)
    request = ResumeOptimizationRequest(
        candidate_profile_id=1,
        job_profile_id=job_id,
        tone="Professional"
    )
    response = await optimizer_service.optimize_resume(user_a, request)
    draft_id = response.email_draft_id

    # Expire to reload updated records
    db_session.expire_all()

    email_repo = EmailRepository(db_session)
    email_service = EmailOutreachService(email_repo)

    from backend.app.shared.exceptions import ValidationException

    # 1. Update with invalid email -> raises ValidationException
    with pytest.raises(ValidationException):
        await email_service.save_draft_update(
            user_id=user_a,
            draft_id=draft_id,
            recipient_email="invalid-email-format",
            recipient_name="Recruiter",
            subject="Subject",
            body="Body"
        )

    # 2. Update with empty subject -> raises ValidationException
    with pytest.raises(ValidationException):
        await email_service.save_draft_update(
            user_id=user_a,
            draft_id=draft_id,
            recipient_email="recruiter@acme.com",
            recipient_name="Recruiter",
            subject="  ",
            body="Body"
        )

    # 3. Update with empty body -> raises ValidationException
    with pytest.raises(ValidationException):
        await email_service.save_draft_update(
            user_id=user_a,
            draft_id=draft_id,
            recipient_email="recruiter@acme.com",
            recipient_name="Recruiter",
            subject="Subject",
            body=""
        )
