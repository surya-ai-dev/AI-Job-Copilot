# backend/tests/shared/test_orchestrator.py
# Unit tests verifying the end-to-end pipeline orchestrator workflow

import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from backend.app.shared.orchestrator import JobApplicationOrchestrator

@pytest.mark.asyncio
async def test_execute_pipeline_success():
    # Arrange: Mock all service components
    mock_job_svc = MagicMock()
    mock_job_svc.ingest_job_from_text = AsyncMock(
        return_value=MagicMock(id=uuid.uuid4(), company_name="Google", job_title="Engineer", recruiter_email="recruiter@google.com")
    )
    
    mock_analysis_svc = MagicMock()
    mock_analysis_svc.analyze_job = AsyncMock(
        return_value=MagicMock(id=uuid.uuid4())
    )
    
    mock_opt_svc = MagicMock()
    mock_opt_svc.optimize_resume = AsyncMock(
        return_value=MagicMock(id=uuid.uuid4(), match_score=95, optimized_file_path="/mock/storage/path.pdf")
    )
    
    mock_email_svc = MagicMock()
    mock_email_svc.generate_outreach_email = AsyncMock(
        return_value=MagicMock(id=uuid.uuid4(), recipient_email="recruiter@google.com")
    )
    
    mock_app_svc = MagicMock()

    orchestrator = JobApplicationOrchestrator(
        job_service=mock_job_svc,
        analysis_service=mock_analysis_svc,
        opt_service=mock_opt_svc,
        email_service=mock_email_svc,
        app_service=mock_app_svc
    )

    user_id = uuid.uuid4()
    job_input = "Need Python developer at Google"

    # Act
    state = await orchestrator.execute_pipeline(user_id, job_input)

    # Assert
    assert state.status == "SUCCESS"
    assert state.job_id is not None
    assert state.analysis_id is not None
    assert state.optimization_id is not None
    assert state.draft_id is not None
    assert state.retry_count == 0
    assert state.error_state is None


@pytest.mark.asyncio
async def test_execute_pipeline_no_contact():
    # Arrange: Mock all service components
    mock_job_svc = MagicMock()
    mock_job_svc.ingest_job_from_text = AsyncMock(
        return_value=MagicMock(id=uuid.uuid4(), company_name="Google", job_title="Engineer", recruiter_email=None)
    )

    mock_analysis_svc = MagicMock()
    mock_analysis_svc.analyze_job = AsyncMock(
        return_value=MagicMock(id=uuid.uuid4())
    )

    mock_opt_svc = MagicMock()
    mock_opt_svc.optimize_resume = AsyncMock(
        return_value=MagicMock(id=uuid.uuid4(), match_score=95, optimized_file_path="/mock/storage/path.pdf")
    )

    mock_email_svc = MagicMock()
    mock_email_svc.generate_outreach_email = AsyncMock()

    mock_app_svc = MagicMock()

    orchestrator = JobApplicationOrchestrator(
        job_service=mock_job_svc,
        analysis_service=mock_analysis_svc,
        opt_service=mock_opt_svc,
        email_service=mock_email_svc,
        app_service=mock_app_svc
    )

    user_id = uuid.uuid4()
    job_input = "Need Python developer at Google"

    # Act
    state = await orchestrator.execute_pipeline(user_id, job_input)

    # Assert
    assert state.status == "SUCCESS"
    assert state.job_id is not None
    assert state.analysis_id is not None
    assert state.optimization_id is not None
    assert state.draft_id is None
    assert state.current_step == "NO_EMAIL_WORKFLOW_STOPPED"
    mock_email_svc.generate_outreach_email.assert_not_called()
