"""Database query functions for reading omni-cortex SQLite databases."""

import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from models import Activity, FilterParams, Memory, MemoryStats, MemoryUpdate, Session, TimelineEntry


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get a read-only connection to the database."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def get_write_connection(db_path: str) -> sqlite3.Connection:
    """Get a writable connection to the database."""
    conn = sqlite3.connect(db_path)
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
        # Parse timestamp - handle both with and without timezone
        ts_str = row["timestamp"]
        try:
            ts = datetime.fromisoformat(ts_str)
        except ValueError:
            # Fallback for edge cases
            ts = datetime.now()

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
                timestamp=ts,
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
        # Use FTS search - FTS5 uses rowid to match the memories table rowid
        # Escape special FTS5 characters and wrap in quotes for phrase search
        safe_query = query.replace('"', '""')
        try:
            cursor = conn.execute(
                """
                SELECT m.* FROM memories m
                JOIN memories_fts fts ON m.rowid = fts.rowid
                WHERE memories_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (f'"{safe_query}"', limit),
            )
        except sqlite3.OperationalError:
            # Fallback if FTS query fails
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


def update_memory(db_path: str, memory_id: str, updates: MemoryUpdate) -> Optional[Memory]:
    """Update a memory and return the updated record."""
    conn = get_write_connection(db_path)

    # Build update query dynamically based on provided fields
    update_fields = []
    params = []

    if updates.content is not None:
        update_fields.append("content = ?")
        params.append(updates.content)

    if updates.context is not None:
        update_fields.append("context = ?")
        params.append(updates.context)

    if updates.memory_type is not None:
        update_fields.append("type = ?")
        params.append(updates.memory_type)

    if updates.status is not None:
        update_fields.append("status = ?")
        params.append(updates.status)

    if updates.importance_score is not None:
        update_fields.append("importance_score = ?")
        params.append(updates.importance_score)

    if updates.tags is not None:
        update_fields.append("tags = ?")
        params.append(json.dumps(updates.tags))

    if not update_fields:
        conn.close()
        return get_memory_by_id(db_path, memory_id)

    # Add updated timestamp
    update_fields.append("last_accessed = ?")
    params.append(datetime.now().isoformat())

    # Add memory_id to params
    params.append(memory_id)

    query = f"UPDATE memories SET {', '.join(update_fields)} WHERE id = ?"
    cursor = conn.execute(query, params)
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        return None

    conn.close()
    return get_memory_by_id(db_path, memory_id)


def delete_memory(db_path: str, memory_id: str) -> bool:
    """Delete a memory by ID. Returns True if deleted, False if not found."""
    conn = get_write_connection(db_path)

    # Also delete related entries in memory_relationships
    conn.execute(
        "DELETE FROM memory_relationships WHERE source_id = ? OR target_id = ?",
        (memory_id, memory_id),
    )

    cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    conn.commit()

    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


# --- Stats Functions for Dashboard Charts ---


def get_activity_heatmap(db_path: str, days: int = 90) -> list[dict]:
    """Get activity counts grouped by day for heatmap visualization."""
    conn = get_connection(db_path)
    query = """
        SELECT date(timestamp) as date, COUNT(*) as count
        FROM activities
        WHERE timestamp >= date('now', ?)
        GROUP BY date(timestamp)
        ORDER BY date
    """
    cursor = conn.execute(query, (f'-{days} days',))
    result = [{"date": row["date"], "count": row["count"]} for row in cursor.fetchall()]
    conn.close()
    return result


def get_tool_usage(db_path: str, limit: int = 10) -> list[dict]:
    """Get tool usage statistics with success rates."""
    conn = get_connection(db_path)
    query = """
        SELECT
            tool_name,
            COUNT(*) as count,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
        FROM activities
        WHERE tool_name IS NOT NULL AND tool_name != ''
        GROUP BY tool_name
        ORDER BY count DESC
        LIMIT ?
    """
    cursor = conn.execute(query, (limit,))
    result = [
        {
            "tool_name": row["tool_name"],
            "count": row["count"],
            "success_rate": round(row["success_rate"], 2) if row["success_rate"] else 1.0,
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return result


def get_memory_growth(db_path: str, days: int = 30) -> list[dict]:
    """Get memory creation over time with cumulative totals."""
    conn = get_connection(db_path)
    query = """
        WITH daily_counts AS (
            SELECT date(created_at) as date, COUNT(*) as count
            FROM memories
            WHERE created_at >= date('now', ?)
            GROUP BY date(created_at)
        )
        SELECT
            date,
            count,
            SUM(count) OVER (ORDER BY date) as cumulative
        FROM daily_counts
        ORDER BY date
    """
    cursor = conn.execute(query, (f'-{days} days',))
    result = [
        {"date": row["date"], "count": row["count"], "cumulative": row["cumulative"]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return result


def get_recent_sessions(db_path: str, limit: int = 5) -> list[dict]:
    """Get recent sessions with activity counts and memory counts."""
    conn = get_connection(db_path)
    query = """
        SELECT
            s.id,
            s.project_path,
            s.started_at,
            s.ended_at,
            s.summary,
            COUNT(DISTINCT a.id) as activity_count
        FROM sessions s
        LEFT JOIN activities a ON a.session_id = s.id
        GROUP BY s.id
        ORDER BY s.started_at DESC
        LIMIT ?
    """
    cursor = conn.execute(query, (limit,))
    result = [
        {
            "id": row["id"],
            "project_path": row["project_path"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
            "summary": row["summary"],
            "activity_count": row["activity_count"],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return result


def bulk_update_memory_status(db_path: str, memory_ids: list[str], status: str) -> int:
    """Update status for multiple memories. Returns count updated."""
    if not memory_ids:
        return 0
    conn = get_write_connection(db_path)
    placeholders = ','.join('?' * len(memory_ids))
    query = f"UPDATE memories SET status = ?, last_accessed = datetime('now') WHERE id IN ({placeholders})"
    cursor = conn.execute(query, [status] + memory_ids)
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count


def get_memories_needing_review(db_path: str, days_threshold: int = 30, limit: int = 50) -> list[Memory]:
    """Get memories that haven't been accessed recently and may need review."""
    conn = get_connection(db_path)
    query = """
        SELECT * FROM memories
        WHERE last_accessed < date('now', ?)
           OR last_accessed IS NULL
        ORDER BY last_accessed ASC NULLS FIRST, importance_score DESC
        LIMIT ?
    """
    cursor = conn.execute(query, (f'-{days_threshold} days', limit))

    memories = []
    for row in cursor.fetchall():
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


def get_relationships(db_path: str, memory_id: Optional[str] = None) -> list[dict]:
    """Get memory relationships for graph visualization."""
    conn = get_connection(db_path)

    # Check if memory_relationships table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_relationships'"
    ).fetchone()

    if not table_check:
        conn.close()
        return []

    query = """
        SELECT
            r.source_memory_id as source_id,
            r.target_memory_id as target_id,
            r.relationship_type,
            r.strength,
            ms.content as source_content,
            ms.type as source_type,
            mt.content as target_content,
            mt.type as target_type
        FROM memory_relationships r
        JOIN memories ms ON r.source_memory_id = ms.id
        JOIN memories mt ON r.target_memory_id = mt.id
    """

    try:
        if memory_id:
            query += " WHERE r.source_memory_id = ? OR r.target_memory_id = ?"
            cursor = conn.execute(query, (memory_id, memory_id))
        else:
            cursor = conn.execute(query)

        result = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[Database] Error querying relationships: {e}")
        result = []
    finally:
        conn.close()

    return result


def get_relationship_graph(db_path: str, center_id: Optional[str] = None, depth: int = 2) -> dict:
    """Get graph data with nodes and edges for D3 visualization."""
    relationships = get_relationships(db_path, center_id)

    nodes = {}
    edges = []

    for rel in relationships:
        # Add source node
        if rel["source_id"] not in nodes:
            nodes[rel["source_id"]] = {
                "id": rel["source_id"],
                "content": rel["source_content"][:100] if rel["source_content"] else "",
                "type": rel["source_type"],
            }
        # Add target node
        if rel["target_id"] not in nodes:
            nodes[rel["target_id"]] = {
                "id": rel["target_id"],
                "content": rel["target_content"][:100] if rel["target_content"] else "",
                "type": rel["target_type"],
            }
        # Add edge
        edges.append({
            "source": rel["source_id"],
            "target": rel["target_id"],
            "type": rel["relationship_type"],
            "strength": rel["strength"] or 1.0,
        })

    return {"nodes": list(nodes.values()), "edges": edges}
