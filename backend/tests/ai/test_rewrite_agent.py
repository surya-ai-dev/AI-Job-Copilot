"""Unit tests for the Resume Rewrite Agent."""



import pytest

from backend.app.ai.schemas.candidate_profile_schema import (

    CandidateProfile,

    ExperienceItem,

    ProjectItem,

    EducationItem

)

from backend.app.ai.agents.planner_agent import OptimizationPlan, OptimizationTask

from backend.app.ai.agents.rewrite_agent import ResumeRewriteAgent





@pytest.fixture

def sample_candidate() -> CandidateProfile:

    """Returns a valid candidate profile for testing."""

    return CandidateProfile(

        full_name="John Doe",

        email="john@example.com",

        phone="+1 555-0199",

        professional_summary="Backend engineer.",

        skills=["Python"],

        experience=[

            ExperienceItem(

                company="Old Corp",

                role="Developer",

                start_date="2020",

                end_date="2022",

                description="Wrote Python APIs.",

                highlights=["Sped up query speeds."]

            )

        ],

        projects=[

            ProjectItem(

                title="Job Matcher",

                description="Built a matching tool."

            )

        ],

        education=[

            EducationItem(

                institution="State Uni",

                degree="BS",

                field_of_study="CS"

            )

        ]

    )





@pytest.fixture

def sample_job_data() -> dict:

    """Returns typical parsed job metadata."""

    return {

        "required_skills": ["Python", "FastAPI"],

        "preferred_skills": ["Docker"]

    }





def test_successful_rewrite(sample_candidate, sample_job_data):

    """Verify that rewrite agent successfully updates summary, skills, experience, and projects."""

    plan = OptimizationPlan(

        tasks=[

            OptimizationTask(

                priority=1,

                target_section="skills",

                action="Align candidate skills list to include core required skill 'FastAPI'.",

                rationale="Missing required skill"

            ),

            OptimizationTask(

                priority=2,

                target_section="summary",

                action="Emphasize depth and leadership to address the experience deficit.",

                rationale="Compensate gap"

            ),

            OptimizationTask(

                priority=3,

                target_section="experience",

                action="Tailor experience descriptions.",

                rationale="Emphasize details"

            ),

            OptimizationTask(

                priority=4,

                target_section="projects",

                action="Optimize project descriptions.",

                rationale="Emphasize details"

            )

        ]

    )



    agent = ResumeRewriteAgent()

    optimized = agent.rewrite(sample_candidate, plan, sample_job_data)



    # Validate Skills alignment

    assert "FastAPI" in optimized.skills

    assert "Python" in optimized.skills



    # Validate Summary rewrite

    assert "Seasoned professional possessing advanced technical capabilities" in optimized.professional_summary



    # Validate Experience rewrite

    assert "Aligned actions to deliver high-quality backend results" in optimized.experience[0].description

    assert "Leveraged core technologies to optimize" in optimized.experience[0].highlights[0]



    # Validate Project rewrite

    assert "Emphasized architecture scalability and robust design" in optimized.projects[0].description





def test_validation_block_full_name_modified(sample_candidate, sample_job_data):

    """Verify that validator blocks integration if the full name is altered."""

    agent = ResumeRewriteAgent()

    plan = OptimizationPlan(tasks=[])



    # Simulate a rewrite that alters full_name

    modified = sample_candidate.model_copy(update={"full_name": "John Changed"})



    with pytest.raises(ValueError) as exc_info:

        agent._validate_integrity(sample_candidate.model_dump(), modified.model_dump())

    assert "Validator Block: Full name was modified" in str(exc_info.value)





def test_validation_block_experience_dates_modified(sample_candidate, sample_job_data):

    """Verify that validator blocks integration if employment dates are altered."""

    agent = ResumeRewriteAgent()



    # Alter start_date of the work experience

    modified = sample_candidate.model_copy(deep=True)

    modified.experience[0].start_date = "2019" # Original was 2020



    with pytest.raises(ValueError) as exc_info:

        agent._validate_integrity(sample_candidate.model_dump(), modified.model_dump())

    assert "Validator Block: Employment start date modified" in str(exc_info.value)





def test_validation_block_experience_company_modified(sample_candidate, sample_job_data):

    """Verify that validator blocks integration if the company name is altered."""

    agent = ResumeRewriteAgent()



    # Alter company name of the work experience

    modified = sample_candidate.model_copy(deep=True)

    modified.experience[0].company = "New Corp" # Original was Old Corp



    with pytest.raises(ValueError) as exc_info:

        agent._validate_integrity(sample_candidate.model_dump(), modified.model_dump())

    assert "Validator Block: Employer company name modified" in str(exc_info.value)





def test_validation_block_education_modified(sample_candidate, sample_job_data):

    """Verify that validator blocks integration if education details are altered."""

    agent = ResumeRewriteAgent()



    # Alter education degree rank

    modified = sample_candidate.model_copy(deep=True)

    modified.education[0].degree = "MS" # Original was BS



    with pytest.raises(ValueError) as exc_info:

        agent._validate_integrity(sample_candidate.model_dump(), modified.model_dump())

    assert "Validator Block: Education details were altered" in str(exc_info.value)
