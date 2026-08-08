# Phase 6 — Testing Reference

### 1. Test Files
*   `backend/tests/test_phase6_e2e.py`: E2E integration test paths.
*   `backend/tests/ai/test_optimization_loop.py`: Loop control tests.
*   `backend/tests/ai/test_optimization_repository.py`: CRUD validations.
*   `backend/tests/ai/test_planner_agent.py`, `test_rewrite_agent.py`, `test_critic_agent.py`, `test_validator_agent.py`: Specialized agent tests.
*   `backend/tests/ai/test_resume_optimizer_api.py`: Endpoint routing tests.

### 2. Unit & Integration Tests
*   `test_optimize_endpoint_success`: Validates E2E run flow.
*   `test_delete_optimization_cascade`: Validates cascade orphan purges.
*   `test_optimizer_rollback_on_deterioration`: Checks rollback logic.

### 3. Verification Commands
Run target tests using:
```bash
.venv/Scripts/python -m pytest backend/tests/test_phase6_e2e.py -v
```
To run the full suite:
```bash
.venv/Scripts/python -m pytest backend/tests/ai/ -v
```
