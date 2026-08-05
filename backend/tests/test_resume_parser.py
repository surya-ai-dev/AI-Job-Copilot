"""Unit tests for the Resume Parser Agent and Service."""

import io
import pytest
from unittest.mock import MagicMock, patch

from backend.app.ai.agents.resume_parser import (
    ResumeParserAgent,
    PDFFormatParser,
    DocxFormatParser
)
from backend.app.ai.services.resume_parser_service import ResumeParserService
from backend.app.ai.exceptions import (
    UnsupportedFileTypeError,
    ResumeFileNotFoundError,
    TextExtractionError
)
from backend.app.ai.schemas.resume_parser_schema import ResumeParserResult


# ==========================================
# 1. Tests for Text Cleaning & Normalization
# ==========================================

def test_clean_text_basic():
    agent = ResumeParserAgent()
    input_text = "   John   Doe  \n\n   Software   Engineer   \n\t  Python  "
    expected = "John Doe\nSoftware Engineer\nPython"
    assert agent.clean_text(input_text) == expected


def test_clean_text_unicode():
    agent = ResumeParserAgent()
    # Normalize ligatures and special spaces
    input_text = "Resume\u200b  with\u00a0special   spaces"
    cleaned = agent.clean_text(input_text)
    assert "special spaces" in cleaned


def test_clean_text_empty():
    agent = ResumeParserAgent()
    assert agent.clean_text("") == ""
    assert agent.clean_text(None) == ""


# ==========================================
# 2. Tests for PDF Parsing (Mocked)
# ==========================================

@patch("pdfplumber.open")
def test_pdf_format_parser_success(mock_pdf_open):
    # Setup mocks
    mock_pdf = MagicMock()
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1 Text Content"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2 Text Content"
    
    mock_pdf.pages = [mock_page1, mock_page2]
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf

    parser = PDFFormatParser()
    dummy_stream = io.BytesIO(b"dummy pdf bytes")
    
    text, pages = parser.extract_text_and_pages(dummy_stream)
    
    assert pages == 2
    assert "Page 1 Text Content" in text
    assert "Page 2 Text Content" in text


@patch("pdfplumber.open")
def test_pdf_format_parser_empty_document(mock_pdf_open):
    mock_pdf = MagicMock()
    mock_pdf.pages = []
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf

    parser = PDFFormatParser()
    dummy_stream = io.BytesIO(b"dummy pdf bytes")
    
    with pytest.raises(TextExtractionError) as exc_info:
        parser.extract_text_and_pages(dummy_stream)
    assert "0 pages" in str(exc_info.value)


@patch("pdfplumber.open")
def test_pdf_format_parser_exception(mock_pdf_open):
    mock_pdf_open.side_effect = Exception("File corruption")

    parser = PDFFormatParser()
    dummy_stream = io.BytesIO(b"dummy pdf bytes")
    
    with pytest.raises(TextExtractionError) as exc_info:
        parser.extract_text_and_pages(dummy_stream)
    assert "PDF parsing error" in str(exc_info.value)


# ==========================================
# 3. Tests for DOCX Parsing (Mocked)
# ==========================================

@patch("backend.app.ai.agents.resume_parser.Document")
def test_docx_format_parser_success(mock_document_class):
    mock_doc = MagicMock()
    
    # Mock paragraphs
    p1 = MagicMock()
    p1.text = "Paragraph 1 Text"
    p2 = MagicMock()
    p2.text = "Paragraph 2 Text"
    mock_doc.paragraphs = [p1, p2]
    
    # Mock tables
    mock_table = MagicMock()
    mock_row = MagicMock()
    cell1 = MagicMock()
    cell1.text = "Skill Name"
    cell2 = MagicMock()
    cell2.text = "Experience Level"
    mock_row.cells = [cell1, cell2]
    mock_table.rows = [mock_row]
    mock_doc.tables = [mock_table]
    
    # Mock XML parts for metadata (Empty list to trigger fallback to 1 page)
    mock_doc.part.package.parts = []
    
    mock_document_class.return_value = mock_doc

    parser = DocxFormatParser()
    dummy_stream = io.BytesIO(b"dummy docx bytes")
    
    text, pages = parser.extract_text_and_pages(dummy_stream)
    
    assert pages == 1
    assert "Paragraph 1 Text" in text
    assert "Paragraph 2 Text" in text
    assert "Skill Name | Experience Level" in text


@patch("backend.app.ai.agents.resume_parser.Document")
def test_docx_format_parser_with_page_metadata(mock_document_class):
    mock_doc = MagicMock()
    mock_doc.paragraphs = []
    mock_doc.tables = []
    
    # Mock XML parts to supply 3 pages
    mock_part = MagicMock()
    mock_part.partname = "/docProps/app.xml"
    mock_part.blob = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
        <Pages>3</Pages>
    </Properties>"""
    
    mock_doc.part.package.parts = [mock_part]
    mock_document_class.return_value = mock_doc

    parser = DocxFormatParser()
    dummy_stream = io.BytesIO(b"dummy docx bytes")
    
    _, pages = parser.extract_text_and_pages(dummy_stream)
    assert pages == 3


@patch("backend.app.ai.agents.resume_parser.Document")
def test_docx_format_parser_exception(mock_document_class):
    mock_document_class.side_effect = Exception("Format structure invalid")

    parser = DocxFormatParser()
    dummy_stream = io.BytesIO(b"dummy docx bytes")
    
    with pytest.raises(TextExtractionError) as exc_info:
        parser.extract_text_and_pages(dummy_stream)
    assert "DOCX parsing error" in str(exc_info.value)


# ==========================================
# 4. Tests for ResumeParserAgent Orchestrator
# ==========================================

def test_agent_unsupported_file_type():
    agent = ResumeParserAgent()
    dummy_stream = io.BytesIO(b"dummy content")
    
    with pytest.raises(UnsupportedFileTypeError) as exc_info:
        agent.parse(dummy_stream, "txt")
    assert "Unsupported file type" in str(exc_info.value)


@patch.object(PDFFormatParser, "extract_text_and_pages")
def test_agent_empty_text_extracted(mock_extract):
    mock_extract.return_value = ("", 1)
    
    agent = ResumeParserAgent()
    dummy_stream = io.BytesIO(b"dummy pdf bytes")
    
    with pytest.raises(TextExtractionError) as exc_info:
        agent.parse(dummy_stream, "pdf")
    assert "no readable text content" in str(exc_info.value)


@patch.object(PDFFormatParser, "extract_text_and_pages")
def test_agent_warnings_short_text(mock_extract):
    mock_extract.return_value = ("Short text", 1)
    
    agent = ResumeParserAgent()
    dummy_stream = io.BytesIO(b"dummy pdf bytes")
    
    result = agent.parse(dummy_stream, "pdf")
    assert isinstance(result, ResumeParserResult)
    assert result.character_count == 10
    assert len(result.warnings) == 1
    assert "extremely short" in result.warnings[0]


@patch.object(PDFFormatParser, "extract_text_and_pages")
def test_agent_warnings_unicode_replacement(mock_extract):
    # Text with replacement character \uFFFD
    mock_extract.return_value = ("Valid length text but with invalid character \uFFFD inside to trigger warning.", 1)
    
    agent = ResumeParserAgent()
    dummy_stream = io.BytesIO(b"dummy pdf bytes")
    
    result = agent.parse(dummy_stream, "pdf")
    assert len(result.warnings) >= 1

    assert any(
        "unicode replacement characters" in warning.lower()
        for warning in result.warnings
    )

# ==========================================
# 5. Tests for ResumeParserService
# ==========================================

@patch.object(ResumeParserAgent, "parse")
def test_service_parse_stream(mock_agent_parse):
    expected_result = ResumeParserResult(
        raw_text="Extracted text from stream",
        page_count=2,
        file_type="pdf",
        character_count=26,
        warnings=[]
    )
    mock_agent_parse.return_value = expected_result
    
    service = ResumeParserService()
    dummy_stream = io.BytesIO(b"dummy content")
    
    result = service.parse_stream(dummy_stream, "pdf")
    assert result == expected_result
    mock_agent_parse.assert_called_once_with(dummy_stream, "pdf")


def test_service_parse_file_not_found():
    service = ResumeParserService()
    
    with pytest.raises(ResumeFileNotFoundError) as exc_info:
        service.parse_file("non_existent_file_path.pdf")
    assert "file not found" in str(exc_info.value).lower()


@patch("os.path.exists", return_value=True)
@patch("builtins.open")
@patch.object(ResumeParserAgent, "parse")
def test_service_parse_file_success(mock_agent_parse, mock_open, mock_exists):
    expected_result = ResumeParserResult(
        raw_text="Extracted text from physical file",
        page_count=1,
        file_type="docx",
        character_count=33,
        warnings=[]
    )
    mock_agent_parse.return_value = expected_result
    
    service = ResumeParserService()
    
    result = service.parse_file("some_valid_file_path.docx")
    assert result == expected_result
    mock_agent_parse.assert_called_once()
