<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { Clock, CheckCircle, Wrench, Database, FileText, RefreshCw, ChevronDown, ChevronRight, Server, Terminal, Copy, Check } from 'lucide-vue-next'
import type { Activity } from '@/types'
import { getActivityDetail, type ActivityDetail } from '@/services/api'

const store = useDashboardStore()

const activities = ref<Activity[]>([])
const isLoading = ref(false)
// const timeRange = ref<number>(24) // TODO: implement time range filtering
const filterEventType = ref<string | null>(null)
const filterToolName = ref<string | null>(null)
const filterCommand = ref<string>('')

// Expandable state
const expandedIds = ref<Set<string>>(new Set())
const loadingDetails = ref<Set<string>>(new Set())
const activityDetails = ref<Map<string, ActivityDetail>>(new Map())
const copiedId = ref<string | null>(null)

const eventTypes = ['pre_tool_use', 'post_tool_use', 'decision', 'observation']

const uniqueToolNames = computed(() => {
  const tools = new Set<string>()
  activities.value.forEach(a => {
    if (a.tool_name) tools.add(a.tool_name)
  })
  return Array.from(tools).sort()
})

// uniqueMcpServers - reserved for future MCP filter dropdown
// const uniqueMcpServers = computed(() => {
//   const servers = new Set<string>()
//   activities.value.forEach(a => {
//     if (a.mcp_server) servers.add(a.mcp_server)
//   })
//   return Array.from(servers).sort()
// })

const filteredActivities = computed(() => {
  return activities.value.filter(a => {
    if (filterEventType.value && a.event_type !== filterEventType.value) return false
    if (filterToolName.value && a.tool_name !== filterToolName.value) return false
    // Command/skill text filter
    if (filterCommand.value) {
      const search = filterCommand.value.toLowerCase()
      const matchesCommand = a.command_name?.toLowerCase().includes(search)
      const matchesSkill = a.skill_name?.toLowerCase().includes(search)
      const matchesTool = a.tool_name?.toLowerCase().includes(search)
      if (!matchesCommand && !matchesSkill && !matchesTool) return false
    }
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

async function toggleExpanded(activityId: string) {
  if (expandedIds.value.has(activityId)) {
    expandedIds.value.delete(activityId)
    expandedIds.value = new Set(expandedIds.value)
  } else {
    expandedIds.value.add(activityId)
    expandedIds.value = new Set(expandedIds.value)

    // Load full details if not cached
    if (!activityDetails.value.has(activityId) && store.currentDbPath) {
      loadingDetails.value.add(activityId)
      loadingDetails.value = new Set(loadingDetails.value)

      try {
        const detail = await getActivityDetail(store.currentDbPath, activityId)
        activityDetails.value.set(activityId, detail)
        activityDetails.value = new Map(activityDetails.value)
      } catch (e) {
        console.error('Failed to load activity details:', e)
      } finally {
        loadingDetails.value.delete(activityId)
        loadingDetails.value = new Set(loadingDetails.value)
      }
    }
  }
}

function formatJson(jsonStr: string | null): string {
  if (!jsonStr) return 'null'
  try {
    const parsed = JSON.parse(jsonStr)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return jsonStr
  }
}

async function copyToClipboard(text: string, id: string) {
  try {
    await navigator.clipboard.writeText(text)
    copiedId.value = id
    setTimeout(() => {
      copiedId.value = null
    }, 2000)
  } catch (e) {
    console.error('Failed to copy:', e)
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

          <!-- Command/Skill Filter -->
          <div>
            <label class="text-sm text-gray-500 dark:text-gray-400 block mb-1">Command/Skill</label>
            <input
              v-model="filterCommand"
              type="text"
              placeholder="Filter by command..."
              class="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg border-none text-sm w-40"
            />
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
              class="rounded-lg border border-transparent hover:border-gray-200 dark:hover:border-gray-600 transition-colors"
            >
              <!-- Main row (clickable to expand) -->
              <div
                class="flex items-start gap-3 p-3 cursor-pointer"
                @click="toggleExpanded(activity.id)"
              >
                <!-- Expand/collapse icon -->
                <div class="mt-0.5 text-gray-400">
                  <ChevronDown v-if="expandedIds.has(activity.id)" class="w-4 h-4" />
                  <ChevronRight v-else class="w-4 h-4" />
                </div>

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
                    <!-- MCP Server Badge -->
                    <span
                      v-if="activity.mcp_server"
                      class="text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 flex items-center gap-1"
                    >
                      <Server class="w-3 h-3" />
                      {{ activity.mcp_server }}
                    </span>
                    <!-- Command/Skill Badge -->
                    <span
                      v-if="activity.skill_name || activity.command_name"
                      class="text-xs px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 flex items-center gap-1"
                    >
                      <Terminal class="w-3 h-3" />
                      {{ activity.skill_name || activity.command_name }}
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

              <!-- Expanded detail section -->
              <div
                v-if="expandedIds.has(activity.id)"
                class="px-3 pb-3 border-t border-gray-100 dark:border-gray-700 mt-2 pt-3"
              >
                <!-- Loading state -->
                <div v-if="loadingDetails.has(activity.id)" class="text-center py-4 text-gray-500">
                  <RefreshCw class="w-5 h-5 animate-spin mx-auto" />
                  <span class="text-sm">Loading details...</span>
                </div>

                <!-- Details content -->
                <template v-else-if="activityDetails.has(activity.id)">
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Input -->
                    <div>
                      <div class="flex items-center justify-between mb-2">
                        <h4 class="font-medium text-sm">Input</h4>
                        <button
                          @click.stop="copyToClipboard(activityDetails.get(activity.id)?.tool_input_full || '', activity.id + '-input')"
                          class="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                          title="Copy to clipboard"
                        >
                          <Check v-if="copiedId === activity.id + '-input'" class="w-4 h-4 text-green-500" />
                          <Copy v-else class="w-4 h-4 text-gray-500" />
                        </button>
                      </div>
                      <pre class="text-xs bg-gray-100 dark:bg-gray-900 p-3 rounded overflow-auto max-h-64 font-mono">{{ formatJson(activityDetails.get(activity.id)?.tool_input_full || null) }}</pre>
                    </div>

                    <!-- Output -->
                    <div>
                      <div class="flex items-center justify-between mb-2">
                        <h4 class="font-medium text-sm">Output</h4>
                        <button
                          @click.stop="copyToClipboard(activityDetails.get(activity.id)?.tool_output_full || '', activity.id + '-output')"
                          class="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                          title="Copy to clipboard"
                        >
                          <Check v-if="copiedId === activity.id + '-output'" class="w-4 h-4 text-green-500" />
                          <Copy v-else class="w-4 h-4 text-gray-500" />
                        </button>
                      </div>
                      <pre class="text-xs bg-gray-100 dark:bg-gray-900 p-3 rounded overflow-auto max-h-64 font-mono">{{ formatJson(activityDetails.get(activity.id)?.tool_output_full || null) }}</pre>
                    </div>
                  </div>

                  <!-- Additional metadata -->
                  <div class="mt-3 flex flex-wrap gap-2 text-xs">
                    <span v-if="activityDetails.get(activity.id)?.command_scope" class="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                      Scope: {{ activityDetails.get(activity.id)?.command_scope }}
                    </span>
                    <span class="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded font-mono">
                      ID: {{ activity.id }}
                    </span>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
