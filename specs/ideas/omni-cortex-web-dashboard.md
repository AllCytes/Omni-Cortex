# Omni-Cortex Web Dashboard Implementation Plan

## Problem Statement

Users cannot easily view the contents of Omni-Cortex SQLite databases (.omni-cortex/cortex.db) because:
1. VS Code cannot display binary SQLite files
2. No visual interface exists for browsing memories, activities, sessions
3. No way to quickly switch between project databases and the global index
4. No real-time visibility into what's happening across projects

## Objectives

1. **Memory Browser**: View, search, filter, and manage memories with full CRUD
2. **Project Switcher**: Dropdown to switch between all project databases + global index
3. **Live Updates**: Real-time WebSocket updates when memories/activities change
4. **Timeline View**: Chronological activity visualization
5. **Statistics Dashboard**: Memory counts, types, tags, activity patterns

## Tech Stack Decision (Based on IndyDevDan Patterns)

### Frontend
- **Framework**: Vue 3 with Composition API + TypeScript
- **Build Tool**: Vite 5
- **State Management**: Pinia
- **Real-time**: Native WebSocket API
- **HTTP Client**: Axios
- **Styling**: TailwindCSS (quick iteration, utility-first)
- **Icons**: lucide-vue-next

### Backend
- **Framework**: FastAPI (Python) - aligns with omni-cortex being Python
- **Server**: Uvicorn
- **Database**: Direct SQLite access (no ORM needed - existing schema)
- **Real-time**: WebSocket via FastAPI
- **Validation**: Pydantic v2

### Why This Stack?
1. **Consistency**: omni-cortex is Python, so FastAPI backend keeps it homogeneous
2. **Speed**: Vue 3 + Vite is IndyDevDan's proven fast stack
3. **Real-time**: WebSocket pattern proven in his orchestrator projects
4. **Simplicity**: Direct SQLite reads, no migration needed

## Project Structure

```
omni-cortex/
├── src/omni_cortex/          # Existing MCP server
├── dashboard/                 # NEW: Web Dashboard
│   ├── backend/
│   │   ├── main.py           # FastAPI app, routes, WebSocket
│   │   ├── database.py       # SQLite connection & queries
│   │   ├── models.py         # Pydantic response models
│   │   ├── websocket_manager.py  # WebSocket broadcast
│   │   ├── project_scanner.py    # Find all .omni-cortex databases
│   │   └── pyproject.toml    # Backend dependencies
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.vue
│   │   │   ├── main.ts
│   │   │   ├── components/
│   │   │   │   ├── AppHeader.vue
│   │   │   │   ├── ProjectSwitcher.vue
│   │   │   │   ├── MemoryBrowser.vue
│   │   │   │   ├── MemoryCard.vue
│   │   │   │   ├── MemoryDetail.vue
│   │   │   │   ├── FilterPanel.vue
│   │   │   │   ├── ActivityTimeline.vue
│   │   │   │   ├── StatsPanel.vue
│   │   │   │   └── SearchBar.vue
│   │   │   ├── composables/
│   │   │   │   ├── useWebSocket.ts
│   │   │   │   ├── useMemories.ts
│   │   │   │   ├── useFilters.ts
│   │   │   │   └── useProjects.ts
│   │   │   ├── stores/
│   │   │   │   └── dashboardStore.ts
│   │   │   ├── services/
│   │   │   │   ├── api.ts
│   │   │   │   └── memoryService.ts
│   │   │   └── types/
│   │   │       └── index.ts
│   │   ├── index.html
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   └── tailwind.config.js
│   └── README.md
```

## Phase 1: Backend Foundation

### Step 1.1: Project Scanner
Create `project_scanner.py` to discover all omni-cortex databases:

```python
# Scan for:
# 1. ~/.omni-cortex/global.db (global index)
# 2. All .omni-cortex/cortex.db in common project directories
# 3. Parse paths from global.db sync records

def scan_projects() -> list[ProjectInfo]:
    """Return list of {name, path, db_path, last_modified}"""
```

**Directories to scan:**
- `D:\Projects\*\.omni-cortex\cortex.db`
- `~/.omni-cortex/global.db`
- Any paths stored in global.db

### Step 1.2: Database Queries
Create `database.py` with read-only queries:

```python
# Memory queries
get_memories(filters, sort, limit, offset)
get_memory_by_id(id)
get_memory_stats()
search_memories(query, mode)

# Activity queries
get_activities(filters, limit, offset)
get_timeline(hours, group_by)

# Session queries
get_sessions(limit)
get_session_summary(session_id)

# Tag/Type queries
get_all_tags()
get_type_distribution()
```

### Step 1.3: FastAPI Application
Create `main.py`:

```python
# REST Endpoints
GET  /api/projects                    # List all project databases
GET  /api/memories                    # List memories with filters
GET  /api/memories/{id}               # Get single memory
GET  /api/memories/stats              # Statistics
GET  /api/activities                  # List activities
GET  /api/timeline                    # Timeline data
GET  /api/tags                        # All tags
GET  /api/sessions                    # Recent sessions

# WebSocket
WS   /ws                              # Real-time updates

# Query params for /api/memories:
# - project: string (db path)
# - type: string
# - status: string
# - tags: string (comma-separated)
# - search: string
# - sort_by: string (created_at, importance_score, last_accessed)
# - sort_order: asc|desc
# - limit: int
# - offset: int
```

### Step 1.4: WebSocket Manager
Create `websocket_manager.py` (IndyDevDan pattern):

```python
class WebSocketManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str)
    async def disconnect(self, client_id: str)
    async def broadcast(self, event: dict)
    async def send_to_client(self, client_id: str, message: dict)
```

**Events to broadcast:**
- `memory_created` - new memory added
- `memory_updated` - memory modified
- `memory_deleted` - memory removed
- `activity_logged` - new activity
- `project_changed` - user switched projects

## Phase 2: Frontend Foundation

### Step 2.1: Vite + Vue Setup
```bash
cd dashboard/frontend
npm create vite@latest . -- --template vue-ts
npm install pinia axios @vueuse/core lucide-vue-next
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### Step 2.2: Pinia Store
Create `stores/dashboardStore.ts`:

```typescript
export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const currentProject = ref<Project | null>(null)
  const projects = ref<Project[]>([])
  const memories = ref<Memory[]>([])
  const filters = ref<FilterState>({})
  const isConnected = ref(false)

  // WebSocket
  const ws = ref<WebSocket | null>(null)

  // Actions
  const loadProjects = async () => {}
  const switchProject = async (projectPath: string) => {}
  const loadMemories = async () => {}
  const applyFilters = (newFilters: FilterState) => {}
  const connectWebSocket = () => {}

  return { ... }
})
```

### Step 2.3: Core Components

**AppHeader.vue**
- Project switcher dropdown
- Global search input
- Stats summary (total memories, recent activity count)
- Connection status indicator

**ProjectSwitcher.vue**
- Dropdown showing all discovered projects
- "Global Index" option at top
- Last modified timestamp per project
- Memory count per project

**MemoryBrowser.vue**
- Grid/List view toggle
- Infinite scroll or pagination
- Memory cards with preview
- Click to expand detail

**FilterPanel.vue**
- Type filter (checkboxes for all 11 types)
- Status filter (fresh, needs_review, outdated, archived)
- Tag filter (multi-select)
- Importance range slider
- Date range picker

**MemoryCard.vue**
- Content preview (truncated)
- Type badge with color
- Tags as chips
- Importance score bar
- Created/accessed timestamps
- Quick actions (view, edit status, delete)

**ActivityTimeline.vue**
- Vertical timeline
- Group by hour/day/session
- Event type icons
- Tool name + duration
- Expandable details

**StatsPanel.vue**
- Memory count by type (bar chart or donut)
- Tag cloud
- Activity over time (line chart)
- Top accessed memories

## Phase 3: Real-Time Integration

### Step 3.1: File Watcher (Backend)
Monitor database files for changes:

```python
# Use watchdog library to monitor .omni-cortex directories
# On change: broadcast update via WebSocket
```

### Step 3.2: WebSocket Composable (Frontend)
Create `composables/useWebSocket.ts`:

```typescript
export function useWebSocket() {
  const store = useDashboardStore()

  const connect = () => {
    const ws = new WebSocket('ws://localhost:8765/ws')

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleEvent(data)
    }
  }

  const handleEvent = (event: WSEvent) => {
    switch (event.type) {
      case 'memory_created':
        store.addMemory(event.memory)
        break
      case 'memory_updated':
        store.updateMemory(event.memory)
        break
      // ...
    }
  }
}
```

### Step 3.3: Polling Fallback
If WebSocket unavailable, poll every 5 seconds for changes.

## Phase 4: Polish & UX

### Step 4.1: Keyboard Shortcuts
- `/` - Focus search
- `Escape` - Clear filters
- `j/k` - Navigate memories
- `Enter` - Open selected memory
- `1-9` - Quick filter by type

### Step 4.2: Dark/Light Theme
- System preference detection
- Manual toggle
- Persist preference

### Step 4.3: Export Features
- Export filtered memories to JSON
- Export to Markdown
- Copy memory content

### Step 4.4: Responsive Design
- Desktop: 3-column layout (filters | list | detail)
- Tablet: 2-column (collapsible filters)
- Mobile: Single column with drawer navigation

## Files to Create/Modify

### New Files (Backend)
| File | Purpose |
|------|---------|
| `dashboard/backend/main.py` | FastAPI app with routes |
| `dashboard/backend/database.py` | SQLite query functions |
| `dashboard/backend/models.py` | Pydantic models |
| `dashboard/backend/websocket_manager.py` | WS broadcast |
| `dashboard/backend/project_scanner.py` | Find databases |
| `dashboard/backend/pyproject.toml` | Dependencies |

### New Files (Frontend)
| File | Purpose |
|------|---------|
| `dashboard/frontend/src/App.vue` | Main layout |
| `dashboard/frontend/src/stores/dashboardStore.ts` | Pinia store |
| `dashboard/frontend/src/components/*.vue` | UI components |
| `dashboard/frontend/src/composables/*.ts` | Reusable logic |
| `dashboard/frontend/src/services/api.ts` | Axios config |
| `dashboard/frontend/src/types/index.ts` | TypeScript types |

## Validation Commands

```bash
# Backend
cd dashboard/backend
uv run ruff check .
uv run pytest -v

# Frontend
cd dashboard/frontend
npm run lint
npm run type-check
npm run build
```

## Dependencies

### Backend (pyproject.toml)
```toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "websockets>=12.0",
    "watchdog>=4.0.0",
]

[project.optional-dependencies]
dev = ["pytest", "ruff", "httpx"]
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "pinia": "^2.1.7",
    "axios": "^1.6.0",
    "@vueuse/core": "^10.0.0",
    "lucide-vue-next": "^0.300.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

## Estimated Effort

| Phase | Description | Effort |
|-------|-------------|--------|
| Phase 1 | Backend Foundation | 3-4 hours |
| Phase 2 | Frontend Foundation | 4-5 hours |
| Phase 3 | Real-Time Integration | 2-3 hours |
| Phase 4 | Polish & UX | 2-3 hours |
| **Total** | | **11-15 hours** |

## Key IndyDevDan Patterns Applied

1. **WebSocket Real-Time**: Broadcast manager pattern from orchestrator
2. **Pinia State**: Central store with WebSocket integration
3. **Composables**: Reusable logic (useWebSocket, useFilters, etc.)
4. **Component Structure**: Mirrors his frontend organization
5. **Type Safety**: Pydantic + TypeScript throughout
6. **Standard Output**: Console logging for debugging
7. **Separation of Concerns**: Backend/Frontend completely separate

## Questions for User

1. **Port preference?** Default 8765 for backend, 5173 for frontend dev?
2. **Authentication?** Start without auth, add later if needed?
3. **Chart library?** Chart.js, ApexCharts, or skip charts initially?
4. **Memory editing?** Read-only initially, or full CRUD?

## Next Steps

1. Create `dashboard/` directory structure
2. Implement backend foundation (Phase 1)
3. Implement frontend foundation (Phase 2)
4. Add WebSocket real-time updates (Phase 3)
5. Polish and add keyboard shortcuts (Phase 4)
