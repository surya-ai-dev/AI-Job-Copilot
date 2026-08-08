"""Exhaustive Unit Tests for the Validator Agent."""



import pytest

from backend.app.ai.schemas.candidate_profile_schema import (

    CandidateProfile,

    ExperienceItem,

    ProjectItem,

    EducationItem

)

from backend.app.ai.agents.validator_agent import ResumeValidatorAgent, ValidationStatus





@pytest.fixture

def original_candidate() -> CandidateProfile:

    """Returns the ground truth candidate profile."""

    return CandidateProfile(

        full_name="Alice Smith",

        skills=["Python", "FastAPI"],

        experience=[

            ExperienceItem(

                company="Tech Corp",

                role="Senior Engineer",

                start_date="Jan 2020",

                end_date="Dec 2022",

                description="Designed Python APIs using FastAPI and SQL.",

                highlights=[]

            )

        ],

        projects=[

            ProjectItem(title="Job Copilot", description="Used FastAPI.")

        ],

        education=[

            EducationItem(institution="State Uni", degree="BS", field_of_study="CS")

        ],

        certifications=["AWS Solution Architect"]

    )





def test_validator_passes_legitimate_resume(original_candidate):

    """Verify validator approves a tailored resume with identical structural and entity constraints."""

    tailored = original_candidate.model_copy(deep=True)

    # Perform permissible rewordings

    tailored.professional_summary = "A results-oriented engineer."

    tailored.experience[0].description = "Architected high throughput APIs using FastAPI and SQL."



    agent = ResumeValidatorAgent()

    report = agent.validate(original_candidate, tailored)



    assert report.status == ValidationStatus.PASSED

    assert len(report.factual_violations) == 0





def test_validator_rejects_added_experience_record(original_candidate):

    """Verify validator blocks tailored profile that adds an extra company history item."""

    tailored = original_candidate.model_copy(deep=True)

    tailored.experience.append(

        ExperienceItem(company="Extra Corp", role="Dev", start_date="2023", end_date="2024")

    )



    agent = ResumeValidatorAgent()

    report = agent.validate(original_candidate, tailored)



    assert report.status == ValidationStatus.FAILED

    assert any("Altered the number of employment history records" in v.description for v in report.factual_violations)





def test_validator_rejects_altered_company_metadata(original_candidate):

    """Verify validator blocks tailored profile that changes company name, role, or dates."""

    agent = ResumeValidatorAgent()



    # 1. Alter company name

    tailored_company = original_candidate.model_copy(deep=True)

    tailored_company.experience[0].company = "Google"

    report_company = agent.validate(original_candidate, tailored_company)

    assert report_company.status == ValidationStatus.FAILED

    assert any("Fabricated/modified company name" in v.description for v in report_company.factual_violations)



    # 2. Alter role title

    tailored_role = original_candidate.model_copy(deep=True)

    tailored_role.experience[0].role = "Lead Architect"

    report_role = agent.validate(original_candidate, tailored_role)

    assert report_role.status == ValidationStatus.FAILED

    assert any("Fabricated/modified job role title" in v.description for v in report_role.factual_violations)



    # 3. Alter employment dates

    tailored_dates = original_candidate.model_copy(deep=True)

    tailored_dates.experience[0].end_date = "Dec 2024" # Original: Dec 2022

    report_dates = agent.validate(original_candidate, tailored_dates)

    assert report_dates.status == ValidationStatus.FAILED

    assert any("Altered employment duration dates" in v.description for v in report_dates.factual_violations)





def test_validator_rejects_altered_education_details(original_candidate):

    """Verify validator blocks tailored profile that alters education history details."""

    tailored = original_candidate.model_copy(deep=True)

    tailored.education[0].degree = "MS" # Original: BS



    agent = ResumeValidatorAgent()

    report = agent.validate(original_candidate, tailored)



    assert report.status == ValidationStatus.FAILED

    assert any("Altered educational credentials" in v.description for v in report.factual_violations)





def test_validator_rejects_added_certification(original_candidate):

    """Verify validator blocks tailored profile that fabricates new certifications."""

    tailored = original_candidate.model_copy(deep=True)

    tailored.certifications.append("Certified Kubernetes Administrator")



    agent = ResumeValidatorAgent()

    report = agent.validate(original_candidate, tailored)



    assert report.status == ValidationStatus.FAILED

    assert any("Fabricated new certification credentials" in v.description for v in report.factual_violations)





def test_validator_rejects_fabricated_experience_claims(original_candidate):

    """Verify validator blocks tailored profile that claims familiarity with technologies/entities not grounded in original resume."""

    tailored = original_candidate.model_copy(deep=True)

    # Claiming Docker expertise inside the experience description when Docker is not listed anywhere in original resume

    tailored.experience[0].description = "Designed Python APIs using FastAPI, SQL, and Docker."



    agent = ResumeValidatorAgent()

    report = agent.validate(original_candidate, tailored)



    assert report.status == ValidationStatus.FAILED

    assert any("Fabricated skill claim in experience 1" in v.description for v in report.factual_violations)

    assert any("Docker" in v.tailored_reference for v in report.factual_violations)
