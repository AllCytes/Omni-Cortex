# Omni-Cortex Dashboard Enhancements v3 (Phase 4)

## Overview

Phase 4 builds on the completed dashboard features to add quality-of-life improvements, data management capabilities, and enhanced interactivity. Focus is on user productivity and data portability.

## Completed Features (Phases 1-3)

- [x] Activity Heatmap (GitHub-style)
- [x] Tool Usage Statistics
- [x] Memory Growth Chart
- [x] Session Context Viewer
- [x] Freshness Review Panel
- [x] Memory Relationships Graph (D3.js)
- [x] AI Chat Panel (Gemini integration)

## Phase 4 Features

| # | Feature | Priority | Complexity | Value |
|---|---------|----------|------------|-------|
| 1 | Memory Export/Import | High | Medium | Data portability |
| 2 | Dark Mode Toggle | High | Low | UX |
| 3 | Keyboard Navigation | High | Medium | Power users |
| 4 | Bulk Operations Panel | Medium | Low | Productivity |
| 5 | Real-time Activity Feed | Medium | Medium | Observability |
| 6 | Memory Quality Score | Medium | Medium | Data quality |
| 7 | Advanced Search/Filters | Low | Medium | Discovery |
| 8 | Memory Comparison View | Low | Medium | Analysis |

---

## Feature 1: Memory Export/Import

### Description
Allow users to export memories to JSON/Markdown and import from other projects.

### Backend Endpoints

```python
@app.get("/api/export")
async def export_memories(
    project: str,
    format: str = "json",  # json, markdown, csv
    memory_ids: Optional[list[str]] = None,  # Export specific or all
    include_relationships: bool = True
):
    """Export memories to specified format."""

@app.post("/api/import")
async def import_memories(
    project: str,
    file: UploadFile,
    merge_strategy: str = "skip"  # skip, overwrite, append
):
    """Import memories from JSON file."""
```

### Frontend Component: ExportImportPanel.vue

```vue
<template>
  <div class="p-4">
    <!-- Export Section -->
    <div class="mb-6">
      <h3>Export Memories</h3>
      <select v-model="format">
        <option value="json">JSON</option>
        <option value="markdown">Markdown</option>
        <option value="csv">CSV</option>
      </select>
      <label>
        <input type="checkbox" v-model="includeRelationships" />
        Include relationships
      </label>
      <button @click="exportMemories">Export</button>
    </div>

    <!-- Import Section -->
    <div>
      <h3>Import Memories</h3>
      <input type="file" accept=".json" @change="handleFile" />
      <select v-model="mergeStrategy">
        <option value="skip">Skip duplicates</option>
        <option value="overwrite">Overwrite existing</option>
        <option value="append">Create new</option>
      </select>
      <button @click="importMemories" :disabled="!selectedFile">Import</button>
    </div>
  </div>
</template>
```

---

## Feature 2: Dark Mode Toggle

### Description
Add a visual toggle in the header to switch between light/dark modes, persisting preference.

### Implementation

Update `AppHeader.vue`:

```vue
<script setup>
import { ref, onMounted } from 'vue'
import { Sun, Moon } from 'lucide-vue-next'

const isDark = ref(false)

onMounted(() => {
  isDark.value = localStorage.getItem('theme') === 'dark' ||
    (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
  updateTheme()
})

function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  updateTheme()
}

function updateTheme() {
  document.documentElement.classList.toggle('dark', isDark.value)
}
</script>

<template>
  <button @click="toggleTheme" class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
    <Sun v-if="isDark" class="w-5 h-5" />
    <Moon v-else class="w-5 h-5" />
  </button>
</template>
```

---

## Feature 3: Keyboard Navigation

### Description
Full keyboard support for power users with vim-like bindings.

### Keybindings

| Key | Action |
|-----|--------|
| `j` / `k` | Navigate memories up/down |
| `Enter` | Open selected memory |
| `Escape` | Close panels/modals |
| `/` | Focus search |
| `1-6` | Switch tabs |
| `r` | Refresh data |
| `?` | Show help modal |
| `e` | Edit selected memory |
| `d` | Delete (with confirm) |
| `g g` | Go to first |
| `G` | Go to last |

### Implementation

Update `composables/useKeyboardShortcuts.ts`:

```typescript
export function useKeyboardShortcuts() {
  const store = useDashboardStore()

  onMounted(() => {
    document.addEventListener('keydown', handleKey)
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKey)
  })

  function handleKey(e: KeyboardEvent) {
    // Skip if typing in input
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
      return
    }

    switch (e.key) {
      case 'j':
        store.selectNext()
        break
      case 'k':
        store.selectPrevious()
        break
      case '/':
        e.preventDefault()
        document.querySelector<HTMLInputElement>('[data-search]')?.focus()
        break
      case '1': case '2': case '3': case '4': case '5': case '6':
        // Switch tabs
        break
      case '?':
        showHelpModal.value = true
        break
    }
  }
}
```

---

## Feature 4: Bulk Operations Panel

### Description
Select multiple memories for batch operations (delete, status change, tagging).

### Frontend Component: BulkActionsBar.vue

```vue
<template>
  <div
    v-if="selectedCount > 0"
    class="fixed bottom-4 left-1/2 -translate-x-1/2 bg-gray-900 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-4"
  >
    <span>{{ selectedCount }} selected</span>
    <button @click="changeStatus('fresh')">Mark Fresh</button>
    <button @click="changeStatus('archived')">Archive</button>
    <button @click="addTags">Add Tags</button>
    <button @click="deleteSelected" class="text-red-400">Delete</button>
    <button @click="clearSelection">Cancel</button>
  </div>
</template>
```

### Store Updates

```typescript
// dashboardStore.ts additions
selectedMemoryIds: Set<string>()

toggleSelection(id: string) {
  if (this.selectedMemoryIds.has(id)) {
    this.selectedMemoryIds.delete(id)
  } else {
    this.selectedMemoryIds.add(id)
  }
}

selectAll() {
  this.memories.forEach(m => this.selectedMemoryIds.add(m.id))
}

clearSelection() {
  this.selectedMemoryIds.clear()
}
```

---

## Feature 5: Real-time Activity Feed

### Description
Live WebSocket-powered activity stream showing tool calls as they happen.

### Backend

Already have WebSocket infrastructure. Add activity broadcast:

```python
# In hooks or activity logging
await manager.broadcast("activity_created", activity.model_dump())
```

### Frontend Component: ActivityFeed.vue

```vue
<template>
  <div class="h-64 overflow-y-auto space-y-1 font-mono text-sm">
    <div
      v-for="activity in recentActivities"
      :key="activity.id"
      class="flex items-center gap-2 px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-700"
    >
      <span class="text-gray-500">{{ formatTime(activity.timestamp) }}</span>
      <ToolIcon :tool="activity.tool_name" class="w-4 h-4" />
      <span :class="activity.success ? 'text-green-600' : 'text-red-600'">
        {{ activity.tool_name }}
      </span>
      <span class="text-gray-500 truncate flex-1">
        {{ activity.file_path || '' }}
      </span>
    </div>
  </div>
</template>
```

---

## Feature 6: Memory Quality Score

### Description
Auto-calculate a quality score for each memory based on multiple factors.

### Algorithm

```python
def calculate_quality_score(memory: Memory) -> int:
    """Calculate 0-100 quality score."""
    score = 50  # Base score

    # Freshness (±20)
    days_since_access = (now - memory.last_accessed).days
    if days_since_access < 7:
        score += 20
    elif days_since_access < 30:
        score += 10
    elif days_since_access > 90:
        score -= 20

    # Has tags (±10)
    if memory.tags and len(memory.tags) > 0:
        score += 10
    else:
        score -= 10

    # Has context (±10)
    if memory.context and len(memory.context) > 50:
        score += 10

    # Access count (±10)
    if memory.access_count >= 5:
        score += 10
    elif memory.access_count == 0:
        score -= 10

    # Content length (±10)
    if 100 <= len(memory.content) <= 1000:
        score += 10
    elif len(memory.content) < 50:
        score -= 10

    return max(0, min(100, score))
```

### Display

Add quality indicator badge to memory cards with color coding:
- Green (80-100): Excellent
- Blue (60-79): Good
- Yellow (40-59): Fair
- Red (0-39): Needs attention

---

## Implementation Order

### Sprint 1 (Quick Wins)
1. Dark Mode Toggle (2h)
2. Bulk Operations Panel (4h)

### Sprint 2 (Core Features)
3. Keyboard Navigation (6h)
4. Memory Export/Import (8h)

### Sprint 3 (Advanced)
5. Real-time Activity Feed (4h)
6. Memory Quality Score (4h)

### Sprint 4 (Polish)
7. Advanced Search/Filters
8. Memory Comparison View

---

## Testing Checklist

- [ ] Dark mode toggle persists across sessions
- [ ] Keyboard shortcuts work and don't interfere with inputs
- [ ] Bulk selection works with Shift+click and Ctrl+click
- [ ] Export produces valid JSON/Markdown/CSV
- [ ] Import handles duplicates correctly
- [ ] Activity feed updates in real-time via WebSocket
- [ ] Quality scores calculate correctly
- [ ] All features work in both light and dark mode

---

## Notes

- All features should be non-breaking additions
- Maintain existing API compatibility
- Follow existing code patterns and styling
- Add loading states for all async operations
