# Style Tab Dashboard Core

## Overview

Add a new "Style" tab to the Omni Cortex dashboard for viewing user message history and communication style analysis. This feature leverages the `user_messages` and `user_style_profiles` tables added in v1.12.0.

## Objectives

1. Display captured user messages with metadata (tone, word count, etc.)
2. Show aggregated style profile statistics with visualizations
3. Display representative sample messages by category
4. Enable message management (view, search, filter, delete)
5. Maintain consistent UX patterns with existing dashboard tabs

## Tech Stack (Existing Patterns)

- **Frontend**: Vue 3 + Vite + Pinia + TypeScript + TailwindCSS
- **Backend**: FastAPI + SQLite
- **Charts**: Chart.js (existing dependency)
- **Icons**: lucide-vue-next (existing dependency)

---

## Phase 1: Backend API Endpoints

### 1.1 Database Queries (database.py)

Add new query functions to `dashboard/backend/database.py`:

```python
def get_user_messages(
    db_path: str,
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
    tone_filter: str | None = None,
    has_questions: bool | None = None,
    has_code_blocks: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """Get user messages with filtering."""
    # Query user_messages table with filters
    # Return: id, session_id, timestamp, content, word_count, char_count,
    #         line_count, has_code_blocks, has_questions, has_commands, tone_indicators
    pass

def get_user_message_count(db_path: str, filters: dict | None = None) -> int:
    """Get total count of user messages (for pagination)."""
    pass

def delete_user_message(db_path: str, message_id: str) -> bool:
    """Delete a single user message."""
    pass

def delete_user_messages_bulk(db_path: str, message_ids: list[str]) -> int:
    """Bulk delete user messages. Returns count deleted."""
    pass

def get_style_profile(db_path: str) -> dict:
    """Get aggregated style statistics."""
    # Aggregate from user_messages:
    # - total_messages
    # - avg_word_count, avg_char_count
    # - tone_distribution (count per tone type)
    # - question_frequency (% with has_questions=1)
    # - code_block_frequency (% with has_code_blocks=1)
    # - command_frequency (% with has_commands=1)
    # - message_length_distribution (short/medium/long/very_long)
    pass

def get_style_samples(db_path: str) -> dict:
    """Get representative sample messages by category."""
    # Return 2-3 samples for each:
    # - short: word_count < 15
    # - medium: 15 <= word_count < 50
    # - detailed: word_count >= 50
    pass
```

### 1.2 Pydantic Models (models.py)

Add to `dashboard/backend/models.py`:

```python
from pydantic import BaseModel
from typing import Optional

class UserMessage(BaseModel):
    id: str
    session_id: Optional[str]
    timestamp: str
    content: str
    word_count: int
    char_count: int
    line_count: int
    has_code_blocks: bool
    has_questions: bool
    has_commands: bool
    tone_indicators: list[str]  # Parsed from JSON

class UserMessageFilters(BaseModel):
    search: Optional[str] = None
    tone_filter: Optional[str] = None
    has_questions: Optional[bool] = None
    has_code_blocks: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

class StyleProfile(BaseModel):
    total_messages: int
    avg_word_count: float
    avg_char_count: float
    tone_distribution: dict[str, int]  # {"direct": 45, "polite": 30, ...}
    question_frequency: float  # 0-100%
    code_block_frequency: float
    command_frequency: float
    length_distribution: dict[str, int]  # {"short": 10, "medium": 25, ...}
    key_markers: list[str]  # Generated style markers

class StyleSamples(BaseModel):
    short: list[UserMessage]
    medium: list[UserMessage]
    detailed: list[UserMessage]

class UserMessagesResponse(BaseModel):
    messages: list[UserMessage]
    total: int
    page: int
    page_size: int
```

### 1.3 API Routes (main.py)

Add endpoints to `dashboard/backend/main.py`:

```python
@app.get("/api/user-messages")
async def api_get_user_messages(
    project: str = Query(...),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    tone: Optional[str] = None,
    has_questions: Optional[bool] = None,
    has_code_blocks: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """Get paginated user messages with filters."""
    pass

@app.delete("/api/user-messages/{message_id}")
async def api_delete_user_message(
    message_id: str,
    project: str = Query(...),
):
    """Delete a single user message."""
    pass

@app.post("/api/user-messages/bulk-delete")
async def api_bulk_delete_user_messages(
    message_ids: list[str],
    project: str = Query(...),
):
    """Bulk delete user messages."""
    pass

@app.get("/api/style-profile")
async def api_get_style_profile(
    project: str = Query(...),
):
    """Get aggregated style statistics."""
    pass

@app.get("/api/style-samples")
async def api_get_style_samples(
    project: str = Query(...),
):
    """Get representative sample messages."""
    pass
```

---

## Phase 2: Frontend Types & API Service

### 2.1 TypeScript Types (types/index.ts)

Add to `dashboard/frontend/src/types/index.ts`:

```typescript
// User Message types
export interface UserMessage {
  id: string
  session_id: string | null
  timestamp: string
  content: string
  word_count: number
  char_count: number
  line_count: number
  has_code_blocks: boolean
  has_questions: boolean
  has_commands: boolean
  tone_indicators: string[]
}

export interface UserMessageFilters {
  search?: string
  tone?: string
  has_questions?: boolean
  has_code_blocks?: boolean
  date_from?: string
  date_to?: string
}

export interface StyleProfile {
  total_messages: number
  avg_word_count: number
  avg_char_count: number
  tone_distribution: Record<string, number>
  question_frequency: number
  code_block_frequency: number
  command_frequency: number
  length_distribution: Record<string, number>
  key_markers: string[]
}

export interface StyleSamples {
  short: UserMessage[]
  medium: UserMessage[]
  detailed: UserMessage[]
}

export interface UserMessagesResponse {
  messages: UserMessage[]
  total: number
  page: number
  page_size: number
}

// Tone type constants
export const TONE_TYPES = [
  'urgent',
  'polite',
  'direct',
  'inquisitive',
  'technical',
  'casual',
] as const

export type ToneType = typeof TONE_TYPES[number]

export const TONE_COLORS: Record<string, string> = {
  urgent: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  polite: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  direct: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  inquisitive: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  technical: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  casual: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
}
```

### 2.2 API Service (services/api.ts)

Add to `dashboard/frontend/src/services/api.ts`:

```typescript
// User Messages API
export async function getUserMessages(
  project: string,
  params: {
    limit?: number
    offset?: number
    search?: string
    tone?: string
    has_questions?: boolean
    has_code_blocks?: boolean
    date_from?: string
    date_to?: string
  } = {}
): Promise<UserMessagesResponse> {
  const searchParams = new URLSearchParams({ project })
  if (params.limit) searchParams.set('limit', params.limit.toString())
  if (params.offset) searchParams.set('offset', params.offset.toString())
  if (params.search) searchParams.set('search', params.search)
  if (params.tone) searchParams.set('tone', params.tone)
  if (params.has_questions !== undefined) searchParams.set('has_questions', params.has_questions.toString())
  if (params.has_code_blocks !== undefined) searchParams.set('has_code_blocks', params.has_code_blocks.toString())
  if (params.date_from) searchParams.set('date_from', params.date_from)
  if (params.date_to) searchParams.set('date_to', params.date_to)

  const response = await fetch(`${API_BASE}/api/user-messages?${searchParams}`)
  return response.json()
}

export async function deleteUserMessage(project: string, messageId: string): Promise<void> {
  await fetch(`${API_BASE}/api/user-messages/${messageId}?project=${encodeURIComponent(project)}`, {
    method: 'DELETE',
  })
}

export async function bulkDeleteUserMessages(project: string, messageIds: string[]): Promise<void> {
  await fetch(`${API_BASE}/api/user-messages/bulk-delete?project=${encodeURIComponent(project)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(messageIds),
  })
}

export async function getStyleProfile(project: string): Promise<StyleProfile> {
  const response = await fetch(`${API_BASE}/api/style-profile?project=${encodeURIComponent(project)}`)
  return response.json()
}

export async function getStyleSamples(project: string): Promise<StyleSamples> {
  const response = await fetch(`${API_BASE}/api/style-samples?project=${encodeURIComponent(project)}`)
  return response.json()
}
```

---

## Phase 3: Frontend Components

### 3.1 StyleTab.vue (Main Container)

Create `dashboard/frontend/src/components/StyleTab.vue`:

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import StyleProfileCard from './style/StyleProfileCard.vue'
import MessageHistoryTable from './style/MessageHistoryTable.vue'
import StyleSamplesPanel from './style/StyleSamplesPanel.vue'
import { getStyleProfile, getStyleSamples } from '@/services/api'
import type { StyleProfile, StyleSamples } from '@/types'
import { RefreshCw, User } from 'lucide-vue-next'

const store = useDashboardStore()
const styleProfile = ref<StyleProfile | null>(null)
const styleSamples = ref<StyleSamples | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const currentProject = computed(() => store.currentProject)

async function loadStyleData() {
  if (!currentProject.value) return

  loading.value = true
  error.value = null

  try {
    const [profile, samples] = await Promise.all([
      getStyleProfile(currentProject.value),
      getStyleSamples(currentProject.value),
    ])
    styleProfile.value = profile
    styleSamples.value = samples
  } catch (e) {
    error.value = 'Failed to load style data'
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStyleData()
})

// Reload when project changes
watch(currentProject, () => {
  loadStyleData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <User class="w-6 h-6 text-indigo-500" />
        <h2 class="text-xl font-semibold">Communication Style</h2>
      </div>
      <button
        @click="loadStyleData"
        :disabled="loading"
        class="flex items-center gap-2 px-3 py-2 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
      >
        <RefreshCw :class="['w-4 h-4', { 'animate-spin': loading }]" />
        Refresh
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !styleProfile" class="flex items-center justify-center py-12">
      <RefreshCw class="w-8 h-8 animate-spin text-gray-400" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-4 rounded-lg">
      {{ error }}
    </div>

    <!-- Content -->
    <template v-else-if="styleProfile">
      <!-- Style Profile Card -->
      <StyleProfileCard :profile="styleProfile" />

      <!-- Message History Table -->
      <MessageHistoryTable />

      <!-- Sample Messages -->
      <StyleSamplesPanel v-if="styleSamples" :samples="styleSamples" />
    </template>

    <!-- Empty State -->
    <div v-else class="text-center py-12 text-gray-500">
      <User class="w-12 h-12 mx-auto mb-4 opacity-50" />
      <p class="text-lg">No messages captured yet</p>
      <p class="text-sm mt-2">Your communication style will be analyzed as you use Claude Code</p>
    </div>
  </div>
</template>
```

### 3.2 StyleProfileCard.vue

Create `dashboard/frontend/src/components/style/StyleProfileCard.vue`:

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { StyleProfile } from '@/types'
import { MessageSquare, Hash, HelpCircle, Code, Zap } from 'lucide-vue-next'

const props = defineProps<{
  profile: StyleProfile
}>()

// Compute primary tone (highest count)
const primaryTone = computed(() => {
  const tones = props.profile.tone_distribution
  const entries = Object.entries(tones)
  if (entries.length === 0) return 'unknown'
  return entries.sort((a, b) => b[1] - a[1])[0][0]
})

// Format percentages
const questionPct = computed(() => Math.round(props.profile.question_frequency))
const codePct = computed(() => Math.round(props.profile.code_block_frequency))
const commandPct = computed(() => Math.round(props.profile.command_frequency))
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
      <Zap class="w-5 h-5 text-indigo-500" />
      Style Profile
    </h3>

    <!-- Stats Grid -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <!-- Total Messages -->
      <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 text-center">
        <MessageSquare class="w-6 h-6 mx-auto mb-2 text-blue-500" />
        <div class="text-2xl font-bold">{{ profile.total_messages }}</div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Messages</div>
      </div>

      <!-- Avg Length -->
      <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 text-center">
        <Hash class="w-6 h-6 mx-auto mb-2 text-green-500" />
        <div class="text-2xl font-bold">{{ Math.round(profile.avg_word_count) }}</div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Avg Words</div>
      </div>

      <!-- Primary Tone -->
      <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 text-center">
        <Zap class="w-6 h-6 mx-auto mb-2 text-purple-500" />
        <div class="text-2xl font-bold capitalize">{{ primaryTone }}</div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Primary Tone</div>
      </div>

      <!-- Questions -->
      <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 text-center">
        <HelpCircle class="w-6 h-6 mx-auto mb-2 text-amber-500" />
        <div class="text-2xl font-bold">{{ questionPct }}%</div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Questions</div>
      </div>
    </div>

    <!-- Tone Distribution Bar -->
    <div class="mb-6">
      <h4 class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Tone Distribution</h4>
      <div class="flex h-4 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
        <div
          v-for="(count, tone) in profile.tone_distribution"
          :key="tone"
          :style="{ width: `${(count / profile.total_messages) * 100}%` }"
          :class="[
            'h-full transition-all',
            tone === 'direct' ? 'bg-blue-500' :
            tone === 'polite' ? 'bg-green-500' :
            tone === 'technical' ? 'bg-gray-500' :
            tone === 'inquisitive' ? 'bg-purple-500' :
            tone === 'casual' ? 'bg-yellow-500' :
            tone === 'urgent' ? 'bg-red-500' : 'bg-gray-400'
          ]"
          :title="`${tone}: ${count} (${Math.round((count / profile.total_messages) * 100)}%)`"
        />
      </div>
      <div class="flex flex-wrap gap-3 mt-2">
        <span
          v-for="(count, tone) in profile.tone_distribution"
          :key="tone"
          class="text-xs flex items-center gap-1"
        >
          <span
            :class="[
              'w-2 h-2 rounded-full',
              tone === 'direct' ? 'bg-blue-500' :
              tone === 'polite' ? 'bg-green-500' :
              tone === 'technical' ? 'bg-gray-500' :
              tone === 'inquisitive' ? 'bg-purple-500' :
              tone === 'casual' ? 'bg-yellow-500' :
              tone === 'urgent' ? 'bg-red-500' : 'bg-gray-400'
            ]"
          />
          <span class="capitalize">{{ tone }}</span>
          <span class="text-gray-400">({{ count }})</span>
        </span>
      </div>
    </div>

    <!-- Key Markers -->
    <div v-if="profile.key_markers?.length">
      <h4 class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Key Style Markers</h4>
      <ul class="space-y-1">
        <li
          v-for="(marker, idx) in profile.key_markers"
          :key="idx"
          class="flex items-start gap-2 text-sm"
        >
          <span class="text-indigo-500 mt-1">*</span>
          <span>{{ marker }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>
```

### 3.3 MessageHistoryTable.vue

Create `dashboard/frontend/src/components/style/MessageHistoryTable.vue`:

```vue
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getUserMessages, deleteUserMessage } from '@/services/api'
import type { UserMessage, UserMessageFilters } from '@/types'
import { TONE_COLORS } from '@/types'
import { Search, Trash2, ChevronDown, ChevronUp, HelpCircle, Code, Terminal, Filter } from 'lucide-vue-next'
import LiveElapsedTime from '@/components/LiveElapsedTime.vue'

const store = useDashboardStore()
const messages = ref<UserMessage[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const expandedId = ref<string | null>(null)
const searchQuery = ref('')
const selectedTone = ref<string | null>(null)
const showFilters = ref(false)

const currentProject = computed(() => store.currentProject)

async function loadMessages() {
  if (!currentProject.value) return

  loading.value = true
  try {
    const result = await getUserMessages(currentProject.value, {
      limit: pageSize,
      offset: (page.value - 1) * pageSize,
      search: searchQuery.value || undefined,
      tone: selectedTone.value || undefined,
    })
    messages.value = result.messages
    total.value = result.total
  } catch (e) {
    console.error('Failed to load messages:', e)
  } finally {
    loading.value = false
  }
}

async function handleDelete(messageId: string) {
  if (!currentProject.value) return
  if (!confirm('Delete this message?')) return

  try {
    await deleteUserMessage(currentProject.value, messageId)
    await loadMessages()
  } catch (e) {
    console.error('Failed to delete message:', e)
  }
}

function toggleExpand(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}

function truncate(text: string, length: number = 80): string {
  if (text.length <= length) return text
  return text.slice(0, length) + '...'
}

// Pagination
const totalPages = computed(() => Math.ceil(total.value / pageSize))

function prevPage() {
  if (page.value > 1) page.value--
}

function nextPage() {
  if (page.value < totalPages.value) page.value++
}

// Watch for filter changes
watch([page, searchQuery, selectedTone], () => {
  loadMessages()
})

watch(currentProject, () => {
  page.value = 1
  loadMessages()
})

onMounted(() => {
  loadMessages()
})
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
    <!-- Header -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-lg font-semibold">Message History</h3>
        <span class="text-sm text-gray-500">{{ total }} messages</span>
      </div>

      <!-- Search & Filter Bar -->
      <div class="flex gap-3">
        <div class="flex-1 relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search messages..."
            class="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg border-0 focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <button
          @click="showFilters = !showFilters"
          :class="[
            'px-3 py-2 rounded-lg flex items-center gap-2 transition-colors',
            showFilters ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600' : 'bg-gray-100 dark:bg-gray-700'
          ]"
        >
          <Filter class="w-4 h-4" />
          Filters
        </button>
      </div>

      <!-- Filter Panel (collapsible) -->
      <div v-if="showFilters" class="mt-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="tone in ['direct', 'polite', 'technical', 'inquisitive', 'casual', 'urgent']"
            :key="tone"
            @click="selectedTone = selectedTone === tone ? null : tone"
            :class="[
              'px-3 py-1 rounded-full text-sm capitalize transition-colors',
              selectedTone === tone
                ? 'bg-indigo-500 text-white'
                : 'bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500'
            ]"
          >
            {{ tone }}
          </button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead class="bg-gray-50 dark:bg-gray-700/50 text-sm">
          <tr>
            <th class="px-4 py-3 text-left font-medium">Time</th>
            <th class="px-4 py-3 text-left font-medium">Message</th>
            <th class="px-4 py-3 text-center font-medium">Words</th>
            <th class="px-4 py-3 text-left font-medium">Tone</th>
            <th class="px-4 py-3 text-center font-medium">Flags</th>
            <th class="px-4 py-3 text-center font-medium">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
          <template v-for="msg in messages" :key="msg.id">
            <!-- Main Row -->
            <tr
              class="hover:bg-gray-50 dark:hover:bg-gray-700/30 cursor-pointer"
              @click="toggleExpand(msg.id)"
            >
              <td class="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                <LiveElapsedTime :timestamp="msg.timestamp" />
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <component
                    :is="expandedId === msg.id ? ChevronUp : ChevronDown"
                    class="w-4 h-4 text-gray-400 flex-shrink-0"
                  />
                  <span class="text-sm">{{ truncate(msg.content) }}</span>
                </div>
              </td>
              <td class="px-4 py-3 text-center text-sm">{{ msg.word_count }}</td>
              <td class="px-4 py-3">
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="tone in msg.tone_indicators"
                    :key="tone"
                    :class="['px-2 py-0.5 rounded-full text-xs capitalize', TONE_COLORS[tone] || 'bg-gray-200 dark:bg-gray-600']"
                  >
                    {{ tone }}
                  </span>
                </div>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center justify-center gap-2">
                  <HelpCircle
                    v-if="msg.has_questions"
                    class="w-4 h-4 text-amber-500"
                    title="Contains questions"
                  />
                  <Code
                    v-if="msg.has_code_blocks"
                    class="w-4 h-4 text-blue-500"
                    title="Contains code"
                  />
                  <Terminal
                    v-if="msg.has_commands"
                    class="w-4 h-4 text-green-500"
                    title="Slash command"
                  />
                </div>
              </td>
              <td class="px-4 py-3 text-center">
                <button
                  @click.stop="handleDelete(msg.id)"
                  class="p-1.5 text-gray-400 hover:text-red-500 rounded transition-colors"
                  title="Delete message"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </td>
            </tr>

            <!-- Expanded Content -->
            <tr v-if="expandedId === msg.id">
              <td colspan="6" class="px-4 py-4 bg-gray-50 dark:bg-gray-700/30">
                <div class="text-sm whitespace-pre-wrap font-mono bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-600">
                  {{ msg.content }}
                </div>
              </td>
            </tr>
          </template>

          <!-- Empty State -->
          <tr v-if="!loading && messages.length === 0">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">
              No messages found
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="p-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
      <span class="text-sm text-gray-500">
        Page {{ page }} of {{ totalPages }}
      </span>
      <div class="flex gap-2">
        <button
          @click="prevPage"
          :disabled="page === 1"
          class="px-3 py-1 bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <button
          @click="nextPage"
          :disabled="page === totalPages"
          class="px-3 py-1 bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>
```

### 3.4 StyleSamplesPanel.vue

Create `dashboard/frontend/src/components/style/StyleSamplesPanel.vue`:

```vue
<script setup lang="ts">
import type { StyleSamples, UserMessage } from '@/types'
import { Zap, MessageSquare, FileText } from 'lucide-vue-next'

const props = defineProps<{
  samples: StyleSamples
}>()

function getCategoryIcon(category: string) {
  switch (category) {
    case 'short': return Zap
    case 'medium': return MessageSquare
    case 'detailed': return FileText
    default: return MessageSquare
  }
}

function getCategoryLabel(category: string) {
  switch (category) {
    case 'short': return 'Quick & Direct'
    case 'medium': return 'Typical Requests'
    case 'detailed': return 'Detailed Instructions'
    default: return category
  }
}

function getCategoryDescription(category: string) {
  switch (category) {
    case 'short': return 'Short, action-oriented messages (< 15 words)'
    case 'medium': return 'Standard length interactions (15-49 words)'
    case 'detailed': return 'Comprehensive instructions (50+ words)'
    default: return ''
  }
}
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <h3 class="text-lg font-semibold mb-4">Sample Messages</h3>
    <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
      Representative examples of how you communicate
    </p>

    <div class="grid md:grid-cols-3 gap-6">
      <!-- Category columns -->
      <div
        v-for="(messages, category) in samples"
        :key="category"
        class="space-y-3"
      >
        <!-- Category Header -->
        <div class="flex items-center gap-2 pb-2 border-b border-gray-200 dark:border-gray-700">
          <component
            :is="getCategoryIcon(category)"
            :class="[
              'w-5 h-5',
              category === 'short' ? 'text-blue-500' :
              category === 'medium' ? 'text-green-500' :
              'text-purple-500'
            ]"
          />
          <div>
            <h4 class="font-medium">{{ getCategoryLabel(category) }}</h4>
            <p class="text-xs text-gray-500">{{ getCategoryDescription(category) }}</p>
          </div>
        </div>

        <!-- Sample Messages -->
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border-l-2"
          :class="[
            category === 'short' ? 'border-l-blue-500' :
            category === 'medium' ? 'border-l-green-500' :
            'border-l-purple-500'
          ]"
        >
          <p class="text-sm italic text-gray-700 dark:text-gray-300">
            "{{ msg.content.length > 200 ? msg.content.slice(0, 200) + '...' : msg.content }}"
          </p>
          <div class="mt-2 flex items-center gap-2 text-xs text-gray-500">
            <span>{{ msg.word_count }} words</span>
            <span v-if="msg.tone_indicators.length">*</span>
            <span v-for="tone in msg.tone_indicators.slice(0, 2)" :key="tone" class="capitalize">
              {{ tone }}
            </span>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-if="!messages || messages.length === 0"
          class="p-4 text-center text-gray-400 text-sm"
        >
          No samples yet
        </div>
      </div>
    </div>
  </div>
</template>
```

---

## Phase 4: App Integration

### 4.1 Update App.vue

Modify `dashboard/frontend/src/App.vue`:

1. Import the new StyleTab component
2. Add 'style' to the activeTab type union
3. Add Style tab button after Sessions
4. Add Style tab content section

```vue
// Add import
import StyleTab from '@/components/StyleTab.vue'

// Update activeTab type
const activeTab = ref<'memories' | 'activity' | 'stats' | 'review' | 'graph' | 'style' | 'chat'>('memories')

// Add tab button (after 'stats', before 'review')
<button
  @click="activeTab = 'style'"
  :class="[
    'px-4 py-2 rounded-lg font-medium transition-colors',
    activeTab === 'style'
      ? 'bg-indigo-600 text-white'
      : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
  ]"
>
  Style
</button>

// Add tab content section
<div v-else-if="activeTab === 'style'" class="max-w-6xl mx-auto">
  <StyleTab />
</div>
```

### 4.2 Create style/ Directory

```bash
mkdir -p dashboard/frontend/src/components/style
```

---

## Testing Strategy

### Backend Tests

```python
# tests/test_dashboard_style.py

def test_get_user_messages_empty():
    """Test getting messages from empty database."""
    pass

def test_get_user_messages_with_data():
    """Test getting messages with actual data."""
    pass

def test_get_user_messages_search():
    """Test search filtering."""
    pass

def test_get_user_messages_tone_filter():
    """Test tone filtering."""
    pass

def test_delete_user_message():
    """Test single message deletion."""
    pass

def test_get_style_profile():
    """Test style profile aggregation."""
    pass

def test_get_style_samples():
    """Test sample message retrieval."""
    pass
```

### Frontend Manual Tests

1. [ ] Style tab appears in navigation
2. [ ] Style profile card shows correct stats
3. [ ] Tone distribution bar is accurate
4. [ ] Message history table loads and paginates
5. [ ] Search filtering works
6. [ ] Tone filtering works
7. [ ] Expand/collapse rows work
8. [ ] Delete message works
9. [ ] Sample messages display correctly
10. [ ] Empty state displays when no messages
11. [ ] Dark mode styling correct
12. [ ] Responsive layout on mobile

---

## Success Criteria

1. **Functional**: All API endpoints return correct data
2. **Visual**: Style tab matches existing dashboard aesthetics
3. **Performance**: Message table handles 1000+ messages smoothly
4. **UX**: Filters, search, pagination work intuitively
5. **Dark Mode**: All new components support dark mode
6. **Empty States**: Graceful handling when no messages exist

---

## File Checklist

### Backend (Phase 1)
- [ ] `dashboard/backend/database.py` - Add query functions
- [ ] `dashboard/backend/models.py` - Add Pydantic models
- [ ] `dashboard/backend/main.py` - Add API routes

### Frontend Types (Phase 2)
- [ ] `dashboard/frontend/src/types/index.ts` - Add TypeScript types
- [ ] `dashboard/frontend/src/services/api.ts` - Add API functions

### Frontend Components (Phase 3)
- [ ] `dashboard/frontend/src/components/StyleTab.vue` - Main container
- [ ] `dashboard/frontend/src/components/style/StyleProfileCard.vue` - Stats card
- [ ] `dashboard/frontend/src/components/style/MessageHistoryTable.vue` - Message table
- [ ] `dashboard/frontend/src/components/style/StyleSamplesPanel.vue` - Sample messages

### Integration (Phase 4)
- [ ] `dashboard/frontend/src/App.vue` - Add tab and routing

---

## Estimated Implementation Order

1. Backend database queries (20 min)
2. Backend Pydantic models (10 min)
3. Backend API routes (15 min)
4. Frontend types (10 min)
5. Frontend API service (10 min)
6. StyleProfileCard component (20 min)
7. MessageHistoryTable component (30 min)
8. StyleSamplesPanel component (15 min)
9. StyleTab container (10 min)
10. App.vue integration (5 min)
11. Testing & refinement (20 min)

**Total: ~2.5 hours**
