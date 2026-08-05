"""Candidate Profile Extractor Agent implementing rule-based and regex heuristics."""

import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from backend.app.ai.schemas.candidate_profile_schema import (
    CandidateProfile,
    ExperienceItem,
    ProjectItem,
    EducationItem
)

logger = logging.getLogger(__name__)

class BaseCandidateProfileExtractor(ABC):
    """Abstract base class for extracting candidate profiles from raw text."""

    @abstractmethod
    def extract(self, raw_text: str) -> CandidateProfile:
        """Extracts structured CandidateProfile from raw resume text.

        Args:
            raw_text (str): The raw text extracted from the resume.

        Returns:
            CandidateProfile: Structured candidate profile.
        """
        pass


class RuleBasedCandidateProfileExtractor(BaseCandidateProfileExtractor):
    """Rule-based and regex-based implementation of candidate profile extraction."""

    # Common section header regex mappings
    SECTION_HEADERS = {
        "summary": re.compile(r'^(?:professional\s+)?summary|profile|about\s+me|objective$', re.IGNORECASE),
        "skills": re.compile(r'^(?:technical\s+|core\s+|key\s+)?skills|technology\s+stack|tech\s+stack|expertise|competencies|programming\s+languages|frameworks|core\s+competencies|technologies$', re.IGNORECASE),
        "experience": re.compile(r'^(?:work\s+|professional\s+|employment\s+)?experience|employment\s+history$', re.IGNORECASE),
        "projects": re.compile(r'^projects|personal\s+projects|key\s+projects$', re.IGNORECASE),
        "education": re.compile(r'^education|academic\s+background|academic\s+credentials$', re.IGNORECASE),
        "certifications": re.compile(r'^certifications|certificates|licenses$', re.IGNORECASE)
    }

    def extract(self, raw_text: str) -> CandidateProfile:
        """Parses the raw text to extract structured CandidateProfile."""
        logger.info("Extracting candidate profile from raw text.")
        if not raw_text or not raw_text.strip():
            logger.warning("Empty raw text provided for extraction.")
            return CandidateProfile()

        # Split text into lines for line-by-line heuristic parsing
        lines = [line.strip() for line in raw_text.split("\n")]
        
        # 1. Extract global contact information using regex
        email = self._extract_email(raw_text)
        phone = self._extract_phone(raw_text)
        linkedin = self._extract_linkedin(raw_text)
        github = self._extract_github(raw_text)
        name = self._extract_name(lines)

        # 2. Segment lines into sections
        sections = self._segment_sections(lines)

        # 3. Parse fields from segmented sections
        summary = self._parse_summary(sections.get("summary", []))
        skills = self._parse_skills(sections.get("skills", []))
        experience = self._parse_experience(sections.get("experience", []))
        projects = self._parse_projects(sections.get("projects", []))
        education = self._parse_education(sections.get("education", []))
        certifications = self._parse_certifications(sections.get("certifications", []))

        return CandidateProfile(
            full_name=name,
            email=email,
            phone=phone,
            linkedin_url=linkedin,
            github_url=github,
            professional_summary=summary,
            skills=skills,
            experience=experience,
            projects=projects,
            education=education,
            certifications=certifications
        )

    def _clean_name(self, name: str) -> str:
        """Cleans decorative prefix/suffix elements and repeated punctuation from a name."""
        if not name:
            return name
        # Strip leading decorative characters and bullets
        name = re.sub(r'^[oO•◦■♦⬦\s\-_*#=~|:]+', '', name)
        # Strip trailing decorative characters
        name = re.sub(r'[\s\-_*#=~|:•◦■♦⬦]+$', '', name)
        # Remove repeated leading and trailing punctuation (2 or more)
        name = re.sub(r'^[.!?,;]{2,}', '', name)
        name = re.sub(r'[.!?,;]{2,}$', '', name)
        # Collapse multiple spaces
        name = re.sub(r'\s+', ' ', name)
        return name.strip()

    def _extract_name(self, lines: List[str]) -> Optional[str]:
        """Extracts the candidate's name based on positioning and content heuristics."""
        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue
            
            # Avoid lines containing contact details or URLs
            if "@" in cleaned or "http" in cleaned or "www" in cleaned:
                continue
            
            # Avoid lines containing digits
            if re.search(r'\d', cleaned):
                continue
                
            # Avoid common headers or sections
            lower_cleaned = cleaned.lower()
            if lower_cleaned in ["resume", "curriculum vitae", "cv", "summary", "profile", "skills", "experience", "education", "projects"]:
                continue
                
            # Clean the name before validation and assignment
            cleaned_name = self._clean_name(cleaned)
            
            # Name should reasonably be short (between 2 to 40 characters)
            if 2 < len(cleaned_name) < 40:
                return cleaned_name
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        match = re.search(r'[\w.%+-]+@[\w.-]+\.[\w]{2,}', text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        # Matches international phone formats starting with '+' or standard US format
        pattern = r'(?:\+\d{1,4}[-.\s]?\(?\d{1,5}\)?(?:[-.\s]?\d{2,9}){1,5})|(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _normalize_url(self, url: Optional[str]) -> Optional[str]:
        """Normalizes the protocol of the extracted URL."""
        if not url:
            return url
        trimmed = url.strip()
        lower_trimmed = trimmed.lower()
        if (lower_trimmed.startswith("github.com") or 
            lower_trimmed.startswith("linkedin.com") or 
            lower_trimmed.startswith("www.")):
            return f"https://{trimmed}"
        return trimmed

    def _extract_linkedin(self, text: str) -> Optional[str]:
        match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w_-]+', text, re.IGNORECASE)
        if match:
            return self._normalize_url(match.group(0))
        return None

    def _extract_github(self, text: str) -> Optional[str]:
        match = re.search(r'(?:https?://)?(?:www\.)?github\.com/[\w_-]+', text, re.IGNORECASE)
        if match:
            return self._normalize_url(match.group(0))
        return None

    def _clean_header(self, text: str) -> str:
        """Strips leading/trailing decorative elements from a section header."""
        # Strip leading decorative characters and bullets
        text = re.sub(r'^[oO•◦■♦⬦\s\-_*#=~|:]+', '', text)
        # Strip trailing decorative characters
        text = re.sub(r'[\s\-_*#=~|:•◦■♦⬦]+$', '', text)
        return text.strip().lower()

    def _segment_sections(self, lines: List[str]) -> Dict[str, List[str]]:
        """Segments lines into sections using matching header lists."""
        sections: Dict[str, List[str]] = {key: [] for key in self.SECTION_HEADERS}
        current_section: Optional[str] = None

        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue

            # Clean and normalize the header for comparison
            cleaned_header = self._clean_header(cleaned)

            # Check if this line matches a section header
            matched_header = False
            for section_key, header_regex in self.SECTION_HEADERS.items():
                # Headers are generally short lines
                if len(cleaned_header) < 40 and header_regex.match(cleaned_header):
                    current_section = section_key
                    matched_header = True
                    break

            if matched_header:
                continue

            # Append content line to active section if one is set
            if current_section:
                sections[current_section].append(line)

        return sections

    def _parse_summary(self, lines: List[str]) -> Optional[str]:
        cleaned_lines = [l.strip() for l in lines if l.strip()]
        return " ".join(cleaned_lines) if cleaned_lines else None

    def _parse_skills(self, lines: List[str]) -> List[str]:
        skills = []
        seen_skills = set()
        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue
            # Split by common separators: comma, semicolon, bullet symbols, pipe, tabs
            parts = re.split(r'[,;|•\t*-]', cleaned)
            for part in parts:
                part_cleaned = part.strip()
                # Remove leading/trailing decorative symbols or bullets from individual skill
                part_cleaned = re.sub(r'^[•◦■♦⬦\s\-_*#=~|:]+', '', part_cleaned)
                part_cleaned = re.sub(r'[\s\-_*#=~|:•◦■♦⬦]+$', '', part_cleaned).strip()
                if part_cleaned and len(part_cleaned) < 50:
                    lower_skill = part_cleaned.lower()
                    if lower_skill not in seen_skills:
                        seen_skills.add(lower_skill)
                        skills.append(part_cleaned)
        return skills

    def _parse_experience(self, lines: List[str]) -> List[ExperienceItem]:
        items = []
        current_item = None

        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue

            # Handle bullets
            if cleaned.startswith(('-', '*', '•', 'o ')):
                bullet_text = re.sub(r'^[-*•o]\s*', '', cleaned).strip()
                if bullet_text:
                    if not current_item:
                        current_item = ExperienceItem()
                        items.append(current_item)
                    current_item.highlights.append(bullet_text)
                continue

            # Check if this line looks like a header (e.g. contains dates or divider marks)
            is_header = False
            date_match = re.search(r'\b(?:19|20)\d{2}\b|present|current', cleaned, re.IGNORECASE)
            separator_match = re.search(r'\s-\s|\s\|\s|\bat\b', cleaned, re.IGNORECASE)

            if date_match or separator_match:
                is_header = True

            if is_header or not current_item:
                current_item = ExperienceItem()
                items.append(current_item)

                parts = re.split(r'\s*[-\|]\s*|\bat\b', cleaned, flags=re.IGNORECASE)
                if len(parts) >= 2:
                    current_item.company = parts[0].strip()
                    current_item.role = parts[1].strip()
                    if len(parts) >= 3:
                        current_item.start_date = parts[2].strip()
                else:
                    current_item.role = cleaned
            else:
                if current_item.description:
                    current_item.description += " " + cleaned
                else:
                    current_item.description = cleaned

        return items

    def _parse_projects(self, lines: List[str]) -> List[ProjectItem]:
        items = []
        current_item = None

        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue

            if cleaned.startswith(('-', '*', '•', 'o ')):
                bullet_text = re.sub(r'^[-*•o]\s*', '', cleaned).strip()
                if bullet_text:
                    if not current_item:
                        current_item = ProjectItem()
                        items.append(current_item)
                    current_item.highlights.append(bullet_text)
                continue

            is_title = False
            url_match = re.search(r'github\.com|http|www', cleaned, re.IGNORECASE)
            if url_match or len(cleaned) < 50:
                is_title = True

            if is_title or not current_item:
                current_item = ProjectItem()
                items.append(current_item)
                heading = cleaned
                if url_match:
                    urls = re.findall(r'https?://[^\s]+|github\.com/[^\s]+', cleaned)
                    if urls:
                        current_item.url = self._normalize_url(urls[0])
                    heading = re.sub(r'https?://[^\s]+|github\.com/[^\s]+', '', cleaned).strip(" -|")
                
                # Split only the first " - " to isolate the project title and role
                if " - " in heading:
                    parts = heading.split(" - ", 1)
                    current_item.title = parts[0].strip()
                    current_item.role = parts[1].strip()
                else:
                    current_item.title = heading.strip()
                    current_item.role = None
            else:
                if current_item.description:
                    current_item.description += " " + cleaned
                else:
                    current_item.description = cleaned

        return items

    def _parse_education(self, lines: List[str]) -> List[EducationItem]:
        items = []
        current_item = None

        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue

            degree_match = re.search(r'\b(?:B\.?S\.?|B\.?A\.?|M\.?S\.?|Ph\.?D\.?|Bachelor|Master|Doctorate|Associate)\b', cleaned, re.IGNORECASE)
            date_match = re.search(r'\b(?:19|20)\d{2}\b', cleaned)

            if degree_match or date_match or not current_item:
                current_item = EducationItem()
                items.append(current_item)

                parts = re.split(r'\s*[-\|]\s*', cleaned)
                if len(parts) >= 2:
                    current_item.institution = parts[0].strip()
                    current_item.degree = parts[1].strip()
                    if len(parts) >= 3:
                        current_item.end_date = parts[2].strip()
                else:
                    current_item.institution = cleaned
            else:
                gpa_match = re.search(r'\bGPA:?\s*([0-4]\.\d+)\b', cleaned, re.IGNORECASE)
                if gpa_match:
                    current_item.gpa = gpa_match.group(1)
                else:
                    if not current_item.field_of_study:
                        current_item.field_of_study = cleaned

        return items

    def _parse_certifications(self, lines: List[str]) -> List[str]:
        certs = []
        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue
            cleaned = re.sub(r'^[-*•o]\s*', '', cleaned).strip()
            if cleaned:
                certs.append(cleaned)
        return certs


class CandidateProfileExtractorAgent:
    """Orchestrates candidate profile extraction by delegating to a parsing strategy."""

    def __init__(self, extractor: BaseCandidateProfileExtractor = None):
        """Initializes the agent with an extractor strategy.

        Args:
            extractor (BaseCandidateProfileExtractor, optional): Extraction logic implementation.
                Defaults to RuleBasedCandidateProfileExtractor.
        """
        self.extractor = extractor or RuleBasedCandidateProfileExtractor()

    def extract_profile(self, raw_text: str) -> CandidateProfile:
        """Invokes the extraction logic to build a structured CandidateProfile.

        Args:
            raw_text (str): Extracted resume text.

        Returns:
            CandidateProfile: Structured profile entity.
        """
        return self.extractor.extract(raw_text)
