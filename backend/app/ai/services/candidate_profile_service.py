"""Candidate Profile Service for coordinating candidate profile extraction logic."""

import logging
from backend.app.ai.agents.candidate_profile_extractor import CandidateProfileExtractorAgent
from backend.app.ai.schemas.candidate_profile_schema import CandidateProfile

logger = logging.getLogger(__name__)

class CandidateProfileService:
    """Service layer that coordinates the extraction of a structured candidate profile from raw resume text."""

    def __init__(self, extractor_agent: CandidateProfileExtractorAgent = None):
        """Initializes the service with a CandidateProfileExtractorAgent.

        Args:
            extractor_agent (CandidateProfileExtractorAgent, optional): Extractor agent to inject.
                Defaults to a new instance.
        """
        self.extractor_agent = extractor_agent or CandidateProfileExtractorAgent()

    def extract_profile(self, raw_text: str) -> CandidateProfile:
        """Extracts a structured CandidateProfile from raw resume text.

        Args:
            raw_text (str): Raw resume text block.

        Returns:
            CandidateProfile: Unified structured candidate profile data transfer object.
        """
        logger.info("Service request received to extract profile from text.")
        try:
            return self.extractor_agent.extract_profile(raw_text)
        except Exception as e:
            logger.error("Failed to extract candidate profile in service layer: %s", str(e), exc_info=True)
            # Re-raise standard exceptions or handle gracefully
            raise
