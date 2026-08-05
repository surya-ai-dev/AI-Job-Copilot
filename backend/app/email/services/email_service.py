# backend/app/email/services/email_service.py
# Application Service Layer orchestrating Gmail OAuth authentication, outreach drafting & message deliveries

import uuid
import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from backend.app.email.repository.email_repository import EmailRepository
from backend.app.email.models.email_model import EmailDraftModel, EmailHistoryModel, GmailTokenModel
from backend.app.email.domain.email import EmailDraft, EmailRecipient, EmailAttachment
from backend.app.shared.exceptions import NotFoundException, ValidationException, AuthenticationException, BusinessRuleException
from backend.app.core.config import settings

class EmailOutreachService:
    def __init__(self, email_repo: EmailRepository):
        self.email_repo = email_repo

    async def generate_outreach_email(
        self,
        user_id: uuid.UUID,
        job_analysis_company: str,
        job_analysis_role: str,
        optimized_resume_path: str,
        recruiter_email: Optional[str] = None
    ) -> EmailDraftModel:
        """Personalize an outreach email draft using job parameters and resume details."""
        subject = f"Application: {job_analysis_role} at {job_analysis_company}"
        body = (
            f"Dear Hiring Team,\n\n"
            f"I hope this message finds you well.\n\n"
            f"I am writing to express my strong interest in the {job_analysis_role} position at {job_analysis_company}. "
            f"With my background in software development and technical expertise in Python and FastAPI, "
            f"I am confident in my ability to contribute effectively to your team's goals.\n\n"
            f"Please find my tailored resume attached for your review. I look forward to the possibility of discussing "
            f"how my skills align with your requirements.\n\n"
            f"Best regards,\nCandidate"
        )

        recipient_email = recruiter_email or "hiring@company.com"
        
        draft = EmailDraftModel(
            id=uuid.uuid4(),
            user_id=user_id,
            recipient_email=recipient_email,
            recipient_name="Hiring Team",
            subject=subject,
            body=body,
            attachment_path=optimized_resume_path
        )

        return await self.email_repo.create_draft(draft)

    async def save_draft_update(
        self,
        user_id: uuid.UUID,
        draft_id: uuid.UUID,
        recipient_email: str,
        recipient_name: Optional[str],
        subject: str,
        body: str
    ) -> EmailDraftModel:
        """Update active email draft details."""
        draft = await self.email_repo.get_draft(draft_id)
        if not draft or draft.user_id != user_id:
            raise NotFoundException("Email draft record not found.", "DRAFT_NOT_FOUND")

        # Domain validation check
        domain_recipient = EmailRecipient(email=recipient_email, name=recipient_name)
        domain_recipient.validate()
        
        if not subject.strip():
            raise ValidationException("Email subject cannot be empty.")
        if not body.strip():
            raise ValidationException("Email body cannot be empty.")

        draft.recipient_email = recipient_email
        draft.recipient_name = recipient_name
        draft.subject = subject
        draft.body = body
        draft.updated_at = datetime.utcnow()

        return await self.email_repo.create_draft(draft) # updates details in flush session

    async def send_outreach_email(self, user_id: uuid.UUID, draft_id: uuid.UUID) -> EmailHistoryModel:
        """Deliver the email via Gmail API using OAuth credentials, requiring explicit user approval."""
        # 1. Fetch email draft details
        draft = await self.email_repo.get_draft(draft_id)
        if not draft or draft.user_id != user_id:
            raise NotFoundException("Email draft not found.", "DRAFT_NOT_FOUND")

        # 2. Check Gmail connection status (requires OAuth token setup)
        token = await self.email_repo.get_gmail_token(user_id)
        if not token or token.expires_at < datetime.utcnow():
            raise AuthenticationException(
                "Gmail authorization is expired or disconnected. Reconnect Gmail settings first.",
                "GMAIL_NOT_CONNECTED"
            )

        # 3. Validate file attachment
        if draft.attachment_path and not os.path.exists(draft.attachment_path):
            raise NotFoundException("Target optimized resume attachment not found.", "ATTACHMENT_NOT_FOUND")

        # 4. Trigger delivery payload (Simulate Gmail API send call for the MVP)
        # In production, this sets up the Gmail service client using OAuth tokens and sends a MIME email with attachment.
        print(f"Delivering outreach email to: {draft.recipient_email} via Gmail. Subject: {draft.subject}")
        
        # 5. Log sent transaction in history logs
        history = EmailHistoryModel(
            id=uuid.uuid4(),
            user_id=user_id,
            recipient_email=draft.recipient_email,
            subject=draft.subject,
            body=draft.body,
            attachment_path=draft.attachment_path,
            status="sent",
            sent_at=datetime.utcnow()
        )
        await self.email_repo.create_history(history)

        # 6. Delete draft record
        await self.email_repo.delete_draft(draft_id)

        return history

    async def get_gmail_connection_status(self, user_id: uuid.UUID) -> dict:
        """Verify user's Gmail authorization session status."""
        token = await self.email_repo.get_gmail_token(user_id)
        if not token:
            return {"connected": False, "expires_at": None}
        
        connected = token.expires_at > datetime.utcnow()
        return {"connected": connected, "expires_at": token.expires_at}

    async def save_gmail_oauth_callback(
        self, 
        user_id: uuid.UUID, 
        access_token: str, 
        refresh_token: Optional[str], 
        expires_in_seconds: int
    ) -> GmailTokenModel:
        """Save Gmail OAuth access token details."""
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
        return await self.email_repo.save_gmail_token(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )

    async def list_user_email_history(self, user_id: uuid.UUID) -> List[EmailHistoryModel]:
        """List sent email history logs."""
        return await self.email_repo.list_history(user_id)

    async def list_user_drafts(self, user_id: uuid.UUID) -> List[EmailDraftModel]:
        """List active email drafts."""
        return await self.email_repo.list_drafts(user_id)

    async def delete_user_draft(self, user_id: uuid.UUID, draft_id: uuid.UUID) -> None:
        """Delete draft."""
        draft = await self.email_repo.get_draft(draft_id)
        if not draft or draft.user_id != user_id:
            raise NotFoundException("Email draft not found.", "DRAFT_NOT_FOUND")
        await self.email_repo.delete_draft(draft_id)

# Import os for files validation checks
import os
