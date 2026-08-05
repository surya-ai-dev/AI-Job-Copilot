# LangGraph Workflow Orchestration Module

This module coordinates the complete, stateful end-to-end job ingestion, analysis, resume tailoring, and email drafting pipeline.

---

## 1. Stateful Pipeline Sequence

The sequence diagram below shows how the orchestrator guides state transitions across modules:

```mermaid
sequenceDiagram
    autonumber
    actor User as Job Seeker
    participant API as FastAPI Router
    participant Orch as JobApplicationOrchestrator
    participant Job as JobService
    participant AI as JobAnalysisService
    participant Opt as ResumeOptimizationService
    participant Email as EmailOutreachService

    User->>API: POST /application/apply (job_input)
    API->>Orch: execute_pipeline(user_id, job_input)
    
    Note over Orch: Step 1: Parse Input
    Orch->>Job: ingest_job_from_text(...)
    Job-->>Orch: JobModel (job_id)
    
    Note over Orch: Step 2: Extract requirements
    Orch->>AI: analyze_job(...)
    AI-->>Orch: JobAnalysisModel (analysis_id)
    
    Note over Orch: Step 3: Match & Tailor Resume
    Orch->>Opt: optimize_resume(...)
    Opt-->>Orch: ResumeOptimizationModel (opt_id)
    
    Note over Orch: Step 4: Draft Outreach Email
    Orch->>Email: generate_outreach_email(...)
    Email-->>Orch: EmailDraftModel (draft_id)
    
    Orch-->>API: WorkflowState (SUCCESS)
    API-->>User: Editable email workspace redirect
```

---

## 2. Shared Workflow State Layout

```python
class WorkflowState:
    user_id: uuid.UUID
    job_input: str
    job_id: Optional[uuid.UUID]
    analysis_id: Optional[uuid.UUID]
    optimization_id: Optional[uuid.UUID]
    draft_id: Optional[uuid.UUID]
    
    current_step: str # JOB_PARSING, AI_UNDERSTANDING, RESUME_OPTIMIZATION, EMAIL_GENERATION, REVIEW
    error_state: Optional[str]
    retry_count: int
    status: str # PENDING, SUCCESS, FAILED
```

---

## 3. Failure Recovery & Event Flow

*   **Retry Mechanism**: Node transitions are protected by try-catch retry loops (maximum of 3 retries). If a transient failure occurs (such as an LLM timeout), the orchestrator waits and re-runs the step.
*   **Domain Event Broadcasting**: Upon the successful completion of each step, the orchestrator triggers events (e.g., `JobParsed`, `ResumeOptimized`, `EmailGenerated`) allowing observers (like dashboard notifications) to update state asynchronously.
