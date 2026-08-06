"""Pydantic schemas for the Job Parser Agent."""

from typing import List, Optional
from pydantic import BaseModel, Field

class JobParserMetadata(BaseModel):
    """Pydantic model representing parsing session metadata."""
    parsed_at: str = Field(..., description="ISO timestamp of when the parsing occurred.")
    character_count: int = Field(..., description="Total length in characters of the original text.")
    warnings: List[str] = Field(default_factory=list, description="List of warnings raised during parsing.")


class JobProfile(BaseModel):
    """Structured Job Profile containing extracted metadata and requirements from a job posting."""
    company_name: Optional[str] = Field(None, description="Name of the company/organization.")
    job_title: Optional[str] = Field(None, description="Title of the job posting.")
    department: Optional[str] = Field(None, description="Target department or business unit.")
    employment_type: Optional[str] = Field(None, description="e.g. Full-time, Part-time, Contract, Internship.")
    work_mode: Optional[str] = Field(None, description="e.g. Remote, Hybrid, On-site.")
    location: Optional[str] = Field(None, description="Geographic location of the role.")
    salary: Optional[str] = Field(None, description="Salary or compensation package details.")
    experience_required: Optional[str] = Field(None, description="Experience requirements or years requested.")
    education_required: Optional[str] = Field(None, description="Target educational credentials.")
    required_skills: List[str] = Field(default_factory=list, description="Extracted required core competencies.")
    preferred_skills: List[str] = Field(default_factory=list, description="Extracted nice-to-have or preferred skills.")
    responsibilities: List[str] = Field(default_factory=list, description="Extracted key job duties and responsibilities.")
    qualifications: List[str] = Field(default_factory=list, description="Required qualifications, skills, and certifications.")
    benefits: List[str] = Field(default_factory=list, description="Offered benefits, perks, and compensation items.")
    recruiter_email: Optional[str] = Field(None, description="Recruiter email address if identified.")
    recruiter_phone: Optional[str] = Field(None, description="Recruiter telephone number if identified.")
    recruiter_whatsapp: Optional[str] = Field(None, description="Recruiter WhatsApp number if identified.")
    application_url: Optional[str] = Field(None, description="Source URL or application page link.")
    original_jd: str = Field(..., description="Original raw job description content parsed.")
    source_type: str = Field(..., description="Source medium used (e.g. 'text', 'url', 'pdf', 'docx').")
    metadata: JobParserMetadata = Field(..., description="Parsing operational session metadata.")
