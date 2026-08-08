"""Unit tests for the Critic Agent."""



import pytest

from backend.app.ai.schemas.candidate_profile_schema import (

    CandidateProfile,

    ExperienceItem

)

from backend.app.ai.agents.critic_agent import CriticAgent, CriticStatus





@pytest.fixture

def clean_candidate() -> CandidateProfile:

    """Returns a stylistically clean candidate profile."""

    return CandidateProfile(

        professional_summary=(

            "Senior Software Engineer with 8 years of Python experience, specializing "

            "in FastAPI, microservices, database optimizations, and Kubernetes deployments."

        ),

        skills=["Python", "FastAPI"],

        experience=[

            ExperienceItem(

                company="A",

                role="Engineer",

                description="Designed high throughput backend APIs.",

                highlights=["Optimized database indexes."]

            )

        ]

    )





@pytest.fixture

def passive_candidate() -> CandidateProfile:

    """Returns a candidate profile with multiple passive voice elements."""

    return CandidateProfile(

        professional_summary="Short summary.",

        skills=["Python"],

        experience=[

            ExperienceItem(

                company="A",

                role="Engineer",

                description="Was responsible for running script updates and assisted in deployment.",

                highlights=["Helped with configuration tasks."]

            )

        ]

    )





@pytest.fixture

def job_data() -> dict:

    """Returns standard job target parameters."""

    return {

        "required_skills": ["Python", "FastAPI"]

    }





def test_critic_approval(clean_candidate, job_data):

    """Verify that critic approves a well-formatted and active-voice resume."""

    agent = CriticAgent()

    report = agent.review(clean_candidate, job_data)



    assert report.status == CriticStatus.APPROVED

    assert len(report.awkward_phrases) == 0

    assert len(report.comments) == 0





def test_critic_rejection_for_passive_phrases(passive_candidate, job_data):

    """Verify that critic rejects a resume containing multiple passive voice elements."""

    agent = CriticAgent()

    report = agent.review(passive_candidate, job_data)



    assert report.status == CriticStatus.REJECTED

    # Assert awkward phrases are parsed

    assert len(report.awkward_phrases) == 3

    # Check original texts identified

    originals = [phrase.original_text.lower() for phrase in report.awkward_phrases]

    assert any("was responsible for" in text for text in originals)

    assert any("assisted in" in text for text in originals)

    assert any("helped with" in text for text in originals)





def test_critic_length_warning(clean_candidate, job_data):

    """Verify that critic flags summary length violations."""

    agent = CriticAgent()



    # 1. Too long summary

    long_summary = "Developer. " * 150

    long_cand = clean_candidate.model_copy(update={"professional_summary": long_summary})

    report_long = agent.review(long_cand, job_data)

    assert report_long.status == CriticStatus.REJECTED

    assert any("too long" in comment for comment in report_long.comments)



    # 2. Too short summary

    short_cand = clean_candidate.model_copy(update={"professional_summary": "Too short."})

    report_short = agent.review(short_cand, job_data)

    assert report_short.status == CriticStatus.APPROVED # Brief is a warning comment, not automatically a rejection

    assert any("too brief" in comment for comment in report_short.comments)





def test_critic_ats_keyword_warning(clean_candidate):

    """Verify that critic identifies missing required skills."""

    agent = CriticAgent()

    # Job requires Go, but candidate only has Python/FastAPI

    job_with_go = {"required_skills": ["Go"]}

    report = agent.review(clean_candidate, job_with_go)



    assert report.status == CriticStatus.APPROVED

    assert any("Missing key required skills: Go" in comment for comment in report.comments)
