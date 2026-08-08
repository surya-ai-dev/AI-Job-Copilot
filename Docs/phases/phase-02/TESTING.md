# Phase 2 — Testing Reference

### 1. Test Files
*   `backend/tests/test_resume_parser.py`: Parser validations.
*   `backend/tests/test_resume.py`: Resume models upload tests.

### 2. Unit Tests
*   `test_resume_parser_pdf`: Verifies pdf extraction using pdfplumber.
*   `test_resume_parser_docx`: Verifies docx extraction using python-docx.
*   `test_resume_upload_size_limit`: Asserts payload errors for files over 10MB.

### 3. Verification Commands
Run target tests using:
```bash
.venv/Scripts/python -m pytest backend/tests/test_resume_parser.py -v
```
