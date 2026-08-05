"""Resume Parser Service that coordinates resume parsing requests using the ResumeParserAgent."""

import logging
import os
from typing import BinaryIO

from backend.app.ai.agents.resume_parser import ResumeParserAgent
from backend.app.ai.exceptions import ResumeFileNotFoundError
from backend.app.ai.schemas.resume_parser_schema import ResumeParserResult

logger = logging.getLogger(__name__)

class ResumeParserService:
    """Service layer coordinating raw file and stream parsing operations for candidate resumes."""

    def __init__(self, parser_agent: ResumeParserAgent = None):
        """Initializes the service with a ResumeParserAgent instance.

        Args:
            parser_agent (ResumeParserAgent, optional): Parser agent to inject. Defaults to a new instance.
        """
        self.parser_agent = parser_agent or ResumeParserAgent()

    def parse_file(self, file_path: str) -> ResumeParserResult:
        """Parses a resume file located at the specified physical file path.

        Args:
            file_path (str): Absolute or relative path to the resume file.

        Returns:
            ResumeParserResult: Structured parse result.

        Raises:
            ResumeFileNotFoundError: If the file path does not exist.
            UnsupportedFileTypeError: If the file extension is not supported.
            TextExtractionError: If text extraction fails or yields no valid text.
        """
        if not os.path.exists(file_path):
            logger.error("Resume file not found at path: %s", file_path)
            raise ResumeFileNotFoundError(f"Resume file not found at path: '{file_path}'")

        file_extension = os.path.splitext(file_path)[1].lower().strip().replace(".", "")
        logger.info("Parsing file: %s with detected extension: %s", file_path, file_extension)

        try:
            with open(file_path, "rb") as file_stream:
                return self.parser_agent.parse(file_stream, file_extension)
        except Exception as e:
            logger.error("Error occurred while parsing file %s: %s", file_path, str(e))
            raise

    def parse_stream(self, file_stream: BinaryIO, file_type: str) -> ResumeParserResult:
        """Parses a resume from an in-memory binary stream.

        Args:
            file_stream (BinaryIO): In-memory binary file stream of the resume.
            file_type (str): The file extension or MIME type key (e.g. 'pdf', 'docx').

        Returns:
            ResumeParserResult: Structured parse result.

        Raises:
            UnsupportedFileTypeError: If the file type is not supported.
            TextExtractionError: If text extraction fails or yields no valid text.
        """
        logger.info("Parsing stream with type identifier: %s", file_type)
        try:
            return self.parser_agent.parse(file_stream, file_type)
        except Exception as e:
            logger.error("Error occurred while parsing binary stream: %s", str(e))
            raise
