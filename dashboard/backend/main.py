"""FastAPI backend for Omni-Cortex Web Dashboard."""
# Trigger reload for relationship graph column fix

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from database import (
    bulk_update_memory_status,
    delete_memory,
    get_activities,
    get_activity_heatmap,
    get_all_tags,
    get_memories,
    get_memories_needing_review,
    get_memory_by_id,
    get_memory_growth,
    get_memory_stats,
    get_recent_sessions,
    get_relationship_graph,
    get_relationships,
    get_sessions,
    get_timeline,
    get_tool_usage,
    get_type_distribution,
    search_memories,
    update_memory,
)
from models import ChatRequest, ChatResponse, FilterParams, MemoryUpdate, ProjectInfo
from project_scanner import scan_projects
from websocket_manager import manager
import chat_service


class DatabaseChangeHandler(FileSystemEventHandler):
    """Handle database file changes for real-time updates."""

    def __init__(self, ws_manager, loop):
        self.ws_manager = ws_manager
        self.loop = loop
        self._debounce_task: Optional[asyncio.Task] = None
        self._last_path: Optional[str] = None

    def on_modified(self, event):
        if event.src_path.endswith("cortex.db") or event.src_path.endswith("global.db"):
            # Debounce rapid changes
            self._last_path = event.src_path
            if self._debounce_task is None or self._debounce_task.done():
                self._debounce_task = asyncio.run_coroutine_threadsafe(
                    self._debounced_notify(), self.loop
                )

    async def _debounced_notify(self):
        await asyncio.sleep(0.5)  # Wait for rapid changes to settle
        if self._last_path:
            await self.ws_manager.broadcast("database_changed", {"path": self._last_path})


# File watcher
observer: Optional[Observer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage file watcher lifecycle."""
    global observer
    loop = asyncio.get_event_loop()
    handler = DatabaseChangeHandler(manager, loop)
    observer = Observer()

    # Watch common project directories
    watch_paths = [
        Path.home() / ".omni-cortex",
        Path("D:/Projects"),
    ]

    for watch_path in watch_paths:
        if watch_path.exists():
            observer.schedule(handler, str(watch_path), recursive=True)
            print(f"[Watcher] Monitoring: {watch_path}")

    observer.start()
    print("[Server] File watcher started")

    yield

    observer.stop()
    observer.join()
    print("[Server] File watcher stopped")


# FastAPI app
app = FastAPI(
    title="Omni-Cortex Dashboard",
    description="Web dashboard for viewing and managing Omni-Cortex memories",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for production build
DASHBOARD_DIR = Path(__file__).parent.parent
DIST_DIR = DASHBOARD_DIR / "frontend" / "dist"


def setup_static_files():
    """Mount static files if dist directory exists (production build)."""
    if DIST_DIR.exists():
        # Mount assets directory
        assets_dir = DIST_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
            print(f"[Static] Serving assets from: {assets_dir}")


# Call setup at module load
setup_static_files()


# --- REST Endpoints ---


@app.get("/api/projects", response_model=list[ProjectInfo])
async def list_projects():
    """List all discovered omni-cortex project databases."""
    return scan_projects()


@app.get("/api/memories")
async def list_memories(
    project: str = Query(..., description="Path to the database file"),
    memory_type: Optional[str] = Query(None, alias="type"),
    status: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    min_importance: Optional[int] = None,
    max_importance: Optional[int] = None,
    sort_by: str = "last_accessed",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
):
    """Get memories with filtering and pagination."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    filters = FilterParams(
        memory_type=memory_type,
        status=status,
        tags=tags.split(",") if tags else None,
        search=search,
        min_importance=min_importance,
        max_importance=max_importance,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )

    return get_memories(project, filters)


# NOTE: These routes MUST be defined before /api/memories/{memory_id} to avoid path conflicts
@app.get("/api/memories/needs-review")
async def get_memories_needing_review_endpoint(
    project: str = Query(..., description="Path to the database file"),
    days_threshold: int = 30,
    limit: int = 50,
):
    """Get memories that may need freshness review."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_memories_needing_review(project, days_threshold, limit)


@app.post("/api/memories/bulk-update-status")
async def bulk_update_status_endpoint(
    project: str = Query(..., description="Path to the database file"),
    memory_ids: list[str] = [],
    status: str = "fresh",
):
    """Update status for multiple memories at once."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    valid_statuses = ["fresh", "needs_review", "outdated", "archived"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    count = bulk_update_memory_status(project, memory_ids, status)

    # Notify connected clients
    await manager.broadcast("memories_bulk_updated", {"count": count, "status": status})

    return {"updated_count": count, "status": status}


@app.get("/api/memories/{memory_id}")
async def get_memory(
    memory_id: str,
    project: str = Query(..., description="Path to the database file"),
):
    """Get a single memory by ID."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    memory = get_memory_by_id(project, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@app.put("/api/memories/{memory_id}")
async def update_memory_endpoint(
    memory_id: str,
    updates: MemoryUpdate,
    project: str = Query(..., description="Path to the database file"),
):
    """Update a memory."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    updated = update_memory(project, memory_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Memory not found")

    # Notify connected clients
    await manager.broadcast("memory_updated", updated.model_dump(by_alias=True))
    return updated


@app.delete("/api/memories/{memory_id}")
async def delete_memory_endpoint(
    memory_id: str,
    project: str = Query(..., description="Path to the database file"),
):
    """Delete a memory."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    deleted = delete_memory(project, memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")

    # Notify connected clients
    await manager.broadcast("memory_deleted", {"id": memory_id})
    return {"message": "Memory deleted", "id": memory_id}


@app.get("/api/memories/stats/summary")
async def memory_stats(
    project: str = Query(..., description="Path to the database file"),
):
    """Get memory statistics."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_memory_stats(project)


@app.get("/api/search")
async def search(
    q: str = Query(..., min_length=1),
    project: str = Query(..., description="Path to the database file"),
    limit: int = 20,
):
    """Search memories."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return search_memories(project, q, limit)


@app.get("/api/activities")
async def list_activities(
    project: str = Query(..., description="Path to the database file"),
    event_type: Optional[str] = None,
    tool_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Get activity log entries."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_activities(project, event_type, tool_name, limit, offset)


@app.get("/api/timeline")
async def get_timeline_view(
    project: str = Query(..., description="Path to the database file"),
    hours: int = 24,
    include_memories: bool = True,
    include_activities: bool = True,
):
    """Get timeline of recent activity."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_timeline(project, hours, include_memories, include_activities)


@app.get("/api/tags")
async def list_tags(
    project: str = Query(..., description="Path to the database file"),
):
    """Get all tags with counts."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_all_tags(project)


@app.get("/api/types")
async def list_types(
    project: str = Query(..., description="Path to the database file"),
):
    """Get memory type distribution."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_type_distribution(project)


@app.get("/api/sessions")
async def list_sessions(
    project: str = Query(..., description="Path to the database file"),
    limit: int = 20,
):
    """Get recent sessions."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_sessions(project, limit)


# --- Stats Endpoints for Charts ---


@app.get("/api/stats/activity-heatmap")
async def get_activity_heatmap_endpoint(
    project: str = Query(..., description="Path to the database file"),
    days: int = 90,
):
    """Get activity counts grouped by day for heatmap visualization."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_activity_heatmap(project, days)


@app.get("/api/stats/tool-usage")
async def get_tool_usage_endpoint(
    project: str = Query(..., description="Path to the database file"),
    limit: int = 10,
):
    """Get tool usage statistics."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_tool_usage(project, limit)


@app.get("/api/stats/memory-growth")
async def get_memory_growth_endpoint(
    project: str = Query(..., description="Path to the database file"),
    days: int = 30,
):
    """Get memory creation over time."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_memory_growth(project, days)


# --- Session Context Endpoints ---


@app.get("/api/sessions/recent")
async def get_recent_sessions_endpoint(
    project: str = Query(..., description="Path to the database file"),
    limit: int = 5,
):
    """Get recent sessions with summaries."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_recent_sessions(project, limit)


# --- Relationship Graph Endpoints ---


@app.get("/api/relationships")
async def get_relationships_endpoint(
    project: str = Query(..., description="Path to the database file"),
    memory_id: Optional[str] = None,
):
    """Get memory relationships for graph visualization."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_relationships(project, memory_id)


@app.get("/api/relationships/graph")
async def get_relationship_graph_endpoint(
    project: str = Query(..., description="Path to the database file"),
    center_id: Optional[str] = None,
    depth: int = 2,
):
    """Get graph data centered on a memory with configurable depth."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    return get_relationship_graph(project, center_id, depth)


# --- Chat Endpoint ---


@app.get("/api/chat/status")
async def chat_status():
    """Check if chat service is available."""
    return {
        "available": chat_service.is_available(),
        "message": "Chat is available" if chat_service.is_available() else "Set GEMINI_API_KEY environment variable to enable chat",
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_memories(
    request: ChatRequest,
    project: str = Query(..., description="Path to the database file"),
):
    """Ask a natural language question about memories."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    result = await chat_service.ask_about_memories(
        project,
        request.question,
        request.max_memories,
    )

    return ChatResponse(**result)


# --- WebSocket Endpoint ---


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    client_id = await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await manager.send_to_client(client_id, "connected", {"client_id": client_id})

        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_text()
            # Echo back for ping/pong
            if data == "ping":
                await manager.send_to_client(client_id, "pong", {})
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
    except Exception as e:
        print(f"[WS] Error: {e}")
        await manager.disconnect(client_id)


# --- Export Endpoints ---


@app.get("/api/export")
async def export_memories(
    project: str = Query(..., description="Path to the database file"),
    format: str = Query("json", description="Export format: json, markdown, csv"),
    memory_ids: Optional[str] = Query(None, description="Comma-separated memory IDs to export, or all if empty"),
    include_relationships: bool = Query(True, description="Include memory relationships"),
):
    """Export memories to specified format."""
    from fastapi.responses import Response
    import csv
    import io

    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    # Get memories
    if memory_ids:
        ids = memory_ids.split(",")
        memories = [get_memory_by_id(project, mid) for mid in ids if mid.strip()]
        memories = [m for m in memories if m is not None]
    else:
        from models import FilterParams
        filters = FilterParams(limit=1000, offset=0, sort_by="created_at", sort_order="desc")
        memories = get_memories(project, filters)

    # Get relationships if requested
    relationships = []
    if include_relationships:
        relationships = get_relationships(project)

    if format == "json":
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "project": project,
            "memory_count": len(memories),
            "memories": [m.model_dump(by_alias=True) for m in memories],
            "relationships": relationships if include_relationships else [],
        }
        return Response(
            content=json.dumps(export_data, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
        )

    elif format == "markdown":
        md_lines = [
            f"# Omni-Cortex Memory Export",
            f"",
            f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Memories:** {len(memories)}",
            f"",
            "---",
            "",
        ]
        for m in memories:
            md_lines.extend([
                f"## {m.type.title()}: {m.content[:50]}{'...' if len(m.content) > 50 else ''}",
                f"",
                f"**ID:** `{m.id}`",
                f"**Type:** {m.type}",
                f"**Status:** {m.status}",
                f"**Importance:** {m.importance_score}",
                f"**Created:** {m.created_at}",
                f"**Tags:** {', '.join(m.tags) if m.tags else 'None'}",
                f"",
                "### Content",
                f"",
                m.content,
                f"",
                "### Context",
                f"",
                m.context or "_No context_",
                f"",
                "---",
                "",
            ])
        return Response(
            content="\n".join(md_lines),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"}
        )

    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "type", "status", "importance", "content", "context", "tags", "created_at", "last_accessed"])
        for m in memories:
            writer.writerow([
                m.id,
                m.type,
                m.status,
                m.importance_score,
                m.content,
                m.context or "",
                ",".join(m.tags) if m.tags else "",
                m.created_at,
                m.last_accessed or "",
            ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}. Use json, markdown, or csv.")


# --- Health Check ---


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "websocket_connections": manager.connection_count,
    }


# --- Static File Serving (SPA) ---
# These routes must come AFTER all API routes


@app.get("/")
async def serve_root():
    """Serve the frontend index.html."""
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Omni-Cortex Dashboard API", "docs": "/docs"}


@app.get("/{path:path}")
async def serve_spa(path: str):
    """Catch-all route to serve SPA for client-side routing."""
    # Skip API routes and known paths
    if path.startswith(("api/", "ws", "health", "docs", "openapi", "redoc")):
        raise HTTPException(status_code=404, detail="Not found")

    # Check if it's a static file
    file_path = DIST_DIR / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))

    # Otherwise serve index.html for SPA routing
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    raise HTTPException(status_code=404, detail="Not found")


def run():
    """Run the dashboard server."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8765,
        reload=True,
        reload_dirs=[str(Path(__file__).parent)],
    )


if __name__ == "__main__":
    run()
