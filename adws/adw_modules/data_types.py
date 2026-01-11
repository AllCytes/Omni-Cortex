"""Pydantic models for ADW state and events."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ADWPhase(str, Enum):
    """ADW execution phases for the complete 9-phase SDLC workflow.

    Standard order: Plan → Build → Validate → Security → Security-Fix →
                   Review → Retrospective → Apply-Learnings → Release
    """
    PLAN = "plan"
    BUILD = "build"
    VALIDATE = "validate"
    SECURITY = "security"
    SECURITY_FIX = "security-fix"
    REVIEW = "review"
    RETROSPECTIVE = "retrospective"
    APPLY_LEARNINGS = "apply-learnings"
    RELEASE = "release"


class PhaseResult(BaseModel):
    """Result of a phase execution."""
    phase: ADWPhase
    success: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    artifacts: list[str] = Field(default_factory=list)


class ADWStateData(BaseModel):
    """Complete state of an ADW execution."""
    adw_id: str
    task_description: str
    created_at: datetime = Field(default_factory=datetime.now)
    current_phase: Optional[ADWPhase] = None
    completed_phases: list[ADWPhase] = Field(default_factory=list)
    phase_results: list[PhaseResult] = Field(default_factory=list)
    spec_file: Optional[str] = None
    project_path: str = ""
    status: str = "pending"  # pending, running, completed, failed


class ReviewIssue(BaseModel):
    """An issue found during review."""
    severity: str  # critical, major, minor, suggestion
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: str = ""
