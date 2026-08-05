# Application Management & Dashboard Module

This module serves as the central hub of the candidate workspace, presenting aggregate dashboard widgets, tracking job applications logs, and exposing search utilities.

---

## 1. Dashboard Ingestion & Logging Workflow

The diagram below shows how applications are logged, details queried, and summaries loaded:

```mermaid
sequenceDiagram
    autonumber
    actor User as Job Seeker
    participant API as FastAPI Router
    participant Svc as ApplicationService
    participant Repo as ApplicationRepository
    participant DB as PostgreSQL DB

    Note over User, DB: 1. Logging Application Event
    User->>API: POST /dashboard/applications (payload)
    API->>Svc: log_new_application(user_id, job_id, resume_opt_id)
    Svc->>Svc: Verify references exist
    Svc->>Repo: create_application(app_model)
    Repo->>DB: Save application row
    DB-->>Repo: Saved row details
    Svc-->>API: JobApplicationResponse
    API-->>User: Registered application log

    Note over User, DB: 2. Querying Dashboard Widgets Stats
    User->>API: GET /dashboard/summary
    API->>Svc: get_dashboard_statistics(user_id)
    Svc->>Repo: get_summary_stats(user_id)
    Repo-->>Svc: total_count, today_count
    Svc->>Svc: Compile count of tailored resumes & drafts
    Svc-->>API: DashboardStatsResponse
    API-->>User: Rendered Dashboard Widgets & Activity lists
```

---

## 2. API Endpoint Specification

*   `GET /api/v1/dashboard/summary`: Retrieve aggregate counters and recent applications details.
*   `POST /api/v1/dashboard/applications`: Log a new job application event.
*   `GET /api/v1/dashboard/applications`: List all application logs.
*   `GET /api/v1/dashboard/applications/search`: Search and filter logged applications.
*   `GET /api/v1/dashboard/applications/{id}`: Retrieve details for a specific logged application by ID.
*   `DELETE /api/v1/dashboard/applications/{id}`: Delete an application log from database tables.

---

## 3. Design Decisions & Trade-offs

*   **Loose Coupling via Relational IDs**: The `applications` table stores UUID references to other entities (resumes, jobs, email histories) rather than duplicating job descriptions or email bodies. This ensures references stay consistent when updates occur elsewhere.
*   **Search Optimization Index**: The `company_name` and `job_title` columns have database indexes to keep search queries fast as the application log history grows.
*   **Encapsulated Stats Calculations**: Statistics queries are handled at the service layer to keep repository code focused on clean CRUD operations.
