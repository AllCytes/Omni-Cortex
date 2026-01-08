# Omni-Cortex Dashboard Enhancements v2

## Overview

Add 6 new features to the Omni-Cortex web dashboard to provide better observability, memory management, and data visualization. These features align with IndyDevDan's TAC methodology for agent observability.

## Features

| # | Feature | Priority | Complexity |
|---|---------|----------|------------|
| 1 | Memory Relationships Graph | High | Medium |
| 2 | Session Context Viewer | High | Low |
| 3 | Freshness Review Panel | High | Low |
| 4 | Activity Heatmap | Medium | Medium |
| 5 | Tool Usage Stats | Medium | Low |
| 6 | Memory Growth Chart | Medium | Low |

## Architecture

### Frontend Stack
- Vue 3 + Composition API
- Pinia for state management
- TailwindCSS for styling
- D3.js for graph visualization (new dependency)
- Chart.js for charts (new dependency)

### Backend Stack
- FastAPI
- SQLite with existing cortex.db schema
- WebSocket for real-time updates

---

## Phase 1: Statistics & Charts (Features 4, 5, 6)

### 1.1 Install Chart Dependencies

```bash
cd dashboard/frontend
npm install chart.js vue-chartjs
```

### 1.2 Backend Endpoints

Add to `dashboard/backend/main.py`:

```python
@app.get("/api/stats/activity-heatmap")
async def get_activity_heatmap(project: str, days: int = 90):
    """Get activity counts grouped by day for heatmap visualization."""
    # Returns: [{"date": "2026-01-07", "count": 15}, ...]

@app.get("/api/stats/tool-usage")
async def get_tool_usage(project: str, limit: int = 10):
    """Get tool usage statistics."""
    # Returns: [{"tool_name": "Read", "count": 150, "success_rate": 0.98}, ...]

@app.get("/api/stats/memory-growth")
async def get_memory_growth(project: str, days: int = 30):
    """Get memory creation over time."""
    # Returns: [{"date": "2026-01-07", "count": 5, "cumulative": 535}, ...]
```

Add to `dashboard/backend/database.py`:

```python
def get_activity_heatmap(db_path: str, days: int = 90) -> list[dict]:
    """Get activity counts grouped by day."""
    conn = get_connection(db_path)
    query = """
        SELECT date(timestamp) as date, COUNT(*) as count
        FROM activities
        WHERE timestamp >= date('now', ?)
        GROUP BY date(timestamp)
        ORDER BY date
    """
    cursor = conn.execute(query, (f'-{days} days',))
    return [{"date": row["date"], "count": row["count"]} for row in cursor.fetchall()]

def get_tool_usage(db_path: str, limit: int = 10) -> list[dict]:
    """Get tool usage statistics."""
    conn = get_connection(db_path)
    query = """
        SELECT
            tool_name,
            COUNT(*) as count,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
        FROM activities
        WHERE tool_name IS NOT NULL
        GROUP BY tool_name
        ORDER BY count DESC
        LIMIT ?
    """
    cursor = conn.execute(query, (limit,))
    return [dict(row) for row in cursor.fetchall()]

def get_memory_growth(db_path: str, days: int = 30) -> list[dict]:
    """Get memory creation over time with cumulative totals."""
    conn = get_connection(db_path)
    query = """
        WITH daily_counts AS (
            SELECT date(created_at) as date, COUNT(*) as count
            FROM memories
            WHERE created_at >= date('now', ?)
            GROUP BY date(created_at)
        )
        SELECT
            date,
            count,
            SUM(count) OVER (ORDER BY date) as cumulative
        FROM daily_counts
        ORDER BY date
    """
    cursor = conn.execute(query, (f'-{days} days',))
    return [dict(row) for row in cursor.fetchall()]
```

### 1.3 Frontend Components

Create `dashboard/frontend/src/components/charts/ActivityHeatmap.vue`:
- GitHub-style calendar heatmap showing daily activity
- Color intensity based on activity count
- Tooltip showing date and count on hover
- Use CSS Grid for calendar layout

Create `dashboard/frontend/src/components/charts/ToolUsageChart.vue`:
- Horizontal bar chart showing top tools
- Include success rate indicator
- Use vue-chartjs Bar component

Create `dashboard/frontend/src/components/charts/MemoryGrowthChart.vue`:
- Line chart showing cumulative memory growth
- Area fill under line
- Use vue-chartjs Line component

### 1.4 Integrate into StatsPanel

Update `dashboard/frontend/src/components/StatsPanel.vue`:
- Add three chart components in a grid layout
- Add API calls to fetch chart data
- Add loading states for each chart

---

## Phase 2: Session & Freshness (Features 2, 3)

### 2.1 Backend Endpoints

Add to `dashboard/backend/main.py`:

```python
@app.get("/api/sessions/recent")
async def get_recent_sessions(project: str, limit: int = 5):
    """Get recent sessions with summaries."""
    # Returns sessions with activity counts

@app.post("/api/memories/bulk-update-status")
async def bulk_update_status(
    project: str,
    memory_ids: list[str],
    status: str
):
    """Update status for multiple memories at once."""
```

Add to `dashboard/backend/database.py`:

```python
def get_recent_sessions(db_path: str, limit: int = 5) -> list[dict]:
    """Get recent sessions with activity counts and summaries."""
    conn = get_connection(db_path)
    query = """
        SELECT
            s.id,
            s.started_at,
            s.ended_at,
            s.summary,
            COUNT(DISTINCT a.id) as activity_count,
            COUNT(DISTINCT m.id) as memory_count
        FROM sessions s
        LEFT JOIN activities a ON a.session_id = s.id
        LEFT JOIN memories m ON date(m.created_at) BETWEEN date(s.started_at) AND COALESCE(date(s.ended_at), date('now'))
        GROUP BY s.id
        ORDER BY s.started_at DESC
        LIMIT ?
    """
    cursor = conn.execute(query, (limit,))
    return [dict(row) for row in cursor.fetchall()]

def bulk_update_memory_status(db_path: str, memory_ids: list[str], status: str) -> int:
    """Update status for multiple memories. Returns count updated."""
    conn = get_connection(db_path, writable=True)
    placeholders = ','.join('?' * len(memory_ids))
    query = f"UPDATE memories SET status = ? WHERE id IN ({placeholders})"
    cursor = conn.execute(query, [status] + memory_ids)
    conn.commit()
    return cursor.rowcount
```

### 2.2 Frontend Components

Create `dashboard/frontend/src/components/SessionContextViewer.vue`:
- Card showing "Last session" context
- Session summary text
- Activity count badge
- Memory count badge
- Timestamp with relative time
- Expandable to show recent sessions list

Create `dashboard/frontend/src/components/FreshnessReviewPanel.vue`:
- Shows memories grouped by status needing review
- Checkboxes for bulk selection
- Quick action buttons: "Mark Fresh", "Mark Outdated", "Archive"
- Filter by days since last access
- Progress indicator showing review completion

### 2.3 Integration

- Add SessionContextViewer to App.vue header area or as collapsible panel
- Add FreshnessReviewPanel as new tab or section in Memories view
- Add keyboard shortcut (Ctrl+R) to open review panel

---

## Phase 3: Memory Relationships Graph (Feature 1)

### 3.1 Install D3.js

```bash
cd dashboard/frontend
npm install d3 @types/d3
```

### 3.2 Backend Endpoints

Add to `dashboard/backend/main.py`:

```python
@app.get("/api/relationships")
async def get_relationships(project: str, memory_id: Optional[str] = None):
    """Get memory relationships for graph visualization."""

@app.get("/api/relationships/graph")
async def get_relationship_graph(project: str, center_id: Optional[str] = None, depth: int = 2):
    """Get graph data centered on a memory with configurable depth."""
```

Add to `dashboard/backend/database.py`:

```python
def get_relationships(db_path: str, memory_id: Optional[str] = None) -> list[dict]:
    """Get memory relationships."""
    conn = get_connection(db_path)
    query = """
        SELECT
            r.source_id,
            r.target_id,
            r.relationship_type,
            r.strength,
            ms.content as source_content,
            ms.type as source_type,
            mt.content as target_content,
            mt.type as target_type
        FROM memory_relationships r
        JOIN memories ms ON r.source_id = ms.id
        JOIN memories mt ON r.target_id = mt.id
    """
    if memory_id:
        query += " WHERE r.source_id = ? OR r.target_id = ?"
        cursor = conn.execute(query, (memory_id, memory_id))
    else:
        cursor = conn.execute(query)
    return [dict(row) for row in cursor.fetchall()]

def get_relationship_graph(db_path: str, center_id: Optional[str] = None, depth: int = 2) -> dict:
    """Get graph data with nodes and edges for D3 visualization."""
    relationships = get_relationships(db_path, center_id)

    nodes = {}
    edges = []

    for rel in relationships:
        # Add source node
        if rel["source_id"] not in nodes:
            nodes[rel["source_id"]] = {
                "id": rel["source_id"],
                "content": rel["source_content"][:100],
                "type": rel["source_type"]
            }
        # Add target node
        if rel["target_id"] not in nodes:
            nodes[rel["target_id"]] = {
                "id": rel["target_id"],
                "content": rel["target_content"][:100],
                "type": rel["target_type"]
            }
        # Add edge
        edges.append({
            "source": rel["source_id"],
            "target": rel["target_id"],
            "type": rel["relationship_type"],
            "strength": rel["strength"]
        })

    return {"nodes": list(nodes.values()), "edges": edges}
```

### 3.3 Frontend Component

Create `dashboard/frontend/src/components/RelationshipGraph.vue`:

```vue
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as d3 from 'd3'

// D3 force-directed graph implementation
// - Nodes colored by memory type
// - Edges styled by relationship type (solid/dashed/dotted)
// - Edge thickness by strength
// - Zoom and pan support
// - Click node to center and load related
// - Tooltip showing memory preview
</script>
```

Key implementation details:
- Use D3 force simulation with collision detection
- Color nodes using TYPE_COLORS from types/index.ts
- Edge types: solid (related_to), dashed (supersedes), dotted (derived_from), red (contradicts)
- Add zoom controls and reset button
- Click node to select memory in MemoryDetail panel
- Double-click to recenter graph on that node

### 3.4 Integration

- Add "Relationships" tab to main navigation
- Or add graph view button to MemoryDetail panel
- Show mini-graph preview in memory cards (optional)

---

## File Structure

New files to create:

```
dashboard/
├── backend/
│   └── database.py (update)
│   └── main.py (update)
├── frontend/
│   └── src/
│       └── components/
│           └── charts/
│               ├── ActivityHeatmap.vue (new)
│               ├── ToolUsageChart.vue (new)
│               └── MemoryGrowthChart.vue (new)
│           ├── SessionContextViewer.vue (new)
│           ├── FreshnessReviewPanel.vue (new)
│           └── RelationshipGraph.vue (new)
│       └── services/
│           └── api.ts (update - add new endpoints)
```

---

## Testing Strategy

### Unit Tests
- Test each database function with mock data
- Test API endpoints return correct shapes

### Component Tests
- Test charts render with mock data
- Test bulk update functionality
- Test graph interactions

### Integration Tests
- Test full flow: API -> Store -> Component
- Test WebSocket updates for new data

---

## Success Criteria

- [ ] Activity Heatmap shows 90 days of activity data
- [ ] Tool Usage shows top 10 tools with success rates
- [ ] Memory Growth shows cumulative chart
- [ ] Session Viewer shows last 5 sessions with summaries
- [ ] Freshness Panel allows bulk status updates
- [ ] Relationship Graph renders nodes and edges
- [ ] All features work in both light and dark mode
- [ ] No console errors
- [ ] Responsive on different screen sizes

---

## Prompt for Next Session

Copy this to start building:

```
/build specs/dashboard-enhancements-v2.md

Build the Omni-Cortex Dashboard Enhancements in 3 phases:

Phase 1: Add chart.js and vue-chartjs, create ActivityHeatmap, ToolUsageChart, and MemoryGrowthChart components with backend endpoints.

Phase 2: Create SessionContextViewer and FreshnessReviewPanel components with bulk update functionality.

Phase 3: Add D3.js and create RelationshipGraph component for memory relationship visualization.

Start with Phase 1. After completing each phase, verify it works before moving to the next.
```

Or for parallel execution with orchestrator:

```
/orchestrate specs/dashboard-enhancements-v2.md

Create 3 agents to work in parallel:
1. Charts Agent: Implement Phase 1 (ActivityHeatmap, ToolUsageChart, MemoryGrowthChart)
2. Session Agent: Implement Phase 2 (SessionContextViewer, FreshnessReviewPanel)
3. Graph Agent: Implement Phase 3 (RelationshipGraph with D3.js)

Each agent should complete their phase and verify it works before reporting done.
```
