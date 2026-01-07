"""Tests for activity operations."""

import pytest
import json

from omni_cortex.database.connection import init_database, close_connection
from omni_cortex.models.activity import (
    ActivityCreate,
    create_activity,
    get_activity,
    get_activities,
)
from omni_cortex.models.session import SessionCreate, create_session


def test_create_activity(temp_db_path):
    """Test creating an activity."""
    conn = init_database(temp_db_path)

    # Create session first to satisfy foreign key
    session = create_session(conn, SessionCreate(
        session_id="sess_test123",
        project_path="/test/project",
    ))

    data = ActivityCreate(
        event_type="post_tool_use",
        tool_name="Read",
        tool_input='{"file_path": "/test/file.py"}',
        success=True,
        duration_ms=150,
    )

    activity = create_activity(
        conn,
        data,
        session_id=session.id,
        project_path="/test/project",
    )

    assert activity.id.startswith("act_")
    assert activity.event_type == "post_tool_use"
    assert activity.tool_name == "Read"
    assert activity.success is True
    assert activity.duration_ms == 150
    assert activity.session_id == session.id
    assert activity.project_path == "/test/project"

    close_connection(temp_db_path)


def test_create_failed_activity(temp_db_path):
    """Test creating an activity with error."""
    conn = init_database(temp_db_path)

    data = ActivityCreate(
        event_type="post_tool_use",
        tool_name="Write",
        success=False,
        error_message="Permission denied",
    )

    activity = create_activity(conn, data)

    assert activity.success is False
    assert activity.error_message == "Permission denied"

    close_connection(temp_db_path)


def test_get_activity(temp_db_path):
    """Test retrieving an activity by ID."""
    conn = init_database(temp_db_path)

    data = ActivityCreate(
        event_type="decision",
        tool_name="Edit",
    )
    created = create_activity(conn, data)

    retrieved = get_activity(conn, created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.event_type == "decision"
    assert retrieved.tool_name == "Edit"

    close_connection(temp_db_path)


def test_get_activities_empty(temp_db_path):
    """Test getting activities when none exist."""
    conn = init_database(temp_db_path)

    activities, total = get_activities(conn)

    assert activities == []
    assert total == 0

    close_connection(temp_db_path)


def test_get_activities_with_filters(temp_db_path):
    """Test getting activities with various filters."""
    conn = init_database(temp_db_path)

    # Create sessions first
    sess1 = create_session(conn, SessionCreate(
        session_id="sess_1",
        project_path="/test",
    ))
    sess2 = create_session(conn, SessionCreate(
        session_id="sess_2",
        project_path="/test",
    ))

    # Create activities with different properties
    for i in range(5):
        create_activity(conn, ActivityCreate(
            event_type="post_tool_use",
            tool_name="Read",
        ), session_id=sess1.id)

    for i in range(3):
        create_activity(conn, ActivityCreate(
            event_type="post_tool_use",
            tool_name="Write",
        ), session_id=sess2.id)

    # Filter by tool name
    activities, total = get_activities(conn, tool_name="Read")
    assert total == 5
    assert all(a.tool_name == "Read" for a in activities)

    # Filter by session
    activities, total = get_activities(conn, session_id=sess2.id)
    assert total == 3
    assert all(a.session_id == sess2.id for a in activities)

    # Filter by event type
    activities, total = get_activities(conn, event_type="post_tool_use")
    assert total == 8

    close_connection(temp_db_path)


def test_get_activities_pagination(temp_db_path):
    """Test activity pagination."""
    conn = init_database(temp_db_path)

    # Create 15 activities
    for i in range(15):
        create_activity(conn, ActivityCreate(
            event_type="post_tool_use",
            tool_name=f"Tool{i}",
        ))

    # Get first page
    activities, total = get_activities(conn, limit=10)
    assert total == 15
    assert len(activities) == 10

    # Get second page
    activities, total = get_activities(conn, limit=10, offset=10)
    assert total == 15
    assert len(activities) == 5

    close_connection(temp_db_path)


def test_activity_truncation(temp_db_path):
    """Test that large inputs/outputs are truncated."""
    conn = init_database(temp_db_path)

    # Create activity with very large input
    large_input = json.dumps({"data": "x" * 20000})

    data = ActivityCreate(
        event_type="post_tool_use",
        tool_name="Read",
        tool_input=large_input,
    )

    activity = create_activity(conn, data)

    # Should be truncated to ~10000 chars
    assert len(activity.tool_input) <= 11000

    close_connection(temp_db_path)


def test_agent_tracking(temp_db_path):
    """Test that agent usage is tracked."""
    conn = init_database(temp_db_path)

    agent_id = "agent_test123"

    # Create activities for the same agent
    for i in range(3):
        create_activity(conn, ActivityCreate(
            event_type="post_tool_use",
            tool_name="Read",
            agent_id=agent_id,
        ))

    # Verify agent was tracked
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
    row = cursor.fetchone()

    assert row is not None
    assert row["id"] == agent_id
    assert row["total_activities"] == 3

    close_connection(temp_db_path)
