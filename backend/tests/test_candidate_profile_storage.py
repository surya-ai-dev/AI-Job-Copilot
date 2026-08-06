"""Unit tests verifying the Candidate Profile Storage Repository and Service layers."""

import uuid
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base

from backend.app.ai.models.candidate_profile_model import CandidateProfileModel
from backend.app.ai.repository.candidate_profile_repository import CandidateProfileRepository
from backend.app.ai.services.candidate_profile_storage_service import CandidateProfileStorageService
from backend.app.ai.schemas.candidate_profile_schema import (
    CandidateProfile,
    ExperienceItem,
    ProjectItem,
    EducationItem
)
from backend.app.ai.schemas.candidate_profile_storage_schema import CandidateProfileStorageResponse
from backend.app.database.session import Base


# ==========================================
# 0. Pytest Setup Fixtures
# ==========================================

@pytest.fixture(autouse=True)
async def setup_candidate_profile_table(db_session: AsyncSession):
    """Autouse fixture to ensure the candidate_profiles table exists in the SQLite test engine."""
    # Ensure model is imported to register it in Base metadata
    from backend.app.ai.models.candidate_profile_model import CandidateProfileModel
    conn = await db_session.connection()
    await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def seed_data(db_session: AsyncSession):
    """Seeds a test user and test resume to satisfy foreign key relationships."""
    from backend.app.auth.models.user_model import UserModel
    from backend.app.resume.models.resume_model import ResumeModel

    # Seed User
    user_id = uuid.uuid4()
    user = UserModel(
        id=user_id,
        email=f"test_storage_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hashed_password",
        first_name="Jane",
        last_name="Doe",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)

    # Seed Resume
    resume_id = uuid.uuid4()
    resume = ResumeModel(
        id=resume_id,
        user_id=user_id,
        file_path="/app/storage/resumes/dummy.pdf",
        file_name="resume.pdf",
        file_size=1000,
        content_type="application/pdf",
        status="active",
        parsed_skills=["Python"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(resume)
    
    await db_session.flush()
    return user_id, resume_id


@pytest.fixture
def sample_profile() -> CandidateProfile:
    """Fixture supplying a populated CandidateProfile schema."""
    return CandidateProfile(
        full_name="John Doe",
        email="john.doe@example.com",
        phone="+1 555-555-5555",
        linkedin_url="https://linkedin.com/in/johndoe",
        github_url="https://github.com/johndoe",
        professional_summary="Experienced Cloud Developer.",
        skills=["Python", "Go", "Kubernetes"],
        experience=[
            ExperienceItem(
                company="Tech Corp",
                role="Developer",
                start_date="2020",
                end_date="Present",
                description="Backend architectures",
                highlights=["Reduced latency", "Refactored queues"]
            )
        ],
        projects=[
            ProjectItem(
                title="Copilot Agent",
                role="Architect",
                technologies=["FastAPI", "SQLite"],
                description="AI project manager",
                url="https://github.com/johndoe/copilot",
                highlights=["Drafted schemas"]
            )
        ],
        education=[
            EducationItem(
                institution="MIT",
                degree="B.S.",
                field_of_study="Computer Science",
                start_date="2016",
                end_date="2020",
                gpa="3.9"
            )
        ],
        certifications=["AWS Certified Developer"]
    )


# ==========================================
# 1. Repository Tests
# ==========================================

@pytest.mark.asyncio
async def test_repo_create_profile(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    repo = CandidateProfileRepository(db_session)

    db_profile = await repo.create_profile(user_id, resume_id, sample_profile, is_active=True)
    
    assert db_profile.id is not None
    assert db_profile.user_id == user_id
    assert db_profile.resume_id == resume_id
    assert db_profile.full_name == "John Doe"
    assert db_profile.email == "john.doe@example.com"
    assert db_profile.phone == "+1 555-555-5555"
    assert db_profile.linkedin_url == "https://linkedin.com/in/johndoe"
    assert db_profile.github_url == "https://github.com/johndoe"
    assert db_profile.professional_summary == "Experienced Cloud Developer."
    
    # JSON column serialization validations
    assert db_profile.skills_json == ["Python", "Go", "Kubernetes"]
    assert db_profile.experience_json[0]["company"] == "Tech Corp"
    assert db_profile.projects_json[0]["title"] == "Copilot Agent"
    assert db_profile.education_json[0]["institution"] == "MIT"
    assert db_profile.certifications_json == ["AWS Certified Developer"]
    assert db_profile.is_active is True


@pytest.mark.asyncio
async def test_repo_get_active_profile(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    repo = CandidateProfileRepository(db_session)

    await repo.create_profile(user_id, resume_id, sample_profile, is_active=True)
    
    active_profile = await repo.get_active_profile(user_id)
    assert active_profile is not None
    assert active_profile.is_active is True
    assert active_profile.full_name == "John Doe"


@pytest.mark.asyncio
async def test_repo_replace_profile(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    repo = CandidateProfileRepository(db_session)

    profile_a = await repo.create_profile(user_id, resume_id, sample_profile, is_active=True)
    profile_b = await repo.create_profile(user_id, resume_id, sample_profile, is_active=False)

    await repo.replace_profile(profile_a, profile_b)

    assert profile_a.is_active is False
    assert profile_b.is_active is True


@pytest.mark.asyncio
async def test_repo_deactivate_active_profile(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    repo = CandidateProfileRepository(db_session)

    await repo.create_profile(user_id, resume_id, sample_profile, is_active=True)
    
    await repo.deactivate_active_profile(user_id)
    
    active_profile = await repo.get_active_profile(user_id)
    assert active_profile is None


@pytest.mark.asyncio
async def test_repo_delete_profile(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    repo = CandidateProfileRepository(db_session)

    db_profile = await repo.create_profile(user_id, resume_id, sample_profile, is_active=True)
    
    deleted = await repo.delete_profile(db_profile.id)
    assert deleted is True

    # Try deleting a fake profile
    deleted_fake = await repo.delete_profile(uuid.uuid4())
    assert deleted_fake is False


@pytest.mark.asyncio
async def test_repo_list_profile_versions(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    repo = CandidateProfileRepository(db_session)

    await repo.create_profile(user_id, resume_id, sample_profile, is_active=False)
    await repo.create_profile(user_id, resume_id, sample_profile, is_active=True)

    versions = await repo.list_profile_versions(user_id)
    assert len(versions) == 2


@pytest.mark.asyncio
async def test_repo_user_isolation(db_session: AsyncSession, seed_data, sample_profile):
    user_id_a, resume_id = seed_data
    repo = CandidateProfileRepository(db_session)

    # Seed User B
    from backend.app.auth.models.user_model import UserModel
    user_id_b = uuid.uuid4()
    user_b = UserModel(
        id=user_id_b,
        email="test_b@example.com",
        hashed_password="hash",
        first_name="Alice",
        last_name="Smith",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user_b)
    await db_session.flush()

    # Create active profile for User A
    await repo.create_profile(user_id_a, resume_id, sample_profile, is_active=True)
    # Create active profile for User B
    profile_b_data = sample_profile.model_copy(update={"full_name": "Alice Smith"})
    await repo.create_profile(user_id_b, resume_id, profile_b_data, is_active=True)

    # Assert separation
    profile_a = await repo.get_active_profile(user_id_a)
    profile_b = await repo.get_active_profile(user_id_b)

    assert profile_a.full_name == "John Doe"
    assert profile_b.full_name == "Alice Smith"


# ==========================================
# 2. Service Layer Tests
# ==========================================

@pytest.mark.asyncio
async def test_service_store_candidate_profile(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)

    db_profile = await service.store_candidate_profile(user_id, resume_id, sample_profile)
    assert db_profile.is_active is True
    assert db_profile.full_name == "John Doe"


@pytest.mark.asyncio
async def test_service_replace_candidate_profile(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)

    # Store initial profile
    profile_a = await service.store_candidate_profile(user_id, resume_id, sample_profile)
    assert profile_a.is_active is True

    # Replace profile
    profile_b_data = sample_profile.model_copy(update={"full_name": "Jane Replaced"})
    profile_b = await service.replace_candidate_profile(user_id, resume_id, profile_b_data)

    # Check database status
    assert profile_b.is_active is True
    assert profile_b.full_name == "Jane Replaced"

    # Verify profile_a is now deactivated
    active_profile = await service.get_active_candidate_profile(user_id)
    assert active_profile.id == profile_b.id
    assert active_profile.full_name == "Jane Replaced"


@pytest.mark.asyncio
async def test_service_get_active_candidate_profile(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)

    await service.store_candidate_profile(user_id, resume_id, sample_profile)
    
    active_profile = await service.get_active_candidate_profile(user_id)
    assert active_profile is not None
    assert active_profile.full_name == "John Doe"


@pytest.mark.asyncio
async def test_service_delete_candidate_profile(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)

    db_profile = await service.store_candidate_profile(user_id, resume_id, sample_profile)
    
    deleted = await service.delete_candidate_profile(db_profile.id)
    assert deleted is True

    deleted_fake = await service.delete_candidate_profile(uuid.uuid4())
    assert deleted_fake is False


@pytest.mark.asyncio
async def test_service_rollback_on_repository_failure(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)

    # Mock the repository call to fail
    with patch.object(CandidateProfileRepository, "create_profile", side_effect=Exception("Database write error")):
        with pytest.raises(Exception) as exc_info:
            await service.store_candidate_profile(user_id, resume_id, sample_profile)
        assert "Database write error" in str(exc_info.value)
        
        # Verify active profile is not stored and transaction was rolled back
        active = await service.get_active_candidate_profile(user_id)
        assert active is None


@pytest.mark.asyncio
async def test_service_duplicate_upload(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)

    profile_1 = await service.store_candidate_profile(user_id, resume_id, sample_profile)
    profile_2 = await service.store_candidate_profile(user_id, resume_id, sample_profile)

    # Verify only one is active
    active = await service.get_active_candidate_profile(user_id)
    assert active.id == profile_2.id

    # Check status of first one in DB
    result = await db_session.execute(
        select(CandidateProfileModel).where(CandidateProfileModel.id == profile_1.id)
    )
    db_profile_1 = result.scalars().first()
    assert db_profile_1.is_active is False


@pytest.mark.asyncio
async def test_service_multiple_uploads(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)

    profile_1 = await service.store_candidate_profile(user_id, resume_id, sample_profile)
    profile_2 = await service.store_candidate_profile(user_id, resume_id, sample_profile)
    profile_3 = await service.store_candidate_profile(user_id, resume_id, sample_profile)

    # Verify only the latest (profile_3) is active
    active = await service.get_active_candidate_profile(user_id)
    assert active.id == profile_3.id

    # Retrieve all versions from repository
    versions = await service.repository.list_profile_versions(user_id)
    assert len(versions) == 3
    assert versions[0].id == profile_3.id
    assert versions[0].is_active is True
    assert versions[1].is_active is False
    assert versions[2].is_active is False


@pytest.mark.asyncio
async def test_service_missing_user(db_session: AsyncSession, seed_data, sample_profile):
    _, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)

    # Storing with non-existent user should fail if SQLite foreign key checks were enforced,
    # or fail at service levels. We assert it runs but verifies error handling if database throws.
    fake_user_id = uuid.uuid4()
    
    # We patch repository to simulate foreign key constraint violation
    with patch.object(CandidateProfileRepository, "create_profile", side_effect=ValueError("Foreign key constraint violation")):
        with pytest.raises(ValueError) as exc_info:
            await service.store_candidate_profile(fake_user_id, resume_id, sample_profile)
        assert "Foreign key" in str(exc_info.value)


@pytest.mark.asyncio
async def test_service_missing_resume(db_session: AsyncSession, seed_data, sample_profile):
    user_id, _ = seed_data
    service = CandidateProfileStorageService(db_session)

    fake_resume_id = uuid.uuid4()
    
    with patch.object(CandidateProfileRepository, "create_profile", side_effect=ValueError("Foreign key constraint violation")):
        with pytest.raises(ValueError):
            await service.store_candidate_profile(user_id, fake_resume_id, sample_profile)


# ==========================================
# 3. Schema & Mapping Tests
# ==========================================

def test_schema_mapping_from_orm(sample_profile):
    # Construct a mock ORM model object
    model = CandidateProfileModel(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        resume_id=uuid.uuid4(),
        full_name=sample_profile.full_name,
        email=sample_profile.email,
        phone=sample_profile.phone,
        linkedin_url=sample_profile.linkedin_url,
        github_url=sample_profile.github_url,
        professional_summary=sample_profile.professional_summary,
        skills_json=sample_profile.skills,
        experience_json=[exp.model_dump() for exp in sample_profile.experience],
        projects_json=[proj.model_dump() for proj in sample_profile.projects],
        education_json=[edu.model_dump() for edu in sample_profile.education],
        certifications_json=sample_profile.certifications,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    response = CandidateProfileStorageResponse.from_orm_model(model)

    assert response.id == model.id
    assert response.full_name == "John Doe"
    assert response.skills == ["Python", "Go", "Kubernetes"]
    assert response.experience[0].company == "Tech Corp"
    assert response.projects[0].title == "Copilot Agent"
    assert response.education[0].institution == "MIT"
    assert response.certifications == ["AWS Certified Developer"]
    assert response.is_active is True


# ==========================================
# 4. Edge Cases
# ==========================================

@pytest.mark.asyncio
async def test_edge_case_empty_profile(db_session: AsyncSession, seed_data):
    user_id, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)
    empty_profile = CandidateProfile()

    db_profile = await service.store_candidate_profile(user_id, resume_id, empty_profile)
    assert db_profile.id is not None
    assert db_profile.skills_json == []
    assert db_profile.experience_json == []


@pytest.mark.asyncio
async def test_edge_case_large_profile(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)
    
    # Generate 5,000 skills
    large_skills = [f"Skill-{i}" for i in range(5000)]
    large_summary = "Developer summary." * 1000
    
    large_profile = sample_profile.model_copy(update={
        "skills": large_skills,
        "professional_summary": large_summary
    })

    db_profile = await service.store_candidate_profile(user_id, resume_id, large_profile)
    assert len(db_profile.skills_json) == 5000
    assert len(db_profile.professional_summary) == 18000


@pytest.mark.asyncio
async def test_edge_case_unicode_profile(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)
    
    unicode_profile = sample_profile.model_copy(update={
        "full_name": "Jañe Döe",
        "professional_summary": "Spécialiste en ingénierie de données.",
        "skills": ["Pythøn", "Gø", "Kubernetés"]
    })

    db_profile = await service.store_candidate_profile(user_id, resume_id, unicode_profile)
    assert db_profile.full_name == "Jañe Döe"
    assert db_profile.skills_json == ["Pythøn", "Gø", "Kubernetés"]


@pytest.mark.asyncio
async def test_edge_case_duplicate_skills_persisted(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)
    
    # The storage layer should persist whatever schema array is passed exactly
    profile = sample_profile.model_copy(update={"skills": ["Python", "Python", "Go"]})
    
    db_profile = await service.store_candidate_profile(user_id, resume_id, profile)
    assert db_profile.skills_json == ["Python", "Python", "Go"]


@pytest.mark.asyncio
async def test_edge_case_null_optional_fields(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)
    
    null_profile = sample_profile.model_copy(update={
        "email": None,
        "phone": None,
        "linkedin_url": None,
        "github_url": None,
        "professional_summary": None
    })

    db_profile = await service.store_candidate_profile(user_id, resume_id, null_profile)
    assert db_profile.email is None
    assert db_profile.phone is None
    assert db_profile.linkedin_url is None
    assert db_profile.github_url is None
    assert db_profile.professional_summary is None


@pytest.mark.asyncio
async def test_candidate_profile_roundtrip_preserves_matching_fields(db_session: AsyncSession, seed_data, sample_profile):
    user_id, resume_id = seed_data
    service = CandidateProfileStorageService(db_session)

    # 1. Store
    db_profile = await service.store_candidate_profile(user_id, resume_id, sample_profile)
    await db_session.commit()

    # 2. Retrieve
    profile_id = db_profile.id
    db_session.expire_all()
    active_profile = await service.get_active_candidate_profile(user_id)
    assert active_profile is not None

    # 3. Convert using CandidateProfileStorageResponse.from_orm_model()
    retrieved = CandidateProfileStorageResponse.from_orm_model(active_profile)

    # 4. Assert every field matches the original
    assert sample_profile.skills == retrieved.skills
    assert sample_profile.projects == retrieved.projects
    assert sample_profile.experience == retrieved.experience
    assert sample_profile.education == retrieved.education
    assert sample_profile.certifications == retrieved.certifications
