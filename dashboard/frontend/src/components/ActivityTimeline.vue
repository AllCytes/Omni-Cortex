<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { Clock, CheckCircle, Wrench, Database, FileText, ChevronDown, ChevronRight, Server, Terminal, Copy, Check, Radio } from 'lucide-vue-next'
import type { Activity } from '@/types'
import { getActivityDetail, type ActivityDetail } from '@/services/api'
import LiveElapsedTime from './LiveElapsedTime.vue'

const store = useDashboardStore()

const isLoading = ref(false)
const filterEventType = ref<string | null>(null)
const filterToolName = ref<string | null>(null)
const filterCommand = ref<string>('')

// Use store activities for live updates
const activities = computed(() => store.activities)

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
    await store.loadActivities()
  } catch (e) {
    console.error('Failed to load activities:', e)
  } finally {
    isLoading.value = false
  }
}

function formatDuration(ms: number | null): string {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

// Generate brief summary for collapsed view (1-12 words)
function generateBriefSummary(activity: Activity): string {
  // Return existing summary if available
  if (activity.summary) return activity.summary

  const toolName = activity.tool_name || 'unknown'
  let inputData: Record<string, unknown> = {}

  // Parse tool input if available
  if (activity.tool_input) {
    try {
      inputData = JSON.parse(activity.tool_input)
    } catch {
      // Ignore parsing errors
    }
  }

  // Generate summaries based on tool type
  if (toolName === 'Read') {
    const path = (inputData.file_path as string) || activity.file_path || 'file'
    const filename = path.split(/[/\\]/).pop() || 'file'
    return `Read file: ${filename}`
  }

  if (toolName === 'Write') {
    const path = (inputData.file_path as string) || activity.file_path || 'file'
    const filename = path.split(/[/\\]/).pop() || 'file'
    return `Write file: ${filename}`
  }

  if (toolName === 'Edit') {
    const path = (inputData.file_path as string) || activity.file_path || 'file'
    const filename = path.split(/[/\\]/).pop() || 'file'
    return `Edit file: ${filename}`
  }

  if (toolName === 'Bash') {
    const cmd = ((inputData.command as string) || '').slice(0, 40)
    return cmd ? `Run: ${cmd}...` : 'Run command'
  }

  if (toolName === 'Grep') {
    const pattern = ((inputData.pattern as string) || '').slice(0, 25)
    return pattern ? `Search: ${pattern}` : 'Search codebase'
  }

  if (toolName === 'Glob') {
    const pattern = ((inputData.pattern as string) || '').slice(0, 25)
    return pattern ? `Find files: ${pattern}` : 'Find files'
  }

  if (toolName === 'Skill') {
    const skill = (inputData.skill as string) || 'unknown'
    return `Run skill: /${skill}`
  }

  if (toolName === 'Task') {
    const desc = ((inputData.description as string) || 'task').slice(0, 30)
    return `Spawn agent: ${desc}`
  }

  if (toolName === 'WebSearch') {
    const query = ((inputData.query as string) || '').slice(0, 25)
    return query ? `Web search: ${query}` : 'Web search'
  }

  if (toolName === 'WebFetch') {
    const url = ((inputData.url as string) || '').slice(0, 35)
    return url ? `Fetch: ${url}` : 'Fetch URL'
  }

  if (toolName === 'TodoWrite') {
    const todos = inputData.todos as unknown[]
    const count = Array.isArray(todos) ? todos.length : 0
    return `Update todos: ${count} items`
  }

  if (toolName === 'AskUserQuestion') {
    const questions = inputData.questions as unknown[]
    const count = Array.isArray(questions) ? questions.length : 1
    return `Ask user: ${count} question(s)`
  }

  if (toolName.startsWith('mcp__')) {
    const parts = toolName.split('__')
    const server = parts[1] || 'unknown'
    const tool = parts[2] || toolName
    return `MCP: ${server}/${tool}`
  }

  if (toolName.includes('remember') || toolName.includes('cortex_remember')) {
    const params = inputData.params as Record<string, unknown>
    const content = (params?.content as string) || ''
    return content ? `Store: ${content.slice(0, 25)}...` : 'Store memory'
  }

  if (toolName.includes('recall') || toolName.includes('cortex_recall')) {
    const params = inputData.params as Record<string, unknown>
    const query = (params?.query as string) || ''
    return query ? `Recall: ${query.slice(0, 25)}` : 'Recall memories'
  }

  if (toolName === 'NotebookEdit') {
    const path = (inputData.notebook_path as string) || ''
    const filename = path.split(/[/\\]/).pop() || 'notebook'
    return `Edit notebook: ${filename}`
  }

  // Default fallback
  return `${activity.event_type.replace('_', ' ')}: ${toolName}`
}

// Generate detailed summary for expanded view (12-20 words)
function generateDetailSummary(activity: Activity, detail?: ActivityDetail | null): string {
  // Return existing detail summary if available
  if (detail?.summary_detail) return detail.summary_detail

  const toolName = activity.tool_name || 'unknown'
  let inputData: Record<string, unknown> = {}

  // Parse tool input (prefer full input from detail if available)
  const toolInput = detail?.tool_input_full || activity.tool_input
  if (toolInput) {
    try {
      inputData = JSON.parse(toolInput)
    } catch {
      // Ignore parsing errors
    }
  }

  const status = activity.success ? '' : '[FAILED] '

  if (toolName === 'Read') {
    const path = (inputData.file_path as string) || activity.file_path || 'unknown file'
    return `${status}Reading contents of file: ${path}`
  }

  if (toolName === 'Write') {
    const path = (inputData.file_path as string) || activity.file_path || 'unknown file'
    return `${status}Writing or creating file at path: ${path}`
  }

  if (toolName === 'Edit') {
    const path = (inputData.file_path as string) || activity.file_path || 'unknown file'
    return `${status}Editing file by replacing text content in: ${path}`
  }

  if (toolName === 'Bash') {
    const cmd = (inputData.command as string) || 'unknown command'
    return `${status}Executing bash command: ${cmd.slice(0, 100)}`
  }

  if (toolName === 'Grep') {
    const pattern = (inputData.pattern as string) || ''
    const path = (inputData.path as string) || 'codebase'
    return `${status}Searching for pattern "${pattern}" in ${path}`
  }

  if (toolName === 'Glob') {
    const pattern = (inputData.pattern as string) || ''
    return `${status}Finding files matching glob pattern: ${pattern}`
  }

  if (toolName === 'Skill') {
    const skill = (inputData.skill as string) || 'unknown'
    const args = (inputData.args as string) || ''
    return `${status}Executing slash command /${skill}${args ? ` with args: ${args}` : ''}`
  }

  if (toolName === 'Task') {
    const desc = (inputData.description as string) || 'task'
    const prompt = (inputData.prompt as string) || desc
    return `${status}Launching sub-agent for: ${prompt.slice(0, 80)}`
  }

  if (toolName === 'WebSearch') {
    const query = (inputData.query as string) || ''
    return `${status}Searching the web for information about: ${query}`
  }

  if (toolName === 'WebFetch') {
    const url = (inputData.url as string) || ''
    return `${status}Fetching and processing content from URL: ${url}`
  }

  if (toolName === 'TodoWrite') {
    const todos = inputData.todos as unknown[]
    const count = Array.isArray(todos) ? todos.length : 0
    return `${status}Managing task list with ${count} todo items`
  }

  if (toolName === 'AskUserQuestion') {
    const questions = inputData.questions as unknown[]
    const count = Array.isArray(questions) ? questions.length : 1
    return `${status}Prompting user for input with ${count} question(s)`
  }

  if (toolName.startsWith('mcp__')) {
    const parts = toolName.split('__')
    const server = parts[1] || 'unknown'
    const tool = parts[2] || toolName
    return `${status}Calling ${tool} tool from MCP server ${server}`
  }

  if (toolName.includes('remember') || toolName.includes('cortex_remember')) {
    const params = inputData.params as Record<string, unknown>
    const content = (params?.content as string) || ''
    return `${status}Saving to memory system: ${content.slice(0, 80)}`
  }

  if (toolName.includes('recall') || toolName.includes('cortex_recall')) {
    const params = inputData.params as Record<string, unknown>
    const query = (params?.query as string) || ''
    return `${status}Searching memories for: ${query}`
  }

  if (toolName === 'NotebookEdit') {
    const path = (inputData.notebook_path as string) || ''
    return `${status}Editing Jupyter notebook: ${path}`
  }

  // Default fallback
  return `${status}Activity type ${activity.event_type} with tool ${toolName}`
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

        <!-- Live indicator (pure push model - no manual refresh needed) -->
        <div class="flex items-center gap-2 px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-lg">
          <Radio class="w-4 h-4 animate-pulse" />
          <span class="text-sm font-medium">Live</span>
        </div>
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
              :class="[
                'rounded-lg border border-transparent hover:border-gray-200 dark:hover:border-gray-600 transition-all',
                store.isNewActivity(activity.id) && 'activity-highlight'
              ]"
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

                  <!-- Natural Language Summary (collapsed view) -->
                  <p class="text-sm text-gray-600 dark:text-gray-400 mt-1 truncate">
                    {{ generateBriefSummary(activity) }}
                  </p>

                  <!-- Error Message -->
                  <p
                    v-if="activity.error_message"
                    class="text-sm text-red-600 dark:text-red-400 mt-1 truncate"
                  >
                    {{ activity.error_message }}
                  </p>

                  <!-- File Path -->
                  <p
                    v-if="activity.file_path && !activity.summary"
                    class="text-sm text-gray-500 dark:text-gray-400 mt-1 truncate font-mono"
                  >
                    {{ activity.file_path }}
                  </p>
                </div>

                <!-- Meta -->
                <div class="text-right text-sm flex-shrink-0">
                  <LiveElapsedTime :timestamp="activity.timestamp" compact show-icon />
                  <div v-if="activity.duration_ms" class="text-gray-400 dark:text-gray-500 mt-1">
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
                  <!-- Detailed Summary (styled description box) -->
                  <div class="mb-4">
                    <div class="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg border border-blue-200 dark:border-blue-800">
                      <p class="text-sm text-gray-700 dark:text-gray-300">
                        {{ generateDetailSummary(activity, activityDetails.get(activity.id)) }}
                      </p>
                    </div>
                  </div>

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

<style scoped>
/* Highlight animation for new activities */
.activity-highlight {
  animation: highlight-glow 3s ease-out;
  background-color: rgb(59 130 246 / 0.1);
  border-color: rgb(59 130 246 / 0.3) !important;
}

@keyframes highlight-glow {
  0% {
    background-color: rgb(59 130 246 / 0.3);
    border-color: rgb(59 130 246 / 0.5);
  }
  100% {
    background-color: transparent;
    border-color: transparent;
  }
}

/* Dark mode highlight */
:deep(.dark) .activity-highlight {
  background-color: rgb(59 130 246 / 0.15);
  border-color: rgb(59 130 246 / 0.4) !important;
}
</style>
