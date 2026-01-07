#!/usr/bin/env python3
"""PreToolUse hook - logs tool call before execution.

This hook is called by Claude Code before each tool is executed.
It logs the tool name and input to the Cortex activity database.

Hook configuration for settings.json:
{
    "hooks": {
        "PreToolUse": [
            {
                "type": "command",
                "command": "python hooks/pre_tool_use.py"
            }
        ]
    }
}
"""

import json
import sys
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def get_db_path() -> Path:
    """Get the database path for the current project."""
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    return Path(project_path) / ".omni-cortex" / "cortex.db"


def ensure_database(db_path: Path) -> sqlite3.Connection:
    """Ensure database exists and is initialized.

    Auto-creates the database and schema if it doesn't exist.
    This enables 'out of the box' functionality.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))

    # Check if schema exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities'")
    if cursor.fetchone() is None:
        # Apply minimal schema for activities (full schema applied by MCP)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS activities (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                agent_id TEXT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                tool_name TEXT,
                tool_input TEXT,
                tool_output TEXT,
                duration_ms INTEGER,
                success INTEGER DEFAULT 1,
                error_message TEXT,
                project_path TEXT,
                file_path TEXT,
                metadata TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_activities_tool ON activities(tool_name);
        """)
        conn.commit()

    return conn


def generate_id() -> str:
    """Generate a unique activity ID."""
    timestamp_ms = int(datetime.now().timestamp() * 1000)
    random_hex = os.urandom(4).hex()
    return f"act_{timestamp_ms}_{random_hex}"


def truncate(text: str, max_length: int = 10000) -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 20] + "\n... [truncated]"


def main():
    """Process PreToolUse hook."""
    try:
        # Read input from stdin with timeout protection
        import select
        if sys.platform != "win32":
            # Unix: use select for timeout
            ready, _, _ = select.select([sys.stdin], [], [], 5.0)
            if not ready:
                print(json.dumps({}))
                return

        # Read all input at once
        raw_input = sys.stdin.read()
        if not raw_input or not raw_input.strip():
            print(json.dumps({}))
            return

        input_data = json.loads(raw_input)

        # Extract data from hook input
        tool_name = input_data.get("tool_name")
        tool_input = input_data.get("tool_input", {})
        agent_id = input_data.get("agent_id")

        # Skip logging our own tools to prevent recursion
        # MCP tools are named like "mcp__omni-cortex__cortex_remember"
        if tool_name and ("cortex_" in tool_name or "omni-cortex" in tool_name):
            print(json.dumps({}))
            return

        session_id = os.environ.get("CLAUDE_SESSION_ID")
        project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

        # Auto-initialize database (creates if not exists)
        db_path = get_db_path()
        conn = ensure_database(db_path)

        # Insert activity record
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO activities (
                id, session_id, agent_id, timestamp, event_type,
                tool_name, tool_input, project_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                generate_id(),
                session_id,
                agent_id,
                datetime.now(timezone.utc).isoformat(),
                "pre_tool_use",
                tool_name,
                truncate(json.dumps(tool_input, default=str)),
                project_path,
            ),
        )
        conn.commit()
        conn.close()

        # Return empty response (no modification to tool call)
        print(json.dumps({}))

    except Exception as e:
        # Hooks should never block - log error but continue
        print(json.dumps({"systemMessage": f"Cortex pre_tool_use: {e}"}))

    sys.exit(0)


if __name__ == "__main__":
    main()
