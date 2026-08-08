# backend/tests/conftest.py

# Production-grade pytest configuration setting up async database contexts, AsyncClient, and reusable mock entities



import pytest

import asyncio

from typing import AsyncGenerator, Generator

from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient



from backend.app.main import app

from backend.app.database.session import Base, get_async_db

from backend.app.auth.models.user_model import UserModel

from backend.app.auth.domain.user import User

from backend.tests.helpers import create_mock_jwt, generate_mock_pdf_content

from backend.tests.constants import TEST_EMAIL, TEST_FIRST_NAME, TEST_LAST_NAME, MOCK_USER_ID, MOCK_JOB_TEXT



# Tell pytest to load shared modular fixtures globally

pytest_plugins = ["backend.tests.fixtures"]



# In-memory SQLite async driver url for testing persistence layers cleanly

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"



@pytest.fixture(scope="session")

def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:

    """Yield a single session-wide asyncio event loop for all async test cases."""

    loop = asyncio.get_event_loop_policy().new_event_loop()

    yield loop

    loop.close()



@pytest.fixture

async def test_engine():

    """Create in-memory SQLite async database engine and create database tables."""

    engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})



    async with engine.begin() as conn:

        # Create all tables defined under SQLAlchemy Base class metadata

        await conn.run_sync(Base.metadata.create_all)



    yield engine



    async with engine.begin() as conn:

        # Drop all tables after the test session completes

        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()



@pytest.fixture

async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:

    """Yield a transactional async database session that rolls back changes automatically after execution."""

    async_session_maker = sessionmaker(

        test_engine, class_=AsyncSession, expire_on_commit=False

    )

    async with async_session_maker() as session:

        yield session

        # Ensure rollback to keep tests isolated and database pristine

        await session.rollback()



@pytest.fixture

async def async_client(db_session) -> AsyncGenerator[AsyncClient, None]:

    """Yield an HTTPX AsyncClient for tracing async API routes requests."""

    # Ensure the default test user exists for API requests authentication

    from sqlalchemy import select

    from backend.app.auth.models.user_model import UserModel

    import uuid

    from datetime import datetime



    result = await db_session.execute(select(UserModel).where(UserModel.email == TEST_EMAIL))

    existing = result.scalars().first()

    if not existing:

        user = UserModel(

            id=uuid.uuid4(),

            email=TEST_EMAIL,

            hashed_password="hashed_password",

            first_name="Jane",

            last_name="Doe",

            created_at=datetime.utcnow(),

            updated_at=datetime.utcnow()

        )

        db_session.add(user)

        await db_session.commit()



    # Override FastAPI database dependency to target the current transactional session

    app.dependency_overrides[get_async_db] = lambda: db_session

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:

        yield client

    app.dependency_overrides.clear()



@pytest.fixture

def test_user() -> User:

    """Fixture returning a validated domain User entity."""

    return User(

        id=MOCK_USER_ID,

        email=TEST_EMAIL,

        hashed_password="$bcrypt$v=2$r=12$mockhashvalueplaceholderpassword",

        first_name=TEST_FIRST_NAME,

        last_name=TEST_LAST_NAME

    )



@pytest.fixture

def jwt_token() -> str:

    """Fixture returning a pre-signed JWT access token string."""

    return create_mock_jwt(TEST_EMAIL)



@pytest.fixture

def auth_headers(jwt_token) -> dict:

    """Fixture returning authorization bearer headers dictionary."""

    return {"Authorization": f"Bearer {jwt_token}"}



@pytest.fixture

def resume_upload_file() -> tuple:

    """Fixture returning a multipart file upload payload for testing resume uploads."""

    return ("resume.pdf", generate_mock_pdf_content(), "application/pdf")



@pytest.fixture

def sample_job_description() -> str:

    """Fixture returning a generic text job description block."""

    return MOCK_JOB_TEXT



@pytest.fixture

async def cleanup_db(db_session) -> AsyncGenerator[None, None]:

    """Cleanup helper rolling back modifications and executing truncate commands on teardown."""

    yield

    # Explicitly verify connection rollback on test teardowns

    await db_session.rollback()





@pytest.fixture

async def seed_users_and_resumes(db_session: AsyncSession):

    """Seeds database with User and Resume records to support ForeignKey integrity."""

    import uuid

    from datetime import datetime

    from backend.app.auth.models.user_model import UserModel

    from backend.app.resume.models.resume_model import ResumeModel



    # Seed User A (reuse if exists)

    from sqlalchemy import select

    result = await db_session.execute(select(UserModel).where(UserModel.email == TEST_EMAIL))

    existing_user_a = result.scalars().first()

    if existing_user_a:

        user_a_id = existing_user_a.id

    else:

        user_a_id = uuid.uuid4()

        user_a = UserModel(

            id=user_a_id,

            email=TEST_EMAIL,

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
