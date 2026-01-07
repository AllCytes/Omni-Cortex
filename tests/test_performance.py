"""Performance tests for Omni Cortex MCP.

These tests measure and benchmark key operations to ensure acceptable performance.
"""

import pytest
import time
import statistics
from typing import Callable


def measure_time(func: Callable, iterations: int = 10) -> dict:
    """Measure execution time statistics for a function."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    return {
        "min_ms": min(times),
        "max_ms": max(times),
        "avg_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "iterations": iterations,
    }


class TestMemoryPerformance:
    """Performance tests for memory operations."""

    def test_create_memory_performance(self, mock_project_env):
        """Benchmark memory creation."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.models.memory import create_memory, MemoryCreate, delete_memory

        conn = init_database()
        created_ids = []

        def create_one():
            mem = create_memory(
                conn,
                MemoryCreate(
                    content="Performance test memory with some content for benchmarking",
                    tags=["perf-test", "benchmark"],
                    type="general",
                ),
                project_path="/test/project",
            )
            created_ids.append(mem.id)

        stats = measure_time(create_one, iterations=20)

        # Cleanup
        for mem_id in created_ids:
            delete_memory(conn, mem_id)

        close_all_connections()

        # Assert reasonable performance (< 50ms per operation)
        assert stats["avg_ms"] < 50, f"Memory creation too slow: {stats['avg_ms']:.2f}ms avg"
        print(f"\nMemory creation: avg={stats['avg_ms']:.2f}ms, median={stats['median_ms']:.2f}ms")

    def test_keyword_search_performance(self, mock_project_env):
        """Benchmark keyword search."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.models.memory import create_memory, MemoryCreate, delete_memory
        from omni_cortex.search.keyword import keyword_search

        conn = init_database()
        created_ids = []

        # Create 50 test memories
        for i in range(50):
            mem = create_memory(
                conn,
                MemoryCreate(
                    content=f"Performance test memory number {i} with searchable content",
                    tags=["perf-test"],
                    type="general",
                ),
                project_path="/test/project",
            )
            created_ids.append(mem.id)

        def search_memories():
            keyword_search(conn, "searchable content", limit=10)

        stats = measure_time(search_memories, iterations=20)

        # Cleanup
        for mem_id in created_ids:
            delete_memory(conn, mem_id)

        close_all_connections()

        # Assert reasonable performance (< 20ms per search)
        assert stats["avg_ms"] < 20, f"Search too slow: {stats['avg_ms']:.2f}ms avg"
        print(f"\nKeyword search (50 memories): avg={stats['avg_ms']:.2f}ms, median={stats['median_ms']:.2f}ms")

    def test_list_memories_performance(self, mock_project_env):
        """Benchmark listing memories."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.models.memory import create_memory, MemoryCreate, list_memories, delete_memory

        conn = init_database()
        created_ids = []

        # Create 100 test memories
        for i in range(100):
            mem = create_memory(
                conn,
                MemoryCreate(
                    content=f"List performance test memory number {i}",
                    tags=["list-perf-test"],
                    type="general",
                ),
                project_path="/test/project",
            )
            created_ids.append(mem.id)

        def list_all():
            list_memories(conn, limit=50)

        stats = measure_time(list_all, iterations=20)

        # Cleanup
        for mem_id in created_ids:
            delete_memory(conn, mem_id)

        close_all_connections()

        # Assert reasonable performance (< 30ms for 50 items)
        assert stats["avg_ms"] < 30, f"List too slow: {stats['avg_ms']:.2f}ms avg"
        print(f"\nList memories (50 of 100): avg={stats['avg_ms']:.2f}ms, median={stats['median_ms']:.2f}ms")


class TestActivityPerformance:
    """Performance tests for activity logging."""

    def test_log_activity_performance(self, mock_project_env):
        """Benchmark activity logging."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.models.activity import create_activity, ActivityCreate

        conn = init_database()

        def log_one():
            create_activity(
                conn,
                ActivityCreate(
                    event_type="post_tool_use",
                    tool_name="TestTool",
                    success=True,
                ),
                project_path="/test/project",
            )

        stats = measure_time(log_one, iterations=20)

        close_all_connections()

        # Assert reasonable performance (< 20ms per log)
        assert stats["avg_ms"] < 20, f"Activity logging too slow: {stats['avg_ms']:.2f}ms avg"
        print(f"\nActivity logging: avg={stats['avg_ms']:.2f}ms, median={stats['median_ms']:.2f}ms")


class TestSessionPerformance:
    """Performance tests for session operations."""

    def test_session_lifecycle_performance(self, mock_project_env):
        """Benchmark session start/end cycle."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.models.session import create_session, end_session, SessionCreate

        conn = init_database()
        counter = [0]

        def session_cycle():
            counter[0] += 1
            session = create_session(
                conn,
                SessionCreate(
                    id=f"perf_test_session_{counter[0]}",
                    project_path="/test/project",
                ),
            )
            end_session(conn, session.id, summary="Test session")

        stats = measure_time(session_cycle, iterations=10)

        close_all_connections()

        # Assert reasonable performance (< 30ms per cycle)
        assert stats["avg_ms"] < 30, f"Session cycle too slow: {stats['avg_ms']:.2f}ms avg"
        print(f"\nSession lifecycle: avg={stats['avg_ms']:.2f}ms, median={stats['median_ms']:.2f}ms")


class TestDatabasePerformance:
    """Performance tests for database operations."""

    def test_database_init_performance(self, temp_db_path):
        """Benchmark database initialization."""
        import os
        from omni_cortex.database.connection import init_database, close_all_connections

        os.environ["CLAUDE_PROJECT_DIR"] = str(temp_db_path.parent.parent)

        def init_db():
            conn = init_database()
            close_all_connections()

        stats = measure_time(init_db, iterations=5)

        # Assert reasonable performance (< 100ms for cold start)
        assert stats["avg_ms"] < 100, f"DB init too slow: {stats['avg_ms']:.2f}ms avg"
        print(f"\nDatabase init: avg={stats['avg_ms']:.2f}ms, median={stats['median_ms']:.2f}ms")
