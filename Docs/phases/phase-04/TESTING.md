# Phase 4 — Testing Reference

### 1. Test Files
*   `backend/tests/test_candidate_profile_storage.py`: Storage service unit tests.
*   `backend/tests/test_candidate_profile_storage_integration.py`: DB transaction tests.

### 2. Unit & Integration Tests
*   `test_deactivate_previous_profiles`: Verifies status deactivation switches.
*   `test_get_active_profile_deterministic`: Verifies sorting priorities.

### 3. Verification Commands
Run target tests using:
```bash
.venv/Scripts/python -m pytest backend/tests/test_candidate_profile_storage.py -v
```
