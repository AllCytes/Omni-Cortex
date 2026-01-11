"""Data types for Omni-Cortex ADW system."""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from enum import Enum


class RetryCode(str, Enum):
    """Reason codes for retry operations."""

    NONE = "none"
    CLAUDE_CODE_ERROR = "claude_code_error"
    TIMEOUT_ERROR = "timeout_error"
    EXECUTION_ERROR = "execution_error"


class ADWPhase(str, Enum):
    """Phases in the ADW workflow."""

    PLAN = "plan"
    BUILD = "build"
    VALIDATE = "validate"
    SECURITY = "security"
    REVIEW = "review"
    RETROSPECTIVE = "retrospective"
    RELEASE = "release"


class ReviewIssueSeverity(str, Enum):
    """Severity levels for review issues."""

    BLOCKER = "blocker"
    TECH_DEBT = "tech_debt"
    SKIPPABLE = "skippable"


class ADWStateData(BaseModel):
    """Persistent state for ADW workflow."""

    adw_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    spec_file: Optional[str] = None
    spec_request: Optional[str] = None
    branch_name: Optional[str] = None
    current_phase: Optional[ADWPhase] = None
    phases_completed: List[ADWPhase] = Field(default_factory=list)
    validation_passed: Optional[bool] = None
    security_passed: Optional[bool] = None
    review_passed: Optional[bool] = None
    screenshots: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class ReviewIssue(BaseModel):
    """Individual review issue."""

    issue_number: int
    description: str
    resolution: str
    severity: ReviewIssueSeverity
    screenshot_path: Optional[str] = None


class ReviewResult(BaseModel):
    """Result from review phase."""

    success: bool
    summary: str
    issues: List[ReviewIssue] = Field(default_factory=list)
    screenshots: List[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Result from validation phase."""

    overall_status: Literal["passed", "failed", "partial"]
    tests: List[dict] = Field(default_factory=list)
    screenshots: List[str] = Field(default_factory=list)
    issues: List[dict] = Field(default_factory=list)
