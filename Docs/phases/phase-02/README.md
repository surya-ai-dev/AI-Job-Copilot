# Phase 2 — Resume Parser

### 1. Objective
Handle stream-based binary file uploads to parse structured text out of physical PDF and DOCX files.

### 2. Problem
Users want to upload actual PDF/DOCX resumes instead of copy-pasting raw text, which requires robust backend stream extraction handling.

### 3. Solution
Integrate `pdfplumber` and `python-docx` file extraction libraries to parse raw text streams and feed them directly into the Candidate Intelligence Layer.

### 4. Main Components
*   `ResumeParserAgent`: Parsing agent extracting content from document streams.
*   `ResumeParserService`: Application service coordinating uploads and parsing steps.
*   `ResumeModel`: Database entity recording upload logs.

### 5. Data Flow
```mermaid
graph TD
    User[User / File] --> API[Upload API]
    API --> Service[ResumeParserService]
    Service --> Parser[ResumeParserAgent]
    Parser --> PDF[pdfplumber (PDF)]
    Parser --> DOCX[python-docx (Word)]
    PDF --> Data[Structured Resume Data]
    DOCX --> Data
    Data --> Persistence[ResumeModel Database Save]
```

### 6. APIs
*   `POST /api/v1/resume/upload` (stream parsing handler)
*   `GET /api/v1/resume/download`
*   `DELETE /api/v1/resume`

### 7. Database
*   Table: `resumes` (`ResumeModel`).

### 8. Testing
*   Test Files: `backend/tests/test_resume_parser.py`, `backend/tests/test_resume.py`.

### 9. Dependencies on Previous Phases
*   Depends on **Phase 1** to process the parsed text.

### 10. Output / Result
*   A saved `ResumeModel` database entry and structured text output.

### 11. Related Documentation
*   `Docs/specs/BACKEND.md`
