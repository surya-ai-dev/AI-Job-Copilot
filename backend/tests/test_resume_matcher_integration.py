"""Integration tests verifying the end-to-end Resume Matching pipeline with database storage."""

import io
import uuid
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.ai.services.resume_parser_service import ResumeParserService
from backend.app.ai.services.candidate_profile_service import CandidateProfileService
from backend.app.ai.services.candidate_profile_storage_service import CandidateProfileStorageService
from backend.app.ai.schemas.candidate_profile_storage_schema import CandidateProfileStorageResponse
from backend.app.ai.services.job_parser_service import JobParserService
from backend.app.ai.services.resume_matcher_service import ResumeMatcherService
from backend.app.jobs.repository.job_repository import JobRepository
from backend.app.jobs.domain.job import Job, JobSource, ParsedJob
from backend.app.database.session import Base


# ==========================================
# Mock Ingest Data
# ==========================================

RESUME_STRONG_TEXT = """
Jane Doe
jane.doe@example.com | +1 555-019-2834
linkedin.com/in/janedoe

Summary
Senior Systems Engineer with 8 years of experience building Python microservices.

Skills
Python, FastAPI, Docker, PostgreSQL, Kubernetes, Go

Work Experience
Google - Tech Lead | 2018 - Present
- Designed cloud platform microservices.

Projects
Job Copilot - Creator
- Built organiser tools using Docker.

Education
Stanford University - MS in Computer Science | 2016 - 2018
"""

RESUME_WEAK_TEXT = """
Bob Smith
bob@example.com

Summary
Junior Frontend Assistant with 1 year experience.

Skills
HTML, CSS, JavaScript

Education
DeVry - Associate Diploma
"""

JOB_JD_TEXT = """
Acme Systems
Senior Python Developer
Department: Engineering
Work Mode: Remote
Experience Required: 6+ years
Education Required: Master's Degree
Salary: $150k

Required Skills
Python, FastAPI, Docker, PostgreSQL

Preferred Skills
Go, Kubernetes
"""


# Helpers for pdfplumber mock
class MockPDF:
    def __init__(self, text: str):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = text
        self.pages = [mock_page]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# ==========================================
# 0. Pytest Setup Fixtures
# ==========================================

@pytest.fixture(autouse=True)
async def setup_integration_tables(db_session: AsyncSession):
    """Ensures all necessary tables are initialized in the SQLite test database."""
    from backend.app.auth.models.user_model import UserModel
    from backend.app.resume.models.resume_model import ResumeModel
    from backend.app.ai.models.candidate_profile_model import CandidateProfileModel
    from backend.app.jobs.models.job_model import JobModel

    conn = await db_session.connection()
    await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def seed_users_and_resumes(db_session: AsyncSession):
    """Seeds database with User and Resume records to support ForeignKey integrity."""
    from backend.app.auth.models.user_model import UserModel
    from backend.app.resume.models.resume_model import ResumeModel

    # Seed User A
    user_a_id = uuid.uuid4()
    user_a = UserModel(
        id=user_a_id,
        email=f"matcher_user_a_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hashed_password",
        first_name="Jane",
        last_name="Doe",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user_a)

    # Seed User B
    user_id_b = uuid.uuid4()
    user_b = UserModel(
        id=user_id_b,
        email=f"matcher_user_b_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hashed_password",
        first_name="Bob",
        last_name="Smith",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user_b)

    # Seed Resume A1
    resume_a1_id = uuid.uuid4()
    resume_a1 = ResumeModel(
        id=resume_a1_id,
        user_id=user_a_id,
        file_path="/app/resumes/dummy_a1.pdf",
        file_name="resume_v1.pdf",
        file_size=1000,
        content_type="application/pdf",
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(resume_a1)

    # Seed Resume A2 (for profile replacement)
    resume_a2_id = uuid.uuid4()
    resume_a2 = ResumeModel(
        id=resume_a2_id,
        user_id=user_a_id,
        file_path="/app/resumes/dummy_a2.pdf",
        file_name="resume_v2.pdf",
        file_size=2000,
        content_type="application/pdf",
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(resume_a2)

    await db_session.flush()
    return {
        "user_a": user_a_id,
        "user_b": user_id_b,
        "resume_a1": resume_a1_id,
        "resume_a2": resume_a2_id
    }


# ==========================================
# 1. Integration Test Cases
# ==========================================

@pytest.mark.asyncio
async def test_integration_matcher_complete_workflow(db_session: AsyncSession, seed_users_and_resumes):
    # Initialize all service and repository components
    resume_parser = ResumeParserService()
    profile_extractor = CandidateProfileService()
    profile_storage = CandidateProfileStorageService(db_session)
    job_parser = JobParserService()
    job_repo = JobRepository(db_session)
    matcher = ResumeMatcherService()

    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # 1. Parse and extract candidate profile from file
    pdf_stream = io.BytesIO(b"dummy pdf bytes")
    with patch("backend.app.ai.agents.resume_parser.pdfplumber.open", return_value=MockPDF(RESUME_STRONG_TEXT)):
        parsed_resume = resume_parser.parse_stream(pdf_stream, "pdf")
    
    extracted_profile = profile_extractor.extract_profile(parsed_resume.raw_text)
    
    # 2. Store Candidate Profile in DB
    db_profile = await profile_storage.store_candidate_profile(user_a, resume_a1, extracted_profile)
    assert db_profile.is_active is True

    # 3. Parse and store Job Posting
    parsed_job = job_parser.parse_job(JOB_JD_TEXT, "text")
    job_domain = Job(
        user_id=user_a,
        source=JobSource(source_type="text"),
        parsed_data=ParsedJob(
            company_name=parsed_job.company_name,
            job_title=parsed_job.job_title,
            description=parsed_job.original_jd,
            recruiter_email=parsed_job.recruiter_email,
            location=parsed_job.location
        ),
        raw_content=parsed_job.original_jd
    )
    db_job = await job_repo.create_job(job_domain)
    await db_session.commit()

    # 4. Fetch profiles back from DB
    job_id = db_job.id
    db_session.expire_all()
    active_profile = await profile_storage.get_active_candidate_profile(user_a)
    fetched_job = await job_repo.get_by_id(job_id)

    # Convert Candidate DB model to schema response
    candidate_profile_schema = CandidateProfileStorageResponse.from_orm_model(active_profile)

    # Convert Job DB model to JobProfile schema
    job_profile_schema = job_parser.parse_job(fetched_job.description, "text")

    # 5. Generate Match Report
    report = matcher.match_profiles(candidate_profile_schema, job_profile_schema)

    # Verify matching calculations
    assert report.overall_match_score == 100.0  # Strong match with Go/Kubernetes preferred
    assert "Python" in report.matched_skills
    assert len(report.missing_required_skills) == 0
    assert report.experience_match_score == 100.0
    assert report.education_match_score == 100.0
    assert len(report.strengths) > 0


@pytest.mark.asyncio
async def test_integration_matcher_weak_match(db_session: AsyncSession, seed_users_and_resumes):
    profile_storage = CandidateProfileStorageService(db_session)
    job_parser = JobParserService()
    matcher = ResumeMatcherService()

    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # Extract & Store Weak candidate
    weak_extractor = CandidateProfileService()
    weak_extracted = weak_extractor.extract_profile(RESUME_WEAK_TEXT)
    db_profile = await profile_storage.store_candidate_profile(user_a, resume_a1, weak_extracted)
    await db_session.commit()

    # Retrieve and Match against standard JD
    db_session.expire_all()
    active_profile = await profile_storage.get_active_candidate_profile(user_a)
    candidate_schema = CandidateProfileStorageResponse.from_orm_model(active_profile)
    job_schema = job_parser.parse_job(JOB_JD_TEXT, "text")

    report = matcher.match_profiles(candidate_schema, job_schema)

    assert report.overall_match_score < 40.0
    assert len(report.missing_required_skills) == 4  # Lacks all 4 required skills
    assert report.experience_match_score == round(1/6 * 100, 1)  # 1 yr vs 6 yr required
    assert len(report.weaknesses) > 0


@pytest.mark.asyncio
async def test_integration_matcher_no_match(db_session: AsyncSession, seed_users_and_resumes):
    profile_storage = CandidateProfileStorageService(db_session)
    job_parser = JobParserService()
    matcher = ResumeMatcherService()

    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # Ingest empty profile
    from backend.app.ai.schemas.candidate_profile_schema import CandidateProfile
    db_profile = await profile_storage.store_candidate_profile(user_a, resume_a1, CandidateProfile())
    await db_session.commit()

    db_session.expire_all()
    active_profile = await profile_storage.get_active_candidate_profile(user_a)
    candidate_schema = CandidateProfileStorageResponse.from_orm_model(active_profile)
    job_schema = job_parser.parse_job(JOB_JD_TEXT, "text")

    report = matcher.match_profiles(candidate_schema, job_schema)
    assert report.overall_match_score == 0.0


@pytest.mark.asyncio
async def test_integration_matcher_user_isolation(db_session: AsyncSession, seed_users_and_resumes):
    profile_storage = CandidateProfileStorageService(db_session)
    job_parser = JobParserService()
    matcher = ResumeMatcherService()

    user_a = seed_users_and_resumes["user_a"]
    user_b = seed_users_and_resumes["user_b"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # Store Strong Candidate for User A
    strong_extracted = CandidateProfileService().extract_profile(RESUME_STRONG_TEXT)
    await profile_storage.store_candidate_profile(user_a, resume_a1, strong_extracted)

    # Store Weak Candidate for User B (linking User B to resume_a1 for simplicity)
    weak_extracted = CandidateProfileService().extract_profile(RESUME_WEAK_TEXT)
    await profile_storage.store_candidate_profile(user_b, resume_a1, weak_extracted)
    await db_session.commit()

    # Query active profiles independently
    db_session.expire_all()
    active_a = await profile_storage.get_active_candidate_profile(user_a)
    active_b = await profile_storage.get_active_candidate_profile(user_b)
    
    schema_a = CandidateProfileStorageResponse.from_orm_model(active_a)
    schema_b = CandidateProfileStorageResponse.from_orm_model(active_b)
    job_schema = job_parser.parse_job(JOB_JD_TEXT, "text")

    report_a = matcher.match_profiles(schema_a, job_schema)
    report_b = matcher.match_profiles(schema_b, job_schema)

    # Verify scores are fully isolated
    assert report_a.overall_match_score == 100.0
    assert report_b.overall_match_score < 40.0


@pytest.mark.asyncio
async def test_integration_matcher_profile_replacement(db_session: AsyncSession, seed_users_and_resumes):
    profile_storage = CandidateProfileStorageService(db_session)
    job_parser = JobParserService()
    matcher = ResumeMatcherService()

    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]
    resume_a2 = seed_users_and_resumes["resume_a2"]

    # 1. Store weak profile first
    weak_extracted = CandidateProfileService().extract_profile(RESUME_WEAK_TEXT)
    await profile_storage.store_candidate_profile(user_a, resume_a1, weak_extracted)

    # 2. Replace with strong profile
    strong_extracted = CandidateProfileService().extract_profile(RESUME_STRONG_TEXT)
    await profile_storage.store_candidate_profile(user_a, resume_a2, strong_extracted)
    await db_session.commit()

    # 3. Fetch active profile (should be the strong one)
    db_session.expire_all()
    active_profile = await profile_storage.get_active_candidate_profile(user_a)
    candidate_schema = CandidateProfileStorageResponse.from_orm_model(active_profile)
    job_schema = job_parser.parse_job(JOB_JD_TEXT, "text")

    report = matcher.match_profiles(candidate_schema, job_schema)
    # Returns 100% (strong profile) instead of weak profile score
    assert report.overall_match_score == 100.0


@pytest.mark.asyncio
async def test_integration_matcher_multiple_jobs(db_session: AsyncSession, seed_users_and_resumes):
    profile_storage = CandidateProfileStorageService(db_session)
    job_parser = JobParserService()
    matcher = ResumeMatcherService()

    user_a = seed_users_and_resumes["user_a"]
    resume_a1 = seed_users_and_resumes["resume_a1"]

    # Store Strong Candidate
    strong_extracted = CandidateProfileService().extract_profile(RESUME_STRONG_TEXT)
    await profile_storage.store_candidate_profile(user_a, resume_a1, strong_extracted)
    await db_session.commit()

    db_session.expire_all()
    active = await profile_storage.get_active_candidate_profile(user_a)
    candidate_schema = CandidateProfileStorageResponse.from_orm_model(active)

    # Match against Job 1 (Senior Developer)
    job_1_schema = job_parser.parse_job(JOB_JD_TEXT, "text")
    report_1 = matcher.match_profiles(candidate_schema, job_1_schema)

    # Match against Job 2 (Lacks Go/Kubernetes requirements, wants Javascript/HTML)
    job_2_jd = """
    Company: Web Corp
    Job Title: Frontend Dev
    Required Skills: HTML, CSS, Javascript
    """
    job_2_schema = job_parser.parse_job(job_2_jd, "text")
    report_2 = matcher.match_profiles(candidate_schema, job_2_schema)

    assert report_1.overall_match_score == 100.0
    assert report_2.overall_match_score < 40.0
