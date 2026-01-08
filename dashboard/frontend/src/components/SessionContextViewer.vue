<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getRecentSessions, type RecentSession } from '@/services/api'
import { Clock, Activity, ChevronDown, ChevronUp, Calendar } from 'lucide-vue-next'

const store = useDashboardStore()
const sessions = ref<RecentSession[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const expanded = ref(false)

const lastSession = computed(() => sessions.value[0] || null)

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} min ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

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
      <!-- Last Session Summary (always visible) -->
      <div class="px-4 pb-4 border-b border-gray-100 dark:border-gray-700">
        <div class="flex items-center gap-4 text-sm">
          <div class="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
            <Calendar class="w-4 h-4" />
            <span>{{ formatRelativeTime(lastSession.started_at) }}</span>
          </div>
          <div class="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
            <Activity class="w-4 h-4" />
            <span>{{ lastSession.activity_count }} activities</span>
          </div>
          <span
            v-if="!lastSession.ended_at"
            class="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-xs"
          >
            Active
          </span>
        </div>
        <p v-if="lastSession.summary" class="mt-2 text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
          {{ lastSession.summary }}
        </p>
      </div>

      <!-- Expanded: All Recent Sessions -->
      <div v-if="expanded" class="divide-y divide-gray-100 dark:divide-gray-700">
        <div
          v-for="session in sessions.slice(1)"
          :key="session.id"
          class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
        >
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-600 dark:text-gray-400">
              {{ formatRelativeTime(session.started_at) }}
            </span>
            <div class="flex items-center gap-3">
              <span class="text-gray-500 dark:text-gray-500">
                {{ formatDuration(session.started_at, session.ended_at) }}
              </span>
              <span class="flex items-center gap-1 text-gray-500">
                <Activity class="w-3.5 h-3.5" />
                {{ session.activity_count }}
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
