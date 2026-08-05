# backend/app/resume/services/resume_service.py
# Application Service Layer orchestrating file uploads, validation, & version tracking

import os
import shutil
import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from backend.app.resume.repository.resume_repository import ResumeRepository
from backend.app.resume.domain.resume import Resume, ResumeVersion, ResumeMetadata
from backend.app.resume.models.resume_model import ResumeModel, ResumeVersionModel
from backend.app.shared.exceptions import ValidationException, NotFoundException, BusinessRuleException

# Max file size limit: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024
SUPPORTED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx"
}

class ResumeService:
    def __init__(self, resume_repo: ResumeRepository, storage_path: str = "/storage"):
        self.resume_repo = resume_repo
        self.storage_path = storage_path
        
        # Ensure base storage directory exists on disk
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path, exist_ok=True)

    async def upload_master_resume(
        self, 
        user_id: uuid.UUID, 
        file_name: str, 
        file_size: int, 
        content_type: str, 
        file_content: bytes
    ) -> ResumeModel:
        """Upload and store user master resume."""
        # 1. Validate file parameters
        self._validate_file_constraints(file_name, file_size, content_type)

        # 2. Check active master resume constraint
        active_resume = await self.resume_repo.get_active_by_user(user_id)
        if active_resume:
            raise BusinessRuleException(
                "An active master resume already exists. Use the replace endpoint to upload a new one.",
                "ACTIVE_RESUME_EXISTS"
            )

        # 3. Generate secure unique file name
        ext = SUPPORTED_MIME_TYPES[content_type]
        unique_file_name = f"{user_id}_{int(datetime.utcnow().timestamp())}_master.{ext}"
        target_file_path = os.path.join(self.storage_path, unique_file_name)

        # 4. Save file to disk
        await self._write_file_to_disk(target_file_path, file_content)

        # 5. Extract metadata details (mocks for initial parsing phase)
        mock_skills = ["Python", "FastAPI", "PostgreSQL", "REST APIs"]
        metadata = ResumeMetadata(
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
            parsed_skills=mock_skills,
            parsed_experience_years=5
        )

        domain_resume = Resume(
            user_id=user_id,
            file_path=target_file_path,
            metadata=metadata,
            status="active"
        )

        return await self.resume_repo.create_resume(domain_resume)

    async def replace_master_resume(
        self,
        user_id: uuid.UUID,
        file_name: str,
        file_size: int,
        content_type: str,
        file_content: bytes
    ) -> ResumeModel:
        """Replace existing master resume, marking the old one as replaced."""
        # 1. Validate file parameters
        self._validate_file_constraints(file_name, file_size, content_type)

        # 2. Fetch existing active resume
        active_resume = await self.resume_repo.get_active_by_user(user_id)
        if not active_resume:
            raise NotFoundException("No active master resume found to replace.", "RESUME_NOT_FOUND")

        # 3. Mark old resume as replaced in DB
        await self.resume_repo.update_status(active_resume, "replaced")

        # 4. Upload new resume
        return await self.upload_master_resume(user_id, file_name, file_size, content_type, file_content)

    async def download_master_resume(self, user_id: uuid.UUID) -> Tuple[str, str, str]:
        """Fetch file path and parameters for downloads. Returns (filepath, filename, mime-type)."""
        active_resume = await self.resume_repo.get_active_by_user(user_id)
        if not active_resume or not os.path.exists(active_resume.file_path):
            raise NotFoundException("Active master resume file not found.", "RESUME_NOT_FOUND")

        return active_resume.file_path, active_resume.file_name, active_resume.content_type

    async def delete_master_resume(self, user_id: uuid.UUID) -> None:
        """Soft-deletes master resume from DB and deletes physical file from disk."""
        active_resume = await self.resume_repo.get_active_by_user(user_id)
        if not active_resume:
            raise NotFoundException("No active master resume found to delete.", "RESUME_NOT_FOUND")

        # Update status to deleted in DB
        await self.resume_repo.update_status(active_resume, "deleted")

        # Delete physical file from storage
        if os.path.exists(active_resume.file_path):
            try:
                os.remove(active_resume.file_path)
            except OSError as e:
                # Log physical delete error but proceed since DB is marked deleted
                print(f"Failed to delete physical file {active_resume.file_path}: {e}")

    async def get_resume_details(self, user_id: uuid.UUID) -> ResumeModel:
        """Retrieve master resume metadata."""
        active_resume = await self.resume_repo.get_active_by_user(user_id)
        if not active_resume:
            raise NotFoundException("No active master resume found.", "RESUME_NOT_FOUND")
        return active_resume

    async def create_resume_version_metadata(
        self,
        user_id: uuid.UUID,
        company: str,
        role: str
    ) -> ResumeVersionModel:
        """Generate version tracking metadata for a tailored resume."""
        active_resume = await self.resume_repo.get_active_by_user(user_id)
        if not active_resume:
            raise NotFoundException("Cannot version profile. Upload master resume first.", "RESUME_NOT_FOUND")

        # Increment version number
        latest_version = await self.resume_repo.get_latest_version_number(user_id)
        next_version = latest_version + 1

        # Naming convention for versions: [user_id]_version_[num].[ext]
        ext = SUPPORTED_MIME_TYPES[active_resume.content_type]
        version_file_name = f"{user_id}_version_{next_version}.{ext}"
        version_file_path = os.path.join(self.storage_path, version_file_name)

        # Mock compile output: Copy master resume file on disk
        if os.path.exists(active_resume.file_path):
            shutil.copy2(active_resume.file_path, version_file_path)

        domain_version = ResumeVersion(
            resume_id=active_resume.id,
            user_id=user_id,
            version_number=next_version,
            file_path=version_file_path,
            optimized_for_company=company,
            optimized_for_role=role
        )

        return await self.resume_repo.create_version(domain_version)

    async def list_resume_versions(self, user_id: uuid.UUID) -> List[ResumeVersionModel]:
        """List all tailored resume versions."""
        return await self.resume_repo.list_versions(user_id)

    # Helper Validations
    def _validate_file_constraints(self, file_name: str, file_size: int, content_type: str) -> None:
        """Validate files against format, size and emptiness constraints."""
        if not file_name:
            raise ValidationException("File upload name cannot be empty.")
            
        if file_size <= 0:
            raise ValidationException("Cannot upload empty files.", [{"field": "file", "error": "File size is 0"}])
            
        if file_size > MAX_FILE_SIZE:
            raise ValidationException(
                "File size exceeds maximum limit of 10MB.", 
                [{"field": "file", "error": "File is too large"}]
            )
            
        if content_type not in SUPPORTED_MIME_TYPES:
            raise ValidationException(
                "Unsupported file type. Only PDF and DOCX formats are allowed.",
                [{"field": "file", "error": "Invalid format"}]
            )

    async def _write_file_to_disk(self, target_path: str, content: bytes) -> None:
        """Write raw binary payloads to storage volume on disk."""
        try:
            with open(target_path, "wb") as f:
                f.write(content)
        except IOError as e:
            raise BusinessRuleException(f"Disk write operations failed: {e}", "DISK_WRITE_ERROR")
