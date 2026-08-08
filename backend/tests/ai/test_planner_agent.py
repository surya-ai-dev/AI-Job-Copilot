"""Unit tests for the Planner Agent."""

import pytest
from pydantic import ValidationError
from backend.app.ai.agents.planner_agent import (
    GapAnalysis,
    OptimizationTask,
    OptimizationPlan,
    PlannerAgent
)


def test_gap_analysis_validation():
    """Verify validation constraints on GapAnalysis."""
    # Valid
    g = GapAnalysis(
        missing_required_skills=["Python"],
        missing_preferred_skills=["Docker"],
        experience_years_deficit=2.5,
        education_mismatch="Missing MS"
    )
    assert g.experience_years_deficit == 2.5

    # Invalid negative experience years deficit
    with pytest.raises(ValidationError) as exc_info:
        GapAnalysis(experience_years_deficit=-1.0)
    assert "Experience years deficit cannot be negative" in str(exc_info.value)


def test_optimization_task_validation():
    """Verify validation constraints on OptimizationTask."""
    # Valid
    t = OptimizationTask(
        priority=1,
        target_section="skills",
        action="Add Python",
        rationale="Missing skill"
    )
    assert t.target_section == "skills"

    # Invalid target_section
    with pytest.raises(ValidationError) as exc_info:
        OptimizationTask(
            priority=1,
            target_section="invalid_section",
            action="Do something",
            rationale="Why"
        )
    assert "target_section must be one of" in str(exc_info.value)


def test_planner_agent_prioritization():
    """Verify that PlannerAgent prioritizes tasks correctly and limits plan to at most 3 tasks."""
    agent = PlannerAgent()

    # Case A: Heavy required skills gap (many missing required skills)
    gaps_heavy = GapAnalysis(
        missing_required_skills=["A", "B", "C", "D"],
        missing_preferred_skills=["E"],
        experience_years_deficit=2.0,
        education_mismatch="Major mismatch"
    )
    plan_heavy = agent.generate_plan(gaps_heavy)

    # Must be capped at exactly 3 tasks
    assert len(plan_heavy.tasks) == 3
    # All 3 tasks must target the required skills "A", "B", "C" because they have the highest priority
    assert plan_heavy.tasks[0].target_section == "skills"
    assert "core required skill 'A'" in plan_heavy.tasks[0].action
    assert plan_heavy.tasks[1].target_section == "skills"
    assert "core required skill 'B'" in plan_heavy.tasks[1].action
    assert plan_heavy.tasks[2].target_section == "skills"
    assert "core required skill 'C'" in plan_heavy.tasks[2].action


def test_planner_agent_mixed_prioritization():
    """Verify mixed prioritization when fewer than 3 required skills are missing."""
    agent = PlannerAgent()

    # Case B: 1 required skill, 1 experience gap, 1 preferred skill, 1 education mismatch
    gaps_mixed = GapAnalysis(
        missing_required_skills=["Python"],
        missing_preferred_skills=["Docker"],
        experience_years_deficit=1.5,
        education_mismatch="Missing CS degree"
    )
    plan_mixed = agent.generate_plan(gaps_mixed)

    # Must be capped at exactly 3 tasks
    assert len(plan_mixed.tasks) == 3

    # Task 1: Required skill (Python)
    assert plan_mixed.tasks[0].priority == 1
    assert plan_mixed.tasks[0].target_section == "skills"
    assert "core required skill 'Python'" in plan_mixed.tasks[0].action

    # Task 2: Experience deficit
    assert plan_mixed.tasks[1].priority == 2
    assert plan_mixed.tasks[1].target_section == "summary"
    assert "1.5-year experience deficit" in plan_mixed.tasks[1].action

    # Task 3: Preferred skill (Docker)
    assert plan_mixed.tasks[2].priority == 3
    assert plan_mixed.tasks[2].target_section == "skills"
    assert "nice-to-have preferred skill 'Docker'" in plan_mixed.tasks[2].action


def test_planner_agent_no_required_skills():
    """Verify prioritization order when there are no missing required skills."""
    agent = PlannerAgent()

    gaps = GapAnalysis(
        missing_required_skills=[],
        missing_preferred_skills=["Docker"],
        experience_years_deficit=0.0,
        education_mismatch="Missing BS"
    )
    plan = agent.generate_plan(gaps)

    assert len(plan.tasks) == 2
    # Task 1: Preferred skill (Docker)
    assert plan.tasks[0].target_section == "skills"
    assert "nice-to-have preferred skill 'Docker'" in plan.tasks[0].action
    # Task 2: Education mismatch
    assert plan.tasks[1].target_section == "summary"
    assert "Missing BS" in plan.tasks[1].action
