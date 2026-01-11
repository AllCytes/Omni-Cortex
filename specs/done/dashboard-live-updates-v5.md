# Dashboard Live Updates & Activity Descriptions Enhancement (v5)

**Date:** 2026-01-10
**Priority:** High
**Estimated Effort:** 3-4 hours
**Status:** Partially Implemented

---

## Progress Tracking

### Completed

| Task | File | Status |
|------|------|--------|
| Create LiveElapsedTime.vue component | `components/LiveElapsedTime.vue` | DONE |
| Add typed broadcast methods to WebSocket manager | `backend/websocket_manager.py` | DONE |
| Update DatabaseChangeHandler to broadcast activities | `backend/main.py` | DONE |
| Add activity_logged, session_updated handlers | `composables/useWebSocket.ts` | DONE |
| Add live feed state and handlers to store | `stores/dashboardStore.ts` | DONE |

### Remaining

| Task | File | Notes |
|------|------|-------|
| Update ActivityTimeline.vue | `components/ActivityTimeline.vue` | Use store.activities, add LiveElapsedTime, remove refresh button, add highlight animation |
| Update SessionContextViewer.vue | `components/SessionContextViewer.vue` | Watch lastActivityTimestamp, use store.recentSessions, add LiveElapsedTime |
| Update MemoryBrowser.vue | `components/MemoryBrowser.vue` | Verify reactivity to store.memories changes, remove refresh if exists |
| Add highlight animation CSS | `App.vue` or `main.css` | Use store.isNewActivity() for glow effect on new items |
| Build and test TypeScript | - | Run `npm run build`, fix any type errors |
| Test live streaming end-to-end | - | Manual testing with dashboard + Claude Code session |

### Implementation Details (Already Written)

#### 1. LiveElapsedTime.vue (NEW FILE)
Location: `dashboard/frontend/src/components/LiveElapsedTime.vue`

Features:
- Props: `timestamp`, `compact`, `showIcon`
- Auto-updating every 1 second
- Page Visibility API for performance (pauses when tab hidden)
- Formats: "Just now", "Xs ago", "Xm Ys ago", "Xh Ym ago", "Xd ago"

#### 2. WebSocket Manager Updates
Location: `dashboard/backend/websocket_manager.py`

Added typed broadcast methods:
```python
async def broadcast_activity_logged(self, project: str, activity: dict)
async def broadcast_session_updated(self, project: str, session: dict)
async def broadcast_stats_updated(self, project: str, stats: dict)
```

#### 3. DatabaseChangeHandler Updates
Location: `dashboard/backend/main.py`

- Reduced debounce from 0.5s to 0.3s for faster updates
- Now fetches recent activities when DB changes and broadcasts them
- Broadcasts session updates when activities are logged

#### 4. useWebSocket.ts Updates
Location: `dashboard/frontend/src/composables/useWebSocket.ts`

Added cases for new event types:
```typescript
case 'activity_logged':
  store.handleActivityLogged(event.data)
  break
case 'session_updated':
  store.handleSessionUpdated(event.data)
  break
case 'stats_updated':
  store.handleStatsUpdated(event.data)
  break
```

#### 5. dashboardStore.ts Updates
Location: `dashboard/frontend/src/stores/dashboardStore.ts`

New state:
```typescript
const recentActivities = ref<Activity[]>([])
const recentSessions = ref<Array<...>>([])
const newActivityIds = ref<Set<string>>(new Set())  // For highlight animation
const lastActivityTimestamp = ref<number>(0)
```

New handlers:
- `handleActivityLogged()` - Adds activity to store, marks as new for 3 seconds
- `handleSessionUpdated()` - Updates session in store
- `handleStatsUpdated()` - Updates stats in store
- `isNewActivity(id)` - Helper for highlight animation

Uses forced reactivity pattern:
```typescript
recentActivities.value = [activity, ...recentActivities.value].slice(0, 100)
```

---

## Problem Statement

The current dashboard has several UX issues that break the real-time experience:

1. **Session Context is static** - Shows "3 days ago" data that doesn't update even when new activities are logged in the project
2. **Activities don't stream live** - Requires manual refresh to see new activities
3. **Memories don't auto-update** - Despite WebSocket infrastructure existing, the memory list doesn't update in real-time
4. **No live elapsed timers** - Activities show static timestamps instead of live "2m 34s ago" counters
5. **Activity descriptions missing** - No natural language explanation of what each activity does

## Objectives

1. **Real-time activity streaming** - Like IndyDevDan's orchestrator-agent-with-adws EventStream
2. **Live elapsed timers** - Each activity shows a ticking timer since it was logged
3. **Activity descriptions** - Brief (1-12 words) collapsed, detailed (12-20 words) expanded
4. **Session context auto-update** - Sessions update via WebSocket, not just on page load
5. **Memories live update** - Memory list responds to WebSocket events properly

## IndyDevDan Live Feed Patterns (from orchestrator-agent-with-adws)

Key patterns discovered from analyzing `D:\Projects\TAC\orchestrator-agent-with-adws`:

### 1. Typed Broadcast Methods
```python
# websocket_manager.py
async def broadcast_adw_event(self, adw_id: str, event_data: dict):
    await self.broadcast({"type": "adw_event", "adw_id": adw_id, "event": event_data})
```

### 2. Frontend Message Routing by Type
```typescript
// chatService.ts
switch (message.type) {
  case 'adw_event':
    callbacks.onAdwEvent?.(message)
    break
}
```

### 3. Forced Reactivity in Vue/Pinia
```typescript
// CRITICAL: Spread operator forces Vue to detect changes
allAdwEvents.value[adwId] = [...allAdwEvents.value[adwId], event]
eventStreamEntries.value = [...eventStreamEntries.value]
```

### 4. Silent Failure
Broadcasts fail silently, never block execution. Connection issues don't crash the app.

### 5. Pure Push Model
No polling. Events flow instantly from backend to frontend via WebSocket.

### 6. Auto-scroll on New Events
```typescript
watch(
  () => filteredEvents.value.length,
  async () => {
    if (autoScroll.value) {
      await nextTick()
      bottomRef.value?.scrollIntoView({ behavior: 'smooth' })
    }
  }
)
```

---

## Technical Approach

### Phase 1: Backend - WebSocket Event Broadcasting

**File: `dashboard/backend/main.py`**

Add new event types for activities and sessions:

```python
# In DatabaseChangeHandler.on_modified - detect activity log changes
async def _debounced_notify(self):
    await asyncio.sleep(0.5)
    if self._last_path:
        # Check if activity_log was modified
        await self.ws_manager.broadcast("database_changed", {"path": self._last_path})
        # Also broadcast activity-specific event for more granular updates
        await self.ws_manager.broadcast("activity_logged", {"path": self._last_path})
```

Add new endpoint for activity streaming:

```python
@app.get("/api/activities/stream")
async def stream_activities(
    project: str = Query(...),
    since: Optional[str] = None,  # ISO timestamp to get only newer activities
):
    """Get activities since a timestamp for incremental updates."""
    # Returns only activities newer than 'since'
```

### Phase 2: Frontend - WebSocket Event Handlers

**File: `dashboard/frontend/src/composables/useWebSocket.ts`**

Add handlers for new event types:

```typescript
case 'activity_logged':
  store.handleActivityLogged(event.data)
  break

case 'session_updated':
  store.handleSessionUpdated(event.data)
  break
```

**File: `dashboard/frontend/src/stores/dashboardStore.ts`**

Add new handlers:

```typescript
// State
const recentActivities = ref<Activity[]>([])
const recentSessions = ref<RecentSession[]>([])

// Handlers
function handleActivityLogged(data: { path: string }) {
  // Fetch latest activities for current project
  if (data.path.includes(currentDbPath.value)) {
    loadLatestActivities()
  }
}

function handleSessionUpdated(data: SessionData) {
  // Update session in recentSessions array
}

async function loadLatestActivities() {
  // Fetch last 20 activities and merge with existing
}
```

### Phase 3: Live Elapsed Time Component

**New File: `dashboard/frontend/src/components/LiveElapsedTime.vue`**

Reusable component for live-updating elapsed time:

```vue
<script setup lang="ts">
import { useElapsedTime } from '@/composables/useElapsedTime'

const props = defineProps<{
  timestamp: string
  compact?: boolean  // For collapsed view
}>()

const { formattedElapsed } = useElapsedTime(
  () => new Date(props.timestamp).getTime()
)
</script>

<template>
  <span :class="compact ? 'text-xs' : 'text-sm'" class="text-gray-500">
    {{ formattedElapsed }}
  </span>
</template>
```

### Phase 4: Activity Descriptions

**Backend Changes:**

Update `get_activities()` in `database.py` to include summary fields:

```python
def get_activities(db_path: str, ...) -> list[Activity]:
    # Already returns summary field from v1.5.0
    # Ensure summary_brief (1-12 words) and summary_detail (12-20 words) are included
```

**Frontend Changes:**

**File: `dashboard/frontend/src/components/ActivityTimeline.vue`**

Update activity display:

```vue
<!-- Collapsed view: 1-12 word description -->
<div class="flex items-center gap-2">
  <span class="font-medium">{{ activity.tool_name }}</span>
  <span class="text-gray-600 text-sm truncate max-w-xs">
    {{ activity.summary || generateBriefSummary(activity) }}
  </span>
  <LiveElapsedTime :timestamp="activity.timestamp" compact />
</div>

<!-- Expanded view: 12-20 word explanation in box -->
<div v-if="expandedIds.has(activity.id)" class="mt-2">
  <!-- Detailed natural language explanation -->
  <div class="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg border border-blue-200 dark:border-blue-800">
    <p class="text-sm text-gray-700 dark:text-gray-300">
      {{ activity.summary_detail || generateDetailedSummary(activity) }}
    </p>
  </div>

  <!-- Raw input/output (user wants to keep this) -->
  <div class="grid grid-cols-2 gap-4 mt-3">
    <div>
      <h4 class="font-medium text-sm mb-1">Raw Input</h4>
      <pre class="...">{{ formatJson(activityDetails.get(activity.id)?.tool_input_full) }}</pre>
    </div>
    <div>
      <h4 class="font-medium text-sm mb-1">Raw Output</h4>
      <pre class="...">{{ formatJson(activityDetails.get(activity.id)?.tool_output_full) }}</pre>
    </div>
  </div>
</div>
```

### Phase 5: Session Context Live Updates

**File: `dashboard/frontend/src/components/SessionContextViewer.vue`**

1. Subscribe to WebSocket events
2. Add live elapsed time for each session
3. Auto-refresh when activities are logged

```vue
<script setup lang="ts">
import { useDashboardStore } from '@/stores/dashboardStore'
import LiveElapsedTime from './LiveElapsedTime.vue'

const store = useDashboardStore()

// Watch for WebSocket activity events
watch(() => store.lastActivityTimestamp, () => {
  loadData()  // Reload sessions when new activity logged
})
</script>

<template>
  <!-- Session with live timer -->
  <div class="flex items-center gap-2">
    <LiveElapsedTime :timestamp="session.started_at" />
    <span class="text-gray-600">{{ session.activity_count }} activities</span>
    <span v-if="!session.ended_at" class="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs animate-pulse">
      Active
    </span>
  </div>
</template>
```

### Phase 6: Memory Browser Live Updates

**File: `dashboard/frontend/src/components/MemoryBrowser.vue`**

Ensure the component properly reacts to WebSocket memory events:

```typescript
// Watch for store memory changes
watch(() => store.memories, (newMemories) => {
  // Update local display
}, { deep: true })
```

## Database Schema (No Changes Needed)

The v1.5.0 schema already includes:
- `summary` column for brief description
- `summary_detail` column for detailed explanation

## Implementation Order

1. **LiveElapsedTime.vue** - New component (15 min)
2. **ActivityTimeline.vue updates** - Add live timers + description display (30 min)
3. **WebSocket handler updates** - Add activity_logged event (20 min)
4. **DashboardStore updates** - Add activity handlers (20 min)
5. **SessionContextViewer.vue** - Live updates + timers (30 min)
6. **MemoryBrowser.vue** - Verify WebSocket reactivity (15 min)
7. **Backend activity streaming** - New incremental endpoint (30 min)
8. **Testing & polish** (30 min)

## Files to Create

| File | Purpose |
|------|---------|
| `components/LiveElapsedTime.vue` | Reusable live-updating elapsed time display |

## Files to Modify

| File | Changes |
|------|---------|
| `composables/useWebSocket.ts` | Add activity_logged, session_updated handlers |
| `stores/dashboardStore.ts` | Add activity/session state and handlers |
| `components/ActivityTimeline.vue` | Add live timers, description display |
| `components/SessionContextViewer.vue` | WebSocket subscription, live timers |
| `components/MemoryBrowser.vue` | Verify WebSocket reactivity |
| `backend/main.py` | Add activity_logged broadcast |

## Success Criteria

1. [ ] Activities appear in timeline within 1 second of being logged
2. [ ] Each activity shows a ticking elapsed time counter
3. [ ] Collapsed activities show 1-12 word description
4. [ ] Expanded activities show 12-20 word explanation in styled box
5. [ ] Raw input/output still visible in expanded view
6. [ ] Session Context updates automatically when activities are logged
7. [ ] Session Context shows live elapsed timers
8. [ ] Memory list updates when memories are created/updated/deleted
9. [ ] No page refresh required for any updates
10. [ ] **Refresh buttons removed** - pure push model, no manual refresh needed

## UX Improvements

### Remove Refresh Buttons
With pure push-based WebSocket updates (IndyDevDan pattern), manual refresh becomes obsolete:

- **ActivityTimeline.vue**: Remove "Refresh" button, data streams live
- **MemoryBrowser.vue**: Remove refresh button, memories update via WebSocket
- **SessionContextViewer.vue**: Remove any manual reload, sessions update automatically
- **StatsPanel.vue**: Stats update when underlying data changes

### Visual Feedback for Live Updates
Instead of refresh buttons, show:
- Pulsing green dot when connected (already exists)
- Brief highlight animation when new items arrive
- "Live" indicator badge near section headers

## Retrospective Action Items (From Previous Build)

Also address these from the v4 retrospective:

1. [ ] Add venv health check to `/build` command
2. [ ] Consider adding TypeScript duplicate detection to pre-commit hook
3. [ ] Review `services/api.ts` types for consolidation opportunities

## Testing Strategy

1. **Manual Testing:**
   - Open dashboard, start a Claude Code session in the project
   - Verify activities appear live in the Activity Timeline
   - Verify elapsed timers tick correctly
   - Verify Session Context updates
   - Verify memory creates/updates appear without refresh

2. **TypeScript Build:**
   - `npm run build` must complete without errors
   - No type errors in new/modified files

3. **Backend Tests:**
   - Existing tests must pass
   - WebSocket broadcast tests for new events
