"""Database query functions for reading omni-cortex SQLite databases."""

import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from models import Activity, FilterParams, Memory, MemoryStats, Session, TimelineEntry


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get a read-only connection to the database."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def parse_tags(tags_str: Optional[str]) -> list[str]:
    """Parse tags from JSON string."""
    if not tags_str:
        return []
    try:
        tags = json.loads(tags_str)
        return tags if isinstance(tags, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def get_memories(db_path: str, filters: FilterParams) -> list[Memory]:
    """Get memories with filtering, sorting, and pagination."""
    conn = get_connection(db_path)

    # Build query
    query = "SELECT * FROM memories WHERE 1=1"
    params: list = []

    if filters.memory_type:
        query += " AND type = ?"
        params.append(filters.memory_type)

    if filters.status:
        query += " AND status = ?"
        params.append(filters.status)

    if filters.min_importance is not None:
        query += " AND importance_score >= ?"
        params.append(filters.min_importance)

    if filters.max_importance is not None:
        query += " AND importance_score <= ?"
        params.append(filters.max_importance)

    if filters.search:
        query += " AND (content LIKE ? OR context LIKE ?)"
        search_term = f"%{filters.search}%"
        params.extend([search_term, search_term])

    # Sorting
    valid_sort_columns = ["created_at", "last_accessed", "importance_score", "access_count"]
    sort_by = filters.sort_by if filters.sort_by in valid_sort_columns else "last_accessed"
    sort_order = "DESC" if filters.sort_order.lower() == "desc" else "ASC"
    query += f" ORDER BY {sort_by} {sort_order}"

    # Pagination
    query += " LIMIT ? OFFSET ?"
    params.extend([filters.limit, filters.offset])

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()

    memories = []
    for row in rows:
        # Parse tags from JSON string
        tags = parse_tags(row["tags"])

        memories.append(
            Memory(
                id=row["id"],
                content=row["content"],
                context=row["context"],
                type=row["type"],
                status=row["status"] or "fresh",
                importance_score=int(row["importance_score"] or 50),
                access_count=row["access_count"] or 0,
                created_at=datetime.fromisoformat(row["created_at"]),
                last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
                tags=tags,
            )
        )

    conn.close()
    return memories


def get_memory_by_id(db_path: str, memory_id: str) -> Optional[Memory]:
    """Get a single memory by ID."""
    conn = get_connection(db_path)

    cursor = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    # Parse tags from JSON string
    tags = parse_tags(row["tags"])

    memory = Memory(
        id=row["id"],
        content=row["content"],
        context=row["context"],
        type=row["type"],
        status=row["status"] or "fresh",
        importance_score=int(row["importance_score"] or 50),
        access_count=row["access_count"] or 0,
        created_at=datetime.fromisoformat(row["created_at"]),
        last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
        tags=tags,
    )

    conn.close()
    return memory


def get_memory_stats(db_path: str) -> MemoryStats:
    """Get statistics about memories in the database."""
    conn = get_connection(db_path)

    # Total count
    total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    # By type
    type_cursor = conn.execute("SELECT type, COUNT(*) as count FROM memories GROUP BY type")
    by_type = {row["type"]: row["count"] for row in type_cursor.fetchall()}

    # By status
    status_cursor = conn.execute("SELECT status, COUNT(*) as count FROM memories GROUP BY status")
    by_status = {(row["status"] or "fresh"): row["count"] for row in status_cursor.fetchall()}

    # Average importance
    avg_cursor = conn.execute("SELECT AVG(importance_score) FROM memories")
    avg_importance = avg_cursor.fetchone()[0] or 0.0

    # Total access count
    access_cursor = conn.execute("SELECT SUM(access_count) FROM memories")
    total_access = access_cursor.fetchone()[0] or 0

    # Tags with counts - extract from JSON column
    tags_cursor = conn.execute("SELECT tags FROM memories WHERE tags IS NOT NULL AND tags != ''")
    tag_counter: Counter = Counter()
    for row in tags_cursor.fetchall():
        tags = parse_tags(row["tags"])
        tag_counter.update(tags)

    tags = [{"name": name, "count": count} for name, count in tag_counter.most_common(50)]

    conn.close()

    return MemoryStats(
        total_count=total,
        by_type=by_type,
        by_status=by_status,
        avg_importance=round(avg_importance, 1),
        total_access_count=total_access,
        tags=tags,
    )


def get_activities(
    db_path: str,
    event_type: Optional[str] = None,
    tool_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Activity]:
    """Get activity log entries."""
    conn = get_connection(db_path)

    query = "SELECT * FROM activities WHERE 1=1"
    params: list = []

    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)

    if tool_name:
        query += " AND tool_name = ?"
        params.append(tool_name)

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = conn.execute(query, params)
    activities = []

    for row in cursor.fetchall():
        activities.append(
            Activity(
                id=row["id"],
                session_id=row["session_id"],
                event_type=row["event_type"],
                tool_name=row["tool_name"],
                tool_input=row["tool_input"],
                tool_output=row["tool_output"],
                success=bool(row["success"]),
                error_message=row["error_message"],
                duration_ms=row["duration_ms"],
                file_path=row["file_path"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
            )
        )

    conn.close()
    return activities


def get_timeline(
    db_path: str,
    hours: int = 24,
    include_memories: bool = True,
    include_activities: bool = True,
) -> list[TimelineEntry]:
    """Get a timeline of memories and activities."""
    conn = get_connection(db_path)
    since = datetime.now() - timedelta(hours=hours)
    since_str = since.isoformat()

    entries: list[TimelineEntry] = []

    if include_memories:
        cursor = conn.execute(
            "SELECT * FROM memories WHERE created_at >= ? ORDER BY created_at DESC",
            (since_str,),
        )
        for row in cursor.fetchall():
            entries.append(
                TimelineEntry(
                    timestamp=datetime.fromisoformat(row["created_at"]),
                    entry_type="memory",
                    data={
                        "id": row["id"],
                        "content": row["content"][:200] + "..." if len(row["content"]) > 200 else row["content"],
                        "type": row["type"],
                        "importance": row["importance_score"],
                    },
                )
            )

    if include_activities:
        cursor = conn.execute(
            "SELECT * FROM activities WHERE timestamp >= ? ORDER BY timestamp DESC",
            (since_str,),
        )
        for row in cursor.fetchall():
            entries.append(
                TimelineEntry(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    entry_type="activity",
                    data={
                        "id": row["id"],
                        "event_type": row["event_type"],
                        "tool_name": row["tool_name"],
                        "success": bool(row["success"]),
                        "duration_ms": row["duration_ms"],
                    },
                )
            )

    # Sort by timestamp descending
    entries.sort(key=lambda e: e.timestamp, reverse=True)

    conn.close()
    return entries


def get_sessions(db_path: str, limit: int = 20) -> list[Session]:
    """Get recent sessions."""
    conn = get_connection(db_path)

    cursor = conn.execute(
        """
        SELECT s.*, COUNT(a.id) as activity_count
        FROM sessions s
        LEFT JOIN activities a ON s.id = a.session_id
        GROUP BY s.id
        ORDER BY s.started_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    sessions = []
    for row in cursor.fetchall():
        sessions.append(
            Session(
                id=row["id"],
                project_path=row["project_path"],
                started_at=datetime.fromisoformat(row["started_at"]),
                ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
                summary=row["summary"],
                activity_count=row["activity_count"],
            )
        )

    conn.close()
    return sessions


def get_all_tags(db_path: str) -> list[dict]:
    """Get all tags with their usage counts."""
    conn = get_connection(db_path)

    # Extract tags from JSON column
    cursor = conn.execute("SELECT tags FROM memories WHERE tags IS NOT NULL AND tags != ''")
    tag_counter: Counter = Counter()
    for row in cursor.fetchall():
        tags = parse_tags(row["tags"])
        tag_counter.update(tags)

    tags = [{"name": name, "count": count} for name, count in tag_counter.most_common()]

    conn.close()
    return tags


def get_type_distribution(db_path: str) -> dict[str, int]:
    """Get memory type distribution."""
    conn = get_connection(db_path)

    cursor = conn.execute("SELECT type, COUNT(*) as count FROM memories GROUP BY type")
    distribution = {row["type"]: row["count"] for row in cursor.fetchall()}

    conn.close()
    return distribution


def search_memories(db_path: str, query: str, limit: int = 20) -> list[Memory]:
    """Search memories using FTS if available, otherwise LIKE."""
    conn = get_connection(db_path)

    # Check if FTS table exists
    fts_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='memories_fts'"
    ).fetchone()

    if fts_check:
        # Use FTS search
        cursor = conn.execute(
            """
            SELECT m.* FROM memories m
            JOIN memories_fts fts ON m.id = fts.id
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        )
    else:
        # Fallback to LIKE
        search_term = f"%{query}%"
        cursor = conn.execute(
            """
            SELECT * FROM memories
            WHERE content LIKE ? OR context LIKE ?
            ORDER BY importance_score DESC
            LIMIT ?
            """,
            (search_term, search_term, limit),
        )

    memories = []
    for row in cursor.fetchall():
        # Parse tags from JSON string
        tags = parse_tags(row["tags"])

        memories.append(
            Memory(
                id=row["id"],
                content=row["content"],
                context=row["context"],
                type=row["type"],
                status=row["status"] or "fresh",
                importance_score=int(row["importance_score"] or 50),
                access_count=row["access_count"] or 0,
                created_at=datetime.fromisoformat(row["created_at"]),
                last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
                tags=tags,
            )
        )

    conn.close()
    return memories
