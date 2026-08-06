"""Integration tests verifying the complete end-to-end Candidate Profile workflow.

Coordinates parsing, extraction, and database persistence layers.
"""

import io
import uuid
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.ai.agents.resume_parser import ResumeParserAgent
from backend.app.ai.services.resume_parser_service import ResumeParserService
from backend.app.ai.agents.candidate_profile_extractor import CandidateProfileExtractorAgent
from backend.app.ai.services.candidate_profile_service import CandidateProfileService
from backend.app.ai.models.candidate_profile_model import CandidateProfileModel
from backend.app.ai.repository.candidate_profile_repository import CandidateProfileRepository
from backend.app.ai.services.candidate_profile_storage_service import CandidateProfileStorageService
from backend.app.database.session import Base


# ==========================================
# Mock Data Constants
# ==========================================

RESUME_TEXT_V1 = """
Jane Doe
jane.doe@example.com | +1 (555) 019-2834
linkedin.com/in/janedoe | github.com/janedoe

Professional Summary
Senior Software Engineer with 5+ years of experience building Python backend services.

Skills
Python, FastAPI, PostgreSQL

Work Experience
Google - Engineer | 2022 - Present
- Built database queries.

Projects
Job Copilot - Creator | github.com/janedoe/jobcopilot
- Developed open source code.

Education
Stanford University - BS | 2018 - 2022
"""

RESUME_TEXT_V2 = """
Jane Doe
jane.doe@example.com | +1 (555) 019-2834
linkedin.com/in/janedoe | github.com/janedoe

Professional Summary
Lead Platform Architect with 7+ years of experience building distributed systems.

Skills
Python, FastAPI, Kubernetes, Go

Work Experience
Google - Lead Architect | 2022 - Present
- Managed kubernetes clusters.

Projects
Cloud Orchestrator - Lead | github.com/janedoe/orchestrator
- Designed high performance API layers.

Education
Stanford University - MS | 2022 - 2024
"""


# ==========================================
# 0. Fixtures Setup
# ==========================================

@pytest.fixture(autouse=True)
async def setup_candidate_profile_table(db_session: AsyncSession):
    """Autouse fixture to ensure the candidate_profiles table exists in the SQLite test engine."""
    from backend.app.ai.models.candidate_profile_model import CandidateProfileModel
    conn = await db_session.connection()
    await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def seed_data(db_session: AsyncSession):
    """Seeds test users and test resumes to satisfy foreign keys."""
    from backend.app.auth.models.user_model import UserModel
    from backend.app.resume.models.resume_model import ResumeModel

    # Seed User A
    user_id_a = uuid.uuid4()
    user_a = UserModel(
        id=user_id_a,
        email=f"integration_a_{uuid.uuid4().hex[:6]}@example.com",
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
        email=f"integration_b_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hashed_password",
        first_name="Bob",
        last_name="Smith",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user_b)

    # Seed Resume A1
    resume_id_a1 = uuid.uuid4()
    resume_a1 = ResumeModel(
        id=resume_id_a1,
        user_id=user_id_a,
        file_path="/app/storage/resumes/dummy_a1.pdf",
        file_name="resume_v1.pdf",
        file_size=1000,
        content_type="application/pdf",
        status="active",
        parsed_skills=["Python"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(resume_a1)

    # Seed Resume A2
    resume_id_a2 = uuid.uuid4()
    resume_a2 = ResumeModel(
        id=resume_id_a2,
        user_id=user_id_a,
        file_path="/app/storage/resumes/dummy_a2.pdf",
        file_name="resume_v2.pdf",
        file_size=2000,
        content_type="application/pdf",
        status="active",
        parsed_skills=["Python", "Go"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(resume_a2)

    await db_session.flush()
    return {
        "user_a": user_id_a,
        "user_b": user_id_b,
        "resume_a1": resume_id_a1,
        "resume_a2": resume_id_a2
    }


class MockPDF:
    """Helper class to emulate pdfplumber.open context manager behavior."""
    def __init__(self, text: str):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = text
        self.pages = [mock_page]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def mock_pdfplumber(extracted_text: str):
    """Factory function returning a MockPDF instance."""
    return MockPDF(extracted_text)


# ==========================================
# 1. Integration Workflows
# ==========================================

@pytest.mark.asyncio
async def test_integration_complete_workflow(db_session: AsyncSession, seed_data):
    # Initialize all service layers using dependency injection
    parser_service = ResumeParserService()
    profile_service = CandidateProfileService()
    storage_service = CandidateProfileStorageService(db_session)
    
    user_id = seed_data["user_a"]
    resume_id_1 = seed_data["resume_a1"]
    resume_id_2 = seed_data["resume_a2"]

    # --------------------------------------------------
    # Step 1: Parse and store FIRST resume version
    # --------------------------------------------------
    pdf_stream_1 = io.BytesIO(b"dummy pdf bytes version 1")
    with patch("backend.app.ai.agents.resume_parser.pdfplumber.open", return_value=mock_pdfplumber(RESUME_TEXT_V1)):
        parse_result_1 = parser_service.parse_stream(pdf_stream_1, "pdf")
        
    assert "jane.doe@example.com" in parse_result_1.raw_text
    assert parse_result_1.page_count == 1

    # Step 2: Extract candidate profile
    profile_1 = profile_service.extract_profile(parse_result_1.raw_text)
    assert profile_1.full_name == "Jane Doe"
    assert "FastAPI" in profile_1.skills

    # Step 3: Persist Profile 1 (First Upload)
    db_profile_1 = await storage_service.store_candidate_profile(user_id, resume_id_1, profile_1)
    assert db_profile_1.is_active is True
    assert db_profile_1.professional_summary.startswith("Senior Software Engineer")

    # Step 4: Retrieve active profile from database
    active_profile_retrieved = await storage_service.get_active_candidate_profile(user_id)
    assert active_profile_retrieved is not None
    assert active_profile_retrieved.id == db_profile_1.id
    assert active_profile_retrieved.is_active is True

    # --------------------------------------------------
    # Step 5: Parse and replace with SECOND resume version
    # --------------------------------------------------
    pdf_stream_2 = io.BytesIO(b"dummy pdf bytes version 2")
    with patch("backend.app.ai.agents.resume_parser.pdfplumber.open", return_value=mock_pdfplumber(RESUME_TEXT_V2)):
        parse_result_2 = parser_service.parse_stream(pdf_stream_2, "pdf")

    # Step 6: Extract updated profile
    profile_2 = profile_service.extract_profile(parse_result_2.raw_text)
    assert "Kubernetes" in profile_2.skills

    # Step 7: Persist Profile 2 (Second Upload - Replacing)
    db_profile_2 = await storage_service.replace_candidate_profile(user_id, resume_id_2, profile_2)
    assert db_profile_2.is_active is True
    assert db_profile_2.professional_summary.startswith("Lead Platform Architect")

    # --------------------------------------------------
    # Step 8: Assert Business Rules & Active statuses
    # --------------------------------------------------
    # Verify ONLY the second profile is active
    active_profile_final = await storage_service.get_active_candidate_profile(user_id)
    assert active_profile_final.id == db_profile_2.id
    assert active_profile_final.is_active is True

    # Capture IDs before expiring session ORM instances
    profile_1_id = db_profile_1.id
    profile_2_id = db_profile_2.id

    # Verify that the first profile is inactive now in the database
    # Clear session to force select queries directly against database rows
    db_session.expire_all()
    
    result = await db_session.execute(
        select(CandidateProfileModel).where(CandidateProfileModel.id == profile_1_id)
    )
    db_profile_1_queried = result.scalars().first()
    assert db_profile_1_queried.is_active is False

    # Verify history versions endpoint list returns both records
    versions = await storage_service.repository.list_profile_versions(user_id)
    assert len(versions) == 2
    assert versions[0].id == profile_2_id  # Newest version first
    assert versions[0].is_active is True
    assert versions[1].id == profile_1_id
    assert versions[1].is_active is False


@pytest.mark.asyncio
async def test_integration_delete_profile(db_session: AsyncSession, seed_data):
    parser_service = ResumeParserService()
    profile_service = CandidateProfileService()
    storage_service = CandidateProfileStorageService(db_session)
    
    user_id = seed_data["user_a"]
    resume_id = seed_data["resume_a1"]

    pdf_stream = io.BytesIO(b"dummy pdf bytes")
    with patch("backend.app.ai.agents.resume_parser.pdfplumber.open", return_value=mock_pdfplumber(RESUME_TEXT_V1)):
        parse_result = parser_service.parse_stream(pdf_stream, "pdf")

    profile = profile_service.extract_profile(parse_result.raw_text)
    db_profile = await storage_service.store_candidate_profile(user_id, resume_id, profile)
    profile_id = db_profile.id

    # Perform transactional delete
    deleted = await storage_service.delete_candidate_profile(profile_id)
    assert deleted is True

    # Verify profile is fully removed from DB
    db_session.expire_all()
    result = await db_session.execute(
        select(CandidateProfileModel).where(CandidateProfileModel.id == profile_id)
    )
    assert result.scalars().first() is None


@pytest.mark.asyncio
async def test_integration_multiple_users_isolation(db_session: AsyncSession, seed_data):
    # This verifies database integration and multi-tenant isolation
    parser_service = ResumeParserService()
    profile_service = CandidateProfileService()
    storage_service = CandidateProfileStorageService(db_session)

    user_a = seed_data["user_a"]
    user_b = seed_data["user_b"]
    resume_a1 = seed_data["resume_a1"]

    # Parse and store User A profile
    pdf_stream_a = io.BytesIO(b"dummy pdf A")
    with patch("backend.app.ai.agents.resume_parser.pdfplumber.open", return_value=mock_pdfplumber(RESUME_TEXT_V1)):
        parse_result_a = parser_service.parse_stream(pdf_stream_a, "pdf")
    profile_a = profile_service.extract_profile(parse_result_a.raw_text)
    db_profile_a = await storage_service.store_candidate_profile(user_a, resume_a1, profile_a)

    # Parse and store User B profile
    pdf_stream_b = io.BytesIO(b"dummy pdf B")
    # Tweak text for B
    resume_text_b = RESUME_TEXT_V1.replace("Jane Doe", "Bob Smith").replace("jane.doe@example.com", "bob@example.com")
    with patch("backend.app.ai.agents.resume_parser.pdfplumber.open", return_value=mock_pdfplumber(resume_text_b)):
        parse_result_b = parser_service.parse_stream(pdf_stream_b, "pdf")
    profile_b = profile_service.extract_profile(parse_result_b.raw_text)
    
    # User B needs a valid resume record in the database for foreign key constraints.
    # For integration test, we can link it to resume_a1 or create one.
    # Linking User B to resume_a1 directly for simplicity.
    db_profile_b = await storage_service.store_candidate_profile(user_b, resume_a1, profile_b)

    profile_a_id = db_profile_a.id
    profile_b_id = db_profile_b.id

    # Verify User isolation in database queries
    db_session.expire_all()
    
    active_a = await storage_service.get_active_candidate_profile(user_a)
    active_b = await storage_service.get_active_candidate_profile(user_b)

    assert active_a.id == profile_a_id
    assert active_a.full_name == "Jane Doe"
    assert active_b.id == profile_b_id
    assert active_b.full_name == "Bob Smith"
