"""Resume Matcher Service coordinates the comparison between a candidate profile and job posting."""

import logging
from backend.app.ai.agents.resume_matcher import ResumeMatcherAgent
from backend.app.ai.schemas.candidate_profile_schema import CandidateProfile
from backend.app.ai.schemas.job_parser_schema import JobProfile
from backend.app.ai.schemas.resume_match_schema import ResumeMatchReport

logger = logging.getLogger(__name__)

class ResumeMatcherService:
    """Service layer coordinating Resume Matching operations using ResumeMatcherAgent."""

    def __init__(self, matcher_agent: ResumeMatcherAgent = None):
        """Initializes the service with dependency-injected matcher agent.

        Args:
            matcher_agent (ResumeMatcherAgent, optional): Injected matcher agent.
                Defaults to a new instance.
        """
        self.matcher_agent = matcher_agent or ResumeMatcherAgent()

    def match_profiles(self, candidate: CandidateProfile, job: JobProfile) -> ResumeMatchReport:
        """Compares Candidate Profile and Job Profile and returns a structured Match Report.

        Args:
            candidate (CandidateProfile): Ingested candidate profile record.
            job (JobProfile): Ingested parsed job description.

        Returns:
            ResumeMatchReport: Structured match report outlining strengths, gaps, and scores.
        """
        logger.info(
            "Service request received to match candidate profile (%s) with job (%s - %s)",
            candidate.full_name,
            job.company_name,
            job.job_title
        )
        try:
            report = self.matcher_agent.match(candidate, job)
            logger.info(
                "Match report generated successfully with overall compatibility score: %s%%", 
                report.overall_match_score
            )
            return report
        except Exception as e:
            logger.error(
                "Failed to run resume match evaluation: %s. Re-raising.", 
                str(e), 
                exc_info=True
            )
            raise
