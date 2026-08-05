"""Schemas for the AI Job Copilot resume parser module."""

from typing import List
from pydantic import BaseModel, Field

class ResumeParserResult(BaseModel):
    """Pydantic model representing the result of parsing a resume file."""
    raw_text: str = Field(..., description="The raw extracted and cleaned text from the resume.")
    page_count: int = Field(..., description="The number of pages extracted from the document.")
    file_type: str = Field(..., description="The file extension/type of the document parsed (e.g., 'pdf', 'docx').")
    character_count: int = Field(..., description="The total number of characters in the cleaned raw text.")
    warnings: List[str] = Field(default_factory=list, description="Any warnings encountered during the parsing process.")
