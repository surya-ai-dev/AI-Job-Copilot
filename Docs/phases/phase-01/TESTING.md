# Phase 1 — Testing Reference

### 1. Test Files
*   `backend/tests/test_candidate_profile_extractor.py`: Extraction rules.
*   `backend/tests/test_candidate_profile.py`: Profile model schemas check.

### 2. Unit Tests
*   `test_candidate_profile_extractor`: Verifies extraction of skills, names, and contact credentials from raw input resume text.
*   `test_candidate_profile_attributes`: Validates schema parsing rules.

### 3. Verification Commands
Run target tests using:
```bash
.venv/Scripts/python -m pytest backend/tests/test_candidate_profile_extractor.py -v
```
