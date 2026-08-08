# Phase 5 — Implementation Details

### 1. Directory Structure
*   `backend/app/ai/agents/resume_matcher.py`: Matcher agent.
*   `backend/app/ai/services/resume_matcher_service.py`: Matcher service.

### 2. Classes
*   `ResumeMatcherAgent`: Executes prompt-based semantic comparison checks.

### 3. Services
*   `ResumeMatcherService`: Computes overall scores.

### 4. Important Implementation Details
*   **Scoring Weights**: Mapped via structured LLM prompt returns. Matches required skills, preferred skills, experience limits, education compliance, and certification requirements.
*   Generates lists of strengths, weaknesses, and keyword gap highlights.
