"""Unit tests for Resume Optimizer Schemas."""

import pytest
from pydantic import ValidationError
from backend.app.ai.schemas.resume_optimizer_schema import (
    OptimizationRunStatus,
    OptimizationDecision,
    OptimizationDiff,
    OptimizationIteration,
    OptimizationHistory,
    ResumeOptimizationRequest,
    ResumeOptimizationResponse
)


def test_optimization_run_status_enum():
    """Verify OptimizationRunStatus enum values."""
    assert OptimizationRunStatus.RUNNING == "RUNNING"
    assert OptimizationRunStatus.SUCCESS == "SUCCESS"
    assert OptimizationRunStatus.FAILED == "FAILED"
    assert OptimizationRunStatus.STOPPED == "STOPPED"


def test_optimization_decision_enum():
    """Verify OptimizationDecision enum values."""
    assert OptimizationDecision.ACCEPTED == "ACCEPTED"
    assert OptimizationDecision.REJECTED == "REJECTED"
    assert OptimizationDecision.FAILED_VALIDATION == "FAILED_VALIDATION"


def test_resume_optimization_request_validation():
    """Verify ResumeOptimizationRequest validation rules."""
    # Valid request
    req = ResumeOptimizationRequest(
        candidate_profile_id=1,
        job_profile_id=2,
        tone="Professional",
        focus_skills=["Python", "FastAPI"]
    )
    assert req.candidate_profile_id == 1
    assert req.job_profile_id == 2
    assert req.tone == "Professional"
    assert req.focus_skills == ["Python", "FastAPI"]

    # Invalid candidate_profile_id (<= 0)
    with pytest.raises(ValidationError) as exc_info:
        ResumeOptimizationRequest(
            candidate_profile_id=0,
            job_profile_id=2
        )
    assert "ID must be greater than 0" in str(exc_info.value)

    # Invalid job_profile_id (<= 0)
    with pytest.raises(ValidationError) as exc_info:
        ResumeOptimizationRequest(
            candidate_profile_id=1,
            job_profile_id=-5
        )
    assert "ID must be greater than 0" in str(exc_info.value)


def test_optimization_diff_schema():
    """Verify OptimizationDiff basic structure."""
    diff = OptimizationDiff(
        section_name="summary",
        original_text="Old summary",
        optimized_text="New summary",
        rationale="More action verbs"
    )
    assert diff.section_name == "summary"
    assert diff.original_text == "Old summary"
    assert diff.optimized_text == "New summary"
    assert diff.rationale == "More action verbs"


def test_optimization_iteration_validation():
    """Verify OptimizationIteration validation rules."""
    # Valid iteration
    iter_obj = OptimizationIteration(
        iteration_number=3,
        pre_score=75.5,
        post_score=82.0,
        planning_tasks=["Highlight FastAPI"],
        critic_feedback=["Reads well"],
        validation_errors=[],
        decision=OptimizationDecision.ACCEPTED,
        is_rolled_back=False
    )
    assert iter_obj.iteration_number == 3
    assert iter_obj.pre_score == 75.5
    assert iter_obj.post_score == 82.0

    # Invalid iteration_number (< 1)
    with pytest.raises(ValidationError) as exc_info:
        iter_obj.model_copy(update={"iteration_number": 0})
    assert "Iteration number must be between 1 and 5" in str(exc_info.value)

    # Invalid iteration_number (> 5)
    with pytest.raises(ValidationError) as exc_info:
        iter_obj.model_copy(update={"iteration_number": 6})
    assert "Iteration number must be between 1 and 5" in str(exc_info.value)

    # Invalid pre_score (< 0)
    with pytest.raises(ValidationError) as exc_info:
        iter_obj.model_copy(update={"pre_score": -1.0})
    assert "Score must be between 0.0 and 100.0" in str(exc_info.value)

    # Invalid post_score (> 100)
    with pytest.raises(ValidationError) as exc_info:
        iter_obj.model_copy(update={"post_score": 105.0})
    assert "Score must be between 0.0 and 100.0" in str(exc_info.value)


def test_optimization_history_validation():
    """Verify OptimizationHistory validation rules."""
    iteration = OptimizationIteration(
        iteration_number=1,
        pre_score=70.0,
        post_score=75.0,
        planning_tasks=[],
        critic_feedback=[],
        validation_errors=[],
        decision=OptimizationDecision.ACCEPTED
    )

    history = OptimizationHistory(
        run_id="run-123",
        initial_score=70.0,
        final_score=75.0,
        total_iterations=1,
        status=OptimizationRunStatus.SUCCESS,
        iterations=[iteration],
        created_at="2026-08-06T12:00:00Z"
    )
    assert history.run_id == "run-123"
    assert history.initial_score == 70.0
    assert history.final_score == 75.0

    # Invalid initial_score (< 0)
    with pytest.raises(ValidationError) as exc_info:
        history.model_copy(update={"initial_score": -5.0})
    assert "Score must be between 0.0 and 100.0" in str(exc_info.value)

    # Invalid final_score (> 100)
    with pytest.raises(ValidationError) as exc_info:
        history.model_copy(update={"final_score": 101.5})
    assert "Score must be between 0.0 and 100.0" in str(exc_info.value)


def test_resume_optimization_response_validation():
    """Verify ResumeOptimizationResponse validation rules."""
    iteration = OptimizationIteration(
        iteration_number=1,
        pre_score=70.0,
        post_score=75.0,
        planning_tasks=[],
        critic_feedback=[],
        validation_errors=[],
        decision=OptimizationDecision.ACCEPTED
    )

    history = OptimizationHistory(
        run_id="run-123",
        initial_score=70.0,
        final_score=75.0,
        total_iterations=1,
        status=OptimizationRunStatus.SUCCESS,
        iterations=[iteration],
        created_at="2026-08-06T12:00:00Z"
    )

    diff = OptimizationDiff(
        section_name="skills",
        original_text="old",
        optimized_text="new"
    )

    res = ResumeOptimizationResponse(
        run_id="run-123",
        candidate_profile_id=1,
        job_profile_id=2,
        status=OptimizationRunStatus.SUCCESS,
        initial_score=70.0,
        final_score=75.0,
        score_improvement=5.0,
        changes=[diff],
        history=history
    )
    assert res.run_id == "run-123"
    assert res.score_improvement == 5.0

    # Invalid initial_score (> 100)
    with pytest.raises(ValidationError) as exc_info:
        res.model_copy(update={"initial_score": 150.0})
    assert "Score must be between 0.0 and 100.0" in str(exc_info.value)
