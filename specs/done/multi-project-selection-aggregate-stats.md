# Multi-Project Selection with Aggregate Statistics

## Problem Statement

Currently, the Omni-Cortex dashboard operates on a single-project model where users can only view one project at a time. Users who work across multiple projects cannot:
1. Select multiple projects to view simultaneously
2. See aggregate statistics across their selected projects
3. Know which project an AI chat response references when querying across projects

This feature will transform the dashboard from single-project to multi-project mode with checkbox selection, aggregate statistics, and enhanced source attribution in Ask AI.

## Objectives

1. **Multi-Project Selection**: Replace single project dropdown with checkbox-based multi-select
2. **Aggregate Statistics**: Show combined stats across all selected projects
3. **Enhanced Ask AI**: Display which project each answer/source comes from

## Technical Approach

### Phase 1: Frontend Multi-Project Selection UI

#### 1.1 Update `dashboardStore.ts`

Replace `currentProject` with `selectedProjects` array:

```typescript
// State changes
const selectedProjects = ref<Project[]>([])
const currentProject = computed(() => selectedProjects.value[0] || null) // Backward compat

// New computed for multi-project db paths
const selectedDbPaths = computed(() => selectedProjects.value.map(p => p.db_path))

// Actions
function toggleProjectSelection(project: Project) {
  const index = selectedProjects.value.findIndex(p => p.db_path === project.db_path)
  if (index >= 0) {
    selectedProjects.value.splice(index, 1)
  } else {
    selectedProjects.value.push(project)
  }
  loadAggregateData()
}

function selectAllProjects() {
  selectedProjects.value = [...projects.value]
  loadAggregateData()
}

function clearProjectSelection() {
  selectedProjects.value = []
}

async function loadAggregateData() {
  await Promise.all([
    loadAggregateMemories(),
    loadAggregateStats(),
    loadAggregateTags(),
  ])
}
```

#### 1.2 Create `MultiProjectSelector.vue`

New component replacing `ProjectSwitcher.vue`:

```vue
<template>
  <div class="multi-project-selector">
    <!-- Header with Select All / Clear -->
    <div class="flex justify-between px-3 py-2 border-b">
      <span class="text-xs font-semibold uppercase">Projects</span>
      <div class="flex gap-2">
        <button @click="selectAll" class="text-xs text-blue-500">Select All</button>
        <button @click="clearAll" class="text-xs text-gray-500">Clear</button>
      </div>
    </div>

    <!-- Project List with Checkboxes -->
    <div v-for="project in store.projects" :key="project.db_path" class="px-3 py-2">
      <label class="flex items-center gap-3 cursor-pointer">
        <input
          type="checkbox"
          :checked="isSelected(project)"
          @change="toggle(project)"
          class="w-4 h-4 rounded"
        />
        <div class="flex-1">
          <div class="font-medium">{{ project.display_name || project.name }}</div>
          <div class="text-xs text-gray-500">{{ project.memory_count }} memories</div>
        </div>
      </label>
    </div>

    <!-- Selection Summary -->
    <div v-if="selectedCount > 0" class="px-3 py-2 bg-blue-50 text-blue-700 text-sm">
      {{ selectedCount }} project{{ selectedCount > 1 ? 's' : '' }} selected
    </div>
  </div>
</template>
```

### Phase 2: Backend Multi-Project Aggregation API

#### 2.1 New Aggregate Endpoints in `main.py`

```python
@app.post("/api/aggregate/memories")
async def get_aggregate_memories(
    projects: list[str] = Body(..., description="List of project paths"),
    filters: FilterParams = Depends(),
):
    """Get memories from multiple projects with project attribution."""
    all_memories = []
    for project_path in projects:
        if Path(project_path).exists():
            memories = get_memories(project_path, filters)
            # Add project attribution to each memory
            for m in memories:
                m_dict = m.model_dump()
                m_dict['source_project'] = project_path
                m_dict['source_project_name'] = Path(project_path).parent.name
                all_memories.append(m_dict)

    # Sort by last_accessed (or other criteria)
    all_memories.sort(key=lambda x: x.get('last_accessed') or '', reverse=True)
    return all_memories[:filters.limit]


@app.post("/api/aggregate/stats")
async def get_aggregate_stats(
    projects: list[str] = Body(..., description="List of project paths"),
):
    """Get combined statistics across multiple projects."""
    total_count = 0
    total_access = 0
    importance_sum = 0
    by_type = {}
    by_status = {}

    for project_path in projects:
        if Path(project_path).exists():
            stats = get_memory_stats(project_path)
            total_count += stats.get('total_count', 0)
            total_access += stats.get('total_access_count', 0)
            importance_sum += stats.get('avg_importance', 0) * stats.get('total_count', 0)

            for type_name, count in stats.get('by_type', {}).items():
                by_type[type_name] = by_type.get(type_name, 0) + count
            for status, count in stats.get('by_status', {}).items():
                by_status[status] = by_status.get(status, 0) + count

    return {
        'total_count': total_count,
        'total_access_count': total_access,
        'avg_importance': round(importance_sum / total_count, 1) if total_count > 0 else 0,
        'by_type': by_type,
        'by_status': by_status,
        'project_count': len(projects),
    }


@app.post("/api/aggregate/tags")
async def get_aggregate_tags(
    projects: list[str] = Body(..., description="List of project paths"),
):
    """Get combined tags across multiple projects."""
    tag_counts = {}

    for project_path in projects:
        if Path(project_path).exists():
            tags = get_all_tags(project_path)
            for tag in tags:
                tag_counts[tag['name']] = tag_counts.get(tag['name'], 0) + tag['count']

    return sorted(
        [{'name': k, 'count': v} for k, v in tag_counts.items()],
        key=lambda x: x['count'],
        reverse=True
    )
```

#### 2.2 Enhanced Chat Endpoint for Multi-Project

```python
@app.post("/api/aggregate/chat")
async def chat_across_projects(
    projects: list[str] = Body(...),
    question: str = Body(...),
    max_memories_per_project: int = Body(5),
):
    """Ask AI about memories across multiple projects."""
    all_sources = []

    # Gather relevant memories from each project
    for project_path in projects:
        if Path(project_path).exists():
            memories = search_memories(project_path, question, max_memories_per_project)
            for m in memories:
                source = {
                    'id': m.id,
                    'type': m.type,
                    'content_preview': m.content[:200],
                    'tags': m.tags,
                    'project_path': project_path,
                    'project_name': Path(project_path).parent.name,  # Attribution!
                }
                all_sources.append(source)

    # Build context with project attribution
    context = "\n\n".join([
        f"[From: {s['project_name']}] {s['content_preview']}"
        for s in all_sources
    ])

    # Query AI with attributed context
    answer = await chat_service.generate_response(question, context)

    return {
        'answer': answer,
        'sources': all_sources,  # Each source has project_name
    }
```

### Phase 3: Frontend Aggregate Stats Display

#### 3.1 Update `StatsPanel.vue`

Add multi-project indicator and breakdown:

```vue
<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <!-- Multi-Project Indicator -->
    <div v-if="selectedProjectCount > 1" class="lg:col-span-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4">
      <div class="flex items-center gap-2">
        <Layers class="w-5 h-5 text-blue-500" />
        <span class="font-medium">Viewing {{ selectedProjectCount }} projects</span>
      </div>
      <div class="flex flex-wrap gap-2 mt-2">
        <span
          v-for="project in selectedProjects"
          :key="project.db_path"
          class="px-2 py-1 bg-white dark:bg-gray-800 rounded text-sm"
        >
          {{ project.display_name || project.name }}
        </span>
      </div>
    </div>

    <!-- Overview Card - Now shows aggregate -->
    <div class="card">
      <h2>Overview {{ selectedProjectCount > 1 ? '(Combined)' : '' }}</h2>
      <div class="stat">
        <span>Total Memories</span>
        <span>{{ aggregateStats?.total_count ?? 0 }}</span>
      </div>
      <!-- ... rest of stats ... -->
    </div>
  </div>
</template>
```

### Phase 4: Enhanced Ask AI with Project Attribution

#### 4.1 Update `ChatPanel.vue`

Add project badges to sources:

```vue
<template>
  <!-- In the sources section -->
  <div v-show="message.sourcesExpanded" class="mt-2 space-y-1">
    <button
      v-for="source in message.sources"
      :key="source.id"
      class="flex items-start gap-2 w-full"
    >
      <!-- Project Badge (NEW) -->
      <span
        v-if="source.project_name"
        class="px-1.5 py-0.5 bg-purple-100 text-purple-800 rounded text-xs font-medium"
        :title="source.project_path"
      >
        {{ source.project_name }}
      </span>

      <!-- Type Badge -->
      <span :class="getTypeColorClass(source.type)">
        {{ source.type }}
      </span>

      <!-- Content Preview -->
      <span class="flex-1 truncate">
        {{ source.content_preview }}
      </span>
    </button>
  </div>
</template>
```

#### 4.2 Update API Types in `api.ts`

```typescript
export interface ChatSource {
  id: string
  type: string
  content_preview: string
  tags: string[]
  project_path?: string      // NEW
  project_name?: string      // NEW
}

// New aggregate API functions
export async function getAggregateMemories(
  projectPaths: string[],
  filters: Partial<FilterState> = {},
  limit = 50,
  offset = 0
): Promise<(Memory & { source_project: string; source_project_name: string })[]> {
  const response = await api.post('/aggregate/memories', {
    projects: projectPaths,
    ...filters,
    limit,
    offset,
  })
  return response.data
}

export async function getAggregateStats(
  projectPaths: string[]
): Promise<MemoryStats & { project_count: number }> {
  const response = await api.post('/aggregate/stats', {
    projects: projectPaths,
  })
  return response.data
}

export async function askAcrossProjects(
  projectPaths: string[],
  question: string,
  maxMemoriesPerProject = 5
): Promise<ChatResponse> {
  const response = await api.post('/aggregate/chat', {
    projects: projectPaths,
    question,
    max_memories_per_project: maxMemoriesPerProject,
  })
  return response.data
}
```

## Implementation Steps

### Step 1: Backend Aggregate Endpoints (2-3 hours)
1. Add `/api/aggregate/memories` endpoint
2. Add `/api/aggregate/stats` endpoint
3. Add `/api/aggregate/tags` endpoint
4. Add `/api/aggregate/chat` endpoint
5. Add project attribution to chat service
6. Write tests for aggregate endpoints

### Step 2: Frontend Store Updates (1-2 hours)
1. Convert `currentProject` to `selectedProjects` array
2. Add `toggleProjectSelection`, `selectAll`, `clearSelection` actions
3. Add computed properties for aggregate data
4. Update `loadAggregateData` to use new endpoints
5. Maintain backward compatibility with single project mode

### Step 3: Multi-Project Selector UI (1-2 hours)
1. Create `MultiProjectSelector.vue` component
2. Add checkbox-based selection
3. Add Select All / Clear buttons
4. Show selection count badge
5. Update `AppHeader.vue` to use new selector

### Step 4: Aggregate Stats Display (1-2 hours)
1. Update `StatsPanel.vue` for aggregate display
2. Add multi-project indicator banner
3. Show per-project breakdown option
4. Update charts to handle multi-project data

### Step 5: Enhanced Ask AI (1-2 hours)
1. Update `ChatPanel.vue` to show project badges on sources
2. Add project filter in chat (optional)
3. Update source tooltip to show full project path
4. Add visual distinction between projects in responses

### Step 6: Testing & Polish (1-2 hours)
1. Test single project backward compatibility
2. Test multi-project selection persistence
3. Test aggregate stats accuracy
4. Test Ask AI attribution
5. Performance testing with many projects

## Potential Challenges

1. **Performance**: Querying multiple databases simultaneously
   - Solution: Use `asyncio.gather()` for parallel queries
   - Consider caching aggregate stats

2. **Memory IDs Collision**: Same ID could exist in different projects
   - Solution: Prefix or qualify IDs with project path

3. **UI Complexity**: Too many projects overwhelming
   - Solution: Add search/filter in project selector, favorites first

4. **WebSocket Updates**: Broadcasting to correct clients
   - Solution: Track which projects each client is watching

## Testing Strategy

### Unit Tests
- `test_aggregate_memories()` - Verify merging logic
- `test_aggregate_stats()` - Verify stat aggregation
- `test_project_attribution()` - Verify source attribution

### Integration Tests
- Multi-project selection persistence
- Aggregate stats across 5+ projects
- Chat with sources from different projects

### Manual Testing Checklist
- [ ] Select/deselect projects with checkboxes
- [ ] Select All / Clear buttons work
- [ ] Stats update when selection changes
- [ ] Memories list shows project attribution
- [ ] Ask AI shows which project each source is from
- [ ] Performance with 10+ projects selected
- [ ] Dark mode styling
- [ ] Mobile responsive

## Success Criteria

1. Users can select multiple projects via checkboxes
2. Stats panel shows combined statistics
3. Each memory/source shows its project of origin
4. Ask AI responses clearly indicate which project each answer references
5. Performance remains acceptable with 5+ projects selected
6. Backward compatible with single-project workflows

## Files to Modify

### Backend
- `dashboard/backend/main.py` - Add aggregate endpoints
- `dashboard/backend/database.py` - Add project attribution to queries
- `dashboard/backend/chat_service.py` - Multi-project context building
- `dashboard/backend/models.py` - Add aggregate response models

### Frontend
- `dashboard/frontend/src/stores/dashboardStore.ts` - Multi-select state
- `dashboard/frontend/src/components/MultiProjectSelector.vue` - NEW
- `dashboard/frontend/src/components/ProjectSwitcher.vue` - Replace/update
- `dashboard/frontend/src/components/StatsPanel.vue` - Aggregate display
- `dashboard/frontend/src/components/ChatPanel.vue` - Project badges
- `dashboard/frontend/src/components/MemoryCard.vue` - Project indicator
- `dashboard/frontend/src/services/api.ts` - Aggregate API functions
- `dashboard/frontend/src/types/index.ts` - Update interfaces

## Estimated Time

- Backend: 3-4 hours
- Frontend: 4-5 hours
- Testing: 1-2 hours
- **Total: 8-11 hours**

---

*Plan created: 2026-01-11*
*Author: Claude Code Assistant*
