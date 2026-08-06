"""End-to-end acceptance tests validating the Phase 5 Resume Matching pipeline."""

import pytest
from backend.app.ai.agents.resume_matcher import ResumeMatcherAgent
from backend.app.ai.schemas.candidate_profile_schema import (
    CandidateProfile,
    ExperienceItem,
    ProjectItem,
    EducationItem
)
from backend.app.ai.schemas.job_parser_schema import JobProfile, JobParserMetadata


# ==========================================
# Fixtures & Helpers
# ==========================================

@pytest.fixture
def base_candidate() -> CandidateProfile:
    """Fixture supplying a fully qualified candidate profile."""
    return CandidateProfile(
        full_name="Alice Smith",
        professional_summary="Senior Software Engineer with 8 years of Python experience.",
        skills=["Python", "FastAPI", "Docker", "AWS"],
        experience=[
            ExperienceItem(
                company="Tech Corp",
                role="Senior Engineer",
                start_date="2018",
                end_date="Present"
            )
        ],
        projects=[
            ProjectItem(title="Project One", role="Lead", technologies=["Python"]),
            ProjectItem(title="Project Two", role="Dev", technologies=["FastAPI"])
        ],
        education=[
            EducationItem(institution="Stanford", degree="Master of Science")
        ],
        certifications=["AWS Certified Solutions Architect"]
    )


@pytest.fixture
def base_job() -> JobProfile:
    """Fixture supplying a job profile with standard matching criteria."""
    metadata = JobParserMetadata(parsed_at="2026-08-06T00:00:00", character_count=100)
    return JobProfile(
        company_name="Acme Systems",
        job_title="Senior Python Developer",
        experience_required="5+ years",
        education_required="Master of Science",
        required_skills=["Python", "FastAPI", "Docker"],
        preferred_skills=[],
        original_jd="We are hiring a Senior Python Developer with 5+ years of experience and a Master's degree. Must know Python, FastAPI, and Docker.",
        source_type="text",
        metadata=metadata
    )


# ==========================================
# End-to-End Acceptance Tests
# ==========================================

def test_acceptance_strong_candidate_vs_matching_job(base_candidate, base_job):
    """1. Strong candidate vs matching job:
       - Overall score = 100
       - Required skills matched
       - Experience matched
       - Education matched
    """
    agent = ResumeMatcherAgent()
    report = agent.match(base_candidate, base_job)

    assert report.overall_match_score == 100.0
    assert len(report.missing_required_skills) == 0
    assert report.experience_match_score == 100.0
    assert report.education_match_score == 100.0


def test_acceptance_weak_candidate_vs_strong_job(base_job):
    """2. Weak candidate vs strong job:
       - Low overall score
       - Missing required skills identified
       - Recommendations generated
    """
    weak_candidate = CandidateProfile(
        full_name="Bob Junior",
        professional_summary="Junior dev.",
        skills=["HTML", "CSS"],
        experience=[
            ExperienceItem(company="A", role="Intern", start_date="2025", end_date="2025")
        ]
    )
    agent = ResumeMatcherAgent()
    report = agent.match(weak_candidate, base_job)

    assert report.overall_match_score < 40.0
    assert "Python" in report.missing_required_skills
    assert "FastAPI" in report.missing_required_skills
    assert len(report.recommendations) > 0


def test_acceptance_empty_candidate(base_job):
    """3. Empty candidate:
       - Overall score = 0
       - Blank profile handled gracefully
    """
    empty = CandidateProfile()
    agent = ResumeMatcherAgent()
    report = agent.match(empty, base_job)

    assert report.overall_match_score == 0.0
    assert report.experience_match_score == 0.0
    assert report.education_match_score == 0.0
    assert report.project_match_score == 0.0
    assert report.certification_match_score == 0.0
    assert report.keyword_coverage == 0.0
    assert len(report.strengths) == 0


def test_acceptance_job_without_project_requirements(base_candidate, base_job):
    """4. Job without project requirements:
       - Project score defaults to 100
    """
    # base_job does not contain any project keywords
    agent = ResumeMatcherAgent()
    report = agent.match(base_candidate, base_job)

    assert report.project_match_score == 100.0


def test_acceptance_job_without_certification_requirements(base_candidate, base_job):
    """5. Job without certification requirements:
       - Certification score defaults to 100
    """
    # base_job does not contain any certification keywords
    agent = ResumeMatcherAgent()
    report = agent.match(base_candidate, base_job)

    assert report.certification_match_score == 100.0


def test_acceptance_job_requiring_projects(base_candidate, base_job):
    """6. Job requiring projects:
       - One project -> 50
       - Two or more projects -> 100
       - No projects -> 0
    """
    job_with_projects = base_job.model_copy(update={
        "original_jd": "Portfolio/github project list required."
    })
    agent = ResumeMatcherAgent()

    # Case A: Two or more projects
    report_two = agent.match(base_candidate, job_with_projects)
    assert report_two.project_match_score == 100.0

    # Case B: One project
    cand_one_proj = base_candidate.model_copy(update={
        "projects": [base_candidate.projects[0]]
    })
    report_one = agent.match(cand_one_proj, job_with_projects)
    assert report_one.project_match_score == 50.0

    # Case C: No projects
    cand_no_proj = base_candidate.model_copy(update={"projects": []})
    report_zero = agent.match(cand_no_proj, job_with_projects)
    assert report_zero.project_match_score == 0.0


def test_acceptance_job_requiring_certifications(base_candidate, base_job):
    """7. Job requiring certifications:
       - Certification present -> 100
       - Certification absent -> 0
    """
    job_with_certs = base_job.model_copy(update={
        "original_jd": "AWS Certification required."
    })
    agent = ResumeMatcherAgent()

    # Case A: Certification present
    report_has_cert = agent.match(base_candidate, job_with_certs)
    assert report_has_cert.certification_match_score == 100.0

    # Case B: Certification absent
    cand_no_cert = base_candidate.model_copy(update={"certifications": []})
    report_no_cert = agent.match(cand_no_cert, job_with_certs)
    assert report_no_cert.certification_match_score == 0.0


def test_acceptance_conditional_scoring_isolation(base_candidate, base_job):
    """8. Ensure conditional scoring does not affect unrelated score categories."""
    agent = ResumeMatcherAgent()

    # Base match with default full credits
    base_report = agent.match(base_candidate, base_job)
    base_skills = base_report.overall_match_score - (base_report.project_match_score * 0.05) - (base_report.certification_match_score * 0.05)

    # Job requiring projects & certs (forcing scoring penalties on those categories)
    job_strict = base_job.model_copy(update={
        "original_jd": "Portfolio projects and PMP certification required."
    })
    # Candidate lacks projects and certifications
    deprived_candidate = base_candidate.model_copy(update={
        "projects": [],
        "certifications": []
    })

    strict_report = agent.match(deprived_candidate, job_strict)

    # Assert project/certification scores changed
    assert strict_report.project_match_score == 0.0
    assert strict_report.certification_match_score == 0.0

    # Assert unrelated score categories remain identical
    assert strict_report.experience_match_score == base_report.experience_match_score
    assert strict_report.education_match_score == base_report.education_match_score
