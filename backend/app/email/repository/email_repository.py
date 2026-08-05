# backend/app/email/repository/email_repository.py
# Database access operations encapsulating SQLAlchemy transactions for drafts, history & OAuth credentials

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from typing import Optional, List
from backend.app.email.models.email_model import EmailDraftModel, EmailHistoryModel, GmailTokenModel

class EmailRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_draft(self, draft: EmailDraftModel) -> EmailDraftModel:
        """Save a new email draft record."""
        self.db.add(draft)
        await self.db.flush()
        return draft

    async def get_draft(self, draft_id: uuid.UUID) -> Optional[EmailDraftModel]:
        """Fetch draft by ID."""
        result = await self.db.execute(select(EmailDraftModel).where(EmailDraftModel.id == draft_id))
        return result.scalars().first()

    async def list_drafts(self, user_id: uuid.UUID) -> List[EmailDraftModel]:
        """List all drafts for a user."""
        result = await self.db.execute(
            select(EmailDraftModel).where(EmailDraftModel.user_id == user_id).order_by(EmailDraftModel.updated_at.desc())
        )
        return result.scalars().all()

    async def delete_draft(self, draft_id: uuid.UUID) -> None:
        """Physically delete draft from logs."""
        result = await self.db.execute(select(EmailDraftModel).where(EmailDraftModel.id == draft_id))
        draft = result.scalars().first()
        if draft:
            await self.db.delete(draft)
            await self.db.flush()

    async def create_history(self, history: EmailHistoryModel) -> EmailHistoryModel:
        """Log sent email transaction in history table."""
        self.db.add(history)
        await self.db.flush()
        return history

    async def list_history(self, user_id: uuid.UUID) -> List[EmailHistoryModel]:
        """List sent emails history logs."""
        result = await self.db.execute(
            select(EmailHistoryModel).where(EmailHistoryModel.user_id == user_id).order_by(EmailHistoryModel.sent_at.desc())
        )
        return result.scalars().all()

    async def save_gmail_token(
        self, 
        user_id: uuid.UUID, 
        access_token: str, 
        refresh_token: Optional[str], 
        expires_at: datetime
    ) -> GmailTokenModel:
        """Save or update Gmail OAuth credentials for a user."""
        existing_token = await self.get_gmail_token(user_id)
        if existing_token:
            existing_token.access_token = access_token
            if refresh_token:
                existing_token.refresh_token = refresh_token
            existing_token.expires_at = expires_at
            await self.db.flush()
            return existing_token
        else:
            db_token = GmailTokenModel(
                id=uuid.uuid4(),
                user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at
            )
            self.db.add(db_token)
            await self.db.flush()
            return db_token

    async def get_gmail_token(self, user_id: uuid.UUID) -> Optional[GmailTokenModel]:
        """Fetch Gmail OAuth credentials."""
        result = await self.db.execute(select(GmailTokenModel).where(GmailTokenModel.user_id == user_id))
        return result.scalars().first()
