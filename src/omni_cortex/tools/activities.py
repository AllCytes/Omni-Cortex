"""Activity logging tools for Omni Cortex MCP."""

import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from mcp.server.fastmcp import FastMCP

from ..database.connection import init_database
from ..config import get_project_path, get_session_id
from ..models.activity import Activity, ActivityCreate, create_activity, get_activities
from ..models.memory import list_memories
from ..utils.formatting import format_activity_markdown, format_timeline_markdown
from ..utils.timestamps import now_iso, parse_iso


# === Input Models ===

class LogActivityInput(BaseModel):
    """Input for logging an activity."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    event_type: str = Field(
        ..., description="Event type: pre_tool_use, post_tool_use, decision, observation"
    )
    tool_name: Optional[str] = Field(None, description="Tool name if applicable")
    tool_input: Optional[str] = Field(None, description="Tool input (JSON string)")
    tool_output: Optional[str] = Field(None, description="Tool output (JSON string)")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds", ge=0)
    success: bool = Field(True, description="Whether the operation succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    file_path: Optional[str] = Field(None, description="Relevant file path")
    agent_id: Optional[str] = Field(None, description="Agent ID")


class GetActivitiesInput(BaseModel):
    """Input for getting activities."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    session_id: Optional[str] = Field(None, description="Filter by session ID")
    agent_id: Optional[str] = Field(None, description="Filter by agent ID")
    event_type: Optional[str] = Field(None, description="Filter by event type")
    tool_name: Optional[str] = Field(None, description="Filter by tool name")
    since: Optional[str] = Field(None, description="Start time (ISO 8601)")
    until: Optional[str] = Field(None, description="End time (ISO 8601)")
    limit: int = Field(50, description="Maximum results", ge=1, le=200)
    offset: int = Field(0, description="Pagination offset", ge=0)


class TimelineInput(BaseModel):
    """Input for getting timeline."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    hours: int = Field(24, description="Hours to look back", ge=1, le=168)
    include_activities: bool = Field(True, description="Include activities")
    include_memories: bool = Field(True, description="Include memories")
    group_by: str = Field("hour", description="Group by: hour, day, or session")


def register_activity_tools(mcp: FastMCP) -> None:
    """Register all activity tools with the MCP server."""

    @mcp.tool(
        name="cortex_log_activity",
        annotations={
            "title": "Log Activity",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def cortex_log_activity(params: LogActivityInput) -> str:
        """Log a tool call, decision, or observation.

        This tool records activities in the audit trail. Most activity logging
        is done automatically by hooks, but this tool allows manual logging.

        Args:
            params: LogActivityInput with event details

        Returns:
            Confirmation with activity ID
        """
        try:
            conn = init_database()
            project_path = str(get_project_path())
            session_id = get_session_id()

            activity_data = ActivityCreate(
                event_type=params.event_type,
                tool_name=params.tool_name,
                tool_input=params.tool_input,
                tool_output=params.tool_output,
                duration_ms=params.duration_ms,
                success=params.success,
                error_message=params.error_message,
                file_path=params.file_path,
                agent_id=params.agent_id,
            )

            activity = create_activity(
                conn,
                activity_data,
                session_id=session_id,
                project_path=project_path,
            )

            return (
                f"Logged: {activity.id}\n"
                f"Type: {activity.event_type}\n"
                f"Tool: {activity.tool_name or 'N/A'}\n"
                f"Success: {'Yes' if activity.success else 'No'}"
            )

        except Exception as e:
            return f"Error logging activity: {e}"

    @mcp.tool(
        name="cortex_get_activities",
        annotations={
            "title": "Get Activities",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_get_activities(params: GetActivitiesInput) -> str:
        """Query the activity log with filters.

        Args:
            params: GetActivitiesInput with filters and pagination

        Returns:
            Activities formatted as markdown
        """
        try:
            conn = init_database()

            activities, total = get_activities(
                conn,
                session_id=params.session_id,
                agent_id=params.agent_id,
                event_type=params.event_type,
                tool_name=params.tool_name,
                since=params.since,
                until=params.until,
                limit=params.limit,
                offset=params.offset,
            )

            if not activities:
                return "No activities found."

            lines = [f"# Activities ({len(activities)} of {total})", ""]

            for activity in activities:
                lines.append(format_activity_markdown(activity.model_dump()))
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return f"Error getting activities: {e}"

    @mcp.tool(
        name="cortex_get_timeline",
        annotations={
            "title": "Get Timeline",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def cortex_get_timeline(params: TimelineInput) -> str:
        """Get a timeline of activities and memories.

        This provides a chronological view of what happened in the project
        over the specified time period.

        Args:
            params: TimelineInput with time range and inclusion options

        Returns:
            Timeline formatted as markdown
        """
        try:
            conn = init_database()

            # Calculate time range
            now = datetime.now(timezone.utc)
            since = (now - timedelta(hours=params.hours)).isoformat()

            activities_list = []
            memories_list = []

            if params.include_activities:
                activities_result, _ = get_activities(
                    conn,
                    since=since,
                    limit=100,
                )
                activities_list = [a.model_dump() for a in activities_result]

            if params.include_memories:
                memories_result, _ = list_memories(
                    conn,
                    sort_by="created_at",
                    sort_order="desc",
                    limit=50,
                )
                # Filter to time range
                memories_list = [
                    m.model_dump()
                    for m in memories_result
                    if parse_iso(m.created_at) >= parse_iso(since)
                ]

            return format_timeline_markdown(
                activities_list,
                memories_list,
                group_by=params.group_by,
            )

        except Exception as e:
            return f"Error getting timeline: {e}"
