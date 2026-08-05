# backend/app/resume/api/routes.py
# FastAPI routes exposing endpoints for master resume upload, download, replacement & versions tracking

import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.app.database.session import get_async_db
from backend.app.auth.api.routes import get_current_active_user
from backend.app.auth.schemas.auth_schema import UserResponse
from backend.app.resume.repository.resume_repository import ResumeRepository
from backend.app.resume.services.resume_service import ResumeService
from backend.app.resume.schemas.resume_schema import (
    ResumeResponse, 
    ResumeVersionResponse, 
    VersionMetadataCreate
)
from backend.app.shared.exceptions import BaseAppException

router = APIRouter(prefix="/resume", tags=["Resume Management"])

def get_resume_service(db: AsyncSession = Depends(get_async_db)) -> ResumeService:
    """Dependency resolver returning initialized ResumeService instance."""
    repo = ResumeRepository(db)
    # Target storage volume folder
    storage_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage")
    return ResumeService(repo, storage_path=storage_path)

# Importing os for file path resolutions inside getter dependency
import os


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_master(
    file: UploadFile = File(..., description="PDF or DOCX resume document file"),
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
    service: ResumeService = Depends(get_resume_service)
):
    """Upload master resume template."""
    try:
        content = await file.read()
        return await service.upload_master_resume(
            user_id=current_user.id,
            file_name=file.filename,
            file_size=len(content),
            content_type=file.content_type,
            file_content=content
        )
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get("", response_model=ResumeResponse)
async def get_details(
    current_user: UserResponse = Depends(get_current_active_user),
    service: ResumeService = Depends(get_resume_service)
):
    """Retrieve details for current active master resume."""
    try:
        return await service.get_resume_details(current_user.id)
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get("/download")
async def download_master(
    current_user: UserResponse = Depends(get_current_active_user),
    service: ResumeService = Depends(get_resume_service)
):
    """Download current active master resume file."""
    try:
        file_path, file_name, content_type = await service.download_master_resume(current_user.id)
        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type=content_type
        )
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.put("/replace", response_model=ResumeResponse)
async def replace_master(
    file: UploadFile = File(..., description="Replacement PDF or DOCX resume document file"),
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
    service: ResumeService = Depends(get_resume_service)
):
    """Replace active master resume with a new file."""
    try:
        content = await file.read()
        return await service.replace_master_resume(
            user_id=current_user.id,
            file_name=file.filename,
            file_size=len(content),
            content_type=file.content_type,
            file_content=content
        )
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.delete("", status_code=status.HTTP_200_OK)
async def delete_master(
    current_user: UserResponse = Depends(get_current_active_user),
    service: ResumeService = Depends(get_resume_service)
):
    """Soft-delete active master resume and clear storage files."""
    try:
        await service.delete_master_resume(current_user.id)
        return {"message": "Master resume deleted successfully."}
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get("/versions", response_model=List[ResumeVersionResponse])
async def list_versions(
    current_user: UserResponse = Depends(get_current_active_user),
    service: ResumeService = Depends(get_resume_service)
):
    """List all tailored resume versions metadata logs."""
    return await service.list_resume_versions(current_user.id)


@router.post("/versions", response_model=ResumeVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version_metadata(
    payload: VersionMetadataCreate,
    current_user: UserResponse = Depends(get_current_active_user),
    service: ResumeService = Depends(get_resume_service)
):
    """Generate version tracking metadata for a tailored resume (mock pipeline trigger)."""
    try:
        return await service.create_resume_version_metadata(
            user_id=current_user.id,
            company=payload.optimized_for_company,
            role=payload.optimized_for_role
        )
    except BaseAppException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
