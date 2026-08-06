"""Candidate Profile Repository for managing candidate profile database operations."""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.ai.models.candidate_profile_model import CandidateProfileModel
from backend.app.ai.schemas.candidate_profile_schema import CandidateProfile

class CandidateProfileRepository:
    """Encapsulates database access operations for candidate profiles using SQLAlchemy ORM."""

    def __init__(self, db: AsyncSession):
        """Initializes the repository with an AsyncSession database transaction reference.

        Args:
            db (AsyncSession): Active async SQLAlchemy database session.
        """
        self.db = db

    async def create_profile(
        self, user_id: uuid.UUID, resume_id: uuid.UUID, profile: CandidateProfile, is_active: bool = True
    ) -> CandidateProfileModel:
        """Saves a new Candidate Profile model inside database persistence.

        Args:
            user_id (uuid.UUID): ID of the user.
            resume_id (uuid.UUID): ID of the parsed resume file.
            profile (CandidateProfile): Structured candidate profile domain schema.
            is_active (bool, optional): Initial active flag. Defaults to True.

        Returns:
            CandidateProfileModel: Persistence model representing the created record.
        """
        # Serialize Pydantic structured schemas into JSON collections
        skills_json = [skill for skill in profile.skills]
        experience_json = [exp.model_dump() for exp in profile.experience]
        projects_json = [proj.model_dump() for proj in profile.projects]
        education_json = [edu.model_dump() for edu in profile.education]
        certifications_json = [cert for cert in profile.certifications]

        db_profile = CandidateProfileModel(
            id=uuid.uuid4(),
            user_id=user_id,
            resume_id=resume_id,
            full_name=profile.full_name,
            email=profile.email,
            phone=profile.phone,
            linkedin_url=profile.linkedin_url,
            github_url=profile.github_url,
            professional_summary=profile.professional_summary,
            skills_json=skills_json,
            experience_json=experience_json,
            projects_json=projects_json,
            education_json=education_json,
            certifications_json=certifications_json,
            is_active=is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(db_profile)
        await self.db.flush()
        return db_profile

    async def get_active_profile(self, user_id: uuid.UUID) -> Optional[CandidateProfileModel]:
        """Fetches the current active Candidate Profile for a user.

        Args:
            user_id (uuid.UUID): ID of the user.

        Returns:
            Optional[CandidateProfileModel]: The active profile model, if found.
        """
        result = await self.db.execute(
            select(CandidateProfileModel).where(
                CandidateProfileModel.user_id == user_id,
                CandidateProfileModel.is_active == True
            )
        )
        return result.scalars().first()

    async def get_profile_by_user(self, user_id: uuid.UUID) -> Optional[CandidateProfileModel]:
        """Fetches the latest profile record (active or inactive) created for a user.

        Args:
            user_id (uuid.UUID): ID of the user.

        Returns:
            Optional[CandidateProfileModel]: The latest profile model, if found.
        """
        result = await self.db.execute(
            select(CandidateProfileModel)
            .where(CandidateProfileModel.user_id == user_id)
            .order_by(CandidateProfileModel.created_at.desc())
        )
        return result.scalars().first()

    async def deactivate_active_profile(self, user_id: uuid.UUID) -> None:
        """Deactivates any active candidate profile records for the user.

        Args:
            user_id (uuid.UUID): ID of the user.
        """
        result = await self.db.execute(
            select(CandidateProfileModel).where(
                CandidateProfileModel.user_id == user_id,
                CandidateProfileModel.is_active == True
            )
        )
        active_profiles = result.scalars().all()
        for profile in active_profiles:
            profile.is_active = False
            profile.updated_at = datetime.utcnow()
        await self.db.flush()

    async def replace_profile(
        self, active_profile: CandidateProfileModel, new_profile: CandidateProfileModel
    ) -> None:
        """Swaps active status flags between an old profile and a new profile record.

        Args:
            active_profile (CandidateProfileModel): Old active profile.
            new_profile (CandidateProfileModel): Newly active profile.
        """
        active_profile.is_active = False
        active_profile.updated_at = datetime.utcnow()
        new_profile.is_active = True
        new_profile.updated_at = datetime.utcnow()
        await self.db.flush()

    async def delete_profile(self, profile_id: uuid.UUID) -> bool:
        """Removes a Candidate Profile database record.

        Args:
            profile_id (uuid.UUID): ID of the profile record to delete.

        Returns:
            bool: True if profile existed and was deleted, False otherwise.
        """
        result = await self.db.execute(
            select(CandidateProfileModel).where(CandidateProfileModel.id == profile_id)
        )
        db_profile = result.scalars().first()
        if db_profile:
            await self.db.delete(db_profile)
            await self.db.flush()
            return True
        return False

    async def list_profile_versions(self, user_id: uuid.UUID) -> List[CandidateProfileModel]:
        """Lists all parsed Candidate Profile versions (active and inactive) for a user.

        Args:
            user_id (uuid.UUID): ID of the user.

        Returns:
            List[CandidateProfileModel]: Collection of candidate profile records.
        """
        result = await self.db.execute(
            select(CandidateProfileModel)
            .where(CandidateProfileModel.user_id == user_id)
            .order_by(CandidateProfileModel.created_at.desc())
        )
        return result.scalars().all()
