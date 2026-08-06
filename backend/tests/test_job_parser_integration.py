"""Integration tests verifying the end-to-end Job Parsing and database storage pipeline."""

import io
import uuid
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.ai.services.job_parser_service import JobParserService
from backend.app.ai.exceptions import UnsupportedFileTypeError, InvalidJobInputError
from backend.app.jobs.models.job_model import JobModel
from backend.app.jobs.repository.job_repository import JobRepository
from backend.app.jobs.domain.job import Job, JobSource, ParsedJob
from backend.app.database.session import Base

# ==========================================
# Mock Job Description Data
# ==========================================

MOCK_JD_TEXT = """
Acme Systems
Senior Python Developer
Department: Engineering
Type: Full-time
Location: Remote
Salary Range: $130k - $160k
Experience: 4+ years
Recruiter: hanna@acme.com

Skills
* Python
* FastAPI
* PostgreSQL

Responsibilities
- Build backend APIs.
- Write unit tests.
"""


# Helper for pdfplumber mock
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
async def setup_jobs_table(db_session: MagicMock):
    """Autouse fixture to ensure the jobs table is created in the SQLite test database."""
    from backend.app.jobs.models.job_model import JobModel
    conn = await db_session.connection()
    await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def seed_users(db_session: AsyncSession):
    """Seeds test users to satisfy foreign key constraints."""
    from backend.app.auth.models.user_model import UserModel

    user_a_id = uuid.uuid4()
    user_a = UserModel(
        id=user_a_id,
        email=f"job_user_a_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hashed_password",
        first_name="User",
        last_name="A",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user_a)

    user_b_id = uuid.uuid4()
    user_b = UserModel(
        id=user_b_id,
        email=f"job_user_b_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hashed_password",
        first_name="User",
        last_name="B",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user_b)

    await db_session.flush()
    return user_a_id, user_b_id


# ==========================================
# 1. Integration Test Cases
# ==========================================

@pytest.mark.asyncio
async def test_integration_parse_complete_jd():
    service = JobParserService()
    profile = service.parse_job(MOCK_JD_TEXT, "text")

    assert profile.company_name == "Acme Systems"
    assert profile.job_title == "Senior Python Developer"
    assert profile.location == "Remote"
    assert profile.recruiter_email == "hanna@acme.com"
    assert "Python" in profile.required_skills
    assert profile.source_type == "text"


@pytest.mark.asyncio
async def test_integration_parse_pdf_jd():
    service = JobParserService()
    pdf_stream = io.BytesIO(b"dummy pdf bytes")

    with patch("backend.app.ai.agents.resume_parser.pdfplumber.open", return_value=MockPDF(MOCK_JD_TEXT)):
        profile = service.parse_job(pdf_stream, "pdf")

    assert profile.source_type == "pdf"
    assert profile.company_name == "Acme Systems"
    assert profile.job_title == "Senior Python Developer"


@pytest.mark.asyncio
async def test_integration_parse_docx_jd():
    service = JobParserService()
    docx_stream = io.BytesIO(b"dummy docx bytes")

    mock_doc = MagicMock()
    p = MagicMock()
    p.text = MOCK_JD_TEXT
    mock_doc.paragraphs = [p]
    mock_doc.tables = []
    mock_doc.part.package.parts = []

    with patch("backend.app.ai.agents.resume_parser.Document", return_value=mock_doc):
        profile = service.parse_job(docx_stream, "docx")

    assert profile.source_type == "docx"
    assert profile.company_name == "Acme Systems"


@pytest.mark.asyncio
async def test_integration_store_parsed_job(db_session: AsyncSession, seed_users):
    user_id, _ = seed_users
    parser_service = JobParserService()
    repo = JobRepository(db_session)

    # 1. Parse raw text to JobProfile
    profile = parser_service.parse_job(MOCK_JD_TEXT, "text")

    # 2. Build domain Job object
    source = JobSource(
        source_type=profile.source_type,
        source_url=profile.application_url
    )
    parsed_data = ParsedJob(
        company_name=profile.company_name,
        job_title=profile.job_title,
        description=profile.original_jd,
        recruiter_email=profile.recruiter_email,
        location=profile.location
    )
    job_domain = Job(
        user_id=user_id,
        source=source,
        parsed_data=parsed_data,
        raw_content=profile.original_jd
    )

    # 3. Store in database
    db_job = await repo.create_job(job_domain)
    await db_session.commit()

    assert db_job.id is not None
    assert db_job.company_name == "Acme Systems"
    assert db_job.job_title == "Senior Python Developer"
    assert db_job.recruiter_email == "hanna@acme.com"

    # 4. Fetch job back
    job_id = db_job.id
    db_session.expire_all()
    fetched_job = await repo.get_by_id(job_id)
    assert fetched_job is not None
    assert fetched_job.company_name == "Acme Systems"


@pytest.mark.asyncio
async def test_integration_list_multiple_jobs(db_session: AsyncSession, seed_users):
    user_id, _ = seed_users
    repo = JobRepository(db_session)

    # Seed two jobs for user with distinct timestamps
    job_1 = Job(
        user_id=user_id,
        source=JobSource(source_type="text"),
        parsed_data=ParsedJob(company_name="Google", job_title="Engineer", description="Test"),
        raw_content="Raw text 1",
        created_at=datetime(2026, 8, 6, 1, 0, 0)
    )
    job_2 = Job(
        user_id=user_id,
        source=JobSource(source_type="text"),
        parsed_data=ParsedJob(company_name="Meta", job_title="Developer", description="Test"),
        raw_content="Raw text 2",
        created_at=datetime(2026, 8, 6, 2, 0, 0)
    )
    await repo.create_job(job_1)
    await repo.create_job(job_2)
    await db_session.commit()

    # List jobs
    jobs = await repo.list_jobs(user_id)
    assert len(jobs) == 2
    assert jobs[0].company_name == "Meta"  # Ordered by created_at desc
    assert jobs[1].company_name == "Google"


@pytest.mark.asyncio
async def test_integration_multiple_users_isolation(db_session: AsyncSession, seed_users):
    user_a, user_b = seed_users
    repo = JobRepository(db_session)

    # Save job for User A
    job_a = Job(
        user_id=user_a,
        source=JobSource(source_type="text"),
        parsed_data=ParsedJob(company_name="Google", job_title="Engineer", description="Test"),
        raw_content="Google job"
    )
    await repo.create_job(job_a)

    # Save job for User B
    job_b = Job(
        user_id=user_b,
        source=JobSource(source_type="text"),
        parsed_data=ParsedJob(company_name="Meta", job_title="Developer", description="Test"),
        raw_content="Meta job"
    )
    await repo.create_job(job_b)
    await db_session.commit()

    # Verify separation
    jobs_a = await repo.list_jobs(user_a)
    jobs_b = await repo.list_jobs(user_b)

    assert len(jobs_a) == 1
    assert jobs_a[0].company_name == "Google"
    assert len(jobs_b) == 1
    assert jobs_b[0].company_name == "Meta"


@pytest.mark.asyncio
async def test_integration_update_parsed_job(db_session: AsyncSession, seed_users):
    user_id, _ = seed_users
    repo = JobRepository(db_session)

    job = Job(
        user_id=user_id,
        source=JobSource(source_type="text"),
        parsed_data=ParsedJob(company_name="Google", job_title="Engineer", description="Test"),
        raw_content="Google job"
    )
    db_job = await repo.create_job(job)
    await db_session.commit()

    # Update attributes
    db_job.company_name = "Alphabet"
    db_job.job_title = "Staff Engineer"
    await db_session.commit()

    # Verify update
    job_id = db_job.id
    db_session.expire_all()
    fetched = await repo.get_by_id(job_id)
    assert fetched.company_name == "Alphabet"
    assert fetched.job_title == "Staff Engineer"


@pytest.mark.asyncio
async def test_integration_delete_parsed_job(db_session: AsyncSession, seed_users):
    user_id, _ = seed_users
    repo = JobRepository(db_session)

    job = Job(
        user_id=user_id,
        source=JobSource(source_type="text"),
        parsed_data=ParsedJob(company_name="Google", job_title="Engineer", description="Test"),
        raw_content="Google job"
    )
    db_job = await repo.create_job(job)
    await db_session.commit()
    job_id = db_job.id

    # Delete
    await repo.delete_job(db_job)
    await db_session.commit()

    # Verify deletion
    db_session.expire_all()
    fetched = await repo.get_by_id(job_id)
    assert fetched is None


@pytest.mark.asyncio
async def test_integration_invalid_document_format():
    service = JobParserService()
    # Invalid extension raises UnsupportedFileTypeError
    with pytest.raises(UnsupportedFileTypeError):
        service.parse_job("dummy text", "xlsx")


@pytest.mark.asyncio
async def test_integration_missing_fields_defaults(db_session: AsyncSession, seed_users):
    user_id, _ = seed_users
    parser_service = JobParserService()
    repo = JobRepository(db_session)

    # Empty optional fields: no location, no email
    jd_minimal = "Company: Stripe\nTitle: API Engineer\nWe write APIs."
    profile = parser_service.parse_job(jd_minimal, "text")

    job_domain = Job(
        user_id=user_id,
        source=JobSource(source_type=profile.source_type),
        parsed_data=ParsedJob(
            company_name=profile.company_name,
            job_title=profile.job_title,
            description=profile.original_jd,
            recruiter_email=profile.recruiter_email, # None
            location=profile.location # None
        ),
        raw_content=profile.original_jd
    )
    
    db_job = await repo.create_job(job_domain)
    await db_session.commit()

    assert db_job.company_name == "Stripe"
    assert db_job.location is None
    assert db_job.recruiter_email is None
