# Phase 3 — Testing Reference

### 1. Test Files
*   `backend/tests/test_job_parser.py`: Ingestion agent tests.
*   `backend/tests/test_job_analysis.py`: Gap analysis tests.
*   `backend/tests/test_jobs.py`: Integration route tests.

### 2. Unit Tests
*   `test_job_parser_extraction`: Asserts correct structural parsing of job title, requirements, and keywords.
*   `test_job_analysis_generation`: Verifies experience deficit calculations.

### 3. Verification Commands
Run target tests using:
```bash
.venv/Scripts/python -m pytest backend/tests/test_job_parser.py -v
```
