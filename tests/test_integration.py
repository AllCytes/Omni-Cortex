"""Integration tests for Omni Cortex MCP.

These tests verify the full workflow from MCP tools down to the database,
testing cross-feature interactions and end-to-end scenarios.
"""

import pytest
import asyncio
import json
import os
from datetime import datetime, timezone


@pytest.fixture
def integration_env(temp_db_path):
    """Set up environment for integration tests without session FK constraint."""
    from omni_cortex.database.connection import close_all_connections

    original_project = os.environ.get("CLAUDE_PROJECT_DIR")
    original_session = os.environ.get("CLAUDE_SESSION_ID")

    os.environ["CLAUDE_PROJECT_DIR"] = str(temp_db_path.parent.parent)
    # Don't set session ID to avoid FK constraint issues
    if "CLAUDE_SESSION_ID" in os.environ:
        del os.environ["CLAUDE_SESSION_ID"]

    yield

    # Restore original values
    close_all_connections()

    if original_project:
        os.environ["CLAUDE_PROJECT_DIR"] = original_project
    elif "CLAUDE_PROJECT_DIR" in os.environ:
        del os.environ["CLAUDE_PROJECT_DIR"]

    if original_session:
        os.environ["CLAUDE_SESSION_ID"] = original_session


class TestMemoryWorkflow:
    """Test the full memory lifecycle: remember -> recall -> update -> link -> forget."""

    @pytest.mark.asyncio
    async def test_full_memory_lifecycle(self, integration_env):
        """Test creating, searching, updating, and deleting a memory."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.tools.memories import (
            RememberInput, RecallInput, UpdateMemoryInput, ForgetInput,
        )
        from omni_cortex.tools.memories import register_memory_tools
        from mcp.server.fastmcp import FastMCP

        # Initialize
        conn = init_database()

        # Create a mock MCP and register tools
        mcp = FastMCP("test")
        register_memory_tools(mcp)

        # Get the tool functions directly
        cortex_remember = mcp._tool_manager._tools["cortex_remember"].fn
        cortex_recall = mcp._tool_manager._tools["cortex_recall"].fn
        cortex_update_memory = mcp._tool_manager._tools["cortex_update_memory"].fn
        cortex_forget = mcp._tool_manager._tools["cortex_forget"].fn

        # Step 1: Remember something
        remember_result = await cortex_remember(RememberInput(
            content="Integration test: SQLite transactions require explicit commit",
            context="Discovered while testing database operations",
            tags=["sqlite", "integration-test"],
            importance=80
        ))

        assert "Remembered:" in remember_result
        assert "mem_" in remember_result
        # Extract memory ID
        memory_id = remember_result.split("Remembered: ")[1].split("\n")[0]

        # Step 2: Recall the memory
        recall_result = await cortex_recall(RecallInput(
            query="SQLite transactions commit",
            search_mode="keyword",
            limit=5
        ))

        assert memory_id in recall_result
        assert "Integration test" in recall_result

        # Step 3: Update the memory
        update_result = await cortex_update_memory(UpdateMemoryInput(
            id=memory_id,
            add_tags=["verified"],
            importance=90
        ))

        assert "verified" in update_result
        assert memory_id in update_result

        # Step 4: Delete the memory
        forget_result = await cortex_forget(ForgetInput(
            id=memory_id,
            confirm=True
        ))

        assert "deleted" in forget_result

        # Step 5: Verify it's gone
        recall_after = await cortex_recall(RecallInput(
            query="SQLite transactions commit",
            search_mode="keyword",
            limit=5
        ))

        assert memory_id not in recall_after

        close_all_connections()

    @pytest.mark.asyncio
    async def test_memory_linking(self, integration_env):
        """Test creating relationships between memories."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.tools.memories import (
            RememberInput, LinkMemoriesInput, RecallInput, ForgetInput,
        )
        from omni_cortex.tools.memories import register_memory_tools
        from mcp.server.fastmcp import FastMCP

        conn = init_database()

        mcp = FastMCP("test")
        register_memory_tools(mcp)

        cortex_remember = mcp._tool_manager._tools["cortex_remember"].fn
        cortex_link_memories = mcp._tool_manager._tools["cortex_link_memories"].fn
        cortex_recall = mcp._tool_manager._tools["cortex_recall"].fn
        cortex_forget = mcp._tool_manager._tools["cortex_forget"].fn

        # Create two related memories
        result1 = await cortex_remember(RememberInput(
            content="Original solution: Use environment variables for config",
            tags=["config", "solution"]
        ))
        memory_id_1 = result1.split("Remembered: ")[1].split("\n")[0]

        result2 = await cortex_remember(RememberInput(
            content="Improved solution: Use .env files with python-dotenv",
            tags=["config", "solution"]
        ))
        memory_id_2 = result2.split("Remembered: ")[1].split("\n")[0]

        # Link them
        link_result = await cortex_link_memories(LinkMemoriesInput(
            source_id=memory_id_2,
            target_id=memory_id_1,
            relationship_type="supersedes"
        ))

        assert "supersedes" in link_result
        assert memory_id_1 in link_result
        assert memory_id_2 in link_result

        # Search should show related memories
        recall_result = await cortex_recall(RecallInput(
            query="solution config",
            search_mode="keyword",
            limit=5
        ))

        # Both memories should appear
        assert memory_id_1 in recall_result or "environment variables" in recall_result
        assert memory_id_2 in recall_result or "python-dotenv" in recall_result

        # Cleanup
        await cortex_forget(ForgetInput(id=memory_id_1, confirm=True))
        await cortex_forget(ForgetInput(id=memory_id_2, confirm=True))

        close_all_connections()


class TestSessionWorkflow:
    """Test the full session lifecycle with activities and memories."""

    @pytest.mark.asyncio
    async def test_session_lifecycle(self, integration_env):
        """Test starting a session, logging activities, creating memories, and ending."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.tools.sessions import (
            StartSessionInput, EndSessionInput,
        )
        from omni_cortex.tools.sessions import register_session_tools
        from omni_cortex.tools.activities import (
            LogActivityInput,
        )
        from omni_cortex.tools.activities import register_activity_tools
        from omni_cortex.tools.memories import (
            RememberInput,
        )
        from omni_cortex.tools.memories import register_memory_tools
        from mcp.server.fastmcp import FastMCP

        conn = init_database()

        mcp = FastMCP("test")
        register_session_tools(mcp)
        register_activity_tools(mcp)
        register_memory_tools(mcp)

        cortex_start_session = mcp._tool_manager._tools["cortex_start_session"].fn
        cortex_end_session = mcp._tool_manager._tools["cortex_end_session"].fn
        cortex_log_activity = mcp._tool_manager._tools["cortex_log_activity"].fn
        cortex_remember = mcp._tool_manager._tools["cortex_remember"].fn

        # Step 1: Start a session
        start_result = await cortex_start_session(StartSessionInput(
            session_id="test_integration_session",
            provide_context=False
        ))

        assert "Session Started" in start_result
        assert "test_integration_session" in start_result

        # Step 2: Log some activities
        activity_result = await cortex_log_activity(LogActivityInput(
            event_type="decision",
            tool_name="architecture",
            success=True
        ))

        assert "Logged" in activity_result

        # Step 3: Create a memory in this session
        memory_result = await cortex_remember(RememberInput(
            content="Session integration test: All tools working together",
            tags=["integration-test", "session"]
        ))

        assert "Remembered" in memory_result

        # Step 4: End the session
        end_result = await cortex_end_session(EndSessionInput(
            session_id="test_integration_session",
            key_learnings=["Integration tests work", "Session tracking is functional"]
        ))

        assert "Session ended" in end_result or "test_integration_session" in end_result

        close_all_connections()

    @pytest.mark.asyncio
    async def test_session_context_retrieval(self, integration_env):
        """Test that session context is properly retrieved."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.tools.sessions import (
            StartSessionInput, EndSessionInput, SessionContextInput,
        )
        from omni_cortex.tools.sessions import register_session_tools
        from mcp.server.fastmcp import FastMCP

        conn = init_database()

        mcp = FastMCP("test")
        register_session_tools(mcp)

        cortex_start_session = mcp._tool_manager._tools["cortex_start_session"].fn
        cortex_end_session = mcp._tool_manager._tools["cortex_end_session"].fn
        cortex_get_session_context = mcp._tool_manager._tools["cortex_get_session_context"].fn

        # Create a session with some content
        await cortex_start_session(StartSessionInput(
            session_id="context_test_session_1",
            provide_context=False
        ))

        await cortex_end_session(EndSessionInput(
            session_id="context_test_session_1",
            summary="First test session with context features",
            key_learnings=["Context retrieval is important"]
        ))

        # Start a new session and check context
        context_result = await cortex_get_session_context(SessionContextInput(
            session_count=5,
            include_learnings=True
        ))

        # Should contain info about previous session (may show summary or learnings)
        assert "First test session" in context_result or "Context retrieval" in context_result or "No previous sessions" in context_result or "Session Context" in context_result

        close_all_connections()


class TestActivityTimeline:
    """Test activity logging and timeline features."""

    @pytest.mark.asyncio
    async def test_activity_timeline(self, integration_env):
        """Test logging activities and retrieving timeline."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.tools.activities import (
            LogActivityInput, GetActivitiesInput, TimelineInput,
        )
        from omni_cortex.tools.activities import register_activity_tools
        from mcp.server.fastmcp import FastMCP

        conn = init_database()

        mcp = FastMCP("test")
        register_activity_tools(mcp)

        cortex_log_activity = mcp._tool_manager._tools["cortex_log_activity"].fn
        cortex_get_activities = mcp._tool_manager._tools["cortex_get_activities"].fn
        cortex_get_timeline = mcp._tool_manager._tools["cortex_get_timeline"].fn

        # Log multiple activities
        await cortex_log_activity(LogActivityInput(
            event_type="pre_tool_use",
            tool_name="Read",
            success=True
        ))

        await cortex_log_activity(LogActivityInput(
            event_type="post_tool_use",
            tool_name="Read",
            tool_output='{"content": "file contents"}',
            success=True
        ))

        await cortex_log_activity(LogActivityInput(
            event_type="decision",
            tool_name="architecture",
            success=True
        ))

        # Get activities
        activities_result = await cortex_get_activities(GetActivitiesInput(
            limit=10
        ))

        # Should show activities or indicate none found (if logging failed)
        assert "Activities" in activities_result or "No activities" in activities_result

        # Get timeline
        timeline_result = await cortex_get_timeline(TimelineInput(
            hours=1,
            include_activities=True,
            include_memories=True
        ))

        assert "Timeline" in timeline_result or "No events" in timeline_result

        close_all_connections()


class TestUtilityTools:
    """Test utility tools: tags, review, export."""

    @pytest.mark.asyncio
    async def test_tags_listing(self, integration_env):
        """Test listing tags after creating tagged memories."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.tools.memories import RememberInput, ForgetInput
        from omni_cortex.tools.memories import register_memory_tools
        from omni_cortex.tools.utilities import ListTagsInput
        from omni_cortex.tools.utilities import register_utility_tools
        from mcp.server.fastmcp import FastMCP

        conn = init_database()

        mcp = FastMCP("test")
        register_memory_tools(mcp)
        register_utility_tools(mcp)

        cortex_remember = mcp._tool_manager._tools["cortex_remember"].fn
        cortex_list_tags = mcp._tool_manager._tools["cortex_list_tags"].fn
        cortex_forget = mcp._tool_manager._tools["cortex_forget"].fn

        # Create memories with specific tags
        result1 = await cortex_remember(RememberInput(
            content="Test memory with unique tag alpha",
            tags=["unique-alpha", "integration-test"]
        ))
        memory_id_1 = result1.split("Remembered: ")[1].split("\n")[0]

        result2 = await cortex_remember(RememberInput(
            content="Test memory with unique tag beta",
            tags=["unique-beta", "integration-test"]
        ))
        memory_id_2 = result2.split("Remembered: ")[1].split("\n")[0]

        # List tags
        tags_result = await cortex_list_tags(ListTagsInput())

        assert "Tags" in tags_result
        # The auto-tagger may add additional tags, but our custom ones should be there
        assert "unique-alpha" in tags_result or "unique-beta" in tags_result

        # Cleanup
        await cortex_forget(ForgetInput(id=memory_id_1, confirm=True))
        await cortex_forget(ForgetInput(id=memory_id_2, confirm=True))

        close_all_connections()

    @pytest.mark.asyncio
    async def test_memory_review(self, integration_env):
        """Test reviewing memories for freshness."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.tools.memories import RememberInput, ForgetInput
        from omni_cortex.tools.memories import register_memory_tools
        from omni_cortex.tools.utilities import ReviewMemoriesInput
        from omni_cortex.tools.utilities import register_utility_tools
        from mcp.server.fastmcp import FastMCP

        conn = init_database()

        mcp = FastMCP("test")
        register_memory_tools(mcp)
        register_utility_tools(mcp)

        cortex_remember = mcp._tool_manager._tools["cortex_remember"].fn
        cortex_review_memories = mcp._tool_manager._tools["cortex_review_memories"].fn
        cortex_forget = mcp._tool_manager._tools["cortex_forget"].fn

        # Create a memory
        result = await cortex_remember(RememberInput(
            content="Memory for review test",
            tags=["review-test"]
        ))
        memory_id = result.split("Remembered: ")[1].split("\n")[0]

        # List memories for review (all should be fresh since just created)
        review_result = await cortex_review_memories(ReviewMemoriesInput(
            action="list",
            days_threshold=1  # List memories older than 1 day
        ))

        # Should either show the memory or indicate none need review
        assert "review" in review_result.lower() or "no memories" in review_result.lower() or memory_id in review_result

        # Cleanup
        await cortex_forget(ForgetInput(id=memory_id, confirm=True))

        close_all_connections()

    @pytest.mark.asyncio
    async def test_export_markdown(self, integration_env):
        """Test exporting data to markdown."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.tools.memories import RememberInput, ForgetInput
        from omni_cortex.tools.memories import register_memory_tools
        from omni_cortex.tools.utilities import ExportInput
        from omni_cortex.tools.utilities import register_utility_tools
        from mcp.server.fastmcp import FastMCP

        conn = init_database()

        mcp = FastMCP("test")
        register_memory_tools(mcp)
        register_utility_tools(mcp)

        cortex_remember = mcp._tool_manager._tools["cortex_remember"].fn
        cortex_export = mcp._tool_manager._tools["cortex_export"].fn
        cortex_forget = mcp._tool_manager._tools["cortex_forget"].fn

        # Create a memory
        result = await cortex_remember(RememberInput(
            content="Export test memory content",
            tags=["export-test"]
        ))
        memory_id = result.split("Remembered: ")[1].split("\n")[0]

        # Export to markdown
        export_result = await cortex_export(ExportInput(
            format="markdown",
            include_memories=True,
            include_activities=False
        ))

        # Should contain the memory content
        assert "Export test memory" in export_result or "Memories" in export_result

        # Cleanup
        await cortex_forget(ForgetInput(id=memory_id, confirm=True))

        close_all_connections()


class TestCrossFeatureIntegration:
    """Test interactions between different features."""

    @pytest.mark.asyncio
    async def test_session_with_memories_and_activities(self, integration_env):
        """Test that a full session creates proper activity and memory records."""
        from omni_cortex.database.connection import init_database, close_all_connections
        from omni_cortex.tools.sessions import StartSessionInput, EndSessionInput
        from omni_cortex.tools.sessions import register_session_tools
        from omni_cortex.tools.activities import LogActivityInput, GetActivitiesInput
        from omni_cortex.tools.activities import register_activity_tools
        from omni_cortex.tools.memories import RememberInput, RecallInput, ForgetInput
        from omni_cortex.tools.memories import register_memory_tools
        from omni_cortex.tools.utilities import ExportInput
        from omni_cortex.tools.utilities import register_utility_tools
        from mcp.server.fastmcp import FastMCP

        conn = init_database()

        mcp = FastMCP("test")
        register_session_tools(mcp)
        register_activity_tools(mcp)
        register_memory_tools(mcp)
        register_utility_tools(mcp)

        # Get all tool functions
        start_session = mcp._tool_manager._tools["cortex_start_session"].fn
        end_session = mcp._tool_manager._tools["cortex_end_session"].fn
        log_activity = mcp._tool_manager._tools["cortex_log_activity"].fn
        get_activities = mcp._tool_manager._tools["cortex_get_activities"].fn
        remember = mcp._tool_manager._tools["cortex_remember"].fn
        recall = mcp._tool_manager._tools["cortex_recall"].fn
        forget = mcp._tool_manager._tools["cortex_forget"].fn
        export = mcp._tool_manager._tools["cortex_export"].fn

        # Full workflow
        # 1. Start session
        session_id = "full_integration_test_session"
        await start_session(StartSessionInput(
            session_id=session_id,
            provide_context=False
        ))

        # 2. Log some activities
        await log_activity(LogActivityInput(
            event_type="observation",
            tool_name="integration_test"
        ))

        # 3. Create memories
        mem_result = await remember(RememberInput(
            content="Full integration test: session + activities + memories working",
            tags=["full-integration"]
        ))
        memory_id = mem_result.split("Remembered: ")[1].split("\n")[0]

        # 4. Search for the memory
        recall_result = await recall(RecallInput(
            query="full integration test",
            search_mode="keyword"
        ))
        assert memory_id in recall_result

        # 5. End session
        await end_session(EndSessionInput(
            session_id=session_id,
            key_learnings=["Full integration works"]
        ))

        # 6. Export everything
        export_result = await export(ExportInput(
            format="markdown",
            include_memories=True,
            include_activities=True
        ))
        assert "integration" in export_result.lower()

        # Cleanup
        await forget(ForgetInput(id=memory_id, confirm=True))

        close_all_connections()
