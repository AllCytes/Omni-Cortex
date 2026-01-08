# Omni-Cortex Web Dashboard

A web-based dashboard for viewing and managing Omni-Cortex memories, activities, and sessions.

## Features

- **Memory Browser**: View, search, filter, and manage memories
- **Project Switcher**: Switch between project databases and global index
- **Real-time Updates**: WebSocket-based live updates when database changes
- **Statistics Dashboard**: Memory counts, types, tags, and activity patterns
- **Filter Panel**: Filter by type, status, tags, and importance

## Quick Start

### Backend

```bash
cd dashboard/backend

# Install dependencies
uv pip install -e .

# Run the server
uv run uvicorn main:app --host 0.0.0.0 --port 8765 --reload
```

### Frontend

```bash
cd dashboard/frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Open http://localhost:5173 in your browser.

## Architecture

### Backend (FastAPI)
- `main.py` - FastAPI app with REST endpoints and WebSocket
- `database.py` - SQLite query functions (read-only)
- `models.py` - Pydantic response models
- `project_scanner.py` - Discovers all .omni-cortex databases
- `websocket_manager.py` - WebSocket broadcast manager

### Frontend (Vue 3 + Vite)
- `stores/dashboardStore.ts` - Pinia state management
- `composables/useWebSocket.ts` - WebSocket connection handling
- `services/api.ts` - Axios API client
- `components/` - Vue components for UI

## API Endpoints

### REST
- `GET /api/projects` - List all project databases
- `GET /api/memories` - List memories with filters
- `GET /api/memories/{id}` - Get single memory
- `GET /api/memories/stats/summary` - Memory statistics
- `GET /api/search` - Search memories
- `GET /api/activities` - Activity log
- `GET /api/timeline` - Timeline view
- `GET /api/tags` - All tags with counts
- `GET /api/sessions` - Recent sessions

### WebSocket
- `WS /ws` - Real-time updates

## Tech Stack

- **Backend**: FastAPI, Uvicorn, SQLite, Watchdog
- **Frontend**: Vue 3, Vite, Pinia, TailwindCSS, Axios, Lucide Icons
