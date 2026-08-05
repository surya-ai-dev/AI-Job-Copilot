# backend/app/auth/repository/user_repository.py
# Database access operations encapsulating SQLAlchemy transactions with UUID & soft-delete validations

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from typing import Optional
from backend.app.auth.models.user_model import UserModel, RefreshTokenModel
from backend.app.auth.domain.user import User

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> UserModel:
        """Create new database User record."""
        db_user = UserModel(
            id=user.id or uuid.uuid4(),
            email=user.email,
            hashed_password=user.hashed_password,
            first_name=user.first_name,
            last_name=user.last_name,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_deleted=False
        )
        self.db.add(db_user)
        await self.db.flush() # Populate ID
        return db_user

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """Fetch user record by email lookup (soft-delete aware)."""
        result = await self.db.execute(
            select(UserModel).where(UserModel.email == email, UserModel.is_deleted == False)
        )
        return result.scalars().first()

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[UserModel]:
        """Fetch user record by database UUID (soft-delete aware)."""
        result = await self.db.execute(
            select(UserModel).where(UserModel.id == user_id, UserModel.is_deleted == False)
        )
        return result.scalars().first()

    async def update(self, db_user: UserModel) -> UserModel:
        """Commit modified user records."""
        db_user.updated_at = datetime.utcnow()
        await self.db.flush()
        return db_user

    async def delete(self, db_user: UserModel, soft_delete: bool = True) -> None:
        """Soft-deletes or physically deletes user record."""
        if soft_delete:
            db_user.is_deleted = True
            db_user.updated_at = datetime.utcnow()
        else:
            await self.db.delete(db_user)
        await self.db.flush()

    async def save_refresh_token(self, token: str, user_id: uuid.UUID, expires_at: datetime) -> RefreshTokenModel:
        """Save refresh token record."""
        db_token = RefreshTokenModel(
            id=uuid.uuid4(),
            token=token,
            user_id=user_id,
            expires_at=expires_at,
            is_revoked=False
        )
        self.db.add(db_token)
        await self.db.flush()
        return db_token

    async def get_refresh_token(self, token: str) -> Optional[RefreshTokenModel]:
        """Retrieve token database entry."""
        result = await self.db.execute(select(RefreshTokenModel).where(RefreshTokenModel.token == token))
        return result.scalars().first()

    async def revoke_refresh_token(self, db_token: RefreshTokenModel) -> None:
        """Mark refresh token as revoked."""
        db_token.is_revoked = True
        await self.db.flush()
window_size = 500
