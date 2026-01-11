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
import re
import sys
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Session timeout in seconds (4 hours of inactivity = new session)
SESSION_TIMEOUT_SECONDS = 4 * 60 * 60

# Patterns for sensitive field names that should be redacted
SENSITIVE_FIELD_PATTERNS = [
    r'(?i)(api[_-]?key|apikey)',
    r'(?i)(password|passwd|pwd)',
    r'(?i)(secret|token|credential)',
    r'(?i)(auth[_-]?token|access[_-]?token)',
    r'(?i)(private[_-]?key|ssh[_-]?key)',
]


def generate_session_id() -> str:
    """Generate a unique session ID matching the MCP format."""
    timestamp_ms = int(time.time() * 1000)
    random_hex = os.urandom(4).hex()
    return f"sess_{timestamp_ms}_{random_hex}"


def get_session_file_path() -> Path:
    """Get the path to the current session file."""
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    return Path(project_path) / ".omni-cortex" / "current_session.json"


def load_session_file() -> Optional[dict]:
    """Load the current session from file if it exists and is valid."""
    session_file = get_session_file_path()
    if not session_file.exists():
        return None

    try:
        with open(session_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_session_file(session_data: dict) -> None:
    """Save the current session to file."""
    session_file = get_session_file_path()
    session_file.parent.mkdir(parents=True, exist_ok=True)

    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)


def is_session_valid(session_data: dict) -> bool:
    """Check if a session is still valid (not timed out)."""
    last_activity = session_data.get("last_activity_at")
    if not last_activity:
        return False

    try:
        last_time = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        elapsed_seconds = (now - last_time).total_seconds()
        return elapsed_seconds < SESSION_TIMEOUT_SECONDS
    except (ValueError, TypeError):
        return False


def create_session_in_db(conn: sqlite3.Connection, session_id: str, project_path: str) -> None:
    """Create a new session record in the database."""
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    # Check if sessions table exists (it might not if only activities table was created)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
    if cursor.fetchone() is None:
        # Create sessions table with minimal schema
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                project_path TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                summary TEXT,
                tags TEXT,
                metadata TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at DESC);
            CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_path);
        """)
        conn.commit()

    cursor.execute(
        """
        INSERT OR IGNORE INTO sessions (id, project_path, started_at)
        VALUES (?, ?, ?)
        """,
        (session_id, project_path, now),
    )
    conn.commit()


def get_or_create_session(conn: sqlite3.Connection, project_path: str) -> str:
    """Get the current session ID, creating a new one if needed.

    Session management logic:
    1. Check for existing session file
    2. If exists and not timed out, use it and update last_activity
    3. If doesn't exist or timed out, create new session

    Returns:
        The session ID to use for activity logging
    """
    session_data = load_session_file()
    now_iso = datetime.now(timezone.utc).isoformat()

    if session_data and is_session_valid(session_data):
        # Update last activity time
        session_data["last_activity_at"] = now_iso
        save_session_file(session_data)
        return session_data["session_id"]

    # Create new session
    session_id = generate_session_id()

    # Create in database
    create_session_in_db(conn, session_id, project_path)

    # Save to file
    session_data = {
        "session_id": session_id,
        "project_path": project_path,
        "started_at": now_iso,
        "last_activity_at": now_iso,
    }
    save_session_file(session_data)

    return session_id


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

        project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

        # Auto-initialize database (creates if not exists)
        db_path = get_db_path()
        conn = ensure_database(db_path)

        # Get or create session (auto-manages session lifecycle)
        session_id = get_or_create_session(conn, project_path)

        # Redact sensitive fields before logging
        safe_input = redact_sensitive_fields(tool_input) if isinstance(tool_input, dict) else tool_input

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
                truncate(json.dumps(safe_input, default=str)),
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
