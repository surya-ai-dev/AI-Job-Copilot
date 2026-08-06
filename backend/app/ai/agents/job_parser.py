"""Job Parser Agent implementing rule-based and regex heuristics for parsing job postings."""

import logging
import re
from datetime import datetime
from typing import BinaryIO, Dict, List, Optional, Any

from backend.app.ai.agents.resume_parser import PDFFormatParser, DocxFormatParser
from backend.app.ai.schemas.job_parser_schema import JobProfile, JobParserMetadata
from backend.app.ai.exceptions import InvalidJobInputError, UnsupportedFileTypeError

logger = logging.getLogger(__name__)

class JobParserAgent:
    """Agent responsible for parsing job descriptions from text, URLs, PDF, and DOCX files.

    Uses deterministic rule-based algorithms and regular expressions.
    """

    # Section mapping regex patterns
    SECTION_PATTERNS = {
        "responsibilities": re.compile(
            r'^(?:key\s+|essential\s+)?responsibilities|what\s+you\s+will\s+do|duties|roles?\s+and\s+responsibilities|job\s+duties$', 
            re.IGNORECASE
        ),
        "qualifications": re.compile(
            r'^requirements|qualifications|what\s+you\s+bring|what\s+we\s+look\s+for|basic\s+qualifications$', 
            re.IGNORECASE
        ),
        "skills": re.compile(
            r'^skills|skill|required\s+skills|skills\s+required|technical\s+skills|core\s+skills|must\s+have\s+skills|required\s+technical\s+skills|technologies|expertise|technology\s+stack|tech\s+stack$', 
            re.IGNORECASE
        ),
        "preferred_skills": re.compile(
            r'^preferred\s+skills|preferred\s+qualifications|nice\s+to\s+have|plusses|plus|desired\s+skills$', 
            re.IGNORECASE
        ),
        "benefits": re.compile(
            r'^benefits|perks|what\s+we\s+offer|compensation\s+and\s+benefits|compensation$', 
            re.IGNORECASE
        )
    }

    def __init__(self):
        """Initializes the agent with file format parsers."""
        self._pdf_parser = PDFFormatParser()
        self._docx_parser = DocxFormatParser()

    def _clean_header(self, text: str) -> str:
        """Strips decorative symbols and whitespace to normalize header string comparison."""
        # Strip leading and trailing decorative characters: *, -, =, |, #, :, [, ], (, )
        text = re.sub(r'^[=\-*#|:\[\]\(\)\s•◦■♦⬦◦oO_~]+|[=\-*#|:\[\]\(\)\s•◦■♦⬦◦oO_~]+$', '', text)
        return text.strip().lower()

    def _segment_sections(self, lines: List[str]) -> Dict[str, List[str]]:
        """Splits raw text lines into categorized section buckets."""
        sections = {key: [] for key in self.SECTION_PATTERNS}
        current_section: Optional[str] = None

        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue

            cleaned_header = self._clean_header(cleaned)
            matched_header = False
            
            # Inline header check for skills/preferred_skills only
            is_inline = False
            if ":" in cleaned:
                parts = cleaned.split(":", 1)
                header_part = parts[0].strip()
                content_part = parts[1].strip()
                cleaned_header_part = self._clean_header(header_part)
                
                for section_key, pattern in self.SECTION_PATTERNS.items():
                    if section_key in ["skills", "preferred_skills"]:
                        if len(cleaned_header_part) < 40 and pattern.match(cleaned_header_part):
                            current_section = section_key
                            matched_header = True
                            is_inline = True
                            if content_part:
                                sections[section_key].append(content_part)
                            break
                            
            if not is_inline:
                for section_key, pattern in self.SECTION_PATTERNS.items():
                    if len(cleaned_header) < 40 and pattern.match(cleaned_header):
                        current_section = section_key
                        matched_header = True
                        break

            if matched_header:
                continue

            if current_section:
                sections[current_section].append(line)

        return sections

    def _extract_company(self, text: str, first_line: str) -> Optional[str]:
        """Extracts company name from job text using explicit regex patterns and positioning."""
        def strip_decorators(s: str) -> str:
            return re.sub(r'^[=\-*#|:\[\]\(\)\s]+|[=\-*#|:\[\]\(\)\s]+$', '', s).strip()

        def is_invalid_company_name(name: str) -> bool:
            if not name:
                return True
            ignored_prefixes = [
                "looking for",
                "we are hiring",
                "join our team",
                "hiring"
            ]
            name_lower = name.lower().strip()
            for prefix in ignored_prefixes:
                if name_lower.startswith(prefix):
                    return True
            if name.endswith(".") or len(name.split()) > 5:
                return True
            return False

        # 1. Check standard labels first
        match = re.search(r'(?:company|employer|organization):\s*([^\n]+)', text, re.IGNORECASE)
        if match:
            cand = strip_decorators(match.group(1))
            if not is_invalid_company_name(cand):
                return cand

        # 2. Heuristic check on lines
        patterns = [
            re.compile(r'about\s+([A-Z\u00C0-\u017F][a-zA-Z0-9\u00C0-\u017F\s&]{2,30}?)(?:\s+is|\s+builds|\s+creates|\.|\s*\n|$)', re.IGNORECASE),
            re.compile(r'at\s+([A-Z\u00C0-\u017F][a-zA-Z0-9\u00C0-\u017F\s&]{2,30}?)(?:\s+we|\s+believe|,|\.|\s*\n|$)', re.IGNORECASE),
            re.compile(r'([A-Z\u00C0-\u017F][a-zA-Z0-9\u00C0-\u017F\s&]{2,30}?)\s+is\s+(?:hiring|looking\s+for|seeking)', re.IGNORECASE)
        ]
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                cand = strip_decorators(match.group(1))
                if not is_invalid_company_name(cand):
                    return cand

        # 3. Fallback to first line if it looks like a simple name (short)
        cleaned_first = strip_decorators(first_line)
        if cleaned_first and len(cleaned_first) < 40 and " - " not in cleaned_first and "@" not in cleaned_first:
            if not is_invalid_company_name(cleaned_first):
                return cleaned_first
        return None

    def _extract_title(
        self, text: str, first_line: str, company_name: Optional[str] = None, lines: Optional[List[str]] = None
    ) -> Optional[str]:
        """Extracts job title from job text using prefix flags and line heuristics."""
        match = re.search(
            r'(?:job\s+)?(?:title|role|position):\s*(.+?)(?=\s*\|\||\s*\||\s*workplace:|\s*location:|\s*department:|\s*employment|\s*salary|\s*experience|\n|$)',
            text,
            re.IGNORECASE
        )
        if match:
            return match.group(1).strip(" -|_*")

        # Standalone line immediately after the company name
        if company_name and lines:
            def clean(s):
                return re.sub(r'[\s\-|_*=~#:|]', '', s).lower()
            cleaned_company = clean(company_name)
            company_idx = -1
            for idx, line in enumerate(lines):
                if clean(line) == cleaned_company:
                    company_idx = idx
                    break
            
            if company_idx != -1:
                for idx in range(company_idx + 1, len(lines)):
                    cand_line = lines[idx].strip()
                    if cand_line:
                        return cand_line.strip(" -|_*")

        # Fallback heuristic: check if first line contains common role terms
        if first_line and len(first_line) < 50:
            role_indicators = ["engineer", "developer", "architect", "manager", "specialist", "analyst", "lead", "designer", "consultant", "scientist"]
            if any(indicator in first_line.lower() for indicator in role_indicators):
                return first_line.strip(" -|_*")
        return None

    def _extract_department(self, text: str) -> Optional[str]:
        match = re.search(r'(?:department|team):\s*([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip(" -|_*")
        
        # Scan for common department terms
        departments = ["Engineering", "Product Management", "Marketing", "Sales", "Finance", "Human Resources", "Operations", "Legal", "Design"]
        for dept in departments:
            if re.search(r'\b' + re.escape(dept) + r'\b', text, re.IGNORECASE):
                return dept
        return None

    def _extract_employment_type(self, text: str) -> Optional[str]:
        match = re.search(r'(?:employment\s+type|job\s+type|status):\s*([^\n]+)', text, re.IGNORECASE)
        val = match.group(1).strip(" -|_*") if match else None

        if not val:
            types = ["full-time", "full time", "part-time", "part time", "contract", "internship", "freelance", "temporary"]
            for t in types:
                if re.search(r'\b' + re.escape(t) + r'\b', text, re.IGNORECASE):
                    val = t
                    break

        if val:
            val_lower = val.lower().strip()
            if "full-time" in val_lower or "full time" in val_lower:
                return "Full-time"
            if "part-time" in val_lower or "part time" in val_lower:
                return "Part-time"
            if "contract" in val_lower:
                return "Contract"
            if "internship" in val_lower:
                return "Internship"
            return val.capitalize()
        return None

    def _extract_work_mode(self, text: str) -> Optional[str]:
        match = re.search(r'(?:work\s+mode|workplace\s+type|mode):\s*([^\n]+)', text, re.IGNORECASE)
        val = match.group(1).strip(" -|_*") if match else None

        if not val:
            modes = ["remote", "hybrid", "on-site", "onsite"]
            for m in modes:
                if re.search(r'\b' + re.escape(m) + r'\b', text, re.IGNORECASE):
                    val = m
                    break

        if val:
            val_lower = val.lower().strip()
            if "remote" in val_lower:
                return "Remote"
            if "hybrid" in val_lower:
                return "Hybrid"
            if "on-site" in val_lower or "onsite" in val_lower:
                return "On-site"
            return val.capitalize()
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        match = re.search(r'(?:location|job\s+location|site):\s*([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip(" -|_*")
        return None

    def _extract_salary(self, text: str) -> Optional[str]:
        match = re.search(r'(?:salary|compensation|salary\s+range|package):\s*([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip(" -|_*")

        # Regex searching for range layouts ($80k - $120k or similar)
        range_match = re.search(
            r'[\$€£₹]\d+(?:[\d,\s]*\d+)?(?:\s*-\s*[\$€£₹]\d+(?:[\d,\s]*\d+)?)?(?:\s*(?:k|thousand|/yr|/hr|/year|/month))?', 
            text, 
            re.IGNORECASE
        )
        return range_match.group(0) if range_match else None

    def _extract_experience(self, text: str) -> Optional[str]:
        match = re.search(r'(?:experience|experience\s+required):\s*([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip(" -|_*")

        exp_match = re.search(r'\b\d+\+?\s*(?:years?|yrs?)(?:\s*(?:of\s*)?experience)?\b', text, re.IGNORECASE)
        return exp_match.group(0) if exp_match else None

    def _extract_education(self, text: str) -> Optional[str]:
        match = re.search(r'(?:education|degree\s+required):\s*([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip(" -|_*")

        edu_indicators = [
            r"\bBachelor's(?:\s+degree)?\b", r"\bMaster's(?:\s+degree)?\b", r"\bPh\.?D\b",
            r"\bB\.?S\.?\b", r"\bM\.?S\.?\b", r"\bB\.?A\.?\b", r"\bM\.?B\.?A\b", r"\bdegree\s+in\s+[a-zA-Z\s]+\b"
        ]
        for pattern in edu_indicators:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None

    def _extract_recruiter_details(self, text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Extracts email, phone, and WhatsApp contacts for the recruiter."""
        email_match = re.search(r'[\w.%+-]+@[\w.-]+\.[\w]{2,}', text)
        email = email_match.group(0) if email_match else None

        phone_pattern = r'(?:\+\d{1,4}[-.\s]?\(?\d{1,5}\)?(?:[-.\s]?\d{2,9}){1,5})|(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        phone_match = re.search(phone_pattern, text)
        phone = phone_match.group(0) if phone_match else None

        # Look specifically for WhatsApp references with various common labels
        whatsapp_pattern = r'(?:whatsapp(?:\s+contact|\s+number|\s+no)?|wa(?:\s+number)?)\s*[:\s-]*\s*(' + phone_pattern + r')'
        whatsapp_match = re.search(whatsapp_pattern, text, re.IGNORECASE)
        whatsapp = whatsapp_match.group(1) if whatsapp_match else None
        
        return email, phone, whatsapp

    def _extract_application_url(self, text: str) -> Optional[str]:
        # Search for URLs containing career portal terms
        match = re.search(r'https?://[^\s]+(?:apply|careers?|jobs?|post|portal)[^\s]+', text, re.IGNORECASE)
        if match:
            return match.group(0).strip(" -|_*()")
        
        # Fallback to any general URL in the text
        general_match = re.search(r'https?://[^\s]+', text)
        return general_match.group(0).strip(" -|_*()") if general_match else None

    def _parse_list_items(self, lines: List[str], split_delimiters: bool = False) -> List[str]:
        """Cleans and extracts list items, stripping bullet points and decorative symbols."""
        items = []
        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue
            cleaned = re.sub(r'^[•◦■♦⬦\s\-_*#=~|:]+', '', cleaned)
            cleaned = re.sub(r'[\s\-_*#=~|:•◦■♦⬦]+$', '', cleaned).strip()
            if cleaned and len(cleaned) < 300:  # avoid collecting whole paragraphs
                if split_delimiters:
                    parts = re.split(r'[,;]', cleaned)
                    for part in parts:
                        part_cleaned = part.strip()
                        if part_cleaned:
                            items.append(part_cleaned)
                else:
                    items.append(cleaned)
        return items

    def parse(self, source_content: Any, source_type: str) -> JobProfile:
        """Parses a job description based on its input format.

        Args:
            source_content (Any): Text content, URL string, or binary file stream.
            source_type (str): The format type ('text', 'url', 'pdf', 'docx').

        Returns:
            JobProfile: Parsed Pydantic job profile result.

        Raises:
            UnsupportedFileTypeError: If the format is not recognized.
            InvalidJobInputError: If input is empty or extraction fails.
        """
        warnings = []
        normalized_type = source_type.lower().strip().replace(".", "")
        original_jd = ""

        # --------------------------------------------------
        # Step 1: Ingest source inputs into raw_text
        # --------------------------------------------------
        if normalized_type == "url":
            if not isinstance(source_content, str) or not source_content.strip():
                raise InvalidJobInputError("Invalid job description URL provided.")
            original_jd = f"Job Posting URL: {source_content}"
            logger.info("URL source type provided. Saving URL and skipping text parsing.")
        elif normalized_type == "text":
            if not isinstance(source_content, str) or not source_content.strip():
                raise InvalidJobInputError("Empty job description text content.")
            original_jd = source_content
        elif normalized_type == "pdf":
            if not source_content:
                raise InvalidJobInputError("Empty PDF stream provided.")
            try:
                # PDFFormatParser expects stream
                original_jd, _ = self._pdf_parser.extract_text_and_pages(source_content)
            except Exception as e:
                raise InvalidJobInputError(f"Failed to extract text from PDF: {str(e)}") from e
        elif normalized_type == "docx":
            if not source_content:
                raise InvalidJobInputError("Empty DOCX stream provided.")
            try:
                original_jd, _ = self._docx_parser.extract_text_and_pages(source_content)
            except Exception as e:
                raise InvalidJobInputError(f"Failed to extract text from DOCX: {str(e)}") from e
        else:
            raise UnsupportedFileTypeError(
                f"Unsupported job parser input type: '{source_type}'. Supported: url, text, pdf, docx"
            )

        # --------------------------------------------------
        # Step 2: Run deterministic parsing rules
        # --------------------------------------------------
        lines = [line.strip() for line in original_jd.split("\n")]
        first_line = ""
        for line in lines:
            if line:
                cleaned = re.sub(r'^[=\-*#|:\[\]\(\)\s]+|[=\-*#|:\[\]\(\)\s]+$', '', line).strip()
                if cleaned:
                    first_line = cleaned
                    break

        # Contact details
        email, phone, whatsapp = self._extract_recruiter_details(original_jd)
        
        # Application URL (if input type was URL, use it, else scan text)
        app_url = source_content if normalized_type == "url" else self._extract_application_url(original_jd)

        # Core header details
        company = self._extract_company(original_jd, first_line)
        title = self._extract_title(original_jd, first_line, company_name=company, lines=lines)
        dept = self._extract_department(original_jd)
        emp_type = self._extract_employment_type(original_jd)
        work_mode = self._extract_work_mode(original_jd)
        location = self._extract_location(original_jd)
        salary = self._extract_salary(original_jd)
        exp = self._extract_experience(original_jd)
        edu = self._extract_education(original_jd)

        # Segment sections
        sections = self._segment_sections(lines)

        # Parse segmented lists
        # Parse segmented lists
        req_skills = self._parse_list_items(sections["skills"], split_delimiters=True)
        pref_skills = self._parse_list_items(sections["preferred_skills"], split_delimiters=True)
        responsibilities = self._parse_list_items(sections["responsibilities"])
        qualifications = self._parse_list_items(sections["qualifications"])
        benefits = self._parse_list_items(sections["benefits"])

        # Warnings logic
        char_count = len(original_jd)
        if char_count < 100 and normalized_type != "url":
            warnings.append("Job description text is extremely short (< 100 characters). Details may be missing.")

        metadata = JobParserMetadata(
            parsed_at=datetime.utcnow().isoformat(),
            character_count=char_count,
            warnings=warnings
        )

        return JobProfile(
            company_name=company,
            job_title=title,
            department=dept,
            employment_type=emp_type,
            work_mode=work_mode,
            location=location,
            salary=salary,
            experience_required=exp,
            education_required=edu,
            required_skills=req_skills,
            preferred_skills=pref_skills,
            responsibilities=responsibilities,
            qualifications=qualifications,
            benefits=benefits,
            recruiter_email=email,
            recruiter_phone=phone,
            recruiter_whatsapp=whatsapp,
            application_url=app_url,
            original_jd=original_jd,
            source_type=normalized_type,
            metadata=metadata
        )
