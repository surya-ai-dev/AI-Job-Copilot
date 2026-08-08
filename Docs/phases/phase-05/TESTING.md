# Phase 5 — Testing Reference

### 1. Test Files
*   `backend/tests/test_resume_matcher.py`: Matcher unit tests.
*   `backend/tests/test_resume_matcher_integration.py`: Integration tests.
*   `backend/tests/test_phase5_acceptance.py`: Acceptance index tests.

### 2. Unit & Integration Tests
*   `test_matcher_score_calculation`: Verifies overall math index bounds.
*   `test_matcher_gap_identification`: Asserts missing skills reports.

### 3. Verification Commands
Run target tests using:
```bash
.venv/Scripts/python -m pytest backend/tests/test_resume_matcher.py -v
```
