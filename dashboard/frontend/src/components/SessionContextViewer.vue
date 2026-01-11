<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getRecentSessions, type RecentSession } from '@/services/api'
import { Clock, Activity, ChevronDown, ChevronUp, Radio, Zap } from 'lucide-vue-next'
import LiveElapsedTime from './LiveElapsedTime.vue'

const store = useDashboardStore()
const sessions = ref<RecentSession[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const expanded = ref(false)

// Use store sessions when available (WebSocket updates), fallback to local fetch
const displaySessions = computed(() => {
  if (store.recentSessions.length > 0) {
    return store.recentSessions
  }
  return sessions.value
})

const lastSession = computed(() => displaySessions.value[0] || null)

// Recent activity count (from store activities, updated via WebSocket)
const recentActivityCount = computed(() => store.activities.length)

// Most recent activity timestamp (for live elapsed time)
const mostRecentActivityTimestamp = computed(() => {
  if (store.activities.length > 0) {
    return store.activities[0].timestamp
  }
  return null
})

// Generate a summary of recent tool usage
const recentToolsSummary = computed(() => {
  const toolCounts = new Map<string, number>()
  // Count tools from recent activities (up to 50)
  store.activities.slice(0, 50).forEach(a => {
    if (a.tool_name) {
      const name = a.tool_name.startsWith('mcp__')
        ? a.tool_name.split('__')[1] || a.tool_name
        : a.tool_name
      toolCounts.set(name, (toolCounts.get(name) || 0) + 1)
    }
  })
  // Sort by count and take top 3
  const sorted = [...toolCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3)
  return sorted.map(([name]) => name).join(', ')
})

function formatDuration(startedAt: string, endedAt: string | null): string {
  if (!endedAt) return 'Ongoing'
  const start = new Date(startedAt)
  const end = new Date(endedAt)
  const diffMs = end.getTime() - start.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const hours = Math.floor(diffMins / 60)
  const mins = diffMins % 60
  if (hours > 0) return `${hours}h ${mins}m`
  return `${mins}m`
}

async function loadData() {
  if (!store.currentProject) return

  loading.value = true
  error.value = null

  try {
    sessions.value = await getRecentSessions(store.currentProject.db_path, 5)
  } catch (e) {
    error.value = 'Failed to load sessions'
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

watch(() => store.currentProject, loadData)

// Auto-reload when new activities are logged (WebSocket push)
watch(() => store.lastActivityTimestamp, () => {
  // Reload sessions when new activity detected
  loadData()
})
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
    <!-- Header -->
    <div
      class="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors rounded-t-lg"
      @click="expanded = !expanded"
    >
      <div class="flex items-center gap-2">
        <Clock class="w-5 h-5 text-blue-500" />
        <h2 class="font-semibold">Session Context</h2>
        <!-- Live indicator -->
        <div class="flex items-center gap-1 px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-xs">
          <Radio class="w-3 h-3 animate-pulse" />
          <span>Live</span>
        </div>
      </div>
      <component :is="expanded ? ChevronUp : ChevronDown" class="w-5 h-5 text-gray-400" />
    </div>

    <div v-if="loading" class="px-4 pb-4">
      <div class="animate-pulse text-gray-500 text-sm">Loading sessions...</div>
    </div>

    <div v-else-if="error" class="px-4 pb-4 text-red-500 text-sm">{{ error }}</div>

    <div v-else-if="!lastSession" class="px-4 pb-4 text-gray-500 text-sm">
      No session data available
    </div>

    <template v-else>
      <!-- Current Activity Snapshot (live data from WebSocket) -->
      <div v-if="recentActivityCount > 0" class="px-4 pb-4 border-b border-gray-100 dark:border-gray-700">
        <div class="flex items-center gap-4 text-sm">
          <div v-if="mostRecentActivityTimestamp" class="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
            <LiveElapsedTime :timestamp="mostRecentActivityTimestamp" show-icon />
          </div>
          <div class="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
            <Zap class="w-4 h-4 text-amber-500" />
            <span>{{ recentActivityCount }} activities loaded</span>
          </div>
          <span class="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-xs animate-pulse">
            Active
          </span>
        </div>
        <p v-if="recentToolsSummary" class="mt-2 text-sm text-gray-700 dark:text-gray-300">
          Recent tools: {{ recentToolsSummary }}
        </p>
      </div>

      <!-- Historical Session Summary (from database) -->
      <div v-if="lastSession" class="px-4 pb-4 border-b border-gray-100 dark:border-gray-700">
        <div class="text-xs text-gray-400 dark:text-gray-500 mb-2">Last recorded session:</div>
        <div class="flex items-center gap-4 text-sm">
          <div class="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
            <LiveElapsedTime :timestamp="lastSession.started_at" show-icon />
          </div>
          <div class="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
            <Activity class="w-4 h-4" />
            <span>{{ lastSession.activity_count }} activities</span>
          </div>
          <span
            v-if="!lastSession.ended_at"
            class="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-full text-xs"
          >
            Not ended
          </span>
        </div>
        <p v-if="lastSession.summary" class="mt-2 text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
          {{ lastSession.summary }}
        </p>
      </div>

      <!-- Expanded: All Recent Sessions -->
      <div v-if="expanded" class="divide-y divide-gray-100 dark:divide-gray-700">
        <div
          v-for="session in displaySessions.slice(1)"
          :key="session.id"
          class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
        >
          <div class="flex items-center justify-between text-sm">
            <LiveElapsedTime :timestamp="session.started_at" compact />
            <div class="flex items-center gap-3">
              <span class="text-gray-500 dark:text-gray-500">
                {{ formatDuration(session.started_at, session.ended_at) }}
              </span>
              <span class="flex items-center gap-1 text-gray-500">
                <Activity class="w-3.5 h-3.5" />
                {{ session.activity_count }}
              </span>
              <span
                v-if="!session.ended_at"
                class="px-1.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded text-xs"
              >
                Active
              </span>
            </div>
          </div>
          <p v-if="session.summary" class="mt-1 text-sm text-gray-700 dark:text-gray-300 line-clamp-1">
            {{ session.summary }}
          </p>
        </div>
      </div>
    </template>
  </div>
</template>
