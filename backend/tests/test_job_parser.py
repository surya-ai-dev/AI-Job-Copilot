"""Unit tests verifying the Job Parser Agent and Service layers."""

import io
import logging
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from pydantic import ValidationError

from backend.app.ai.agents.job_parser import JobParserAgent
from backend.app.ai.services.job_parser_service import JobParserService
from backend.app.ai.exceptions import (
    UnsupportedFileTypeError,
    InvalidJobInputError
)
from backend.app.ai.schemas.job_parser_schema import JobProfile, JobParserMetadata


# ==========================================
# Mock Job Descriptions for Testing
# ==========================================

COMPLETE_JD = """
Acme Systems
Staff Engineer - Core Platform
Department: Engineering
Employment Status: Full-time
Work Workplace Type: Hybrid
Location: San Francisco, CA
Salary Range: $150,000 - $190,000 / year
Experience Required: 5+ years of experience
Education Required: Bachelor's degree in Computer Science
Recruiter Email: recruiter@acme.com | Recruiter Phone: +1 555-123-4567
WhatsApp Contact: +1 555-987-6543
Apply Here: https://acme.com/careers/staff-engineer-apply

About Acme Systems
We are building the future of distributed API databases.

Skills
* Python
* Go
* PostgreSQL
* Redis

Preferred Skills
* Kubernetes
* Rust

Key Responsibilities
- Architect high-throughput microservices.
- Optimize database queries.
- Mentor junior engineers.

Requirements
- BS/MS in Computer Science.
- Background in cloud platforms.

Benefits
- Health, dental, and vision insurance.
- Flexible remote work options.
- Annual learning stipend.
"""

UNICODE_JD = """
München Tech GmbĤ
Sênior Backend Devêloper
Location: Berlin, Germany
Salary: 80.000€ - 95.000€
Recruiter Email: händshake@münchen.de
Skills
* Pythøn
* Gø
"""

WEIRD_FORMATTING_JD = """
   ================== Acme Systems ==================
   || Position: Senior Developer || Workplace: Remote ||
   
   *** Job Description ***
   Looking for a developer.
   
   --- Skills Required ---
   * Python
   * Docker
"""


# ==========================================
# 1. Job parser core parsing tests
# ==========================================

def test_parse_complete_job_description():
    agent = JobParserAgent()
    profile = agent.parse(COMPLETE_JD, "text")

    # Assert basic details
    assert profile.company_name == "Acme Systems"
    assert profile.job_title == "Staff Engineer - Core Platform"
    assert profile.department == "Engineering"
    assert profile.employment_type == "Full-time"
    assert profile.work_mode == "Hybrid"
    assert profile.location == "San Francisco, CA"
    assert profile.salary == "$150,000 - $190,000 / year"
    assert profile.experience_required == "5+ years of experience"
    assert profile.education_required == "Bachelor's degree"

    # Assert contact details
    assert profile.recruiter_email == "recruiter@acme.com"
    assert profile.recruiter_phone == "+1 555-123-4567"
    assert profile.recruiter_whatsapp == "+1 555-987-6543"
    assert profile.application_url == "https://acme.com/careers/staff-engineer-apply"

    # Assert lists
    assert "Python" in profile.required_skills
    assert "Kubernetes" in profile.preferred_skills
    assert "Architect high-throughput microservices." in profile.responsibilities
    assert "BS/MS in Computer Science." in profile.qualifications
    assert "Annual learning stipend." in profile.benefits
    
    # Assert metadata
    assert profile.source_type == "text"
    assert profile.metadata.character_count > 0
    assert len(profile.metadata.warnings) == 0


def test_parse_missing_company():
    agent = JobParserAgent()
    # Resume parser should return None or fallback without crashes if company details cannot be resolved
    jd_no_company = "Looking for a Staff Engineer.\nSkills\n* Python"
    profile = agent.parse(jd_no_company, "text")
    assert profile.company_name is None


def test_parse_missing_experience():
    agent = JobParserAgent()
    jd_no_exp = "Company: Google\nJob Title: SWE\nLooking for someone smart."
    profile = agent.parse(jd_no_exp, "text")
    assert profile.experience_required is None


def test_parse_missing_skills():
    agent = JobParserAgent()
    jd_no_skills = "Company: Google\nJob Title: SWE\nWe are looking for engineers."
    profile = agent.parse(jd_no_skills, "text")
    assert len(profile.required_skills) == 0
    assert len(profile.preferred_skills) == 0


def test_parse_missing_salary():
    agent = JobParserAgent()
    profile = agent.parse("Company: Google\nJob Title: SWE\nGood benefits.", "text")
    assert profile.salary is None


# ==========================================
# 2. Contact Point Extraction Tests
# ==========================================

def test_parse_multiple_emails():
    agent = JobParserAgent()
    jd_text = "Apply at recruiter@acme.com or reach out to support@acme.com."
    profile = agent.parse(jd_text, "text")
    # Returns the first match
    assert profile.recruiter_email == "recruiter@acme.com"


def test_parse_multiple_phone_numbers():
    agent = JobParserAgent()
    jd_text = "Call us at +1 555-123-4567 or fax to +1 555-987-6543."
    profile = agent.parse(jd_text, "text")
    assert profile.recruiter_phone == "+1 555-123-4567"


def test_parse_whatsapp_number():
    agent = JobParserAgent()
    jd_text = "Contact via WhatsApp: +91 98765 43210 for quick updates."
    profile = agent.parse(jd_text, "text")
    assert profile.recruiter_whatsapp == "+91 98765 43210"


def test_parse_application_url():
    agent = JobParserAgent()
    jd_text = "Apply via our hiring portal: https://careers.google.com/jobs/apply-now today."
    profile = agent.parse(jd_text, "text")
    assert profile.application_url == "https://careers.google.com/jobs/apply-now"


# ==========================================
# 3. Employment & Work Modes Heuristics
# ==========================================

def test_parse_work_mode_remote():
    agent = JobParserAgent()
    profile = agent.parse("Job Title: Engineer\nWork workplace: Remote", "text")
    assert profile.work_mode == "Remote"


def test_parse_work_mode_hybrid():
    agent = JobParserAgent()
    profile = agent.parse("Job Title: Engineer\nThis is a hybrid workplace role.", "text")
    assert profile.work_mode == "Hybrid"


def test_parse_work_mode_onsite():
    agent = JobParserAgent()
    profile = agent.parse("Job Title: Engineer\nRole requires onsite presence in Chicago.", "text")
    assert profile.work_mode == "On-site"


def test_parse_employment_contract():
    agent = JobParserAgent()
    profile = agent.parse("Job Title: Engineer\nThis is a contract position.", "text")
    assert profile.employment_type == "Contract"


def test_parse_employment_internship():
    agent = JobParserAgent()
    profile = agent.parse("Job Title: Engineer\nSummer Internship program.", "text")
    assert profile.employment_type == "Internship"


def test_parse_employment_fulltime():
    agent = JobParserAgent()
    profile = agent.parse("Job Title: Engineer\nRole is full-time.", "text")
    assert profile.employment_type == "Full-time"


def test_parse_employment_parttime():
    agent = JobParserAgent()
    profile = agent.parse("Job Title: Engineer\nLooking for a part-time helper.", "text")
    assert profile.employment_type == "Part-time"


# ==========================================
# 4. Ingest and Format Parsing Tests (Mocked)
# ==========================================

@patch("pdfplumber.open")
def test_parse_pdf_source(mock_pdf_open):
    # Setup context manager mocks
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Acme Systems\nTitle: PDF Job Title"
    mock_pdf.pages = [mock_page]
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf

    agent = JobParserAgent()
    dummy_pdf_stream = io.BytesIO(b"dummy pdf bytes")
    
    profile = agent.parse(dummy_pdf_stream, "pdf")
    assert profile.source_type == "pdf"
    assert profile.job_title == "PDF Job Title"


@patch("backend.app.ai.agents.resume_parser.Document")
def test_parse_docx_source(mock_docx_document):
    mock_doc = MagicMock()
    p = MagicMock()
    p.text = "Acme Systems\nTitle: DOCX Job Title"
    mock_doc.paragraphs = [p]
    mock_doc.tables = []
    mock_doc.part.package.parts = []
    mock_docx_document.return_value = mock_doc

    agent = JobParserAgent()
    dummy_docx_stream = io.BytesIO(b"dummy docx bytes")

    profile = agent.parse(dummy_docx_stream, "docx")
    assert profile.source_type == "docx"
    assert profile.job_title == "DOCX Job Title"


def test_parse_url_source():
    agent = JobParserAgent()
    profile = agent.parse("https://google.com/jobs/123", "url")
    assert profile.source_type == "url"
    assert profile.application_url == "https://google.com/jobs/123"
    assert "Job Posting URL:" in profile.original_jd


# ==========================================
# 5. Exception & Input Validations
# ==========================================

def test_parse_empty_jd_raises_exception():
    agent = JobParserAgent()
    with pytest.raises(InvalidJobInputError) as exc_info:
        agent.parse("", "text")
    assert "Empty job description" in str(exc_info.value)


def test_parse_invalid_type_raises_exception():
    agent = JobParserAgent()
    with pytest.raises(InvalidJobInputError):
        agent.parse(12345, "text")


def test_parse_unsupported_format_raises_exception():
    agent = JobParserAgent()
    with pytest.raises(UnsupportedFileTypeError) as exc_info:
        agent.parse("dummy content", "xlsx")
    assert "Unsupported job parser input" in str(exc_info.value)


# ==========================================
# 6. Edge Cases
# ==========================================

def test_parse_unicode_characters():
    agent = JobParserAgent()
    profile = agent.parse(UNICODE_JD, "text")
    
    assert profile.company_name == "München Tech GmbĤ"
    assert profile.job_title == "Sênior Backend Devêloper"
    assert profile.recruiter_email == "händshake@münchen.de"
    assert "Pythøn" in profile.required_skills


def test_parse_very_large_jd():
    agent = JobParserAgent()
    # Large 20k word job description
    large_jd = "Google\nTitle: Staff Dev\n" + "Responsibilities:\n- Do task.\n" * 2000
    profile = agent.parse(large_jd, "text")
    
    assert profile.company_name == "Google"
    assert len(profile.responsibilities) == 2000


def test_parse_weird_formatting():
    agent = JobParserAgent()
    profile = agent.parse(WEIRD_FORMATTING_JD, "text")
    
    assert profile.company_name == "Acme Systems"
    assert profile.job_title == "Senior Developer"
    assert profile.work_mode == "Remote"
    assert "Python" in profile.required_skills


def test_parse_duplicate_skills_persisted():
    # Job parser list parsing should preserve duplicate list values as raw parsed or verify length
    agent = JobParserAgent()
    jd_duplicate_skills = "Skills\n* Python\n* Python\n* SQL"
    profile = agent.parse(jd_duplicate_skills, "text")
    assert len(profile.required_skills) == 3
    assert profile.required_skills.count("Python") == 2


def test_parse_duplicate_responsibilities():
    agent = JobParserAgent()
    jd_duplicate_resp = "Key Responsibilities\n- Code microservices.\n- Code microservices."
    profile = agent.parse(jd_duplicate_resp, "text")
    assert len(profile.responsibilities) == 2


# ==========================================
# 7. Telemetry & Schema Verification
# ==========================================

def test_schema_validation_constraints():
    # Schema checks
    metadata = JobParserMetadata(parsed_at=datetime.utcnow().isoformat(), character_count=100)
    
    # Required skills must be list, not string
    with pytest.raises(ValidationError):
        JobProfile(
            original_jd="text",
            source_type="text",
            metadata=metadata,
            required_skills="not a list"
        )


def test_logging_emitted_during_parsing(caplog):
    with caplog.at_level(logging.INFO):
        service = JobParserService()
        service.parse_job(COMPLETE_JD, "text")
        assert any("Successfully parsed job profile" in record.message for record in caplog.records)


def test_job_skills_splitting_regression():
    agent = JobParserAgent()
    jd = (
        "Required Skills:\n"
        "Python, FastAPI, Docker, PostgreSQL\n\n"
        "Preferred Skills:\n"
        "Go, Kubernetes\n"
    )
    profile = agent.parse(jd, "text")

    # Verify required_skills splitting
    assert len(profile.required_skills) == 4
    assert profile.required_skills == ["Python", "FastAPI", "Docker", "PostgreSQL"]

    # Verify preferred_skills splitting
    assert len(profile.preferred_skills) == 2
    assert profile.preferred_skills == ["Go", "Kubernetes"]


def test_job_inline_skills_parsing_regression():
    agent = JobParserAgent()
    jd = (
        "Required Skills: HTML, CSS, Javascript\n"
        "Preferred Skills: Go, Kubernetes\n"
    )
    profile = agent.parse(jd, "text")

    # Verify required_skills splitting
    assert len(profile.required_skills) == 3
    assert profile.required_skills == ["HTML", "CSS", "Javascript"]

    # Verify preferred_skills splitting
    assert len(profile.preferred_skills) == 2
    assert profile.preferred_skills == ["Go", "Kubernetes"]
