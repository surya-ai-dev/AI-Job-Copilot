"""Unit tests for the Autonomous Resume Optimization Loop Controller."""



import pytest

from unittest.mock import patch, MagicMock

from backend.app.ai.schemas.candidate_profile_schema import (

    CandidateProfile,

    ExperienceItem,

    EducationItem

)

from backend.app.ai.schemas.job_parser_schema import JobProfile, JobParserMetadata

from backend.app.ai.services.optimization_loop import OptimizationLoopController

from backend.app.ai.schemas.resume_optimizer_schema import (

    OptimizationRunStatus,

    OptimizationDecision

)

from backend.app.ai.agents.critic_agent import CriticReport, CriticStatus

from backend.app.ai.agents.validator_agent import ValidationReport, ValidationStatus, FactualViolation





@pytest.fixture

def base_candidate() -> CandidateProfile:

    """Returns a basic candidate profile."""

    return CandidateProfile(

        full_name="Alice Smith",

        skills=["Python"],

        professional_summary="Backend developer.",

        experience=[

            ExperienceItem(

                company="Tech Corp",

                role="Dev",

                start_date="2020",

                end_date="2022",

                description="Designed Python APIs."

            )

        ],

        education=[

            EducationItem(institution="State Uni", degree="BS")

        ]

    )





@pytest.fixture

def base_job() -> JobProfile:

    """Returns a basic job profile."""

    metadata = JobParserMetadata(parsed_at="2026-08-06T12:00:00Z", character_count=100)

    return JobProfile(

        company_name="Acme Systems",

        job_title="Developer",

        experience_required="3 years",

        education_required="BS",

        required_skills=["Python", "FastAPI"],

        preferred_skills=[],

        original_jd="Wants Python and FastAPI.",

        source_type="text",

        metadata=metadata

    )





def test_loop_exits_early_if_no_gaps(base_candidate, base_job):

    """Verify that loop controller exits immediately if no gaps are identified."""

    # Ensure candidate already has all skills

    candidate = base_candidate.model_copy(update={"skills": ["Python", "FastAPI"]})

    controller = OptimizationLoopController()



    # Mock Matcher returns to prevent external agent calculation overhead

    with patch.object(controller.matcher, "match") as mock_match:

        mock_match.return_value.overall_match_score = 95.0



        response = controller.optimize(candidate, base_job)



        assert response.status == OptimizationRunStatus.SUCCESS

        assert response.initial_score == 95.0

        assert len(response.history.iterations) == 0  # Zero iterations executed





def test_loop_runs_successfully_and_reaches_target_score(base_candidate, base_job):

    """Verify loop runs, improves score, and terminates when score exceeds target_score."""

    controller = OptimizationLoopController()



    with patch.object(controller.matcher, "match") as mock_match:

        # Mock initial match = 70.0; iteration 1 match = 92.5

        mock_match.side_effect = [

            MagicMock(overall_match_score=70.0), # baseline

            MagicMock(overall_match_score=92.5)  # iteration 1 post

        ]



        response = controller.optimize(base_candidate, base_job, target_score=90.0)



        assert response.status == OptimizationRunStatus.SUCCESS

        assert response.initial_score == 70.0

        assert response.final_score == 92.5

        assert len(response.history.iterations) == 1

        assert response.history.iterations[0].decision == OptimizationDecision.ACCEPTED

        assert not response.history.iterations[0].is_rolled_back





def test_loop_handles_validation_failures_and_rollback(base_candidate, base_job):

    """Verify that iteration is discarded (rolled back) if validation fails."""

    controller = OptimizationLoopController()



    with (
    patch.object(controller.matcher, "match") as mock_match,
    patch.object(controller.validator, "validate") as mock_validate,
):
        mock_match.return_value.overall_match_score = 75.0

        # Mock validation fail

        mock_validate.return_value = ValidationReport(

            status=ValidationStatus.FAILED,

            factual_violations=[

                FactualViolation(

                    field="experience",

                    description="Fabricated company name",

                    original_reference="Old Corp",

                    tailored_reference="New Corp"

                )

            ]

        )



        response = controller.optimize(base_candidate, base_job)



        # Iteration 1 fails validation -> rolled back. Since validation failed, loop continues.

        # Repeated validation failures limit is 3. After 3 consecutive fails, loop aborts.

        assert response.status == OptimizationRunStatus.FAILED

        assert len(response.history.iterations) == 3

        assert all(it.decision == OptimizationDecision.FAILED_VALIDATION for it in response.history.iterations)

        assert all(it.is_rolled_back for it in response.history.iterations)





def test_loop_stagnation_rollback_and_convergence_stop(base_candidate, base_job):

    """Verify that loop controller rolls back if score decreases/stagnates, and exits on convergence."""

    controller = OptimizationLoopController()



    with patch.object(controller.matcher, "match") as mock_match:

        # baseline = 70.0; iteration 1 post = 70.0 (stagnated)

        mock_match.side_effect = [

            MagicMock(overall_match_score=70.0), # baseline

            MagicMock(overall_match_score=70.0)  # iteration 1 post

        ]



        response = controller.optimize(base_candidate, base_job)



        assert response.status == OptimizationRunStatus.SUCCESS

        assert response.final_score == 70.0

        assert len(response.history.iterations) == 1

        assert response.history.iterations[0].decision == OptimizationDecision.REJECTED

        assert response.history.iterations[0].is_rolled_back





def test_loop_exception_handling_resilience(base_candidate, base_job):

    """Verify loop is resilient to exceptions inside sub-agents (e.g. Rewrite Agent)."""

    controller = OptimizationLoopController()


    with (
        patch.object(controller.matcher, "match") as mock_match,
        patch.object(controller.rewriter, "rewrite") as mock_rewrite,
    ):



        mock_match.return_value.overall_match_score = 70.0

        # Force rewriter to raise exception

        mock_rewrite.side_effect = Exception("OpenAI API rate limit")



        response = controller.optimize(base_candidate, base_job)



        # Continues loop and logs error per iteration, exits when max_iterations reached

        assert response.status == OptimizationRunStatus.SUCCESS

        assert len(response.history.iterations) == 5

        assert all(it.decision == OptimizationDecision.REJECTED for it in response.history.iterations)

        assert all(it.is_rolled_back for it in response.history.iterations)

        assert "Rewrite failure" in response.history.iterations[0].critic_feedback[0]
