"""Pydantic Schemas for the Autonomous Resume Optimizer Engine."""



from enum import Enum

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator





class OptimizationRunStatus(str, Enum):

    """Execution status of an optimization run."""

    RUNNING = "RUNNING"

    SUCCESS = "SUCCESS"

    FAILED = "FAILED"

    STOPPED = "STOPPED"





class OptimizationDecision(str, Enum):

    """Decision outcome for a specific optimization iteration."""

    ACCEPTED = "ACCEPTED"

    REJECTED = "REJECTED"

    FAILED_VALIDATION = "FAILED_VALIDATION"





class OptimizationDiff(BaseModel):

    """Structured segment before/after changes representation."""

    section_name: str = Field(

        ...,

        description="Name of the section modified (e.g. summary, experience, projects)."

    )

    original_text: str = Field(

        ...,

        description="Original text of the section prior to optimization."

    )

    optimized_text: str = Field(

        ...,

        description="Optimized text of the section after optimization."

    )

    rationale: Optional[str] = Field(

        default=None,

        description="Explanation of why this optimization was performed."

    )





class OptimizationIteration(BaseModel):

    """Structured log details of a single loop iteration cycle."""

    iteration_number: int = Field(

    ...,

    description="Index of the optimization iteration (1 to 5)."

  )

    pre_score: float = Field(

        ...,

        description="Match score before this iteration's rewrites (0.0 to 100.0)."

    )

    post_score: float = Field(

        ...,

        description="Match score after this iteration's rewrites (0.0 to 100.0)."

    )

    planning_tasks: List[str] = Field(

        default_factory=list,

        description="List of tasks sequenced for this iteration."

    )

    critic_feedback: List[str] = Field(

        default_factory=list,

        description="Style and formatting feedback from the critic."

    )

    validation_errors: List[str] = Field(

        default_factory=list,

        description="Compliance and fact validation errors."

    )

    decision: OptimizationDecision = Field(

        ...,

        description="Resulting decision (ACCEPTED/REJECTED/FAILED_VALIDATION)."

    )

    is_rolled_back: bool = Field(

        default=False,

        description="Whether this iteration's changes were rolled back."

    )



    @field_validator("iteration_number")

    @classmethod

    def validate_iteration_number(cls, value: int) -> int:

        if value < 1 or value > 5:

            raise ValueError("Iteration number must be between 1 and 5")

        return value







    @field_validator("pre_score", "post_score")

    @classmethod

    def validate_scores(cls, v: float) -> float:

        if not (0.0 <= v <= 100.0):

            raise ValueError("Score must be between 0.0 and 100.0")

        return v



    def model_copy(self, *, update=None, deep=False):

        copied = super().model_copy(update=update, deep=deep)

        if update is not None:

            self.__class__.model_validate(copied.__dict__)

        return copied





class OptimizationHistory(BaseModel):

    """Aggregated execution logs for an entire optimization session."""

    run_id: str = Field(

        ...,

        description="Unique ID tracking the optimization run."

    )

    initial_score: float = Field(

        ...,

        description="Initial ATS match score."

    )



    final_score: float = Field(

        ...,

        description="Final ATS match score."

    )

    total_iterations: int = Field(

        ...,

        description="Total iteration cycles executed."

    )

    status: OptimizationRunStatus = Field(

        ...,

        description="Termination status of the optimization run."

    )

    iterations: List[OptimizationIteration] = Field(

        default_factory=list,

        description="Details of every iteration cycle."

    )

    created_at: str = Field(

        ...,

        description="Timestamp of when the optimization run started."

    )

    completed_at: Optional[str] = Field(

        default=None,

        description="Timestamp of when the optimization completed."

    )



    @field_validator("initial_score", "final_score")

    @classmethod

    def validate_scores(cls, v: float) -> float:

        if not (0.0 <= v <= 100.0):

            raise ValueError("Score must be between 0.0 and 100.0")

        return v



    def model_copy(self, *, update=None, deep=False):

        copied = super().model_copy(update=update, deep=deep)

        if update is not None:

            return self.__class__.model_validate(copied.model_dump())

        return copied





import uuid

from typing import List, Optional, Union



class ResumeOptimizationRequest(BaseModel):

    """Parameters to initiate an autonomous resume optimization process."""

    candidate_profile_id: Optional[Union[uuid.UUID, int, str]] = Field(

        default=None,

        description="Reference ID to the CandidateProfile record."

    )

    job_profile_id: Optional[Union[uuid.UUID, int, str]] = Field(

        default=None,

        description="Reference ID to the JobProfile record."

    )

    job_analysis_id: Optional[uuid.UUID] = Field(

        default=None,

        description="Backward compatibility job analysis ID."

    )

    tone: str = Field(

        default="Professional",

        description="Desired tone of the tailored content (e.g. Professional, Bold, Technical)."

    )

    focus_skills: List[str] = Field(

        default_factory=list,

        description="Specific skills the candidate wishes to emphasize."

    )



    @field_validator("candidate_profile_id", "job_profile_id")

    @classmethod

    def validate_ids(cls, v: Optional[Union[uuid.UUID, int, str]]) -> Optional[Union[uuid.UUID, int, str]]:

        if v is not None and isinstance(v, int) and v <= 0:

            raise ValueError("ID must be greater than 0")

        return v





class ResumeOptimizationResponse(BaseModel):

    """Response payload containing optimization status and changes delta."""

    run_id: str = Field(

        ...,

        description="Unique ID tracking the optimization run."

    )

    candidate_profile_id: Union[uuid.UUID, int, str] = Field(

        ...,

        description="Associated candidate profile record ID."

    )

    job_profile_id: Union[uuid.UUID, int, str] = Field(

        ...,

        description="Associated job description record ID."

    )

    status: OptimizationRunStatus = Field(

        ...,

        description="Current status of the optimization run."

    )

    initial_score: float = Field(

        ...,

        description="Baseline match score."

    )

    final_score: float = Field(

        ...,

        description="Optimized match score."

    )

    score_improvement: float = Field(

        ...,

        description="Difference between baseline and final scores."

    )

    changes: List[OptimizationDiff] = Field(

        default_factory=list,

        description="List of changes made during optimization."

    )

    history: OptimizationHistory = Field(

        ...,

        description="Full execution history log."

    )



    @field_validator("initial_score", "final_score")

    @classmethod

    def validate_scores(cls, v: float) -> float:

        if not (0.0 <= v <= 100.0):

            raise ValueError("Score must be between 0.0 and 100.0")

        return v



    def model_copy(self, *, update=None, deep=False):

        copied = super().model_copy(update=update, deep=deep)

        if update is not None:

            return self.__class__.model_validate(copied.model_dump())

        return copied
