# Quick Capture Widget Implementation Plan

## Overview

Add a floating action button (FAB) that opens a minimal modal for rapidly creating memories directly from the dashboard. This feature enables users to quickly capture thoughts, decisions, and insights without navigating away from their current view.

## Requirements

### Core Features
1. **Floating Action Button (FAB)** - Bottom-right corner, always visible
2. **Quick Capture Modal** - Minimal, focused interface for rapid memory creation
3. **Keyboard Shortcut** - `Ctrl+Shift+N` to open modal from anywhere
4. **Success Feedback** - Toast notification on successful save
5. **Rapid Capture Mode** - "Keep open after save" checkbox for batch entry

### Modal Fields
| Field | Type | Details |
|-------|------|---------|
| Content | Textarea | Auto-focus on open, required |
| Type | Dropdown | From `MEMORY_TYPES` constant |
| Tags | Input | Comma-separated with existing tag suggestions |
| Importance | Slider | 1-100 range, default 50 |
| Keep Open | Checkbox | For rapid capture workflow |

## Technical Architecture

### Backend Changes

**File: `dashboard/backend/main.py`**

Add a new POST endpoint for creating memories:

```python
@app.post("/api/memories")
@rate_limit("30/minute")
async def create_memory(
    request: MemoryCreateRequest,
    project: str = Query(..., description="Path to the database file"),
):
    """Create a new memory."""
    if not Path(project).exists():
        raise HTTPException(status_code=404, detail="Database not found")

    memory = create_new_memory(project, request)

    # Broadcast to WebSocket clients
    await manager.broadcast("memory_created", memory.model_dump(by_alias=True))

    return memory
```

**File: `dashboard/backend/models.py`**

Add request model:

```python
class MemoryCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    memory_type: str = Field(default="general")
    context: Optional[str] = None
    importance_score: int = Field(default=50, ge=1, le=100)
    tags: list[str] = Field(default_factory=list)
```

**File: `dashboard/backend/database.py`**

Add function to create memory:

```python
def create_memory(db_path: str, request: MemoryCreateRequest) -> Memory:
    """Create a new memory in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    memory_id = f"mem_{int(time.time()*1000)}_{secrets.token_hex(4)}"
    now = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO memories (id, content, context, type, status, importance_score,
                             access_count, created_at, last_accessed)
        VALUES (?, ?, ?, ?, 'fresh', ?, 0, ?, ?)
    """, (memory_id, request.content, request.context, request.memory_type,
          request.importance_score, now, now))

    # Insert tags
    for tag in request.tags:
        cursor.execute("INSERT OR IGNORE INTO memory_tags (memory_id, tag) VALUES (?, ?)",
                      (memory_id, tag.strip().lower()))

    conn.commit()
    conn.close()

    return get_memory_by_id(db_path, memory_id)
```

### Frontend Changes

#### 1. API Service

**File: `dashboard/frontend/src/services/api.ts`**

Add create memory function:

```typescript
export interface MemoryCreateRequest {
  content: string
  memory_type?: string
  context?: string
  importance_score?: number
  tags?: string[]
}

export async function createMemory(
  dbPath: string,
  request: MemoryCreateRequest
): Promise<Memory> {
  const response = await api.post<Record<string, unknown>>(
    `/memories?project=${encodeURIComponent(dbPath)}`,
    request
  )
  return normalizeMemory(response.data)
}
```

#### 2. Dashboard Store

**File: `dashboard/frontend/src/stores/dashboardStore.ts`**

Add createMemory action:

```typescript
async function createMemory(request: MemoryCreateRequest): Promise<Memory | null> {
  if (!currentDbPath.value) return null

  try {
    const created = await api.createMemory(currentDbPath.value, request)
    handleMemoryCreated(created)
    // Refresh tags to include any new ones
    await loadTags()
    return created
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to create memory'
    console.error('Failed to create memory:', e)
    return null
  }
}
```

#### 3. Quick Capture Modal Component

**File: `dashboard/frontend/src/components/QuickCaptureModal.vue`**

```vue
<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { MEMORY_TYPES } from '@/types'
import { useDashboardStore } from '@/stores/dashboardStore'
import { X, Plus, Loader2, Check, Zap } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'success', memory: { id: string; content: string }): void
}>()

const store = useDashboardStore()

// Form state
const content = ref('')
const memoryType = ref('decision')
const tagsInput = ref('')
const importance = ref(50)
const keepOpen = ref(false)
const isSaving = ref(false)

// Refs for DOM elements
const contentTextarea = ref<HTMLTextAreaElement | null>(null)

// Computed
const parsedTags = computed(() => {
  if (!tagsInput.value.trim()) return []
  return tagsInput.value.split(',').map(t => t.trim().toLowerCase()).filter(t => t.length > 0)
})

const canSave = computed(() => {
  return content.value.trim().length > 0 && !isSaving.value
})

// Tag suggestions based on existing tags
const tagSuggestions = computed(() => {
  const input = tagsInput.value.split(',').pop()?.trim().toLowerCase() || ''
  if (!input || input.length < 1) return []

  return store.tags
    .filter(t => t.name.toLowerCase().startsWith(input))
    .filter(t => !parsedTags.value.includes(t.name.toLowerCase()))
    .slice(0, 5)
    .map(t => t.name)
})

const showSuggestions = ref(false)

// Reset form
function resetForm() {
  content.value = ''
  memoryType.value = 'decision'
  tagsInput.value = ''
  importance.value = 50
}

// Auto-focus content textarea when modal opens
watch(() => props.isOpen, async (isOpen) => {
  if (isOpen) {
    await nextTick()
    contentTextarea.value?.focus()
  }
})

// Save memory
async function handleSave() {
  if (!canSave.value) return

  isSaving.value = true

  try {
    const created = await store.createMemory({
      content: content.value.trim(),
      memory_type: memoryType.value,
      importance_score: importance.value,
      tags: parsedTags.value,
    })

    if (created) {
      emit('success', { id: created.id, content: created.content })

      if (keepOpen.value) {
        resetForm()
        await nextTick()
        contentTextarea.value?.focus()
      } else {
        resetForm()
        emit('close')
      }
    }
  } finally {
    isSaving.value = false
  }
}

// Handle tag suggestion click
function addSuggestion(tag: string) {
  const parts = tagsInput.value.split(',')
  parts.pop()
  parts.push(tag)
  tagsInput.value = parts.join(', ') + ', '
  showSuggestions.value = false
}

// Close modal
function handleClose() {
  if (!isSaving.value) {
    resetForm()
    emit('close')
  }
}

// Handle Escape key
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    handleClose()
  } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    handleSave()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      leave-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
        @click.self="handleClose"
      >
        <Transition
          enter-active-class="transition-all duration-200"
          leave-active-class="transition-all duration-200"
          enter-from-class="opacity-0 scale-95"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="isOpen"
            class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-hidden flex flex-col"
          >
            <!-- Header -->
            <div class="px-5 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between bg-gradient-to-r from-blue-600 to-purple-600">
              <div class="flex items-center gap-2 text-white">
                <Zap class="w-5 h-5" />
                <h2 class="text-lg font-semibold">Quick Capture</h2>
              </div>
              <button
                @click="handleClose"
                :disabled="isSaving"
                class="p-1 hover:bg-white/20 rounded transition-colors text-white disabled:opacity-50"
              >
                <X class="w-5 h-5" />
              </button>
            </div>

            <!-- Form -->
            <div class="flex-1 overflow-y-auto p-5 space-y-4">
              <!-- Content -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  What do you want to remember?
                </label>
                <textarea
                  ref="contentTextarea"
                  v-model="content"
                  rows="4"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  placeholder="Enter your memory content..."
                  @keydown.ctrl.enter="handleSave"
                  @keydown.meta.enter="handleSave"
                />
              </div>

              <!-- Type and Importance (side by side) -->
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Type
                  </label>
                  <select
                    v-model="memoryType"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option v-for="type in MEMORY_TYPES" :key="type" :value="type">
                      {{ type.charAt(0).toUpperCase() + type.slice(1) }}
                    </option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Importance: {{ importance }}
                  </label>
                  <input
                    v-model.number="importance"
                    type="range"
                    min="1"
                    max="100"
                    class="w-full accent-blue-600 mt-2"
                  />
                </div>
              </div>

              <!-- Tags with suggestions -->
              <div class="relative">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tags (comma-separated)
                </label>
                <input
                  v-model="tagsInput"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="tag1, tag2, tag3"
                  @focus="showSuggestions = true"
                  @blur="setTimeout(() => showSuggestions = false, 200)"
                />
                <!-- Tag suggestions dropdown -->
                <div
                  v-if="showSuggestions && tagSuggestions.length > 0"
                  class="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg"
                >
                  <button
                    v-for="tag in tagSuggestions"
                    :key="tag"
                    @mousedown.prevent="addSuggestion(tag)"
                    class="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg"
                  >
                    {{ tag }}
                  </button>
                </div>
                <!-- Parsed tags preview -->
                <div v-if="parsedTags.length > 0" class="flex flex-wrap gap-1 mt-2">
                  <span
                    v-for="tag in parsedTags"
                    :key="tag"
                    class="px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-xs"
                  >
                    {{ tag }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="px-5 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <input
                  v-model="keepOpen"
                  type="checkbox"
                  class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                />
                Keep open after save
              </label>
              <div class="flex items-center gap-2">
                <span class="text-xs text-gray-400">Ctrl+Enter to save</span>
                <button
                  @click="handleSave"
                  :disabled="!canSave"
                  class="flex items-center gap-2 px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" />
                  <Plus v-else class="w-4 h-4" />
                  {{ isSaving ? 'Saving...' : 'Create Memory' }}
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
```

#### 4. Floating Action Button

**Add to: `dashboard/frontend/src/App.vue`**

Add FAB button and toast notification system:

```vue
<!-- In template, after OnboardingOverlay -->

<!-- Floating Action Button -->
<button
  @click="showQuickCapture = true"
  class="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center z-40 group"
  title="Quick Capture (Ctrl+Shift+N)"
>
  <Plus class="w-6 h-6 group-hover:rotate-90 transition-transform duration-200" />
</button>

<!-- Quick Capture Modal -->
<QuickCaptureModal
  :is-open="showQuickCapture"
  @close="showQuickCapture = false"
  @success="handleQuickCaptureSuccess"
/>

<!-- Toast Notification -->
<Transition
  enter-active-class="transition-all duration-300 ease-out"
  leave-active-class="transition-all duration-200 ease-in"
  enter-from-class="opacity-0 translate-y-2"
  leave-to-class="opacity-0 translate-y-2"
>
  <div
    v-if="toast.show"
    class="fixed bottom-24 right-6 bg-green-600 text-white px-4 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2"
  >
    <Check class="w-5 h-5" />
    <span>{{ toast.message }}</span>
  </div>
</Transition>
```

```typescript
// In script setup
import QuickCaptureModal from '@/components/QuickCaptureModal.vue'
import { Plus, Check } from 'lucide-vue-next'

const showQuickCapture = ref(false)
const toast = ref({ show: false, message: '' })

function showToast(message: string, duration = 3000) {
  toast.value = { show: true, message }
  setTimeout(() => {
    toast.value.show = false
  }, duration)
}

function handleQuickCaptureSuccess(memory: { id: string; content: string }) {
  const preview = memory.content.slice(0, 30) + (memory.content.length > 30 ? '...' : '')
  showToast(`Memory created: "${preview}"`)
}
```

#### 5. Keyboard Shortcut

**File: `dashboard/frontend/src/composables/useKeyboardShortcuts.ts`**

Add Ctrl+Shift+N handler:

```typescript
// Add new case in handleKeydown function, before the switch statement ends:

// Ctrl+Shift+N - Quick capture
if (e.ctrlKey && e.shiftKey && e.key === 'N') {
  e.preventDefault()
  window.dispatchEvent(new CustomEvent('show-quick-capture'))
  return
}
```

**In App.vue**, add event listener:

```typescript
onMounted(async () => {
  // ... existing code

  // Listen for quick capture keyboard shortcut
  window.addEventListener('show-quick-capture', () => {
    showQuickCapture.value = true
  })
})
```

#### 6. Update Help Modal

**File: `dashboard/frontend/src/components/HelpModal.vue`**

Add the new shortcut to the keyboard shortcuts list:

```typescript
// In the shortcuts array, add:
{ key: 'Ctrl+Shift+N', description: 'Quick capture new memory' },
```

## Implementation Steps

### Phase 1: Backend (30 mins)
1. Add `MemoryCreateRequest` model to `models.py`
2. Add `create_memory` function to `database.py`
3. Add `POST /api/memories` endpoint to `main.py`
4. Test endpoint with curl/Postman

### Phase 2: Frontend API & Store (20 mins)
1. Add `MemoryCreateRequest` interface to `api.ts`
2. Add `createMemory` function to `api.ts`
3. Add `createMemory` action to `dashboardStore.ts`
4. Export the new function

### Phase 3: Quick Capture Modal (45 mins)
1. Create `QuickCaptureModal.vue` component
2. Implement form fields with validation
3. Add tag suggestions from store
4. Add keyboard shortcuts (Ctrl+Enter, Escape)
5. Test modal functionality

### Phase 4: Integration (30 mins)
1. Add FAB button to `App.vue`
2. Add toast notification system
3. Wire up modal open/close
4. Add global keyboard shortcut (Ctrl+Shift+N)
5. Update Help modal with new shortcut

### Phase 5: Testing & Polish (25 mins)
1. Test rapid capture workflow (keep open mode)
2. Test keyboard navigation
3. Test tag suggestions
4. Verify WebSocket broadcasts
5. Test dark mode styling
6. Test mobile responsiveness

## Success Criteria

- [ ] FAB button visible on all tabs, bottom-right corner
- [ ] Clicking FAB opens Quick Capture modal
- [ ] Ctrl+Shift+N opens modal from anywhere
- [ ] Content textarea auto-focuses on open
- [ ] Type dropdown shows all memory types
- [ ] Tags input shows suggestions from existing tags
- [ ] Importance slider works (1-100 range)
- [ ] "Keep open after save" maintains modal for rapid entry
- [ ] Success toast appears after save
- [ ] Ctrl+Enter saves from textarea
- [ ] Escape closes modal
- [ ] New memory appears in memory list (via WebSocket)
- [ ] Help modal shows new keyboard shortcut

## Edge Cases & Error Handling

1. **Empty content** - Disable save button, show validation
2. **Network error** - Show error toast, keep modal open
3. **Very long content** - Backend validates max 50,000 chars
4. **Duplicate tags** - Deduplicate before saving
5. **Special characters in tags** - Sanitize to lowercase alphanumeric + hyphens
6. **Modal open during tab switch** - Keep state, don't close
7. **Rapid save clicks** - Disable button during save

## Performance Considerations

1. **Debounce tag suggestions** - 150ms delay on input
2. **Lazy load modal** - Use `defineAsyncComponent` if needed
3. **Minimize re-renders** - Use `v-once` for static content
4. **Optimize tag search** - Binary search if >100 tags

## Estimated Effort

| Phase | Time |
|-------|------|
| Backend | 30 min |
| Frontend API/Store | 20 min |
| Modal Component | 45 min |
| Integration | 30 min |
| Testing & Polish | 25 min |
| **Total** | **~2.5 hours** |

---

*Plan created: 2026-01-11*
*Target: Omni-Cortex Dashboard v0.2.0*
