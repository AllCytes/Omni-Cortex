"""FastAPI backend for Omni-Cortex Web Dashboard."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from database import (
    get_activities,
    get_all_tags,
    get_memories,
    get_memory_by_id,
    get_memory_stats,
    get_sessions,
    get_timeline,
    get_type_distribution,
    search_memories,
)
from models import FilterParams, ProjectInfo
from project_scanner import scan_projects
from websocket_manager import manager


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


# --- Health Check ---


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "websocket_connections": manager.connection_count,
    }


def run():
    """Run the dashboard server."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8765,
        reload=True,
        reload_dirs=["dashboard/backend"],
    )


if __name__ == "__main__":
    run()
