"""Schemas for the AI Job Copilot Candidate Profile Extractor."""

from typing import List, Optional
from pydantic import BaseModel, Field

class ExperienceItem(BaseModel):
    """Pydantic model representing a single work experience record."""
    company: Optional[str] = Field(None, description="Name of the company or organization.")
    role: Optional[str] = Field(None, description="Job title or role held.")
    start_date: Optional[str] = Field(None, description="Start date of employment (e.g., 'Jan 2020').")
    end_date: Optional[str] = Field(None, description="End date of employment (e.g., 'Present').")
    description: Optional[str] = Field(None, description="Paragraph description of the role.")
    highlights: List[str] = Field(default_factory=list, description="Bullet points or key accomplishments.")


class ProjectItem(BaseModel):
    """Pydantic model representing a single project record."""
    title: Optional[str] = Field(None, description="Title of the project.")
    role: Optional[str] = Field(None, description="Role held in the project.")
    technologies: List[str] = Field(default_factory=list, description="Technologies or languages used.")
    description: Optional[str] = Field(None, description="Description of the project's goals or details.")
    url: Optional[Optional[str]] = Field(None, description="Link/URL to the project repository or landing page.")
    highlights: List[str] = Field(default_factory=list, description="Bullet points or achievements in the project.")


class EducationItem(BaseModel):
    """Pydantic model representing an educational qualification."""
    institution: Optional[str] = Field(None, description="Name of the university, college, or school.")
    degree: Optional[str] = Field(None, description="Degree type (e.g., 'B.S.', 'M.S.').")
    field_of_study: Optional[str] = Field(None, description="Major or field of study (e.g., 'Computer Science').")
    start_date: Optional[str] = Field(None, description="Start date of the study.")
    end_date: Optional[str] = Field(None, description="End date or graduation date.")
    gpa: Optional[str] = Field(None, description="Grade point average (GPA).")


class CandidateProfile(BaseModel):
    """Unified candidate profile model containing all parsed resume details."""
    full_name: Optional[str] = Field(None, description="Full name of the candidate.")
    email: Optional[str] = Field(None, description="Email address extracted from the resume.")
    phone: Optional[str] = Field(None, description="Phone number extracted from the resume.")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile link.")
    github_url: Optional[str] = Field(None, description="GitHub profile link.")
    professional_summary: Optional[str] = Field(None, description="Brief professional summary or objective.")
    skills: List[str] = Field(default_factory=list, description="List of technical/soft skills.")
    experience: List[ExperienceItem] = Field(default_factory=list, description="List of work experience entries.")
    projects: List[ProjectItem] = Field(default_factory=list, description="List of project entries.")
    education: List[EducationItem] = Field(default_factory=list, description="List of educational entries.")
    certifications: List[str] = Field(default_factory=list, description="List of certifications or licenses.")
