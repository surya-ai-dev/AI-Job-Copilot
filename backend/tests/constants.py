# backend/tests/constants.py
# Constants and static mock payloads used across the backend test suite

import uuid

# Mock User Constants
TEST_EMAIL = "developer@example.com"
TEST_PASSWORD = "Password@123"
TEST_FIRST_NAME = "Surya"
TEST_LAST_NAME = "Charan"

# Mock IDs
MOCK_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
MOCK_RESUME_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
MOCK_JOB_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
MOCK_ANALYSIS_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
MOCK_OPTIMIZATION_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")
MOCK_DRAFT_ID = uuid.UUID("66666666-6666-6666-6666-666666666666")
MOCK_APPLICATION_ID = uuid.UUID("77777777-7777-7777-7777-777777777777")

# Static Test Documents Content
MOCK_RESUME_TEXT = "Surya Charan. Python Software Engineer with 5 years experience in FastAPI, Docker, and PostgreSQL."
MOCK_JOB_TEXT = "We are seeking a Python Engineer to develop FastAPI services, manage PostgreSQL databases, and run Docker container deployments."
