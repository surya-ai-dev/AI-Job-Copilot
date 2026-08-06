"""Candidate Profile Storage Service coordinates transactional state swaps and updates."""

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.ai.models.candidate_profile_model import CandidateProfileModel
from backend.app.ai.repository.candidate_profile_repository import CandidateProfileRepository
from backend.app.ai.schemas.candidate_profile_schema import CandidateProfile

logger = logging.getLogger(__name__)

class CandidateProfileStorageService:
    """Service coordinates storage, status swaps, and commits of Candidate Profiles."""

    def __init__(self, db: AsyncSession, repository: CandidateProfileRepository = None):
        """Initializes the service with dependency-injected session and repository instances.

        Args:
            db (AsyncSession): Active async SQLAlchemy database session.
            repository (CandidateProfileRepository, optional): Profile repository to inject.
                Defaults to a new instance.
        """
        self.db = db
        self.repository = repository or CandidateProfileRepository(db)

    async def store_candidate_profile(
        self, user_id: uuid.UUID, resume_id: uuid.UUID, profile: CandidateProfile
    ) -> CandidateProfileModel:
        """Atomically deactivates any existing active profile and saves a new active profile.

        Args:
            user_id (uuid.UUID): ID of the user.
            resume_id (uuid.UUID): ID of the parsed resume file.
            profile (CandidateProfile): Structured candidate profile domain schema.

        Returns:
            CandidateProfileModel: The newly created active database record.

        Raises:
            Exception: Re-raises any exceptions encountered to trigger API errors.
        """
        logger.info(
            "Transaction start: Storing candidate profile for user: %s (resume source: %s)",
            user_id,
            resume_id
        )
        try:
            # 1. Deactivate existing active profile (Business Rule: Max 1 active profile per user)
            await self.repository.deactivate_active_profile(user_id)
            
            # 2. Persist the new active profile record
            db_profile = await self.repository.create_profile(
                user_id=user_id,
                resume_id=resume_id,
                profile=profile,
                is_active=True
            )
            
            # 3. Commit transaction
            await self.db.commit()
            logger.info("Successfully stored and committed new active profile: %s", db_profile.id)
            return db_profile
        except Exception as e:
            logger.error(
                "Failed to store candidate profile for user %s: %s. Rolling back transaction.",
                user_id,
                str(e),
                exc_info=True
            )
            await self.db.rollback()
            raise

    async def replace_candidate_profile(
        self, user_id: uuid.UUID, resume_id: uuid.UUID, profile: CandidateProfile
    ) -> CandidateProfileModel:
        """Transactional helper to replace the current active profile with a new one.

        Keeps parity with store_candidate_profile workflow to support replacement requests.

        Args:
            user_id (uuid.UUID): ID of the user.
            resume_id (uuid.UUID): ID of the parsed resume file.
            profile (CandidateProfile): Structured candidate profile domain schema.

        Returns:
            CandidateProfileModel: The newly created active database record.
        """
        logger.info(
            "Transaction start: Replacing candidate profile for user: %s (resume source: %s)",
            user_id,
            resume_id
        )
        try:
            # Deactivate previous profile
            await self.repository.deactivate_active_profile(user_id)
            
            # Persist new active profile
            db_profile = await self.repository.create_profile(
                user_id=user_id,
                resume_id=resume_id,
                profile=profile,
                is_active=True
            )
            
            # Commit transaction
            await self.db.commit()
            logger.info("Successfully replaced active profile: %s", db_profile.id)
            return db_profile
        except Exception as e:
            logger.error(
                "Failed to replace candidate profile for user %s: %s. Rolling back.",
                user_id,
                str(e),
                exc_info=True
            )
            await self.db.rollback()
            raise

    async def get_active_candidate_profile(self, user_id: uuid.UUID) -> Optional[CandidateProfileModel]:
        """Fetches the current active Candidate Profile for a user without modifying data.

        Args:
            user_id (uuid.UUID): ID of the user.

        Returns:
            Optional[CandidateProfileModel]: The active profile model, if found.
        """
        logger.info("Fetching active candidate profile for user: %s", user_id)
        return await self.repository.get_active_profile(user_id)

    async def delete_candidate_profile(self, profile_id: uuid.UUID) -> bool:
        """Removes a Candidate Profile database record in a transaction.

        Args:
            profile_id (uuid.UUID): ID of the profile record to delete.

        Returns:
            bool: True if profile existed and was deleted, False otherwise.
        """
        logger.info("Transaction start: Deleting candidate profile ID: %s", profile_id)
        try:
            deleted = await self.repository.delete_profile(profile_id)
            if deleted:
                await self.db.commit()
                logger.info("Successfully deleted and committed profile deletion: %s", profile_id)
            else:
                logger.warning("Profile ID %s not found for deletion.", profile_id)
            return deleted
        except Exception as e:
            logger.error(
                "Failed to delete candidate profile %s: %s. Rolling back transaction.",
                profile_id,
                str(e),
                exc_info=True
            )
            await self.db.rollback()
            raise
