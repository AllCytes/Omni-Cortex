"""ADW State management with JSON persistence."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .data_types import ADWPhase, ADWStateData, PhaseResult
from .utils import get_agents_dir


class ADWState:
    """Manages ADW state with JSON file persistence.

    State is stored in: agents/{adw_id}/adw_state.json
    """

    def __init__(self, adw_id: str, task_description: str = "", project_path: str = ""):
        """Initialize or load ADW state."""
        self.adw_id = adw_id
        self.state_file = get_agents_dir(adw_id) / "adw_state.json"

        if self.state_file.exists():
            self.data = self._load()
        else:
            self.data = ADWStateData(
                adw_id=adw_id,
                task_description=task_description,
                project_path=project_path or str(Path.cwd()),
            )
            self._save()

    def _load(self) -> ADWStateData:
        """Load state from JSON file."""
        with open(self.state_file, "r") as f:
            data = json.load(f)
        return ADWStateData(**data)

    def _save(self) -> None:
        """Save state to JSON file."""
        with open(self.state_file, "w") as f:
            json.dump(self.data.model_dump(mode="json"), f, indent=2, default=str)

    def start_phase(self, phase: ADWPhase) -> None:
        """Mark a phase as started."""
        self.data.current_phase = phase
        self.data.status = "running"

        # Create phase result entry
        result = PhaseResult(
            phase=phase,
            success=False,
            started_at=datetime.now(),
        )
        self.data.phase_results.append(result)
        self._save()

    def complete_phase(
        self,
        phase: ADWPhase,
        success: bool,
        output_file: Optional[str] = None,
        error_message: Optional[str] = None,
        artifacts: Optional[list[str]] = None,
    ) -> None:
        """Mark a phase as completed."""
        # Find and update the phase result
        for result in self.data.phase_results:
            if result.phase == phase and result.completed_at is None:
                result.success = success
                result.completed_at = datetime.now()
                result.output_file = output_file
                result.error_message = error_message
                if artifacts:
                    result.artifacts = artifacts
                break

        if success:
            self.data.completed_phases.append(phase)

        self.data.current_phase = None
        self._save()

    def set_spec_file(self, spec_file: str) -> None:
        """Set the spec file path."""
        self.data.spec_file = spec_file
        self._save()

    def mark_completed(self) -> None:
        """Mark the entire ADW as completed."""
        self.data.status = "completed"
        self._save()

    def mark_failed(self, error: str) -> None:
        """Mark the entire ADW as failed."""
        self.data.status = "failed"
        # Update current phase result if exists
        if self.data.current_phase:
            self.complete_phase(
                self.data.current_phase,
                success=False,
                error_message=error,
            )
        self._save()

    def get_phase_result(self, phase: ADWPhase) -> Optional[PhaseResult]:
        """Get the result of a specific phase."""
        for result in self.data.phase_results:
            if result.phase == phase:
                return result
        return None

    def is_phase_completed(self, phase: ADWPhase) -> bool:
        """Check if a phase has been completed successfully."""
        return phase in self.data.completed_phases

    @property
    def task(self) -> str:
        """Get the task description."""
        return self.data.task_description

    @property
    def spec(self) -> Optional[str]:
        """Get the spec file path."""
        return self.data.spec_file
