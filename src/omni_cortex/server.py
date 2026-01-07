#!/usr/bin/env python3
"""Omni Cortex MCP Server - Universal Memory System for Claude Code.

This server provides a dual-layer memory system combining:
- Activity logging (audit trail of all tool calls and decisions)
- Knowledge storage (distilled insights, solutions, and learnings)

Features:
- 15 tools across 4 categories: Activities, Memories, Sessions, Utilities
- Full-text search with FTS5
- Auto-categorization and smart tagging
- Multi-factor relevance ranking
- Session continuity ("Last time you were working on...")
- Importance decay over time
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from mcp.server.fastmcp import FastMCP

from .database.connection import init_database, close_all_connections
from .tools.memories import register_memory_tools
from .tools.activities import register_activity_tools
from .tools.sessions import register_session_tools
from .tools.utilities import register_utility_tools


@asynccontextmanager
async def lifespan(mcp: FastMCP) -> AsyncGenerator[dict, None]:
    """Manage server lifecycle - initialize and cleanup resources."""
    # Initialize database on startup
    try:
        init_database()
        init_database(is_global=True)
    except Exception as e:
        print(f"Warning: Failed to initialize database: {e}")

    yield {}

    # Cleanup on shutdown
    close_all_connections()


# Create the MCP server
mcp = FastMCP(
    "omni_cortex",
    lifespan=lifespan,
)

# Register all tools
register_memory_tools(mcp)
register_activity_tools(mcp)
register_session_tools(mcp)
register_utility_tools(mcp)


# === MCP Resources ===

@mcp.resource("cortex://stats")
async def get_stats() -> str:
    """Get statistics about the Cortex database."""
    try:
        conn = init_database()
        cursor = conn.cursor()

        stats = {}

        # Count memories
        cursor.execute("SELECT COUNT(*) FROM memories")
        stats["total_memories"] = cursor.fetchone()[0]

        # Count by type
        cursor.execute("""
            SELECT type, COUNT(*) as cnt
            FROM memories
            GROUP BY type
            ORDER BY cnt DESC
        """)
        stats["memories_by_type"] = {row["type"]: row["cnt"] for row in cursor.fetchall()}

        # Count by status
        cursor.execute("""
            SELECT status, COUNT(*) as cnt
            FROM memories
            GROUP BY status
        """)
        stats["memories_by_status"] = {row["status"]: row["cnt"] for row in cursor.fetchall()}

        # Count activities
        cursor.execute("SELECT COUNT(*) FROM activities")
        stats["total_activities"] = cursor.fetchone()[0]

        # Count sessions
        cursor.execute("SELECT COUNT(*) FROM sessions")
        stats["total_sessions"] = cursor.fetchone()[0]

        import json
        return json.dumps(stats, indent=2)

    except Exception as e:
        return f"Error getting stats: {e}"


@mcp.resource("cortex://types")
async def get_memory_types() -> str:
    """Get available memory types with descriptions."""
    types = {
        "general": "General information or notes",
        "warning": "Warnings, cautions, things to avoid",
        "tip": "Tips, tricks, best practices",
        "config": "Configuration, settings, environment variables",
        "troubleshooting": "Problem solving, debugging guides",
        "code": "Code snippets, functions, algorithms",
        "error": "Errors, exceptions, failure cases",
        "solution": "Solutions to problems, fixes",
        "command": "CLI commands, terminal operations",
        "concept": "Definitions, explanations, concepts",
        "decision": "Decisions made, architectural choices",
    }
    import json
    return json.dumps(types, indent=2)


@mcp.resource("cortex://config")
async def get_config() -> str:
    """Get current Cortex configuration."""
    from .config import load_config

    config = load_config()
    import json
    return json.dumps({
        "schema_version": config.schema_version,
        "embedding_model": config.embedding_model,
        "embedding_enabled": config.embedding_enabled,
        "decay_rate_per_day": config.decay_rate_per_day,
        "freshness_review_days": config.freshness_review_days,
        "auto_provide_context": config.auto_provide_context,
        "context_depth": config.context_depth,
        "default_search_mode": config.default_search_mode,
        "global_sync_enabled": config.global_sync_enabled,
    }, indent=2)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
