"""Resume Matching Agent comparing Candidate Profile and Job Profile to evaluate matches."""

import logging
import re
from typing import List, Optional, Any, Dict
from backend.app.ai.schemas.candidate_profile_schema import CandidateProfile
from backend.app.ai.schemas.job_parser_schema import JobProfile
from backend.app.ai.schemas.resume_match_schema import ResumeMatchReport

logger = logging.getLogger(__name__)

class ResumeMatcherAgent:
    """Agent responsible for deterministic rule-based comparison between candidate and job postings."""

    # Stopwords list for keyword coverage metrics
    STOPWORDS = {
        "and", "or", "in", "the", "of", "to", "for", "with", "a", "an", "is", "at", "by", 
        "on", "about", "as", "from", "that", "this", "these", "are", "be", "has", "have", "had"
    }

    def __init__(self):
        """Initializes the agent."""
        pass

    def _extract_year(self, date_str: str) -> Optional[int]:
        """Utility helper to parse a 4-digit year from any date string."""
        if not date_str:
            return None
        match = re.search(r'\b(19\d{2}|20\d{2})\b', date_str)
        return int(match.group(1)) if match else None

    def _calculate_experience_years(self, candidate: CandidateProfile) -> float:
        """Determines total years of experience accumulated in candidate profile."""
        total_years = 0.0
        current_year = datetime_now_year = 2026 # Frozen baseline target year

        for exp in candidate.experience:
            start_year = self._extract_year(exp.start_date)
            end_year = None
            if exp.end_date:
                end_lower = exp.end_date.lower().strip()
                if "present" in end_lower or "current" in end_lower or "now" in end_lower:
                    end_year = current_year
                else:
                    end_year = self._extract_year(exp.end_date)
            
            if start_year and end_year:
                # Minimum of 1 year per project/experience range to avoid zero years
                total_years += max(end_year - start_year, 1.0)
            elif start_year:
                # Default to 1 year if only start is known
                total_years += 1.0
            else:
                # Default fallback per entry
                total_years += 1.0

        return total_years

    def _parse_job_experience_required(self, exp_required: Optional[str]) -> float:
        """Extracts numerical years required from the job experience string."""
        if not exp_required:
            return 0.0
        match = re.search(r'(\d+)', exp_required)
        return float(match.group(1)) if match else 0.0

    def _get_degree_rank(self, degree_str: Optional[str]) -> int:
        """Maps educational degree titles into rank values for compatibility checks."""
        if not degree_str:
            return 0
        deg = degree_str.lower().strip()
        if "ph" in deg or "doctor" in deg or "d.phil" in deg:
            return 4
        if "master" in deg or "ms" in deg or "mba" in deg or "m.s." in deg or "m.a." in deg:
            return 3
        if "bachelor" in deg or "bs" in deg or "ba" in deg or "b.s." in deg or "b.a." in deg or "degree" in deg:
            return 2
        if "associate" in deg or "diploma" in deg:
            return 1
        return 0

    def _calculate_keyword_coverage(self, candidate: CandidateProfile, job: JobProfile) -> float:
        """Calculates percentage of unique job keywords found in candidate's text resume areas."""
        # 1. Gather job keywords
        job_words = []
        if job.job_title:
            job_words.extend(job.job_title.split())
        job_words.extend(job.required_skills)
        job_words.extend(job.preferred_skills)

        # Normalize and filter stopwords
        unique_job_keywords = set()
        for word in job_words:
            cleaned_word = re.sub(r'[^a-zA-Z0-9]', '', word).lower()
            if cleaned_word and cleaned_word not in self.STOPWORDS:
                unique_job_keywords.add(cleaned_word)

        if not unique_job_keywords:
            return 100.0

        # 2. Gather candidate profile texts safely (handling potential None values)
        cand_skills = candidate.skills or []
        cand_certs = candidate.certifications or []

        exp_strings = []
        for exp in (candidate.experience or []):
            comp = exp.company or ""
            role = exp.role or ""
            desc = exp.description or ""
            hi = " ".join(exp.highlights or [])
            exp_strings.append(f"{comp} {role} {desc} {hi}")

        proj_strings = []
        for proj in (candidate.projects or []):
            title = proj.title or ""
            role = proj.role or ""
            desc = proj.description or ""
            techs = " ".join(proj.technologies or [])
            hi = " ".join(proj.highlights or []) if hasattr(proj, "highlights") else ""
            proj_strings.append(f"{title} {role} {desc} {techs} {hi}")

        edu_strings = []
        for edu in (candidate.education or []):
            inst = edu.institution or ""
            deg = edu.degree or ""
            field = edu.field_of_study or ""
            edu_strings.append(f"{inst} {deg} {field}")

        candidate_text = " ".join([
            candidate.full_name or "",
            candidate.professional_summary or "",
            " ".join(cand_skills),
            " ".join(exp_strings),
            " ".join(proj_strings),
            " ".join(edu_strings),
            " ".join(cand_certs)
        ]).lower()

        # 3. Match keyword counts
        matched_count = 0
        for kw in unique_job_keywords:
            # Match word boundary or exact substring
            if kw in candidate_text:
                matched_count += 1

        return (matched_count / len(unique_job_keywords)) * 100.0

    def match(self, candidate: CandidateProfile, job: JobProfile) -> ResumeMatchReport:
        """Executes a rule-based comparison between candidate and job profiles.

        Args:
            candidate (CandidateProfile): Candidate profile domain model.
            job (JobProfile): Parsed job description profile.

        Returns:
            ResumeMatchReport: Structured compatibility match report.
        """
        logger.info("Executing resume match evaluation agent.")

        # Ingestion Liveness Check: Detect empty/blank profile
        if (not candidate.skills and 
            not candidate.experience and 
            not candidate.education and 
            not candidate.projects and 
            not candidate.certifications and 
            not candidate.professional_summary):
            logger.warning("Empty candidate profile provided. Returning zero match report.")
            return ResumeMatchReport(
                overall_match_score=0.0,
                matched_skills=[],
                missing_required_skills=[],
                missing_preferred_skills=[],
                experience_match_score=0.0,
                education_match_score=0.0,
                project_match_score=0.0,
                certification_match_score=0.0,
                keyword_coverage=0.0,
                strengths=[],
                weaknesses=[],
                recommendations=["The candidate resume contains no usable profile information."]
            )

        # --------------------------------------------------
        # 1. Skills Comparison (Required: 60% weight, Preferred: 10% weight)
        # --------------------------------------------------
        cand_skills_lower = {s.lower().strip() for s in candidate.skills}
        
        # Match required skills
        matched_skills = []
        missing_required = []
        for s in job.required_skills:
            if s.lower().strip() in cand_skills_lower:
                matched_skills.append(s)
            else:
                missing_required.append(s)

        # Match preferred skills
        missing_preferred = []
        for s in job.preferred_skills:
            if s.lower().strip() in cand_skills_lower:
                matched_skills.append(s)  # Add preferred matches here too
            else:
                missing_preferred.append(s)

        # Scores calculation
        req_skills_score = (len(matched_skills) - (len(job.preferred_skills) - len(missing_preferred)))
        # Adjust matched_skills for only required list matches in score calculation
        matched_req_count = len(job.required_skills) - len(missing_required)
        req_score_val = (matched_req_count / len(job.required_skills) * 100.0) if job.required_skills else 100.0

        matched_pref_count = len(job.preferred_skills) - len(missing_preferred)
        pref_score_val = (matched_pref_count / len(job.preferred_skills) * 100.0) if job.preferred_skills else 100.0

        # Deduplicate matched_skills display collection
        display_matched_skills = sorted(list(set(matched_skills)))

        # --------------------------------------------------
        # 2. Experience Comparison (10% weight)
        # --------------------------------------------------
        job_req_years = self._parse_job_experience_required(job.experience_required)
        candidate_years = self._calculate_experience_years(candidate)
        if job_req_years > 0:
            exp_score = min(candidate_years / job_req_years, 1.0) * 100.0
        else:
            exp_score = 100.0

        # --------------------------------------------------
        # 3. Education Comparison (10% weight)
        # --------------------------------------------------
        job_edu_rank = self._get_degree_rank(job.education_required)
        candidate_max_rank = 0
        for edu in candidate.education:
            rank = self._get_degree_rank(edu.degree)
            if rank > candidate_max_rank:
                candidate_max_rank = rank
        
        if job_edu_rank > 0:
            edu_score = min(candidate_max_rank / job_edu_rank, 1.0) * 100.0
        else:
            edu_score = 100.0

        # --------------------------------------------------
        # 4. Project Comparison (5% weight)
        # --------------------------------------------------
        project_keywords = ["project", "projects", "portfolio", "github", "gitlab", "side project", "personal project"]
        
        job_text_parts = [job.original_jd or ""]
        if job.qualifications:
            job_text_parts.extend(job.qualifications)
        if job.responsibilities:
            job_text_parts.extend(job.responsibilities)
            
        combined_job_text = " ".join(job_text_parts).lower()
        values_projects = any(kw in combined_job_text for kw in project_keywords)

        if not values_projects:
            proj_score = 100.0
        else:
            proj_count = len(candidate.projects)
            if proj_count >= 2:
                proj_score = 100.0
            elif proj_count == 1:
                proj_score = 50.0
            else:
                proj_score = 0.0

        # --------------------------------------------------
        # 5. Certification Comparison (5% weight)
        # --------------------------------------------------
        cert_count = len(candidate.certifications)
        cert_keywords = [
            "certification", "certifications", "certified", "cert", 
            "aws certified", "azure certified", "gcp certified", 
            "pmp", "cissp", "csm"
        ]
        
        job_cert_parts = [job.original_jd or ""]
        if job.qualifications:
            job_cert_parts.extend(job.qualifications)
        if job.education_required:
            job_cert_parts.append(job.education_required)
            
        combined_cert_text = " ".join(job_cert_parts).lower()
        values_certs = any(kw in combined_cert_text for kw in cert_keywords)
        
        if not values_certs:
            cert_score = 100.0
        else:
            cert_score = 100.0 if cert_count >= 1 else 0.0

        # --------------------------------------------------
        # 6. Overall Match Calculation
        # --------------------------------------------------
        overall_match = (
            (req_score_val * 0.60) +
            (pref_score_val * 0.10) +
            (exp_score * 0.10) +
            (edu_score * 0.10) +
            (proj_score * 0.05) +
            (cert_score * 0.05)
        )

        # Cap overall match score at 39.9 if required skills exist but candidate matches zero
        if job.required_skills and len(missing_required) == len(job.required_skills):
            overall_match = min(overall_match, 39.9)

        # Keyword Coverage Calculation
        keyword_cov = self._calculate_keyword_coverage(candidate, job)

        # --------------------------------------------------
        # 7. Strengths, Weaknesses, and Recommendations
        # --------------------------------------------------
        strengths = []
        weaknesses = []
        recommendations = []

        # Strengths mapping
        if req_score_val >= 80:
            strengths.append("Excellent alignment with core required skills.")
        if exp_score >= 100:
            strengths.append(f"Meets or exceeds the experience requirement of {int(job_req_years)} years.")
        if edu_score >= 100:
            strengths.append("Academic qualifications meet or exceed target expectations.")
        if cert_count >= 1:
            strengths.append("Possesses professional candidate certifications.")

        # Weaknesses mapping
        if missing_required:
            weaknesses.append(f"Missing core required skills: {', '.join(missing_required[:4])}")
        if exp_score < 70:
            weaknesses.append("Overall years of experience are lower than requested.")
        if missing_preferred:
            weaknesses.append(f"Missing preferred skills: {', '.join(missing_preferred[:4])}")

        # Recommendations mapping
        if missing_required:
            recommendations.append(f"Gain hands-on practice in required skills: {', '.join(missing_required[:3])}")
        if missing_preferred:
            recommendations.append(f"Learn nice-to-have preferred competencies: {', '.join(missing_preferred[:3])}")
        if proj_score < 100:
            recommendations.append("Build additional portfolio projects that highlight your expertise.")
        if cert_score < 100:
            recommendations.append("Obtain relevant professional certifications to demonstrate skill validation.")

        return ResumeMatchReport(
            overall_match_score=round(overall_match, 1),
            matched_skills=display_matched_skills,
            missing_required_skills=missing_required,
            missing_preferred_skills=missing_preferred,
            experience_match_score=round(exp_score, 1),
            education_match_score=round(edu_score, 1),
            project_match_score=round(proj_score, 1),
            certification_match_score=round(cert_score, 1),
            keyword_coverage=round(keyword_cov, 1),
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
