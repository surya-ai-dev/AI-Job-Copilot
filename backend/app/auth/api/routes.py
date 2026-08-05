# backend/app/auth/api/routes.py
# FastAPI routes exposing endpoints for authentication and user profile management

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.session import get_async_db
from backend.app.auth.repository.user_repository import UserRepository
from backend.app.auth.services.auth_service import AuthService
from backend.app.auth.domain.user import User, UserProfile
from backend.app.core import security
from backend.app.auth.schemas.auth_schema import (
    UserRegister, 
    TokenSchema, 
    TokenRefreshRequest, 
    UserResponse, 
    UserUpdate
)
from backend.app.shared.exceptions import BaseAppException, AuthenticationException

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_router = APIRouter(prefix="/users", tags=["Users"])

# OAuth2 schema configuration to support Swagger/OpenAPI token logins
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_active_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_async_db)
) -> UserResponse:
    """Dependency resolver verifying active JWT access tokens and loading user profile."""
    repo = UserRepository(db)
    service = AuthService(repo)
    try:
        db_user = await service.get_current_user(token)
        return db_user
    except BaseAppException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_async_db)):
    """Register a new user account."""
    repo = UserRepository(db)
    service = AuthService(repo)
    try:
        # 1. Hash plain password first
        hashed_password = security.get_password_hash(payload.password)
        
        # 2. Create domain User with hashed password
        domain_user = User(
            email=payload.email,
            hashed_password=hashed_password,
            first_name=payload.first_name,
            last_name=payload.last_name
        )
        return await service.register_user(domain_user)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post("/token", response_model=TokenSchema)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_async_db)
):
    """OAuth2 compatible token login endpoint."""
    repo = UserRepository(db)
    service = AuthService(repo)
    try:
        access_token, refresh_token = await service.login_user(
            email=form_data.username,
            plain_pw=form_data.password
        )
        return TokenSchema(access_token=access_token, refresh_token=refresh_token)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)


@router.post("/refresh", response_model=TokenSchema)
async def refresh_token(payload: TokenRefreshRequest, db: AsyncSession = Depends(get_async_db)):
    """Refresh access token using a refresh token."""
    repo = UserRepository(db)
    service = AuthService(repo)
    try:
        new_access_token = await service.refresh_access_token(payload.refresh_token)
        return TokenSchema(access_token=new_access_token, refresh_token=payload.refresh_token)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(payload: TokenRefreshRequest, db: AsyncSession = Depends(get_async_db)):
    """Revoke refresh token to logout user."""
    repo = UserRepository(db)
    service = AuthService(repo)
    await service.logout_user(payload.refresh_token)
    return {"message": "Logged out successfully."}


@user_router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_active_user)):
    """Retrieve details for current authenticated user."""
    return current_user


@user_router.put("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update active user profile data."""
    repo = UserRepository(db)
    service = AuthService(repo)
    try:
        domain_profile = UserProfile(
            first_name=payload.first_name,
            last_name=payload.last_name
        )
        return await service.update_user_profile(current_user, domain_profile)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
