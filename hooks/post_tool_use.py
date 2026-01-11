#!/usr/bin/env python3
"""PostToolUse hook - logs tool result after execution.

This hook is called by Claude Code after each tool completes.
It logs the tool output, duration, and success/error status.

Hook configuration for settings.json:
{
    "hooks": {
        "PostToolUse": [
            {
                "type": "command",
                "command": "python hooks/post_tool_use.py"
            }
        ]
    }
}
"""

import json
import re
import sys
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Import shared session management
from session_utils import get_or_create_session


# Patterns for sensitive field names that should be redacted
SENSITIVE_FIELD_PATTERNS = [
    r'(?i)(api[_-]?key|apikey)',
    r'(?i)(password|passwd|pwd)',
    r'(?i)(secret|token|credential)',
    r'(?i)(auth[_-]?token|access[_-]?token)',
    r'(?i)(private[_-]?key|ssh[_-]?key)',
]


def redact_sensitive_fields(data: dict) -> dict:
    """Redact sensitive fields from a dictionary for safe logging.

    Recursively processes nested dicts and lists.
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        # Check if key matches sensitive patterns
        is_sensitive = any(
            re.search(pattern, str(key))
            for pattern in SENSITIVE_FIELD_PATTERNS
        )

        if is_sensitive:
            result[key] = '[REDACTED]'
        elif isinstance(value, dict):
            result[key] = redact_sensitive_fields(value)
        elif isinstance(value, list):
            result[key] = [
                redact_sensitive_fields(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


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
    """Process PostToolUse hook."""
    try:
        # Read all input at once (more reliable than json.load on stdin)
        raw_input = sys.stdin.read()
        if not raw_input or not raw_input.strip():
            print(json.dumps({}))
            return

        input_data = json.loads(raw_input)

        # Extract data from hook input
        tool_name = input_data.get("tool_name")
        tool_input = input_data.get("tool_input", {})
        tool_output = input_data.get("tool_output", {})
        agent_id = input_data.get("agent_id")

        # Determine success/error
        is_error = input_data.get("is_error", False)
        error_message = None
        if is_error and isinstance(tool_output, dict):
            error_message = tool_output.get("error") or tool_output.get("message")

        # Skip logging our own tools to prevent recursion
        # MCP tools are named like "mcp__omni-cortex__cortex_remember"
        if tool_name and ("cortex_" in tool_name or "omni-cortex" in tool_name):
            print(json.dumps({}))
            return

        project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

        # Auto-initialize database (creates if not exists)
        db_path = get_db_path()
        conn = ensure_database(db_path)

        # Get or create session (auto-manages session lifecycle)
        session_id = get_or_create_session(conn, project_path)

        # Redact sensitive fields before logging
        safe_input = redact_sensitive_fields(tool_input) if isinstance(tool_input, dict) else tool_input
        safe_output = redact_sensitive_fields(tool_output) if isinstance(tool_output, dict) else tool_output

        # Insert activity record
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO activities (
                id, session_id, agent_id, timestamp, event_type,
                tool_name, tool_input, tool_output, success, error_message, project_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                generate_id(),
                session_id,
                agent_id,
                datetime.now(timezone.utc).isoformat(),
                "post_tool_use",
                tool_name,
                truncate(json.dumps(safe_input, default=str)),
                truncate(json.dumps(safe_output, default=str)),
                0 if is_error else 1,
                error_message,
                project_path,
            ),
        )
        conn.commit()
        conn.close()

        # Return empty response (no modification)
        print(json.dumps({}))

    except Exception as e:
        # Hooks should never block - log error but continue
        print(json.dumps({"systemMessage": f"Cortex post_tool_use: {e}"}))

    sys.exit(0)


if __name__ == "__main__":
    main()
