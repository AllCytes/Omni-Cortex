"""Utility functions for ADWs."""

import os
import secrets
from datetime import datetime
from pathlib import Path


def generate_adw_id() -> str:
    """Generate a unique ADW ID.

    Format: adw_{timestamp}_{random_hex}
    Example: adw_1704825600_a1b2c3d4
    """
    timestamp = int(datetime.now().timestamp())
    random_hex = secrets.token_hex(4)
    return f"adw_{timestamp}_{random_hex}"


def get_project_root() -> Path:
    """Get the project root directory.

    Walks up from current directory looking for markers like:
    - .git directory
    - pyproject.toml
    - package.json
    """
    current = Path.cwd()

    for path in [current] + list(current.parents):
        if (path / ".git").exists():
            return path
        if (path / "pyproject.toml").exists():
            return path
        if (path / "package.json").exists():
            return path

    return current


def get_agents_dir(adw_id: str) -> Path:
    """Get the agents directory for an ADW.

    Creates: agents/{adw_id}/
    """
    project_root = get_project_root()
    agents_dir = project_root / "agents" / adw_id
    agents_dir.mkdir(parents=True, exist_ok=True)
    return agents_dir


def get_phase_dir(adw_id: str, phase: str) -> Path:
    """Get the directory for a specific phase.

    Creates: agents/{adw_id}/{phase}/
    """
    phase_dir = get_agents_dir(adw_id) / phase
    phase_dir.mkdir(parents=True, exist_ok=True)
    return phase_dir


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"
