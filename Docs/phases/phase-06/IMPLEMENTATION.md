# Phase 6 — Implementation Details

### 1. Directory Structure
*   `backend/app/ai/agents/planner_agent.py`: Planning focus task lists.
*   `backend/app/ai/agents/rewrite_agent.py`: Content rewriter.
*   `backend/app/ai/agents/critic_agent.py`: Style critic.
*   `backend/app/ai/agents/validator_agent.py`: Factual compliance validator.
*   `backend/app/ai/services/optimization_loop.py`: Iteration loop controller.
*   `backend/app/ai/services/resume_optimizer_service.py`: Top-level optimizer entry.
*   `backend/app/ai/models/optimization_model.py`: SQLAlchemy run history entities.
*   `backend/app/ai/repository/optimization_repository.py`: CRUD operations.

### 2. Classes
*   `OptimizationLoopController`: Manages loop execution flow.
*   `PlannerAgent`, `ResumeRewriteAgent`, `CriticAgent`, `ResumeValidatorAgent`: Core NLP agents.

### 3. Services
*   `ResumeOptimizerService`: Entry-point orchestrator.

### 4. Repositories
*   `OptimizationRepository` (CRUD maps for runs, iterations, history).

### 5. Models
*   `OptimizationRunModel` (table: `optimization_runs`).
*   `OptimizationIterationModel` (table: `optimization_iterations`).
*   `OptimizationHistoryModel` (table: `optimization_history`).

### 6. Endpoints
*   `POST /api/v1/resume/optimize`
*   `GET /api/v1/resume/optimization/{id}`
*   `GET /api/v1/resume/history/{candidate}`
*   `GET /api/v1/resume/best/{candidate}`
*   `DELETE /api/v1/resume/optimization/{id}`

### 7. Important Implementation Details
*   **Cascade Deletion Behavior**: Standard SQLite relationships cascade deletes to child records:
    ```python
    iterations = relationship("OptimizationIterationModel", back_populates="run", cascade="all, delete-orphan")
    history = relationship("OptimizationHistoryModel", back_populates="run", cascade="all, delete-orphan")
    ```
    Purges iteration checkpoints automatically upon deleting the parent run.
*   **Status Transitions**: Optimization runs transition states from `PENDING` $\rightarrow$ `RUNNING` $\rightarrow$ `SUCCESS` / `FAILED`, saving completion scores.
