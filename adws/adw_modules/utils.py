"""Utilities for ADW system."""

import secrets
import os
from datetime import datetime


def generate_adw_id() -> str:
    """Generate unique 8-character ADW ID."""
    return secrets.token_hex(4)


def get_project_root() -> str:
    """Get project root directory."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def format_timestamp() -> str:
    """Get formatted timestamp for filenames."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def ensure_directory(path: str) -> str:
    """Ensure directory exists, return path."""
    os.makedirs(path, exist_ok=True)
    return path


def get_spec_dir() -> str:
    """Get the specs directory path."""
    return os.path.join(get_project_root(), "specs")


def get_agents_dir() -> str:
    """Get the agents directory path."""
    return os.path.join(get_project_root(), "agents")
