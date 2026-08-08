# Phase 3 — Implementation Details

### 1. Directory Structure
*   `backend/app/ai/agents/job_parser.py`: Parser agent.
*   `backend/app/jobs/services/job_service.py`: Job service.
*   `backend/app/jobs/services/analysis_service.py`: Analysis service.
*   `backend/app/jobs/models/job_model.py`: Database job model.
*   `backend/app/jobs/models/analysis_model.py`: Database analysis model.

### 2. Classes
*   `JobParserAgent`: Parses job posting texts.

### 3. Services
*   `JobService`: Ingests and lists jobs.
*   `JobAnalysisService`: Triggers baseline requirement checks.

### 4. Repositories
*   `JobRepository` & `AnalysisRepository`: DB mapping helpers.

### 5. Models
*   `JobModel` (table: `jobs`), `JobAnalysisModel` (table: `job_analyses`).

### 6. Schemas
*   `JobSchema`, `AnalysisSchema` (Pydantic validation schemas).

### 7. Endpoints
*   `POST /api/v1/jobs/ingest`
*   `GET /api/v1/jobs/{id}`
*   `POST /api/v1/jobs/analysis/analyze`
*   `GET /api/v1/jobs/analysis/{id}`

### 8. Important Implementation Details
*   Extracts required/preferred skills, seniority metrics, responsibilities lists, and parses commas/semicolons inline.
