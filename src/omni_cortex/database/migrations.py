"""Database migration management for Omni Cortex."""

import sqlite3
from typing import Optional
from pathlib import Path

from .schema import SCHEMA_VERSION, get_schema_sql
from .connection import get_connection
from ..utils.timestamps import now_iso


# Migration definitions: version -> SQL
MIGRATIONS: dict[str, str] = {
    # Command analytics columns for slash command/skill tracking
    "1.1": """
        -- Add command analytics columns to activities table
        ALTER TABLE activities ADD COLUMN command_name TEXT;
        ALTER TABLE activities ADD COLUMN command_scope TEXT;
        ALTER TABLE activities ADD COLUMN mcp_server TEXT;
        ALTER TABLE activities ADD COLUMN skill_name TEXT;

        -- Create indexes for new columns
        CREATE INDEX IF NOT EXISTS idx_activities_command ON activities(command_name);
        CREATE INDEX IF NOT EXISTS idx_activities_mcp ON activities(mcp_server);
        CREATE INDEX IF NOT EXISTS idx_activities_skill ON activities(skill_name);
    """,
    # Natural language summary columns for activity display
    "1.2": """
        -- Add natural language summary columns to activities table
        ALTER TABLE activities ADD COLUMN summary TEXT;
        ALTER TABLE activities ADD COLUMN summary_detail TEXT;
    """,
}


def get_current_version(conn: sqlite3.Connection) -> Optional[str]:
    """Get the current schema version from the database."""
    try:
        cursor = conn.execute(
            "SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return None


def apply_migration(conn: sqlite3.Connection, version: str, sql: str) -> None:
    """Apply a single migration."""
    conn.executescript(sql)
    conn.execute(
        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
        (version, now_iso())
    )
    conn.commit()


def migrate(db_path: Optional[Path] = None, is_global: bool = False) -> str:
    """Run all pending migrations.

    Returns:
        The final schema version
    """
    conn = get_connection(db_path, is_global)
    current = get_current_version(conn)

    if current is None:
        # Fresh database - apply full schema
        conn.executescript(get_schema_sql())
        conn.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, now_iso())
        )
        conn.commit()
        return SCHEMA_VERSION

    # Apply pending migrations in order
    versions = sorted(MIGRATIONS.keys())
    for version in versions:
        if version > current:
            apply_migration(conn, version, MIGRATIONS[version])
            current = version

    return current


def needs_migration(conn: sqlite3.Connection) -> bool:
    """Check if database needs migration."""
    current = get_current_version(conn)
    if current is None:
        return True
    return any(v > current for v in MIGRATIONS.keys())
