"""Test fixtures for Omni Cortex."""

import gc
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_dir = Path(tmpdir) / ".omni-cortex"
        db_dir.mkdir(parents=True)
        db_path = db_dir / "cortex.db"
        yield db_path

        # Ensure connections are closed before cleanup
        from omni_cortex.database.connection import close_all_connections
        close_all_connections()
        gc.collect()


@pytest.fixture
def mock_project_env(temp_db_path):
    """Set up environment variables for testing."""
    original_project = os.environ.get("CLAUDE_PROJECT_DIR")
    original_session = os.environ.get("CLAUDE_SESSION_ID")

    os.environ["CLAUDE_PROJECT_DIR"] = str(temp_db_path.parent.parent)
    os.environ["CLAUDE_SESSION_ID"] = "test_session_123"

    yield

    # Restore original values
    if original_project:
        os.environ["CLAUDE_PROJECT_DIR"] = original_project
    elif "CLAUDE_PROJECT_DIR" in os.environ:
        del os.environ["CLAUDE_PROJECT_DIR"]

    if original_session:
        os.environ["CLAUDE_SESSION_ID"] = original_session
    elif "CLAUDE_SESSION_ID" in os.environ:
        del os.environ["CLAUDE_SESSION_ID"]
