"""Tests for session operations."""

import pytest
import time

from omni_cortex.database.connection import init_database, close_connection
from omni_cortex.models.session import (
    SessionCreate,
    create_session,
    get_session,
    end_session,
    get_recent_sessions,
    get_session_summary,
)
from omni_cortex.models.activity import ActivityCreate, create_activity
from omni_cortex.models.memory import MemoryCreate, create_memory


def test_create_session(temp_db_path):
    """Test creating a session."""
    conn = init_database(temp_db_path)

    data = SessionCreate(
        session_id="sess_test123",
        project_path="/test/project",
    )

    session = create_session(conn, data)

    assert session.id == "sess_test123"
    assert session.project_path == "/test/project"
    assert session.started_at is not None
    assert session.ended_at is None

    close_connection(temp_db_path)


def test_create_session_auto_id(temp_db_path):
    """Test session ID is auto-generated if not provided."""
    conn = init_database(temp_db_path)

    data = SessionCreate(
        project_path="/test/project",
    )

    session = create_session(conn, data)

    assert session.id.startswith("sess_")
    assert len(session.id) > 5

    close_connection(temp_db_path)


def test_get_session(temp_db_path):
    """Test retrieving a session by ID."""
    conn = init_database(temp_db_path)

    data = SessionCreate(
        session_id="sess_get_test",
        project_path="/test",
    )
    created = create_session(conn, data)

    retrieved = get_session(conn, created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.project_path == created.project_path

    close_connection(temp_db_path)


def test_get_session_not_found(temp_db_path):
    """Test retrieving non-existent session."""
    conn = init_database(temp_db_path)

    retrieved = get_session(conn, "sess_nonexistent")

    assert retrieved is None

    close_connection(temp_db_path)


def test_end_session(temp_db_path):
    """Test ending a session."""
    conn = init_database(temp_db_path)

    session = create_session(conn, SessionCreate(
        session_id="sess_end_test",
        project_path="/test",
    ))

    # End the session
    ended = end_session(
        conn,
        session_id=session.id,
        summary="Test session completed",
        key_learnings=["Learned something useful"],
    )

    assert ended is not None
    assert ended.ended_at is not None
    assert ended.summary == "Test session completed"

    close_connection(temp_db_path)


def test_end_session_not_found(temp_db_path):
    """Test ending non-existent session."""
    conn = init_database(temp_db_path)

    result = end_session(conn, session_id="sess_nonexistent")

    assert result is None

    close_connection(temp_db_path)


def test_get_recent_sessions(temp_db_path):
    """Test getting recent sessions."""
    conn = init_database(temp_db_path)

    # Create multiple sessions
    for i in range(5):
        create_session(conn, SessionCreate(
            session_id=f"sess_recent_{i}",
            project_path="/test/project",
        ))
        time.sleep(0.01)  # Ensure different timestamps

    recent = get_recent_sessions(conn, project_path="/test/project", limit=3)

    assert len(recent) == 3
    # Most recent should be first
    assert recent[0].id == "sess_recent_4"

    close_connection(temp_db_path)


def test_get_recent_sessions_project_filter(temp_db_path):
    """Test filtering recent sessions by project."""
    conn = init_database(temp_db_path)

    # Create sessions for different projects
    create_session(conn, SessionCreate(
        session_id="sess_proj_a",
        project_path="/project/a",
    ))
    create_session(conn, SessionCreate(
        session_id="sess_proj_b",
        project_path="/project/b",
    ))

    # Filter by project
    recent = get_recent_sessions(conn, project_path="/project/a")

    assert len(recent) == 1
    assert recent[0].project_path == "/project/a"

    close_connection(temp_db_path)


def test_session_summary(temp_db_path):
    """Test session summary generation."""
    conn = init_database(temp_db_path)

    # Create session
    session = create_session(conn, SessionCreate(
        session_id="sess_summary_test",
        project_path="/test",
    ))

    # Add some activities
    for i in range(3):
        create_activity(conn, ActivityCreate(
            event_type="post_tool_use",
            tool_name="Read",
        ), session_id=session.id)

    # End session with learnings
    end_session(
        conn,
        session_id=session.id,
        key_learnings=["Learning 1", "Learning 2"],
    )

    # Get summary
    summary = get_session_summary(conn, session.id)

    assert summary is not None
    assert summary.session_id == session.id
    assert summary.total_activities == 3
    assert "Learning 1" in summary.key_learnings
    assert "Learning 2" in summary.key_learnings

    close_connection(temp_db_path)


def test_session_tracks_tools(temp_db_path):
    """Test that session summary tracks tool usage."""
    conn = init_database(temp_db_path)

    session = create_session(conn, SessionCreate(
        session_id="sess_tools_test",
        project_path="/test",
    ))

    # Add activities with different tools
    for _ in range(5):
        create_activity(conn, ActivityCreate(
            event_type="post_tool_use",
            tool_name="Read",
        ), session_id=session.id)

    for _ in range(3):
        create_activity(conn, ActivityCreate(
            event_type="post_tool_use",
            tool_name="Write",
        ), session_id=session.id)

    end_session(conn, session_id=session.id)

    summary = get_session_summary(conn, session.id)

    assert summary.tools_used is not None
    assert summary.tools_used.get("Read") == 5
    assert summary.tools_used.get("Write") == 3

    close_connection(temp_db_path)


def test_session_tracks_files(temp_db_path):
    """Test that session summary tracks files modified."""
    conn = init_database(temp_db_path)

    session = create_session(conn, SessionCreate(
        session_id="sess_files_test",
        project_path="/test",
    ))

    # Add activities with file paths
    create_activity(conn, ActivityCreate(
        event_type="post_tool_use",
        tool_name="Edit",
        file_path="/src/main.py",
    ), session_id=session.id)

    create_activity(conn, ActivityCreate(
        event_type="post_tool_use",
        tool_name="Edit",
        file_path="/src/utils.py",
    ), session_id=session.id)

    end_session(conn, session_id=session.id)

    summary = get_session_summary(conn, session.id)

    assert summary.files_modified is not None
    assert len(summary.files_modified) == 2
    assert "/src/main.py" in summary.files_modified

    close_connection(temp_db_path)


def test_session_tracks_errors(temp_db_path):
    """Test that session summary tracks errors."""
    conn = init_database(temp_db_path)

    session = create_session(conn, SessionCreate(
        session_id="sess_errors_test",
        project_path="/test",
    ))

    # Add failed activity
    create_activity(conn, ActivityCreate(
        event_type="post_tool_use",
        tool_name="Write",
        success=False,
        error_message="Permission denied",
    ), session_id=session.id)

    end_session(conn, session_id=session.id)

    summary = get_session_summary(conn, session.id)

    assert summary.key_errors is not None
    assert "Permission denied" in summary.key_errors

    close_connection(temp_db_path)


def test_session_tracks_memories(temp_db_path):
    """Test that session summary tracks memories created."""
    conn = init_database(temp_db_path)

    session = create_session(conn, SessionCreate(
        session_id="sess_memories_test",
        project_path="/test",
    ))

    # Create memories linked to session
    cursor = conn.cursor()
    for i in range(3):
        mem = create_memory(conn, MemoryCreate(
            content=f"Memory {i}",
        ))
        # Link memory to session
        cursor.execute(
            "UPDATE memories SET source_session_id = ? WHERE id = ?",
            (session.id, mem.id),
        )
    conn.commit()

    end_session(conn, session_id=session.id)

    summary = get_session_summary(conn, session.id)

    assert summary.total_memories_created == 3

    close_connection(temp_db_path)
