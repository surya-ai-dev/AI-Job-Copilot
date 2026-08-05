# backend/app/resume/services/optimization_service.py
# Application Service Layer orchestrating the optimization loop, quality evaluations, and file copies

import os
import shutil
import uuid
import time
from datetime import datetime
from typing import List, Optional, Tuple
from backend.app.resume.repository.resume_repository import ResumeRepository
from backend.app.jobs.repository.analysis_repository import JobAnalysisRepository
from backend.app.resume.repository.optimization_repository import ResumeOptimizationRepository
from backend.app.resume.domain.optimization import (
    ResumeOptimization, 
    ResumeMatch, 
    ATSScore, 
    OptimizationRecommendation, 
    ResumeEvaluation
)
from backend.app.resume.domain.resume import ResumeVersion
from backend.app.resume.models.optimization_model import ResumeOptimizationModel
from backend.app.shared.exceptions import NotFoundException, ValidationException, BusinessRuleException

class ResumeOptimizationService:
    def __init__(
        self, 
        opt_repo: ResumeOptimizationRepository, 
        resume_repo: ResumeRepository,
        analysis_repo: JobAnalysisRepository,
        storage_path: str = "/storage"
    ):
        self.opt_repo = opt_repo
        self.resume_repo = resume_repo
        self.analysis_repo = analysis_repo
        self.storage_path = storage_path

    async def optimize_resume(
        self, 
        user_id: uuid.UUID, 
        job_analysis_id: uuid.UUID
    ) -> ResumeOptimizationModel:
        """Run the AI optimization loop to tailor the master resume for a job posting."""
        # 1. Fetch active master resume
        active_resume = await self.resume_repo.get_active_by_user(user_id)
        if not active_resume:
            raise NotFoundException("Active master resume not found. Upload a resume first.", "RESUME_NOT_FOUND")

        # 2. Fetch structured job analysis details
        job_analysis = await self.analysis_repo.get_by_id(job_analysis_id)
        if not job_analysis or job_analysis.user_id != user_id:
            raise NotFoundException("Job analysis record not found.", "ANALYSIS_NOT_FOUND")

        # 3. Calculate initial match scores
        match_details = self._run_matching_assessment(active_resume, job_analysis)

        # 4. Initialize Optimization Loop (Iterative Critic Pipeline)
        optimized_summary = ""
        optimized_skills = []
        recommendations = []
        ats_evaluation = None
        
        max_iterations = 3
        iteration = 0
        quality_target_achieved = False

        while iteration < max_iterations and not quality_target_achieved:
            iteration += 1
            
            # Step A: Generate optimizations suggestions (summary & skills)
            optimized_summary, optimized_skills, recommendations = self._run_tailoring_pass(
                active_resume, job_analysis, iteration
            )

            # Step B: Critic Evaluation Check
            evaluation = self._evaluate_optimized_resume(
                active_resume, job_analysis, optimized_summary, optimized_skills
            )

            # Calculate estimated ATS Score based on evaluation
            ats_score = int(evaluation.keyword_coverage * 0.5 + evaluation.readability_score * 0.3 + 20)
            ats_evaluation = ATSScore(
                score=min(ats_score, 100),
                explanation=f"Keyword coverage at {evaluation.keyword_coverage}%. Readability score is {evaluation.readability_score:.1f}.",
                keyword_coverage_percent=evaluation.keyword_coverage,
                readability_index=evaluation.readability_score
            )

            # Loop exit criteria
            if ats_evaluation.score >= 90 and evaluation.formatting_is_valid:
                quality_target_achieved = True

        # 5. Generate secure tailored files version metadata and copy physical templates
        optimized_file_path = self._compile_optimized_resume_file(
            user_id, active_resume, job_analysis, optimized_summary, optimized_skills
        )

        # 6. Save active version metadata in resume history database
        latest_version = await self.resume_repo.get_latest_version_number(user_id)
        next_version = latest_version + 1
        domain_version = ResumeVersion(
            resume_id=active_resume.id,
            user_id=user_id,
            version_number=next_version,
            file_path=optimized_file_path,
            optimized_for_company=job_analysis.metadata_json["company_name"] if "company_name" in job_analysis.metadata_json else "TargetCompany",
            optimized_for_role=job_analysis.metadata_json["job_title"] if "job_title" in job_analysis.metadata_json else "TargetRole"
        )
        await self.resume_repo.create_version(domain_version)

        # 7. Save optimization results details
        domain_opt = ResumeOptimization(
            resume_id=active_resume.id,
            job_analysis_id=job_analysis_id,
            user_id=user_id,
            match_details=match_details,
            ats_evaluation=ats_evaluation,
            recommendations=recommendations,
            optimized_summary=optimized_summary,
            optimized_skills=optimized_skills,
            optimized_file_path=optimized_file_path
        )

        return await self.opt_repo.create_optimization(domain_opt)

    async def get_optimization_details(self, user_id: uuid.UUID, opt_id: uuid.UUID) -> ResumeOptimizationModel:
        """Fetch optimization details by ID."""
        db_opt = await self.opt_repo.get_by_id(opt_id)
        if not db_opt or db_opt.user_id != user_id:
            raise NotFoundException("Optimization record not found.", "OPTIMIZATION_NOT_FOUND")
        return db_opt

    async def get_optimization_report(self, user_id: uuid.UUID, opt_id: uuid.UUID) -> dict:
        """Expose readable match audits and recommendation summaries."""
        db_opt = await self.get_optimization_details(user_id, opt_id)
        return {
            "optimization_id": db_opt.id,
            "match_score": db_opt.match_score,
            "ats_score": db_opt.ats_score,
            "ats_report": db_opt.ats_evaluation_json,
            "recommendations": db_opt.recommendations_json,
            "summary_preview": db_opt.optimized_summary
        }

    async def download_optimized_resume(self, user_id: uuid.UUID, opt_id: uuid.UUID) -> Tuple[str, str]:
        """Retrieve optimized PDF file path for secure downloads."""
        db_opt = await self.opt_repo.get_by_id(opt_id)
        if not db_opt or db_opt.user_id != user_id or not os.path.exists(db_opt.optimized_file_path):
            raise NotFoundException("Optimized resume file not found.", "FILE_NOT_FOUND")
        
        # Extrapolate clean download filename
        filename = os.path.basename(db_opt.optimized_file_path)
        return db_opt.optimized_file_path, filename

    async def list_user_optimizations(self, user_id: uuid.UUID) -> List[ResumeOptimizationModel]:
        """List all optimizations run by the user."""
        return await self.opt_repo.list_optimizations(user_id)

    # Core Logic Implementations (Mocks for initial NLP loop phase)
    def _run_matching_assessment(self, resume: any, analysis: any) -> ResumeMatch:
        """Check overlaps between master skills and job details to calculate scores."""
        # Simple match comparison logic
        job_skills = {s["name"].lower() for s in analysis.skills_json}
        master_skills = {s.lower() for s in resume.parsed_skills}

        matching = job_skills.intersection(master_skills)
        missing = job_skills.difference(master_skills)

        skills_score = int((len(matching) / len(job_skills) * 100)) if job_skills else 100
        match_score = int(skills_score * 0.8 + 20) # base experience score weighting

        return ResumeMatch(
            resume_id=resume.id,
            job_analysis_id=analysis.id,
            match_score=min(match_score, 100),
            skills_match_score=min(skills_score, 100),
            experience_match_score=85,
            gap_skills=list(missing)
        )

    def _run_tailoring_pass(
        self, 
        resume: any, 
        analysis: any, 
        iteration: int
    ) -> Tuple[str, List[str], List[OptimizationRecommendation]]:
        """Mock optimization pass generating tailored summaries and skill order lists."""
        company = analysis.metadata_json["company_name"] if "company_name" in analysis.metadata_json else "TargetCompany"
        role = analysis.metadata_json["job_title"] if "job_title" in analysis.metadata_json else "TargetRole"
        
        # Tailored summary rephrases
        summary = f"Results-driven Software Engineer with extensive experience in Python, FastAPI, and Postgres. Proven track record designing APIs and managing databases to deliver business value. Highly interested in joining the {company} team as a {role}."
        
        # Group and order skills: prioritize skills listed in job requirements
        job_skills = [s["name"] for s in analysis.skills_json]
        master_skills = list(resume.parsed_skills)
        
        # Deduplicate and sort matching skills first
        reordered_skills = [s for s in job_skills if s in master_skills]
        reordered_skills.extend([s for s in master_skills if s not in reordered_skills])

        # Generate recommendations list
        recommendations = [
            OptimizationRecommendation(
                section="summary",
                change_type="rephrase",
                description="Aligned professional statement to highlight Python backend skills and fit with target company details.",
                original_text="Software engineer with experience in Python.",
                suggested_text=summary
            ),
            OptimizationRecommendation(
                section="skills",
                change_type="reorder",
                description="Prioritized required skills (FastAPI, Postgres) first to optimize ATS parsing index.",
                original_text=str(master_skills),
                suggested_text=str(reordered_skills)
            )
        ]

        return summary, reordered_skills, recommendations

    def _evaluate_optimized_resume(
        self, 
        resume: any, 
        analysis: any, 
        summary: str, 
        skills: List[str]
    ) -> ResumeEvaluation:
        """Audit the tailored drafts against the master profile to ensure zero fabrication."""
        # Check for skill inflation: verify all optimized skills exist in master resume
        master_skills_set = {s.lower() for s in resume.parsed_skills}
        inflated_skills = [s for s in skills if s.lower() not in master_skills_set]

        # Calculate keyword coverage score
        job_skills = {s["name"].lower() for s in analysis.skills_json}
        optimized_skills_set = {s.lower() for s in skills}
        matches = job_skills.intersection(optimized_skills_set)
        coverage_score = int(len(matches) / len(job_skills) * 100) if job_skills else 100

        # Enforce zero-fabrication constraint: if skills are inflated, fail validation check
        formatting_is_valid = True
        if inflated_skills:
            formatting_is_valid = False

        return ResumeEvaluation(
            grammar_issues=[],
            readability_score=72.5,
            keyword_coverage=coverage_score,
            formatting_is_valid=formatting_is_valid
        )

    def _compile_optimized_resume_file(
        self,
        user_id: uuid.UUID,
        resume: any,
        analysis: any,
        summary: str,
        skills: List[str]
    ) -> str:
        """Generate optimized files. Preserves original template and exports to naming pattern."""
        company = analysis.metadata_json["company_name"] if "company_name" in analysis.metadata_json else "Target"
        role = analysis.metadata_json["job_title"] if "job_title" in analysis.metadata_json else "Role"
        
        # Clean company and role names for file paths
        clean_company = re.sub(r"\s+", "", company)
        clean_role = re.sub(r"\s+", "", role)
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

        # Filename format: UserName_Role_Company_Date.pdf (fallback username to UserID for mock)
        filename = f"{user_id}_{clean_role}_{clean_company}_{date_str}.pdf"
        target_path = os.path.join(self.storage_path, filename)

        # Mock document compilation: copy master resume file
        if os.path.exists(resume.file_path):
            shutil.copy2(resume.file_path, target_path)
        else:
            # Fallback scratch file if master missing in test runs
            with open(target_path, "w") as f:
                f.write(f"Tailored Summary: {summary}\nSkills: {', '.join(skills)}")

        return target_path
