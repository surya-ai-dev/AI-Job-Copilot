"""Autonomous Resume Optimization Loop Controller."""



import logging

from datetime import datetime

import uuid

import re

from typing import List, Tuple



from backend.app.ai.schemas.candidate_profile_schema import CandidateProfile

from backend.app.ai.schemas.job_parser_schema import JobProfile

from backend.app.ai.agents.resume_matcher import ResumeMatcherAgent

from backend.app.ai.agents.planner_agent import PlannerAgent, GapAnalysis, OptimizationPlan

from backend.app.ai.agents.rewrite_agent import ResumeRewriteAgent

from backend.app.ai.agents.critic_agent import CriticAgent, CriticStatus

from backend.app.ai.agents.validator_agent import ResumeValidatorAgent, ValidationStatus

from backend.app.ai.schemas.resume_optimizer_schema import (

    OptimizationRunStatus,

    OptimizationDecision,

    OptimizationDiff,

    OptimizationIteration,

    OptimizationHistory,

    ResumeOptimizationResponse

)



logger = logging.getLogger(__name__)





class OptimizationLoopController:

    """Orchestrates the multi-agent optimization state machine loop."""



    def __init__(self):

        self.matcher = ResumeMatcherAgent()

        self.planner = PlannerAgent()

        self.rewriter = ResumeRewriteAgent()

        self.critic = CriticAgent()

        self.validator = ResumeValidatorAgent()



    def optimize(

        self,

        candidate: CandidateProfile,

        job: JobProfile,

        target_score: float = 90.0,

        max_iterations: int = 5

    ) -> ResumeOptimizationResponse:

        """Executes the loop controller state machine exactly according to the optimization algorithm."""

        run_id = f"opt-{uuid.uuid4()}"

        created_at = datetime.utcnow().isoformat() + "Z"

        logger.info(f"Initializing optimization run: {run_id}")



        # Deep copies to prevent side-effects

        original = candidate.model_copy(deep=True)

        current_profile = candidate.model_copy(deep=True)

        best_profile = candidate.model_copy(deep=True)



        # 1. Baseline matching

        baseline_report = self.matcher.match(original, job)

        initial_score = baseline_report.overall_match_score

        best_score = initial_score

        current_score = initial_score



        logger.info(f"Baseline Match Score: {initial_score:.1f}")



        # Check baseline score and gaps prior to loop execution

        gap_analysis = self._run_gap_analysis(original, job)

        experience_gap = gap_analysis.experience_years_deficit



        if initial_score >= target_score:

            status = OptimizationRunStatus.SUCCESS

            reason = "No optimization required. Baseline score exceeds target score."

            logger.info(f"""

Status={status}

Reason={reason}

Missing Required={gap_analysis.missing_required_skills}

Missing Preferred={gap_analysis.missing_preferred_skills}

Experience Gap={experience_gap}

Iteration=0

""")

            completed_at = datetime.utcnow().isoformat() + "Z"

            history = OptimizationHistory(

                run_id=run_id,

                initial_score=initial_score,

                final_score=best_score,

                total_iterations=0,

                status=status,

                iterations=[],

                created_at=created_at,

                completed_at=completed_at

            )

            return ResumeOptimizationResponse(

                run_id=run_id,

                candidate_profile_id=1,

                job_profile_id=2,

                status=status,

                initial_score=initial_score,

                final_score=best_score,

                score_improvement=0.0,

                changes=[],

                history=history

            )



        iterations: List[OptimizationIteration] = []

        validation_failures_count = 0

        status = OptimizationRunStatus.RUNNING



        # Loop execution

        for i in range(1, max_iterations + 1):

            logger.info(f"=== Iteration {i} of {max_iterations} ===")



            # Step 1: Gap Analysis

            gap_analysis = self._run_gap_analysis(current_profile, job)



            # Check if gaps list is completely empty

            if (not gap_analysis.missing_required_skills and

                not gap_analysis.missing_preferred_skills and

                gap_analysis.experience_years_deficit == 0.0 and

                not gap_analysis.education_mismatch):

                logger.info("No gaps remaining. Exiting loop.")

                status = OptimizationRunStatus.SUCCESS

                break



            # Step 2: Planning

            plan = self.planner.generate_plan(gap_analysis)

            if not plan.tasks:

                logger.info("Planner generated an empty plan. Exiting loop.")

                status = OptimizationRunStatus.SUCCESS

                break



            # Step 3: Rewrite

            job_dict = {

                "required_skills": job.required_skills or [],

                "preferred_skills": job.preferred_skills or []

            }



            try:

                # LLM/Rewrite Agent Mutation

                draft = self.rewriter.rewrite(current_profile, plan, job_dict)

            except Exception as exc:

                logger.error(f"Rewrite Agent encountered exception: {exc}")

                # Log failed iteration step

                iterations.append(

                    OptimizationIteration(

                        iteration_number=i,

                        pre_score=current_score,

                        post_score=current_score,

                        planning_tasks=[t.action for t in plan.tasks],

                        critic_feedback=[f"Rewrite failure: {str(exc)}"],

                        validation_errors=["Exception raised during rewrite execution"],

                        decision=OptimizationDecision.REJECTED,

                        is_rolled_back=True

                    )

                )

                current_profile = best_profile.model_copy(deep=True)  # Rollback

                continue



            # Step 4: Critic style review

            critic_report = self.critic.review(draft, job_dict)



            # Step 5: Validator factual check

            val_report = self.validator.validate(

                original,

                draft,

                job_skills=job_dict.get("required_skills", []) + job_dict.get("preferred_skills", [])

            )



            # Evaluate validation and critic approvals

            if val_report.status == ValidationStatus.FAILED or critic_report.status == CriticStatus.REJECTED:

                validation_failures_count += 1

                logger.warning(f"Draft validation or style critique rejected. Failures count: {validation_failures_count}")



                errors = [v.description for v in val_report.factual_violations]

                if critic_report.status == CriticStatus.REJECTED:

                    errors.append("Critic style review rejected the draft.")



                iterations.append(

                    OptimizationIteration(

                        iteration_number=i,

                        pre_score=current_score,

                        post_score=current_score,

                        planning_tasks=[t.action for t in plan.tasks],

                        critic_feedback=critic_report.comments,

                        validation_errors=errors,

                        decision=OptimizationDecision.FAILED_VALIDATION,

                        is_rolled_back=True

                    )

                )



                # Rollback draft

                current_profile = best_profile.model_copy(deep=True)



                # Check for repeated validation failures stopping condition (3 failures limit)

                if validation_failures_count >= 3:

                    logger.warning("Repeated validation failures threshold exceeded. Aborting loop.")

                    status = OptimizationRunStatus.FAILED

                    break



                continue



            # Step 6: Recalculate match score

            new_report = self.matcher.match(draft, job)

            new_score = new_report.overall_match_score

            improvement = new_score - best_score



            # Step 7: Acceptance / Rollback logic

            if new_score > best_score:

                # Accept: Update best states

                best_score = new_score

                best_profile = draft.model_copy(deep=True)

                current_profile = draft.model_copy(deep=True)

                decision = OptimizationDecision.ACCEPTED

                is_rolled_back = False

                logger.info(f"Changes accepted. Score improved to: {new_score:.1f}")

            else:

                # Reject/Stagnate: Roll back

                current_profile = best_profile.model_copy(deep=True)

                decision = OptimizationDecision.REJECTED

                is_rolled_back = True

                logger.info(f"Score stagnated or decreased ({new_score:.1f} vs {best_score:.1f}). Rolling back changes.")



            # Record iteration details

            iterations.append(

                OptimizationIteration(

                    iteration_number=i,

                    pre_score=current_score,

                    post_score=new_score,

                    planning_tasks=[t.action for t in plan.tasks],

                    critic_feedback=critic_report.comments,

                    validation_errors=[],

                    decision=decision,

                    is_rolled_back=is_rolled_back

                )

            )



            current_score = best_score



            # Step 8: Core Stopping Conditions

            # A: Target Score reached

            if best_score >= target_score:

                logger.info(f"Target score ({target_score:.1f}) reached. Terminating loop.")

                status = OptimizationRunStatus.SUCCESS

                break



            # B: Score improvement convergence (Improvement < 2% over last iteration)

            last_iter_delta = iterations[-1].post_score - iterations[-1].pre_score

            if decision == OptimizationDecision.REJECTED or (i >= 2 and (last_iter_delta >= 0.0 and last_iter_delta < 2.0)):

                logger.info("Score improvement converged (delta < 2%). Terminating loop.")

                status = OptimizationRunStatus.SUCCESS

                break



        if status == OptimizationRunStatus.RUNNING:

            status = OptimizationRunStatus.SUCCESS



        completed_at = datetime.utcnow().isoformat() + "Z"



        # Calculate final diff changes

        changes = self._generate_diffs(original, best_profile)



        history = OptimizationHistory(

            run_id=run_id,

            initial_score=initial_score,

            final_score=best_score,

            total_iterations=len(iterations),

            status=status,

            iterations=iterations,

            created_at=created_at,

            completed_at=completed_at

        )



        reason = "Repeated validation failures threshold exceeded" if status == OptimizationRunStatus.FAILED else "Gaps resolved or converged"

        logger.info(f"""

Status={status}

Reason={reason}

Missing Required={gap_analysis.missing_required_skills}

Missing Preferred={gap_analysis.missing_preferred_skills}

Experience Gap={experience_gap}

Iteration={len(iterations)}

""")



        return ResumeOptimizationResponse(

            run_id=run_id,

            candidate_profile_id=1,  # Mocked profile id mapping

            job_profile_id=2,        # Mocked job id mapping

            status=status,

            initial_score=initial_score,

            final_score=best_score,

            score_improvement=round(best_score - initial_score, 1),

            changes=changes,

            history=history

        )



    def _run_gap_analysis(self, candidate: CandidateProfile, job: JobProfile) -> GapAnalysis:

        """Helper to run gap analysis vector difference calculations."""

        candidate_skills = {s.lower().strip() for s in candidate.skills}



        # Missing required

        missing_req = []

        for s in (job.required_skills or []):

            if s.lower().strip() not in candidate_skills:

                missing_req.append(s)



        # Missing preferred

        missing_pref = []

        for s in (job.preferred_skills or []):

            if s.lower().strip() not in candidate_skills:

                missing_pref.append(s)



        # Parse years deficit

        candidate_years = 0.0

        for exp in candidate.experience:

            # Basic years calculation helper

            # e.g., "2020" to "2022" -> 2 years

            years = self._parse_years(exp.start_date, exp.end_date)

            candidate_years += years



        # Required experience years

        required_years = 0.0

        if job.experience_required:

            digits = re.findall(r"\d+", job.experience_required)

            if digits:

                required_years = float(digits[0])



        deficit = max(0.0, required_years - candidate_years)



        # Education mismatch

        edu_mismatch = None

        if job.education_required:

            candidate_degrees = [e.degree.lower() for e in candidate.education if e.degree]

            req_degree = job.education_required.lower()

            if not any(req_degree in deg for deg in candidate_degrees):

                edu_mismatch = f"Candidate lacks degree ranking: {job.education_required}"



        return GapAnalysis(

            missing_required_skills=missing_req,

            missing_preferred_skills=missing_pref,

            experience_years_deficit=round(deficit, 1),

            education_mismatch=edu_mismatch

        )



    def _parse_years(self, start: str | None, end: str | None) -> float:

        """Calculates years of experience from employment date labels."""

        if not start:

            return 1.0 # Default fallback per item



        start_year = self._extract_year(start)

        end_year = self._extract_year(end) if end else 2026 # Assume present is 2026



        diff = end_year - start_year

        return max(1.0, float(diff))



    def _extract_year(self, date_str: str) -> int:

        """Extracts integer year value from date string label."""

        digits = re.findall(r"\d{4}", date_str)

        if digits:

            return int(digits[0])

        return 2020  # Default fallback



    def _generate_diffs(self, original: CandidateProfile, optimized: CandidateProfile) -> List[OptimizationDiff]:

        """Generates before/after diff representations for the changed sections."""

        diffs = []

        # Professional summary diff

        if original.professional_summary != optimized.professional_summary:

            diffs.append(

                OptimizationDiff(

                    section_name="summary",

                    original_text=original.professional_summary or "",

                    optimized_text=optimized.professional_summary or "",

                    rationale="Aligned professional statement to job goals and highlighted depth metrics."

                )

            )



        # Skills list diff

        if set(original.skills) != set(optimized.skills):

            added_skills = list(set(optimized.skills) - set(original.skills))

            diffs.append(

                OptimizationDiff(

                    section_name="skills",

                    original_text=", ".join(original.skills),

                    optimized_text=", ".join(optimized.skills),

                    rationale=f"Added skills taxonomy keywords matching job requirements: {', '.join(added_skills)}."

                )

            )



        # Experience descriptions diff

        for i in range(min(len(original.experience), len(optimized.experience))):

            o_exp = original.experience[i]

            t_exp = optimized.experience[i]

            if o_exp.description != t_exp.description:

                diffs.append(

                    OptimizationDiff(

                        section_name=f"experience_{i+1}_description",

                        original_text=o_exp.description or "",

                        optimized_text=t_exp.description or "",

                        rationale="Refined bullet statements using high-impact active verbs."

                    )

                )



        return diffs
