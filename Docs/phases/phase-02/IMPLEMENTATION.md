# Phase 2 — Implementation Details

### 1. Directory Structure
*   `backend/app/ai/agents/resume_parser.py`: Ingestion agent.
*   `backend/app/ai/services/resume_parser_service.py`: Coordinator service.
*   `backend/app/resume/models/resume_model.py`: Database resume model.

### 2. Classes
*   `ResumeParserAgent`: Matches binary streams and parses text.

### 3. Services
*   `ResumeParserService`: Handles validations and file storage logic.

### 4. Repositories
*   `ResumeRepository`: DB mapping helper.

### 5. Models
*   `ResumeModel` (table: `resumes`).

### 6. Schemas
*   `ResumeSchema` (Pydantic model validating file metadata).

### 7. Endpoints
*   `POST /api/v1/resume/upload`
*   `GET /api/v1/resume/download`
*   `DELETE /api/v1/resume`

### 8. Important Implementation Details
*   Enforces file size constraints (max 10MB) and content type validations (`application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`).
