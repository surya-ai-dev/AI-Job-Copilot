# Production Hardening, Performance & Security Report

This guide outlines security configurations, cache details, operational metrics thresholds, and troubleshooting procedures for the production deployment of the **AI Job Copilot** platform.

---

## 1. Security Hardening Configurations

*   **Security Headers Middleware**: public endpoints automatically attach production-grade protection headers:
    *   `X-Frame-Options: DENY` (prevents clickjacking attacks)
    *   `X-Content-Type-Options: nosniff` (prevents mime-sniffing exploits)
    *   `Strict-Transport-Security` (enforces encrypted HTTPS connections)
    *   `Content-Security-Policy` (mitigates cross-site scripting risks)
*   **Request Correlation ID**: Injected context headers allow tracing user transaction paths across asynchronous nodes and services logs.
*   **OAuth Credentials Privacy**: Recruiter Gmail OAuth tokens are stored in the database and filtered securely by the user's UUID scope.

---

## 2. Caching Strategy & Redis Expirations

The caching interface is structured to decrease database loads and API cost overhead:

| Cache Key | Target Content | Expiration Limit |
| :--- | :--- | :--- |
| `dash_summary:[user_id]` | Dashboard statistics summaries widgets | 10 Minutes |
| `job_analysis:[job_id]` | Extracted structured job requirements details | 24 Hours |
| `resume_opt:[opt_id]` | AI-generated tailored drafts suggestions | 1 Hour |

---

## 3. Monitoring & Health Probes Guide

The system exposes operational metrics via `GET /api/v1/health/metrics` providing CPU, memory, and disk utilization statistics.

### Target Performance Thresholds
*   **API Response Latency**: <= 200ms (p95) for ingestion and lists requests.
*   **Document Generation Time**: <= 3 seconds for optimized PDF conversions.
*   **Disk Usage Alert**: Trigger SRE warning notifications if disk usage exceeds 85%.

---

## 4. Troubleshooting & Operational Runbook

### Scenario A: Gmail API Token Expiration
1.  **Symptom**: User receives `GMAIL_NOT_CONNECTED` exception when sending outreach.
2.  **Resolution**: Guide the user to the outreach wizard workspace. The UI automatically displays the Gmail connection button when authorization is disconnected, allowing them to reconnect the Google OAuth flow.

### Scenario B: High Database Connection Pool Usage
1.  **Symptom**: API response times degrade, and logs display database checkout timeouts.
2.  **Resolution**: Scale up SQLAlchemy connection pool size limits via env variables:
    ```env
    POSTGRES_POOL_SIZE=30
    POSTGRES_MAX_OVERFLOW=10
    ```
