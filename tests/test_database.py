"""Tests for database layer."""

import pytest
from pathlib import Path

from omni_cortex.database.connection import init_database, get_connection, close_connection
from omni_cortex.database.schema import SCHEMA_VERSION


def test_init_database(temp_db_path):
    """Test database initialization creates all tables."""
    conn = init_database(temp_db_path)

    cursor = conn.cursor()

    # Check all tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    expected_tables = {
        "sessions",
        "agents",
        "activities",
        "memories",
        "memories_fts",
        "memory_relationships",
        "activity_memory_links",
        "embeddings",
        "session_summaries",
        "config",
        "schema_migrations",
    }

    for table in expected_tables:
        assert table in tables, f"Missing table: {table}"

    close_connection(temp_db_path)


def test_schema_version_recorded(temp_db_path):
    """Test that schema version is recorded."""
    conn = init_database(temp_db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1")
    row = cursor.fetchone()

    assert row is not None
    assert row[0] == SCHEMA_VERSION

    close_connection(temp_db_path)


def test_fts_triggers_exist(temp_db_path):
    """Test that FTS sync triggers are created."""
    conn = init_database(temp_db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
    triggers = {row[0] for row in cursor.fetchall()}

    assert "memories_ai" in triggers
    assert "memories_ad" in triggers
    assert "memories_au" in triggers

    close_connection(temp_db_path)
