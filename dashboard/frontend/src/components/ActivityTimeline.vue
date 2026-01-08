<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { Clock, CheckCircle, XCircle, Wrench, Database, FileText, RefreshCw } from 'lucide-vue-next'
import type { Activity } from '@/types'

const store = useDashboardStore()

const activities = ref<Activity[]>([])
const isLoading = ref(false)
const timeRange = ref<number>(24) // hours
const filterEventType = ref<string | null>(null)
const filterToolName = ref<string | null>(null)

const eventTypes = ['pre_tool_use', 'post_tool_use', 'decision', 'observation']

const uniqueToolNames = computed(() => {
  const tools = new Set<string>()
  activities.value.forEach(a => {
    if (a.tool_name) tools.add(a.tool_name)
  })
  return Array.from(tools).sort()
})

const filteredActivities = computed(() => {
  return activities.value.filter(a => {
    if (filterEventType.value && a.event_type !== filterEventType.value) return false
    if (filterToolName.value && a.tool_name !== filterToolName.value) return false
    return true
  })
})

const groupedActivities = computed(() => {
  const groups: Map<string, Activity[]> = new Map()

  filteredActivities.value.forEach(activity => {
    const date = new Date(activity.timestamp)
    const key = date.toLocaleDateString()

    if (!groups.has(key)) {
      groups.set(key, [])
    }
    groups.get(key)!.push(activity)
  })

  return groups
})

async function loadActivities() {
  if (!store.currentDbPath) return

  isLoading.value = true
  try {
    const response = await fetch(
      `/api/activities?project=${encodeURIComponent(store.currentDbPath)}&limit=200`
    )
    activities.value = await response.json()
  } catch (e) {
    console.error('Failed to load activities:', e)
  } finally {
    isLoading.value = false
  }
}

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function formatDuration(ms: number | null): string {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function getEventIcon(eventType: string) {
  switch (eventType) {
    case 'pre_tool_use': return Wrench
    case 'post_tool_use': return CheckCircle
    case 'decision': return Database
    case 'observation': return FileText
    default: return Clock
  }
}

function getEventColor(eventType: string, success: boolean): string {
  if (!success) return 'text-red-500'
  switch (eventType) {
    case 'pre_tool_use': return 'text-blue-500'
    case 'post_tool_use': return 'text-green-500'
    case 'decision': return 'text-purple-500'
    case 'observation': return 'text-amber-500'
    default: return 'text-gray-500'
  }
}

onMounted(() => {
  loadActivities()
})

watch(() => store.currentDbPath, () => {
  loadActivities()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      <div class="flex items-center justify-between gap-4 flex-wrap">
        <div class="flex items-center gap-4">
          <!-- Event Type Filter -->
          <div>
            <label class="text-sm text-gray-500 dark:text-gray-400 block mb-1">Event Type</label>
            <select
              v-model="filterEventType"
              class="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg border-none text-sm"
            >
              <option :value="null">All Events</option>
              <option v-for="type in eventTypes" :key="type" :value="type">
                {{ type.replace('_', ' ') }}
              </option>
            </select>
          </div>

          <!-- Tool Filter -->
          <div>
            <label class="text-sm text-gray-500 dark:text-gray-400 block mb-1">Tool</label>
            <select
              v-model="filterToolName"
              class="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg border-none text-sm"
            >
              <option :value="null">All Tools</option>
              <option v-for="tool in uniqueToolNames" :key="tool" :value="tool">
                {{ tool }}
              </option>
            </select>
          </div>
        </div>

        <!-- Refresh -->
        <button
          @click="loadActivities"
          :disabled="isLoading"
          class="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <RefreshCw :class="['w-4 h-4', isLoading && 'animate-spin']" />
          Refresh
        </button>
      </div>

      <!-- Stats -->
      <div class="flex items-center gap-6 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 text-sm">
        <div>
          <span class="text-gray-500 dark:text-gray-400">Total:</span>
          <span class="ml-1 font-medium">{{ filteredActivities.length }}</span>
        </div>
        <div>
          <span class="text-gray-500 dark:text-gray-400">Success:</span>
          <span class="ml-1 font-medium text-green-600">
            {{ filteredActivities.filter(a => a.success).length }}
          </span>
        </div>
        <div>
          <span class="text-gray-500 dark:text-gray-400">Failed:</span>
          <span class="ml-1 font-medium text-red-600">
            {{ filteredActivities.filter(a => !a.success).length }}
          </span>
        </div>
      </div>
    </div>

    <!-- Timeline -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <!-- Loading -->
      <div v-if="isLoading" class="p-8 text-center">
        <RefreshCw class="w-8 h-8 animate-spin mx-auto text-blue-600" />
        <p class="mt-2 text-gray-500">Loading activities...</p>
      </div>

      <!-- Empty -->
      <div v-else-if="filteredActivities.length === 0" class="p-8 text-center">
        <Clock class="w-12 h-12 mx-auto text-gray-400" />
        <p class="mt-2 text-gray-500">No activities found</p>
      </div>

      <!-- Timeline Groups -->
      <div v-else class="divide-y divide-gray-200 dark:divide-gray-700">
        <div v-for="[date, items] in groupedActivities" :key="date" class="p-4">
          <!-- Date Header -->
          <div class="flex items-center gap-2 mb-4">
            <div class="h-px flex-1 bg-gray-200 dark:bg-gray-700"></div>
            <span class="text-sm font-medium text-gray-500 dark:text-gray-400 px-2">
              {{ date }}
            </span>
            <div class="h-px flex-1 bg-gray-200 dark:bg-gray-700"></div>
          </div>

          <!-- Activity Items -->
          <div class="space-y-3">
            <div
              v-for="activity in items"
              :key="activity.id"
              class="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            >
              <!-- Icon -->
              <div :class="['mt-0.5', getEventColor(activity.event_type, activity.success)]">
                <component :is="getEventIcon(activity.event_type)" class="w-5 h-5" />
              </div>

              <!-- Content -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-medium">{{ activity.tool_name || 'Unknown' }}</span>
                  <span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700">
                    {{ activity.event_type.replace('_', ' ') }}
                  </span>
                  <span
                    v-if="!activity.success"
                    class="text-xs px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300"
                  >
                    Failed
                  </span>
                </div>

                <!-- Error Message -->
                <p
                  v-if="activity.error_message"
                  class="text-sm text-red-600 dark:text-red-400 mt-1 truncate"
                >
                  {{ activity.error_message }}
                </p>

                <!-- File Path -->
                <p
                  v-if="activity.file_path"
                  class="text-sm text-gray-500 dark:text-gray-400 mt-1 truncate font-mono"
                >
                  {{ activity.file_path }}
                </p>
              </div>

              <!-- Meta -->
              <div class="text-right text-sm flex-shrink-0">
                <div class="text-gray-500 dark:text-gray-400">
                  {{ formatTime(activity.timestamp) }}
                </div>
                <div v-if="activity.duration_ms" class="text-gray-400 dark:text-gray-500">
                  {{ formatDuration(activity.duration_ms) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
