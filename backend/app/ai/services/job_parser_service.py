"""Job Parser Service coordinating job parsing operations."""

import logging
from typing import Any

from backend.app.ai.agents.job_parser import JobParserAgent
from backend.app.ai.schemas.job_parser_schema import JobProfile

logger = logging.getLogger(__name__)

class JobParserService:
    """Service layer that coordinates Job Parsing using the JobParserAgent."""

    def __init__(self, parser_agent: JobParserAgent = None):
        """Initializes the service with dependency-injected parser agent.

        Args:
            parser_agent (JobParserAgent, optional): Injected parser agent. Defaults to a new instance.
        """
        self.parser_agent = parser_agent or JobParserAgent()

    def parse_job(self, source_content: Any, source_type: str) -> JobProfile:
        """Parses a job description from raw text, URL, PDF, or DOCX formats.

        Args:
            source_content (Any): The payload string (text/url) or file-like binary stream.
            source_type (str): Input format (e.g. 'text', 'url', 'pdf', 'docx').

        Returns:
            JobProfile: Structured Pydantic job profile data.

        Raises:
            UnsupportedFileTypeError: If the format is not recognized.
            InvalidJobInputError: If input is empty or extraction fails.
        """
        logger.info("Job parser service request received for source type: %s", source_type)
        try:
            profile = self.parser_agent.parse(source_content, source_type)
            logger.info(
                "Successfully parsed job profile: %s - %s", 
                profile.company_name, 
                profile.job_title
            )
            return profile
        except Exception as e:
            logger.error(
                "Failed to parse job description: %s. Re-raising exceptions.", 
                str(e), 
                exc_info=True
            )
            raise
