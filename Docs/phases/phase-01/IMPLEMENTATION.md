# Phase 1 — Implementation Details

### 1. Directory Structure
*   `backend/app/ai/agents/candidate_profile_extractor.py`: Extraction logic.
*   `backend/app/ai/models/candidate_profile_model.py`: Database profile model.

### 2. Classes
*   `CandidateProfileExtractor`: Orchestrates LLM prompt execution.

### 3. Services
*   `CandidateProfileService`: Standardizes profile loads and structural verification.

### 4. Repositories
*   `CandidateProfileRepository`: CRUD database wrappers for profiles.

### 5. Models
*   `CandidateProfileModel` (table: `candidate_profiles`).

### 6. Schemas
*   `CandidateProfile` (Pydantic model representing structured resume profile attributes).

### 7. Endpoints
*   Ingested via `POST /api/v1/resume/upload` route handler.

### 8. Important Implementation Details
*   Extracts dynamic fields such as name, contact information, skills taxonomy, parsed work experience list, project details, and certifications.
