"""State management for ADW workflows."""

import json
import os
from typing import Optional

from .data_types import ADWStateData, ADWPhase


class ADWState:
    """Container for ADW workflow state with file persistence."""

    STATE_FILENAME = "adw_state.json"

    def __init__(self, adw_id: str):
        self.adw_id = adw_id
        self.data = ADWStateData(adw_id=adw_id)

    def get_agents_dir(self) -> str:
        """Get path to agents directory for this ADW."""
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return os.path.join(project_root, "agents", self.adw_id)

    def get_state_path(self) -> str:
        """Get path to state file."""
        return os.path.join(self.get_agents_dir(), self.STATE_FILENAME)

    def get_screenshot_dir(self, phase: str) -> str:
        """Get screenshot directory for a phase."""
        if phase == "validate":
            return os.path.join(self.get_agents_dir(), "validator", "screenshots")
        elif phase == "review":
            return os.path.join(self.get_agents_dir(), "reviewer", "review_img")
        return os.path.join(self.get_agents_dir(), phase, "screenshots")

    def get_output_dir(self, agent_name: str) -> str:
        """Get output directory for an agent."""
        return os.path.join(self.get_agents_dir(), agent_name)

    def update(self, **kwargs) -> None:
        """Update state with new values."""
        for key, value in kwargs.items():
            if hasattr(self.data, key):
                setattr(self.data, key, value)

    def mark_phase_complete(self, phase: ADWPhase) -> None:
        """Mark a phase as completed."""
        if phase not in self.data.phases_completed:
            self.data.phases_completed.append(phase)
        self.data.current_phase = None

    def add_screenshot(self, path: str) -> None:
        """Add a screenshot path to the state."""
        if path not in self.data.screenshots:
            self.data.screenshots.append(path)

    def add_error(self, error: str) -> None:
        """Add an error to the state."""
        self.data.errors.append(error)

    def save(self) -> None:
        """Save state to file."""
        state_path = self.get_state_path()
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, "w") as f:
            json.dump(self.data.model_dump(mode="json"), f, indent=2, default=str)

    @classmethod
    def load(cls, adw_id: str) -> Optional["ADWState"]:
        """Load state from file if exists."""
        state = cls(adw_id)
        state_path = state.get_state_path()
        if os.path.exists(state_path):
            with open(state_path, "r") as f:
                data = json.load(f)
            state.data = ADWStateData(**data)
            return state
        return None

    @classmethod
    def load_or_create(cls, adw_id: str) -> "ADWState":
        """Load existing state or create new."""
        existing = cls.load(adw_id)
        if existing:
            return existing
        return cls(adw_id)
