# Email Outreach & Gmail Integration Module

This module manages drafting recruiter outreach messages based on job details and tailored resumes, updates drafts, processes Google OAuth credentials, and delivers emails securely via the Gmail API.

---

## 1. OAuth & Outreach Delivery Sequence

The sequence diagram below shows the OAuth callbacks, email updates, and secure sending processes:

```mermaid
sequenceDiagram
    autonumber
    actor User as Job Seeker
    participant API as FastAPI Router
    participant Svc as EmailOutreachService
    participant Gmail as Google Gmail API
    participant Repo as EmailRepository
    participant DB as PostgreSQL DB

    Note over User, Gmail: 1. Gmail Authorization
    User->>API: GET /email/oauth/status
    API->>Svc: get_gmail_connection_status(user_id)
    Svc->>Repo: get_gmail_token(user_id)
    Repo->>DB: Query token
    DB-->>Repo: GmailTokenModel
    Svc-->>API: Connection Status (connected: true/false)
    
    alt Status is Connected
        Note over User, Gmail: 2. Generating & Sending Outreach
        User->>API: POST /email/generate (job_id, resume_opt_id)
        API->>Svc: generate_outreach_email(...)
        Svc->>Repo: create_draft(draft)
        Repo->>DB: Save draft
        Svc-->>API: EmailDraft details
        API-->>User: Editable email workspace
        
        User->>API: POST /email/send (draft_id)
        API->>Svc: send_outreach_email(user_id, draft_id)
        Svc->>Repo: get_gmail_token(user_id)
        Repo-->>Svc: OAuth Tokens
        Svc->>Gmail: Send MIME email message (with resume attachment)
        Gmail-->>Svc: Sent delivery confirmation
        Svc->>Repo: create_history(history)
        Repo->>DB: Log transaction status (sent)
        Svc->>Repo: delete_draft(draft_id)
        Repo->>DB: Clear draft
        Svc-->>API: Sent history details
        API-->>User: Success Notification
    else Status is Disconnected
        User->>API: Trigger Gmail OAuth authentication flow
        API-->>Gmail: Redirect to Google authorization scopes page
        Gmail-->>User: OAuth callback redirect (with tokens)
        User->>API: POST /email/oauth/callback (tokens)
        API->>Svc: save_gmail_oauth_callback(...)
        Svc->>Repo: save_gmail_token(...)
        Repo->>DB: Save tokens
        Svc-->>API: OAuth Success
    end
```

---

## 2. API Endpoint Specification

*   `POST /api/v1/email/generate`: Generate outreach draft text.
*   `PUT /api/v1/email/draft/{id}`: Update active draft details in the workspace.
*   `POST /api/v1/email/send`: Deliver the outreach email via the Gmail API (requires explicit user confirmation).
*   `GET /api/v1/email/drafts`: List active drafts.
*   `DELETE /api/v1/email/draft/{id}`: Delete an email draft.
*   `GET /api/v1/email/history`: List sent email history logs.
*   `GET /api/v1/email/oauth/status`: Check Gmail connection status.
*   `POST /api/v1/email/oauth/callback`: Save Google OAuth tokens.

---

## 3. Design Decisions & Trade-offs

*   **Explicit User Approval**: The system is strictly prohibited from sending emails automatically. Every message must be reviewed, edited, and approved by the user in the workspace before sending.
*   **Gmail API vs. Standard SMTP**: The system uses the Google Gmail API instead of SMTP. This allows the application to manage refresh tokens securely and send emails directly from the user's personal Gmail account.
*   **Encrypted Token Storage**: OAuth access and refresh tokens are encrypted before storage to protect Gmail session credentials.
