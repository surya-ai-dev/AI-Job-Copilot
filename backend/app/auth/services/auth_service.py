# backend/app/auth/services/auth_service.py
# Application Service Layer orchestrating authentication use cases and transactions

from datetime import datetime, timedelta
from typing import Tuple
from backend.app.auth.repository.user_repository import UserRepository
from backend.app.auth.domain.user import User, UserProfile
from backend.app.auth.domain.token import Token
from backend.app.auth.models.user_model import UserModel
from backend.app.core import security
from backend.app.shared.exceptions import AuthenticationException, NotFoundException

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(self, user_reg: User) -> UserModel:
        """Orchestrate new user registration."""
        # 1. Check if user already exists
        existing_user = await self.user_repo.get_by_email(user_reg.email)
        if existing_user:
            raise AuthenticationException(
                f"Account with email {user_reg.email} already registered.", 
                "USER_ALREADY_EXISTS"
            )

        # 3. Create user in database (password is already hashed)
        return await self.user_repo.create(user_reg)

    async def login_user(self, email: str, plain_pw: str) -> Tuple[str, str]:
        """Authenticate user credentials and return access & refresh tokens."""
        # 1. Fetch user by email
        db_user = await self.user_repo.get_by_email(email)
        if not db_user:
            raise AuthenticationException("Invalid email or password.", "INVALID_CREDENTIALS")

        # 2. Verify password hash
        if not security.verify_password(plain_pw, db_user.hashed_password):
            raise AuthenticationException("Invalid email or password.", "INVALID_CREDENTIALS")

        # 3. Create tokens
        access_token = security.create_access_token(subject=db_user.email)
        refresh_token = security.create_refresh_token(subject=db_user.email)

        # 4. Save refresh token in database (expires after 7 days)
        expires_at = datetime.utcnow() + timedelta(days=7)
        await self.user_repo.save_refresh_token(
            token=refresh_token, 
            user_id=db_user.id, 
            expires_at=expires_at
        )

        return access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> str:
        """Verify refresh token and return a new access token."""
        # 1. Verify token signature and expiration
        email = security.verify_token(refresh_token, token_type="refresh")

        # 2. Check token in database
        db_token = await self.user_repo.get_refresh_token(refresh_token)
        if not db_token or db_token.is_revoked or db_token.expires_at < datetime.utcnow():
            raise AuthenticationException("Token is revoked or expired.", "INVALID_TOKEN")

        # 3. Generate new access token
        new_access_token = security.create_access_token(subject=email)
        return new_access_token

    async def logout_user(self, refresh_token: str) -> None:
        """Revoke refresh token to logout user."""
        db_token = await self.user_repo.get_refresh_token(refresh_token)
        if db_token:
            await self.user_repo.revoke_refresh_token(db_token)

    async def get_current_user(self, token: str) -> UserModel:
        """Decode access token and fetch user entity."""
        email = security.verify_token(token, token_type="access")
        db_user = await self.user_repo.get_by_email(email)
        if not db_user:
            raise NotFoundException("User account not found.", "USER_NOT_FOUND")
        return db_user

    async def update_user_profile(self, db_user: UserModel, profile_update: UserProfile) -> UserModel:
        """Update active user profile data."""
        # Map user model parameters to domain User for validation check
        domain_user = User(
            email=db_user.email,
            hashed_password=db_user.hashed_password,
            first_name=profile_update.first_name,
            last_name=profile_update.last_name
        )
        
        db_user.first_name = domain_user.first_name
        db_user.last_name = domain_user.last_name
        
        return await self.user_repo.update(db_user)
