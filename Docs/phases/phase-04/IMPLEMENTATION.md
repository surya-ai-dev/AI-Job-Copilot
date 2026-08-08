# Phase 4 — Implementation Details

### 1. Directory Structure
*   `backend/app/ai/services/candidate_profile_storage_service.py`: Service logic.
*   `backend/app/ai/repository/candidate_profile_repository.py`: CRUD queries.
*   `backend/app/ai/models/candidate_profile_model.py`: Model schema.

### 2. Classes
*   `CandidateProfileStorageService`: Runs version status updates.
*   `CandidateProfileRepository`: Executes queries.

### 3. Repositories
*   `CandidateProfileRepository` (encapsulating select/update statements).

### 4. Models
*   `CandidateProfileModel` (table: `candidate_profiles`).

### 5. Endpoints
*   `POST /api/v1/resume/version`
*   `GET /api/v1/resume/versions`

### 6. Important Implementation Details
*   **Active/Inactive Lifecycle**: When a new master profile is activated, the service runs a transactional query setting `is_active = False` on all other profiles matching that `user_id`.
*   **Deterministic Retrieval**: Candidate profile listings are sorted using `.order_by(CandidateProfileModel.created_at.desc(), CandidateProfileModel.id.desc())` to ensure stable result order during parallel/asynchronous test executions.
