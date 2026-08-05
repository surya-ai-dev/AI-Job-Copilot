"""Unit tests for the Candidate Profile Extractor Agent and Service."""

import pytest
from backend.app.ai.agents.candidate_profile_extractor import (
    CandidateProfileExtractorAgent,
    RuleBasedCandidateProfileExtractor
)
from backend.app.ai.services.candidate_profile_service import CandidateProfileService
from backend.app.ai.schemas.candidate_profile_schema import CandidateProfile


# Sample complete resume text
COMPLETE_RESUME_TEXT = """
Jane Doe
jane.doe@example.com | (555) 019-2834
linkedin.com/in/janedoe | github.com/janedoe

Professional Summary
Senior Backend Engineer with 5+ years of experience building resilient microservices using Python and FastAPI. Highly skilled in SQL optimization and scalable database architectures.

Skills
Python, FastAPI, Django, PostgreSQL, Redis, Docker, Kubernetes, CI/CD, Git, Unit Testing

Work Experience
Google - Senior Software Engineer | Jan 2022 - Present
- Led database migration to PostgreSQL reducing API response latencies by 35%.
- Designed and built authentication endpoints securing multi-tenant APIs.
Acme Corp - Software Engineer | Jun 2019 - Dec 2021
- Maintained legacy Django codebases and modernized key services using FastAPI.
- Implemented Celery queue configurations to process async mail merges.

Projects
Job Copilot - Tech Lead | github.com/janedoe/jobcopilot
- Developed LangGraph optimization state charts for resume rewriting loops.
- Set up Docker local network setups for PostgreSQL database environments.
Portfolio Site - Owner
- Built a portfolio webpage hosted on cloud buckets showing personal dashboard telemetry.

Education
Stanford University - Master of Science | CS | 2017 - 2019
GPA: 3.9
Stanford University - Bachelor of Science | CS | 2013 - 2017

Certifications
AWS Certified Solutions Architect - Professional
Google Cloud Professional Cloud Architect
"""


def test_complete_resume():
    agent = CandidateProfileExtractorAgent()
    profile = agent.extract_profile(COMPLETE_RESUME_TEXT)
    
    assert profile.full_name == "Jane Doe"
    assert profile.email == "jane.doe@example.com"
    assert profile.phone == "(555) 019-2834"
    assert profile.linkedin_url == "https://linkedin.com/in/janedoe"
    assert profile.github_url == "https://github.com/janedoe"
    assert "Senior Backend Engineer" in profile.professional_summary
    
    # Skills checks
    assert "Python" in profile.skills
    assert "FastAPI" in profile.skills
    assert "Kubernetes" in profile.skills

    # Experience checks
    assert len(profile.experience) == 2
    assert profile.experience[0].company == "Google"
    assert profile.experience[0].role == "Senior Software Engineer"
    assert profile.experience[0].start_date == "Jan 2022"
    assert len(profile.experience[0].highlights) == 2
    assert "database migration" in profile.experience[0].highlights[0]
    
    # Projects checks
    assert len(profile.projects) == 2
    assert profile.projects[0].title == "Job Copilot"
    assert profile.projects[0].role == "Tech Lead"
    assert profile.projects[0].url == "https://github.com/janedoe/jobcopilot"
    assert "Docker local network" in profile.projects[0].highlights[1]
    
    # Education checks
    assert len(profile.education) == 2
    assert profile.education[0].institution == "Stanford University"
    assert profile.education[0].degree == "Master of Science"
    assert profile.education[0].gpa == "3.9"

    # Certifications checks
    assert len(profile.certifications) == 2
    assert "AWS Certified Solutions Architect - Professional" in profile.certifications


def test_resume_missing_phone():
    resume_text = """
    John Smith
    jsmith@example.com
    linkedin.com/in/jsmith | github.com/jsmith
    
    Summary
    Experienced front-end engineer.
    """
    agent = CandidateProfileExtractorAgent()
    profile = agent.extract_profile(resume_text)
    
    assert profile.full_name == "John Smith"
    assert profile.email == "jsmith@example.com"
    assert profile.phone is None
    assert profile.linkedin_url == "https://linkedin.com/in/jsmith"


def test_resume_missing_linkedin():
    resume_text = """
    Bob Johnson
    bjohnson@example.com | +1 555-555-5555
    github.com/bjohnson
    
    Summary
    Systems engineer specializing in Rust.
    """
    agent = CandidateProfileExtractorAgent()
    profile = agent.extract_profile(resume_text)
    
    assert profile.full_name == "Bob Johnson"
    assert profile.email == "bjohnson@example.com"
    assert profile.phone == "+1 555-555-5555"
    assert profile.linkedin_url is None
    assert profile.github_url == "https://github.com/bjohnson"


def test_resume_multiple_projects():
    resume_text = """
    Projects
    Alpha Parser - Lead
    - Designed custom AST interpreters.
    Beta Optimizer - Lead
    - Resized deep network parameter weights.
    Gamma Compiler - Owner
    - Compiled byte code targets for hardware emulator.
    """
    agent = CandidateProfileExtractorAgent()
    profile = agent.extract_profile(resume_text)
    
    assert len(profile.projects) == 3
    assert profile.projects[0].title == "Alpha Parser"
    assert profile.projects[0].role == "Lead"
    assert profile.projects[1].title == "Beta Optimizer"
    assert profile.projects[1].role == "Lead"
    assert profile.projects[2].title == "Gamma Compiler"
    assert profile.projects[2].role == "Owner"


def test_resume_no_certifications():
    resume_text = """
    Summary
    Developer profile.
    
    Skills
    Python, SQL
    """
    agent = CandidateProfileExtractorAgent()
    profile = agent.extract_profile(resume_text)
    
    assert len(profile.certifications) == 0


def test_empty_resume():
    agent = CandidateProfileExtractorAgent()
    profile = agent.extract_profile("")
    
    assert profile.full_name is None
    assert profile.email is None
    assert len(profile.skills) == 0
    assert len(profile.experience) == 0


def test_invalid_resume_text():
    resume_text = "lorem ipsum dolor sit amet, arbitrary text profile with email but no headers test@email.com"
    agent = CandidateProfileExtractorAgent()
    profile = agent.extract_profile(resume_text)
    
    assert profile.email == "test@email.com"
    assert profile.full_name is None
    assert len(profile.skills) == 0
    assert len(profile.experience) == 0


def test_service_extraction():
    # Test service class calls orchestrator successfully
    service = CandidateProfileService()
    profile = service.extract_profile(COMPLETE_RESUME_TEXT)
    
    assert profile.full_name == "Jane Doe"
    assert profile.email == "jane.doe@example.com"
