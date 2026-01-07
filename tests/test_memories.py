"""Tests for memory operations."""

import pytest
import json

from omni_cortex.database.connection import init_database, close_connection
from omni_cortex.models.memory import (
    MemoryCreate,
    MemoryUpdate,
    create_memory,
    get_memory,
    update_memory,
    delete_memory,
    list_memories,
)


def test_create_memory(temp_db_path):
    """Test creating a memory."""
    conn = init_database(temp_db_path)

    data = MemoryCreate(
        content="This is a test memory about Python debugging.",
        context="Testing the memory system",
        tags=["python", "testing"],
    )

    memory = create_memory(conn, data, project_path="/test/project")

    assert memory.id.startswith("mem_")
    assert memory.content == data.content
    assert memory.context == data.context
    assert "python" in memory.tags
    assert "testing" in memory.tags
    assert memory.status == "fresh"
    assert memory.importance_score == 50.0

    close_connection(temp_db_path)


def test_auto_categorization(temp_db_path):
    """Test that memories are auto-categorized."""
    conn = init_database(temp_db_path)

    # Should be detected as "warning"
    warning_data = MemoryCreate(
        content="WARNING: Never use eval() with untrusted input.",
    )
    warning_mem = create_memory(conn, warning_data)
    assert warning_mem.type == "warning"

    # Should be detected as "command"
    command_data = MemoryCreate(
        content="$ npm install express",
    )
    command_mem = create_memory(conn, command_data)
    assert command_mem.type == "command"

    # Should be detected as "error"
    error_data = MemoryCreate(
        content="TypeError: Cannot read property 'foo' of undefined",
    )
    error_mem = create_memory(conn, error_data)
    assert error_mem.type == "error"

    close_connection(temp_db_path)


def test_get_memory(temp_db_path):
    """Test retrieving a memory by ID."""
    conn = init_database(temp_db_path)

    data = MemoryCreate(content="Test memory content")
    created = create_memory(conn, data)

    retrieved = get_memory(conn, created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.content == created.content

    close_connection(temp_db_path)


def test_update_memory(temp_db_path):
    """Test updating a memory."""
    conn = init_database(temp_db_path)

    data = MemoryCreate(
        content="Original content",
        tags=["original"],
    )
    memory = create_memory(conn, data)

    # Update content and add tags
    update_data = MemoryUpdate(
        content="Updated content",
        add_tags=["new-tag"],
    )
    updated = update_memory(conn, memory.id, update_data)

    assert updated.content == "Updated content"
    assert "original" in updated.tags
    assert "new-tag" in updated.tags

    close_connection(temp_db_path)


def test_delete_memory(temp_db_path):
    """Test deleting a memory."""
    conn = init_database(temp_db_path)

    data = MemoryCreate(content="Memory to delete")
    memory = create_memory(conn, data)

    # Verify it exists
    assert get_memory(conn, memory.id) is not None

    # Delete it
    deleted = delete_memory(conn, memory.id)
    assert deleted is True

    # Verify it's gone
    assert get_memory(conn, memory.id) is None

    close_connection(temp_db_path)


def test_list_memories(temp_db_path):
    """Test listing memories with filters."""
    conn = init_database(temp_db_path)

    # Create some memories
    for i in range(5):
        create_memory(conn, MemoryCreate(
            content=f"Memory {i}",
            tags=["test"],
        ))

    # Create one with different type
    create_memory(conn, MemoryCreate(
        content="WARNING: This is important",
        tags=["warning"],
    ))

    # List all
    memories, total = list_memories(conn)
    assert total == 6
    assert len(memories) == 6

    # Filter by tag
    memories, total = list_memories(conn, tags_filter=["warning"])
    assert total == 1

    close_connection(temp_db_path)
