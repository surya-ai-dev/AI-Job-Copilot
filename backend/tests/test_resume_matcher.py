"""Unit tests verifying the Resume Matcher Agent and Service layers."""

import logging
import pytest
from pydantic import ValidationError

from backend.app.ai.agents.resume_matcher import ResumeMatcherAgent
from backend.app.ai.services.resume_matcher_service import ResumeMatcherService
from backend.app.ai.schemas.candidate_profile_schema import (
    CandidateProfile,
    ExperienceItem,
    ProjectItem,
    EducationItem
)
from backend.app.ai.schemas.job_parser_schema import JobProfile, JobParserMetadata
from backend.app.ai.schemas.resume_match_schema import ResumeMatchReport


# ==========================================
# Reusable Mock Setup Fixtures
# ==========================================

@pytest.fixture
def empty_candidate() -> CandidateProfile:
    """Fixture returning an empty CandidateProfile."""
    return CandidateProfile()


@pytest.fixture
def empty_job() -> JobProfile:
    """Fixture returning an empty JobProfile."""
    metadata = JobParserMetadata(parsed_at="2026-08-06T00:00:00", character_count=0)
    return JobProfile(original_jd="", source_type="text", metadata=metadata)


@pytest.fixture
def candidate_full() -> CandidateProfile:
    """Fixture supplying a fully populated candidate profile."""
    return CandidateProfile(
        full_name="Jane Doe",
        email="jane.doe@example.com",
        phone="+1 555-019-2834",
        linkedin_url="https://linkedin.com/in/janedoe",
        github_url="https://github.com/janedoe",
        professional_summary="Senior Software Engineer with experience in cloud platforms and backend architectures.",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker", "Go"],
        experience=[
            ExperienceItem(
                company="Google",
                role="Senior Engineer",
                start_date="Jan 2021",
                end_date="Present",
                description="Built high-performance API architectures and database scaling solutions.",
                highlights=["Reduced latency by 40%", "Migrated legacy services"]
            )
        ],
        projects=[
            ProjectItem(
                title="Job Copilot",
                role="Lead Creator",
                technologies=["FastAPI", "SQLite", "Docker"],
                description="AI-driven job application organizer tool.",
                url="https://github.com/janedoe/jobcopilot",
                highlights=["Integrated extraction APIs"]
            ),
            ProjectItem(
                title="Log Analyzer",
                role="Developer",
                technologies=["Go", "Redis"],
                description="High throughput logs processor.",
                url="https://github.com/janedoe/loganalyzer",
                highlights=["Processed 10k QPS"]
            )
        ],
        education=[
            EducationItem(
                institution="Stanford University",
                degree="Master of Science",
                field_of_study="Computer Science",
                start_date="2018",
                end_date="2020",
                gpa="3.9"
            )
        ],
        certifications=["AWS Certified Solutions Architect"]
    )


@pytest.fixture
def job_full() -> JobProfile:
    """Fixture supplying a fully populated job profile."""
    metadata = JobParserMetadata(parsed_at="2026-08-06T00:00:00", character_count=100)
    return JobProfile(
        company_name="Acme Inc",
        job_title="Senior Backend Engineer",
        department="Engineering",
        employment_type="Full-time",
        work_mode="Remote",
        location="Chicago, IL",
        salary="$140k - $170k",
        experience_required="5 years",
        education_required="Master of Science",
        required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        preferred_skills=["Go", "Kubernetes"],
        responsibilities=["Build high throughput microservices", "Optimize database performance"],
        qualifications=["MS in Computer Science", "AWS Certifications"],
        benefits=["Full healthcare coverage", "Unlimited PTO"],
        recruiter_email="hr@acme.com",
        recruiter_phone="+1 555-987-6543",
        recruiter_whatsapp="+1 555-987-6543",
        application_url="https://acme.com/careers/apply",
        original_jd="Acme Inc looking for a Senior Backend Engineer. Required: Python, FastAPI, PostgreSQL, Docker. Preferred: Go, Kubernetes. MS in CS, 5 years experience.",
        source_type="text",
        metadata=metadata
    )


# ==========================================
# 1. Functional Matching Tests
# ==========================================

def test_complete_match(candidate_full, job_full):
    # Setup candidate to match every criteria of job
    candidate = candidate_full.model_copy(update={
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Go", "Kubernetes"]
    })
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    assert report.overall_match_score == 100.0
    assert report.experience_match_score == 100.0
    assert report.education_match_score == 100.0
    assert report.project_match_score == 100.0
    assert report.certification_match_score == 100.0
    assert len(report.missing_required_skills) == 0
    assert len(report.missing_preferred_skills) == 0
    assert "Kubernetes" in report.matched_skills


def test_no_match(empty_candidate, job_full):
    agent = ResumeMatcherAgent()
    report = agent.match(empty_candidate, job_full)

    # Empty candidate matches nothing
    assert report.overall_match_score == 0.0
    assert report.experience_match_score == 0.0
    assert report.education_match_score == 0.0
    assert report.project_match_score == 0.0
    assert report.certification_match_score == 0.0
    assert report.missing_required_skills == []
    assert report.missing_preferred_skills == []


def test_partial_match(candidate_full, job_full):
    # Candidate lacks preferred skills Go/Kubernetes and has 1 project
    candidate = candidate_full.model_copy(update={
        "skills": ["Python", "FastAPI"],
        "projects": [candidate_full.projects[0]]
    })
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    assert 0.0 < report.overall_match_score < 100.0
    assert report.project_match_score == 100.0
    assert "PostgreSQL" in report.missing_required_skills


# ==========================================
# 2. Skill Gaps Match Tests
# ==========================================

def test_missing_required_skills(candidate_full, job_full):
    candidate = candidate_full.model_copy(update={"skills": ["Go", "Kubernetes"]})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    # Required skills score is 0.0
    assert len(report.missing_required_skills) == len(job_full.required_skills)
    assert "Python" in report.missing_required_skills


def test_missing_preferred_skills(candidate_full, job_full):
    candidate = candidate_full.model_copy(update={"skills": ["Python", "FastAPI", "PostgreSQL", "Docker"]})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    # Required skills matched, but preferred missing
    assert len(report.missing_required_skills) == 0
    assert len(report.missing_preferred_skills) == len(job_full.preferred_skills)
    assert "Kubernetes" in report.missing_preferred_skills


def test_case_insensitive_skills_matching(candidate_full, job_full):
    candidate = candidate_full.model_copy(update={"skills": ["python", "fastapi", "postgresql", "docker"]})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    # Lower case skills should match upper case job requirements
    assert len(report.missing_required_skills) == 0


def test_whitespace_skills_matching(candidate_full, job_full):
    candidate = candidate_full.model_copy(update={"skills": [" Python ", " FastAPI"]})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    assert "Python" in report.matched_skills
    assert "FastAPI" in report.matched_skills


# ==========================================
# 3. Experience Match Tests
# ==========================================

def test_no_experience(candidate_full, job_full):
    candidate = candidate_full.model_copy(update={"experience": []})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    assert report.experience_match_score == 0.0


def test_partial_experience(candidate_full, job_full):
    # Candidate has 2 years (2022 to 2024), Job requires 5 years
    exp = ExperienceItem(company="A", role="Dev", start_date="2022", end_date="2024")
    candidate = candidate_full.model_copy(update={"experience": [exp]})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    # Score: 2 / 5 = 40.0%
    assert report.experience_match_score == 40.0


def test_excessive_experience(candidate_full, job_full):
    # Candidate has 10 years (2016 to 2026), Job requires 5 years
    exp = ExperienceItem(company="A", role="Dev", start_date="2016", end_date="Present")
    candidate = candidate_full.model_copy(update={"experience": [exp]})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    # Score capped at 100.0%
    assert report.experience_match_score == 100.0


def test_experience_no_job_requirement(candidate_full, job_full):
    job = job_full.model_copy(update={"experience_required": None})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate_full, job)

    assert report.experience_match_score == 100.0


# ==========================================
# 4. Education Match Tests
# ==========================================

def test_education_exact_match(candidate_full, job_full):
    agent = ResumeMatcherAgent()
    report = agent.match(candidate_full, job_full)

    # Both have Master's
    assert report.education_match_score == 100.0


def test_education_exceeds_requirement(candidate_full, job_full):
    # Job requires BS, Candidate has MS
    job = job_full.model_copy(update={"education_required": "Bachelor of Science"})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate_full, job)

    assert report.education_match_score == 100.0


def test_education_missing_requirement(candidate_full, job_full):
    # Candidate has Bachelor's, Job requires Master's
    edu = EducationItem(institution="A", degree="Bachelor of Science")
    candidate = candidate_full.model_copy(update={"education": [edu]})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    # Score: 2 (BS rank) / 3 (MS rank) = 66.7%
    assert report.education_match_score == round(2/3 * 100, 1)


def test_education_no_job_requirement(candidate_full, job_full):
    job = job_full.model_copy(update={"education_required": None})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate_full, job)

    assert report.education_match_score == 100.0


def test_education_candidate_no_degree(candidate_full, job_full):
    candidate = candidate_full.model_copy(update={"education": []})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    assert report.education_match_score == 0.0


# ==========================================
# 5. Project & Certification Match Tests
# ==========================================

def test_projects_perfect_match(candidate_full, job_full):
    agent = ResumeMatcherAgent()
    report = agent.match(candidate_full, job_full)

    # Has 2 projects
    assert report.project_match_score == 100.0


def test_projects_partial_match(candidate_full, job_full):
    job = job_full.model_copy(update={"original_jd": "Portfolio required"})
    candidate = candidate_full.model_copy(update={"projects": [candidate_full.projects[0]]})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job)

    # Has 1 project
    assert report.project_match_score == 50.0


def test_projects_missing(candidate_full, job_full):
    job = job_full.model_copy(update={"original_jd": "Portfolio required"})
    candidate = candidate_full.model_copy(update={"projects": []})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job)

    assert report.project_match_score == 0.0


def test_certifications_present(candidate_full, job_full):
    agent = ResumeMatcherAgent()
    report = agent.match(candidate_full, job_full)

    assert report.certification_match_score == 100.0


def test_certifications_missing(candidate_full, job_full):
    candidate = candidate_full.model_copy(update={"certifications": []})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    assert report.certification_match_score == 0.0


# ==========================================
# 6. Edge Cases & Unicode
# ==========================================

def test_unicode_matching(candidate_full, job_full):
    candidate = candidate_full.model_copy(update={"skills": ["Pythøn", "Gø"]})
    job = job_full.model_copy(update={
        "required_skills": ["Pythøn"],
        "preferred_skills": ["Gø"]
    })
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job)

    assert "Pythøn" in report.matched_skills
    assert len(report.missing_required_skills) == 0


def test_duplicate_skills_in_lists(candidate_full, job_full):
    candidate = candidate_full.model_copy(update={"skills": ["Python", "Python", "FastAPI"]})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    # Check that duplication doesn't crash or double add to matches
    assert report.matched_skills.count("Python") == 1


def test_large_skills_list(candidate_full, job_full):
    large_skills = [f"Skill-{i}" for i in range(1000)]
    candidate = candidate_full.model_copy(update={"skills": large_skills + ["Python"]})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    assert "Python" in report.matched_skills


def test_large_resume_description(candidate_full, job_full):
    large_summary = "Developer summary. " * 2000
    candidate = candidate_full.model_copy(update={"professional_summary": large_summary})
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job_full)

    # Keyword coverage should work fine
    assert report.keyword_coverage > 0.0


def test_empty_candidate_profile(empty_candidate, job_full):
    agent = ResumeMatcherAgent()
    report = agent.match(empty_candidate, job_full)
    assert report.overall_match_score == 0.0


def test_empty_job_profile(candidate_full, empty_job):
    agent = ResumeMatcherAgent()
    report = agent.match(candidate_full, empty_job)
    # 100% since job asks for nothing
    assert report.overall_match_score == 100.0


# ==========================================
# 7. Keyword Coverage & Report Telemetry
# ==========================================

def test_keyword_coverage_perfect(candidate_full, job_full):
    # Job has small content, all matched
    job = job_full.model_copy(update={
        "job_title": "Engineer",
        "required_skills": ["Python"],
        "preferred_skills": []
    })
    candidate = candidate_full.model_copy(update={
        "skills": ["Python"],
        "professional_summary": "Engineer"
    })
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job)

    assert report.keyword_coverage == 100.0


def test_keyword_coverage_zero(candidate_full, job_full):
    job = job_full.model_copy(update={
        "job_title": "Kubernetes",
        "required_skills": ["Kubernetes"],
        "preferred_skills": []
    })
    candidate = candidate_full.model_copy(update={
        "skills": ["Python"],
        "professional_summary": "Architect",
        "experience": [],
        "projects": [],
        "education": [],
        "certifications": [],
        "full_name": ""
    })
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job)

    assert report.keyword_coverage == 0.0


def test_strengths_weaknesses_recommendations(candidate_full, job_full):
    agent = ResumeMatcherAgent()
    report = agent.match(candidate_full, job_full)

    # Fully matched candidate should have strengths, no missing required weaknesses
    assert len(report.strengths) > 0
    assert len(report.weaknesses) == 1  # Missing Kubernetes preferred skill
    assert len(report.recommendations) == 1


def test_logging_emitted_in_service(caplog, candidate_full, job_full):
    with caplog.at_level(logging.INFO):
        service = ResumeMatcherService()
        service.match_profiles(candidate_full, job_full)
        assert any("Match report generated successfully" in record.message for record in caplog.records)


def test_schema_validation_constraints():
    # Schema properties types check
    with pytest.raises(ValidationError):
        ResumeMatchReport(
            overall_match_score="not-a-float",
            experience_match_score=90.0,
            education_match_score=80.0,
            project_match_score=100.0,
            certification_match_score=100.0,
            keyword_coverage=75.0
        )


def test_empty_candidate_profile_always_returns_zero(job_full):
    agent = ResumeMatcherAgent()
    empty = CandidateProfile()
    report = agent.match(empty, job_full)
    assert report.overall_match_score == 0.0
    assert report.experience_match_score == 0.0
    assert report.education_match_score == 0.0
    assert report.project_match_score == 0.0
    assert report.certification_match_score == 0.0
    assert report.keyword_coverage == 0.0
    assert len(report.strengths) == 0
    assert len(report.recommendations) == 1
    assert "no usable profile information" in report.recommendations[0]


def test_zero_required_skills_match_score_capped(candidate_full, job_full):
    # Candidate matches zero required skills
    candidate = candidate_full.model_copy(update={"skills": ["Java", "Ruby"]})
    job = job_full.model_copy(update={
        "required_skills": ["Python", "FastAPI"],
        "preferred_skills": []
    })
    agent = ResumeMatcherAgent()
    report = agent.match(candidate, job)

    # Component scores are high, but overall is capped
    assert report.experience_match_score == 100.0
    assert report.education_match_score == 100.0
    assert report.project_match_score == 100.0
    assert report.certification_match_score == 100.0
    assert report.overall_match_score <= 39.9
