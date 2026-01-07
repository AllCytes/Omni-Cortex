"""Output formatting utilities for Omni Cortex."""

import json
from typing import Any, Optional
from datetime import datetime

from .timestamps import format_relative_time


def format_memory_markdown(memory: dict[str, Any]) -> str:
    """Format a memory as markdown.

    Args:
        memory: Memory dictionary

    Returns:
        Markdown formatted string
    """
    lines = []

    # Header with ID and type
    mem_type = memory.get("type", "general")
    lines.append(f"## [{mem_type}] {memory.get('id', 'unknown')}")
    lines.append("")

    # Content
    content = memory.get("content", "")
    lines.append(content)
    lines.append("")

    # Metadata
    lines.append("---")

    # Tags
    tags = memory.get("tags")
    if tags:
        if isinstance(tags, str):
            tags = json.loads(tags)
        if tags:
            lines.append(f"**Tags:** {', '.join(tags)}")

    # Context
    context = memory.get("context")
    if context:
        lines.append(f"**Context:** {context}")

    # Timestamps
    created = memory.get("created_at")
    if created:
        lines.append(f"**Created:** {format_relative_time(created)}")

    accessed = memory.get("last_accessed")
    if accessed:
        lines.append(f"**Last accessed:** {format_relative_time(accessed)}")

    # Importance
    importance = memory.get("importance_score", 50)
    lines.append(f"**Importance:** {importance:.0f}/100")

    # Status
    status = memory.get("status", "fresh")
    lines.append(f"**Status:** {status}")

    return "\n".join(lines)


def format_memories_list_markdown(memories: list[dict[str, Any]], total: int = 0) -> str:
    """Format a list of memories as markdown.

    Args:
        memories: List of memory dictionaries
        total: Total count (for pagination info)

    Returns:
        Markdown formatted string
    """
    if not memories:
        return "No memories found."

    lines = []
    lines.append(f"# Memories ({len(memories)}" + (f" of {total})" if total > len(memories) else ")"))
    lines.append("")

    for memory in memories:
        lines.append(format_memory_markdown(memory))
        lines.append("")

    return "\n".join(lines)


def format_activity_markdown(activity: dict[str, Any]) -> str:
    """Format an activity as markdown.

    Args:
        activity: Activity dictionary

    Returns:
        Markdown formatted string
    """
    lines = []

    timestamp = activity.get("timestamp", "")
    event_type = activity.get("event_type", "")
    tool_name = activity.get("tool_name", "")

    # Header
    header = f"**{event_type}**"
    if tool_name:
        header += f": `{tool_name}`"
    lines.append(header)

    lines.append(f"  - Time: {format_relative_time(timestamp)}")

    # Success/Error
    success = activity.get("success", 1)
    if not success:
        error = activity.get("error_message", "Unknown error")
        lines.append(f"  - Status: Failed - {error}")
    elif activity.get("duration_ms"):
        lines.append(f"  - Duration: {activity['duration_ms']}ms")

    return "\n".join(lines)


def format_timeline_markdown(
    activities: list[dict[str, Any]],
    memories: list[dict[str, Any]],
    group_by: str = "hour"
) -> str:
    """Format a timeline as markdown.

    Args:
        activities: List of activity dictionaries
        memories: List of memory dictionaries
        group_by: How to group items (hour, day, session)

    Returns:
        Markdown formatted string
    """
    lines = []
    lines.append("# Timeline")
    lines.append("")

    # Combine and sort by timestamp
    items = []
    for act in activities:
        items.append({
            "type": "activity",
            "timestamp": act.get("timestamp"),
            "data": act
        })
    for mem in memories:
        items.append({
            "type": "memory",
            "timestamp": mem.get("created_at"),
            "data": mem
        })

    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    if not items:
        return "# Timeline\n\nNo items found."

    for item in items:
        if item["type"] == "activity":
            lines.append(format_activity_markdown(item["data"]))
        else:
            mem = item["data"]
            lines.append(f"**Memory created**: [{mem.get('type')}] {mem.get('id')}")
            content = mem.get("content", "")[:100]
            lines.append(f"  > {content}...")
        lines.append("")

    return "\n".join(lines)


def format_session_context_markdown(
    sessions: list[dict[str, Any]],
    learnings: list[str],
    decisions: list[str],
    errors: list[str]
) -> str:
    """Format session context as markdown for continuity.

    Args:
        sessions: Recent sessions
        learnings: Key learnings
        decisions: Key decisions
        errors: Key errors encountered

    Returns:
        Markdown formatted context string
    """
    lines = []
    lines.append("# Session Context")
    lines.append("")

    if sessions:
        last = sessions[0]
        ended = last.get("ended_at")
        if ended:
            lines.append(f"Last session ended {format_relative_time(ended)}")
            lines.append("")

    if learnings:
        lines.append("## Key Learnings")
        for learning in learnings[:5]:
            lines.append(f"- {learning}")
        lines.append("")

    if decisions:
        lines.append("## Key Decisions")
        for decision in decisions[:5]:
            lines.append(f"- {decision}")
        lines.append("")

    if errors:
        lines.append("## Errors Encountered")
        for error in errors[:5]:
            lines.append(f"- {error}")
        lines.append("")

    return "\n".join(lines)
