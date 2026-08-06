"""Pydantic Schema for the Resume Matching Agent."""

from typing import List
from pydantic import BaseModel, Field

class ResumeMatchReport(BaseModel):
    """Structured report detailing the match evaluation between a Candidate Profile and a Job Profile."""
    overall_match_score: float = Field(
        ..., 
        description="Overall compatibility score ranging from 0.0 to 100.0."
    )
    matched_skills: List[str] = Field(
        default_factory=list, 
        description="Skills present in both the candidate profile and the job posting."
    )
    missing_required_skills: List[str] = Field(
        default_factory=list, 
        description="Required job skills that are missing from the candidate profile."
    )
    missing_preferred_skills: List[str] = Field(
        default_factory=list, 
        description="Preferred/Nice-to-have job skills that are missing from the candidate profile."
    )
    experience_match_score: float = Field(
        ..., 
        description="Experience compatibility score (0.0 to 100.0) based on years and roles."
    )
    education_match_score: float = Field(
        ..., 
        description="Education compatibility score (0.0 to 100.0) based on target degrees."
    )
    project_match_score: float = Field(
        ..., 
        description="Project compatibility score (0.0 to 100.0) based on project highlights."
    )
    certification_match_score: float = Field(
        ..., 
        description="Certification compatibility score (0.0 to 100.0)."
    )
    keyword_coverage: float = Field(
        ..., 
        description="Percentage of job keywords found within candidate's text resume areas (0.0 to 100.0)."
    )
    strengths: List[str] = Field(
        default_factory=list, 
        description="Identified candidate highlights matching job prerequisites."
    )
    weaknesses: List[str] = Field(
        default_factory=list, 
        description="Identified areas where the candidate profile falls short of requirements."
    )
    recommendations: List[str] = Field(
        default_factory=list, 
        description="Actionable steps the candidate can take to improve their match compatibility."
    )
