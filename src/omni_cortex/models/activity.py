"""Activity model and CRUD operations."""

import json
import sqlite3
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict

from ..utils.ids import generate_activity_id
from ..utils.timestamps import now_iso
from ..utils.truncation import truncate_json


class ActivityCreate(BaseModel):
    """Input model for creating an activity."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    event_type: str = Field(
        ..., description="Event type: pre_tool_use, post_tool_use, decision, observation"
    )
    tool_name: Optional[str] = Field(None, description="Tool name if applicable")
    tool_input: Optional[str] = Field(None, description="Tool input (JSON)")
    tool_output: Optional[str] = Field(None, description="Tool output (JSON)")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds", ge=0)
    success: bool = Field(True, description="Whether the operation succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    file_path: Optional[str] = Field(None, description="File path if relevant")
    agent_id: Optional[str] = Field(None, description="Agent ID")


class Activity(BaseModel):
    """Full activity model from database."""

    id: str
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    timestamp: str
    event_type: str
    tool_name: Optional[str] = None
    tool_input: Optional[str] = None
    tool_output: Optional[str] = None
    duration_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    project_path: Optional[str] = None
    file_path: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


def create_activity(
    conn: sqlite3.Connection,
    data: ActivityCreate,
    session_id: Optional[str] = None,
    project_path: Optional[str] = None,
) -> Activity:
    """Create a new activity in the database.

    Args:
        conn: Database connection
        data: Activity creation data
        session_id: Current session ID
        project_path: Current project path

    Returns:
        Created activity object
    """
    activity_id = generate_activity_id()
    timestamp = now_iso()

    # Truncate large inputs/outputs
    tool_input = data.tool_input
    if tool_input and len(tool_input) > 10000:
        tool_input = truncate_json(tool_input, 10000)

    tool_output = data.tool_output
    if tool_output and len(tool_output) > 10000:
        tool_output = truncate_json(tool_output, 10000)

    cursor = conn.cursor()

    # Upsert agent BEFORE inserting activity (foreign key constraint)
    if data.agent_id:
        cursor.execute(
            """
            INSERT INTO agents (id, type, first_seen, last_seen, total_activities)
            VALUES (?, 'main', ?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET
                last_seen = ?,
                total_activities = total_activities + 1
            """,
            (data.agent_id, timestamp, timestamp, timestamp),
        )

    cursor.execute(
        """
        INSERT INTO activities (
            id, session_id, agent_id, timestamp, event_type,
            tool_name, tool_input, tool_output, duration_ms,
            success, error_message, project_path, file_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            activity_id,
            session_id,
            data.agent_id,
            timestamp,
            data.event_type,
            data.tool_name,
            tool_input,
            tool_output,
            data.duration_ms,
            1 if data.success else 0,
            data.error_message,
            project_path,
            data.file_path,
        ),
    )

    conn.commit()

    return Activity(
        id=activity_id,
        session_id=session_id,
        agent_id=data.agent_id,
        timestamp=timestamp,
        event_type=data.event_type,
        tool_name=data.tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        duration_ms=data.duration_ms,
        success=data.success,
        error_message=data.error_message,
        project_path=project_path,
        file_path=data.file_path,
    )


def get_activity(conn: sqlite3.Connection, activity_id: str) -> Optional[Activity]:
    """Get an activity by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
    row = cursor.fetchone()
    return _row_to_activity(row) if row else None


def get_activities(
    conn: sqlite3.Connection,
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    event_type: Optional[str] = None,
    tool_name: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Activity], int]:
    """Get activities with filters.

    Returns:
        Tuple of (activities list, total count)
    """
    where_clauses = []
    params: list[Any] = []

    if session_id:
        where_clauses.append("session_id = ?")
        params.append(session_id)

    if agent_id:
        where_clauses.append("agent_id = ?")
        params.append(agent_id)

    if event_type:
        where_clauses.append("event_type = ?")
        params.append(event_type)

    if tool_name:
        where_clauses.append("tool_name = ?")
        params.append(tool_name)

    if since:
        where_clauses.append("timestamp >= ?")
        params.append(since)

    if until:
        where_clauses.append("timestamp <= ?")
        params.append(until)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    cursor = conn.cursor()

    # Get total count
    cursor.execute(f"SELECT COUNT(*) FROM activities {where_sql}", params)
    total = cursor.fetchone()[0]

    # Get page
    params_page = params + [limit, offset]
    cursor.execute(
        f"""
        SELECT * FROM activities {where_sql}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
        """,
        params_page,
    )

    activities = [_row_to_activity(row) for row in cursor.fetchall()]
    return activities, total


def _row_to_activity(row: sqlite3.Row) -> Activity:
    """Convert database row to Activity object."""
    metadata = row["metadata"]
    if metadata and isinstance(metadata, str):
        metadata = json.loads(metadata)

    return Activity(
        id=row["id"],
        session_id=row["session_id"],
        agent_id=row["agent_id"],
        timestamp=row["timestamp"],
        event_type=row["event_type"],
        tool_name=row["tool_name"],
        tool_input=row["tool_input"],
        tool_output=row["tool_output"],
        duration_ms=row["duration_ms"],
        success=bool(row["success"]),
        error_message=row["error_message"],
        project_path=row["project_path"],
        file_path=row["file_path"],
        metadata=metadata,
    )
