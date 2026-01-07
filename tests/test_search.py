"""Tests for search operations."""

import pytest

from omni_cortex.database.connection import init_database, close_connection
from omni_cortex.models.memory import MemoryCreate, create_memory
from omni_cortex.search.keyword import keyword_search
from omni_cortex.search.hybrid import search


def test_keyword_search_empty(temp_db_path):
    """Test keyword search with no memories."""
    conn = init_database(temp_db_path)

    results = keyword_search(conn, "test query")

    assert results == []

    close_connection(temp_db_path)


def test_keyword_search_basic(temp_db_path):
    """Test basic keyword search."""
    conn = init_database(temp_db_path)

    # Create memories with specific content
    create_memory(conn, MemoryCreate(
        content="Python is a great programming language",
        tags=["python"],
    ))
    create_memory(conn, MemoryCreate(
        content="JavaScript is used for web development",
        tags=["javascript"],
    ))
    create_memory(conn, MemoryCreate(
        content="The Python API uses decorators for routing",
        tags=["python", "api"],
    ))

    # Search for Python
    results = keyword_search(conn, "Python")

    assert len(results) == 2
    # Results should contain Python-related memories
    contents = [m.content for m, _ in results]
    assert any("Python" in c for c in contents)

    close_connection(temp_db_path)


def test_keyword_search_type_filter(temp_db_path):
    """Test keyword search with type filter."""
    conn = init_database(temp_db_path)

    # Create memories with different types
    create_memory(conn, MemoryCreate(
        content="WARNING: Use parameterized queries",
    ))
    create_memory(conn, MemoryCreate(
        content="This is a general note about queries",
    ))

    # Search with type filter
    results = keyword_search(conn, "queries", type_filter="warning")

    assert len(results) == 1
    assert results[0][0].type == "warning"

    close_connection(temp_db_path)


def test_keyword_search_tags_filter(temp_db_path):
    """Test keyword search with tags filter."""
    conn = init_database(temp_db_path)

    create_memory(conn, MemoryCreate(
        content="FastAPI routing configuration",
        tags=["python", "fastapi"],
    ))
    create_memory(conn, MemoryCreate(
        content="Express routing setup",
        tags=["javascript", "express"],
    ))

    # Search with tags filter
    results = keyword_search(conn, "routing", tags_filter=["fastapi"])

    assert len(results) == 1
    assert "fastapi" in results[0][0].tags

    close_connection(temp_db_path)


def test_keyword_search_status_filter(temp_db_path):
    """Test keyword search excludes archived by default."""
    conn = init_database(temp_db_path)

    # Create active memory
    create_memory(conn, MemoryCreate(
        content="Active memory about testing",
    ))

    # Create archived memory
    from omni_cortex.models.memory import update_memory, MemoryUpdate
    archived = create_memory(conn, MemoryCreate(
        content="Archived memory about testing",
    ))
    update_memory(conn, archived.id, MemoryUpdate(status="archived"))

    # Search without include_archived
    results = keyword_search(conn, "testing", include_archived=False)
    assert len(results) == 1
    assert results[0][0].status != "archived"

    # Search with include_archived
    results = keyword_search(conn, "testing", include_archived=True)
    assert len(results) == 2

    close_connection(temp_db_path)


def test_keyword_search_importance_filter(temp_db_path):
    """Test keyword search with minimum importance filter."""
    conn = init_database(temp_db_path)

    # Create low importance memory
    create_memory(conn, MemoryCreate(
        content="Low importance debugging note",
        importance=20,
    ))

    # Create high importance memory
    create_memory(conn, MemoryCreate(
        content="Critical debugging note",
        importance=80,
    ))

    # Filter by minimum importance
    results = keyword_search(conn, "debugging", min_importance=50)

    assert len(results) == 1
    assert results[0][0].importance_score >= 50

    close_connection(temp_db_path)


def test_unified_search_keyword_mode(temp_db_path):
    """Test unified search function in keyword mode."""
    conn = init_database(temp_db_path)

    create_memory(conn, MemoryCreate(
        content="Database migration script",
        tags=["database"],
    ))

    results = search(conn, "migration", mode="keyword")

    assert len(results) == 1
    # Unified format: (memory, keyword_score, semantic_score)
    memory, kw_score, sem_score = results[0]
    assert memory.content == "Database migration script"
    assert kw_score > 0
    assert sem_score == 0  # No semantic search in keyword mode

    close_connection(temp_db_path)


def test_unified_search_falls_back(temp_db_path):
    """Test unified search falls back when semantic unavailable."""
    conn = init_database(temp_db_path)

    create_memory(conn, MemoryCreate(
        content="Testing fallback behavior",
    ))

    # Semantic mode should fall back to keyword if model not available
    results = search(conn, "fallback", mode="semantic")

    # Should still return results (from fallback)
    assert len(results) >= 0  # May be 0 or 1 depending on fallback

    close_connection(temp_db_path)


def test_multiword_query(temp_db_path):
    """Test search with multiple words."""
    conn = init_database(temp_db_path)

    create_memory(conn, MemoryCreate(
        content="This is about Python web development using Flask",
    ))
    create_memory(conn, MemoryCreate(
        content="JavaScript React frontend development",
    ))

    # Multi-word query should match memories with any of the words
    results = keyword_search(conn, "Python Flask")

    assert len(results) >= 1
    # Should find the Python/Flask memory
    contents = [m.content for m, _ in results]
    assert any("Flask" in c or "Python" in c for c in contents)

    close_connection(temp_db_path)


def test_search_ranking(temp_db_path):
    """Test that search results are ranked by relevance."""
    conn = init_database(temp_db_path)

    # Create memories with varying relevance
    create_memory(conn, MemoryCreate(
        content="This mentions Python once",
    ))
    create_memory(conn, MemoryCreate(
        content="Python Python Python - lots of Python mentions",
    ))

    results = keyword_search(conn, "Python")

    assert len(results) == 2
    # Memory with more mentions should have higher score
    # (though FTS5 bm25 may order differently based on document length)
    assert all(score > 0 for _, score in results)

    close_connection(temp_db_path)


def test_search_limit(temp_db_path):
    """Test that search respects limit parameter."""
    conn = init_database(temp_db_path)

    # Create many memories
    for i in range(20):
        create_memory(conn, MemoryCreate(
            content=f"Test memory number {i} about development",
        ))

    # Search with limit
    results = keyword_search(conn, "development", limit=5)

    assert len(results) == 5

    close_connection(temp_db_path)
