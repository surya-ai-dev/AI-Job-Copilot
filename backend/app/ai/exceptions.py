"""Exceptions for the AI Job Copilot AI Layer parsing module."""

class ResumeParserError(Exception):
    """Base exception class for all resume parsing errors."""
    pass

class UnsupportedFileTypeError(ResumeParserError):
    """Raised when the uploaded file type is not supported (i.e. not PDF or DOCX)."""
    pass

class ResumeFileNotFoundError(ResumeParserError):
    """Raised when the specified resume file path cannot be found."""
    pass

class TextExtractionError(ResumeParserError):
    """Raised when text extraction from a resume fails or results in empty text."""
    pass
