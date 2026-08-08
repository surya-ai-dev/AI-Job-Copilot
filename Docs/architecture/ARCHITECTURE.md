# JobCopilot AI — Current System Architecture

## AI Resume Optimization — End-to-End Data & Agent Flow

This document details the architectural design and structural layers implemented in the **JobCopilot AI** project, verified against the active classes, files, and relationships in the codebase.

```mermaid
graph TB
    subgraph ClientLayer ["1. USER / CLIENT LAYER (Blue)"]
        Client["Web / API Client (HTTP Requests)"]
    end

    subgraph ApiLayer ["2. API & SECURITY LAYER (Blue)"]
        Router["FastAPI Router: resume_optimizer.py (resume_optimizer_router) [NEW / PHASE 6]"]
        Auth["JWT Token Decode & Verification (auth.py)"]
        CurrentUser["get_current_active_user Dependency"]
        Client -->|POST /api/v1/resume/optimize| Router
        Router -->|Authenticate| Auth
        Auth -->|Authorize| CurrentUser
    end

    subgraph ServiceLayer ["3. SERVICE LAYER (Green)"]
        OptimizerService["ResumeOptimizerService [NEW / PHASE 6]"]
        ProfileStorage["CandidateProfileStorageService"]
        JobService["JobService & JobAnalysisService"]
        CurrentUser --> OptimizerService
    end

    subgraph AgentLayer ["4. AI / AGENT LAYER (Purple)"]
        LoopController["OptimizationLoopController [NEW / PHASE 6]"]
        Planner["PlannerAgent (Task List Planning) [NEW / PHASE 6]"]
        Rewriter["ResumeRewriteAgent (Factual Candidate Rewrites) [NEW / PHASE 6]"]
        Critic["CriticAgent (Formatting & Style Feedback) [NEW / PHASE 6]"]
        Validator["ResumeValidatorAgent (Compliance Check) [NEW / PHASE 6]"]
        Matcher["ResumeMatcherService (ATS Score Evaluation)"]

        OptimizerService -->|Triggers| LoopController
        LoopController -->|Plan Gaps| Planner
        Planner -->|Rewrite Sections| Rewriter
        Rewriter -->|Assess Quality| Critic
        Critic -->|Factual Audit| Validator
        Validator -->|Assign Score| Matcher
        Matcher -->|Iterate or Converge| LoopController
    end

    subgraph RepoLayer ["5. REPOSITORY LAYER (Gray)"]
        OptRepo["OptimizationRepository [NEW / PHASE 6]"]
        ProfileRepo["CandidateProfileRepository"]
        JobRepo["JobRepository & AnalysisRepository"]
        UserRepo["UserRepository"]

        OptimizerService --> OptRepo
        OptimizerService --> ProfileRepo
        JobService --> JobRepo
        Auth --> UserRepo
    end

    subgraph DbLayer ["6. DATA / PERSISTENCE LAYER (Orange)"]
        classDef dbClass fill:#FFD700,stroke:#FF8C00,stroke-width:2px;

        UserModel[("UserModel (users table)")]
        ProfileModel[("CandidateProfileModel (candidate_profiles)")]
        ResumeModel[("ResumeModel (resumes)")]
        JobModel[("JobModel (jobs)")]
        AnalysisModel[("JobAnalysisModel (job_analyses)")]
        RunModel[("OptimizationRunModel (runs) [NEW / PHASE 6]")]
        IterModel[("OptimizationIterationModel (iterations) [NEW / PHASE 6]")]
        HistoryModel[("OptimizationHistoryModel (histories) [NEW / PHASE 6]")]

        UserRepo --> UserModel
        ProfileRepo --> ProfileModel
        ProfileRepo --> ResumeModel
        JobRepo --> JobModel
        JobRepo --> AnalysisModel
        OptRepo --> RunModel
        OptRepo --> IterModel
        OptRepo --> HistoryModel
    end

    subgraph TestLayer ["7. TESTING LAYER (Gray)"]
        Pytest["Pytest Test Suite (269 Tests Passing)"]
        E2E["End-to-End Flow (test_phase6_e2e.py) [NEW / PHASE 6]"]
        UnitTests["Unit & API Tests (test_resume_optimizer_api.py, etc.)"]
        Pytest --> E2E
        Pytest --> UnitTests
    end

    %% Component Legend
    %% Blue = API / Client
    %% Green = Services
    %% Purple = AI / Agents
    %% Orange = Database
    %% Gray = Repository / Testing

    %% Styling
    style ClientLayer fill:#F0F8FF,stroke:#4682B4,stroke-width:2px;
    style ApiLayer fill:#F0F8FF,stroke:#4682B4,stroke-width:2px;
    style ServiceLayer fill:#F0FFF0,stroke:#2E8B57,stroke-width:2px;
    style AgentLayer fill:#E6E6FA,stroke:#8A2BE2,stroke-width:2px;
    style RepoLayer fill:#F5F5F5,stroke:#808080,stroke-width:2px;
    style DbLayer fill:#FFF5EE,stroke:#FF8C00,stroke-width:2px;
    style TestLayer fill:#FAFAFA,stroke:#A9A9A9,stroke-width:2px;
```
