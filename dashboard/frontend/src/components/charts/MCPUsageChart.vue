<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getMcpUsage, type MCPUsageEntry } from '@/services/api'
import { Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Server } from 'lucide-vue-next'

// Register Chart.js components
ChartJS.register(ArcElement, Title, Tooltip, Legend)

const store = useDashboardStore()
const data = ref<MCPUsageEntry[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// Color palette for MCP servers
const mcpColors = [
  'rgba(59, 130, 246, 0.8)',   // Blue
  'rgba(16, 185, 129, 0.8)',   // Green
  'rgba(245, 158, 11, 0.8)',   // Amber
  'rgba(239, 68, 68, 0.8)',    // Red
  'rgba(139, 92, 246, 0.8)',   // Violet
  'rgba(236, 72, 153, 0.8)',   // Pink
  'rgba(20, 184, 166, 0.8)',   // Teal
  'rgba(251, 146, 60, 0.8)',   // Orange
]

const chartData = computed(() => ({
  labels: data.value.map(d => d.mcp_server),
  datasets: [
    {
      data: data.value.map(d => d.total_calls),
      backgroundColor: data.value.map((_, i) => mcpColors[i % mcpColors.length]),
      borderColor: data.value.map((_, i) =>
        mcpColors[i % mcpColors.length].replace('0.8', '1')
      ),
      borderWidth: 2,
    }
  ]
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right' as const,
      labels: {
        color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280',
        padding: 10,
        usePointStyle: true,
      }
    },
    tooltip: {
      callbacks: {
        afterLabel: (context: { dataIndex: number }) => {
          const entry = data.value[context.dataIndex]
          return [
            `Tools: ${entry.tool_count}`,
            `Success rate: ${Math.round(entry.success_rate * 100)}%`
          ]
        }
      }
    }
  }
}))

const totalCalls = computed(() =>
  data.value.reduce((sum, d) => sum + d.total_calls, 0)
)

const totalTools = computed(() =>
  data.value.reduce((sum, d) => sum + d.tool_count, 0)
)

async function loadData() {
  if (!store.currentProject) return

  loading.value = true
  error.value = null

  try {
    data.value = await getMcpUsage(store.currentProject.db_path, 30)
  } catch (e) {
    error.value = 'Failed to load MCP usage data'
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

watch(() => store.currentProject, loadData)
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
      <Server class="w-5 h-5 text-blue-500" />
      MCP Server Usage
    </h2>

    <div v-if="loading" class="flex items-center justify-center h-48">
      <div class="animate-pulse text-gray-500">Loading...</div>
    </div>

    <div v-else-if="error" class="text-red-500 text-sm">{{ error }}</div>

    <div v-else-if="data.length === 0" class="text-gray-500 text-center py-8">
      No MCP usage data available
    </div>

    <template v-else>
      <!-- Summary stats -->
      <div class="grid grid-cols-3 gap-4 mb-4">
        <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {{ data.length }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">Servers</div>
        </div>
        <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold text-green-600 dark:text-green-400">
            {{ totalTools }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">Tools</div>
        </div>
        <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">
            {{ totalCalls.toLocaleString() }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">Total Calls</div>
        </div>
      </div>

      <!-- Chart -->
      <div class="h-48">
        <Doughnut :data="chartData" :options="chartOptions" />
      </div>

      <!-- MCP server list -->
      <div class="mt-4 space-y-2">
        <div
          v-for="(mcp, index) in data.slice(0, 5)"
          :key="mcp.mcp_server"
          class="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded text-sm"
        >
          <div class="flex items-center gap-2">
            <span
              class="w-3 h-3 rounded-full"
              :style="{ backgroundColor: mcpColors[index % mcpColors.length] }"
            ></span>
            <span class="font-medium truncate">{{ mcp.mcp_server }}</span>
          </div>
          <div class="flex items-center gap-3 text-gray-500 dark:text-gray-400">
            <span class="text-xs">{{ mcp.tool_count }} tools</span>
            <span>{{ mcp.total_calls }} calls</span>
            <span
              :class="[
                'px-2 py-0.5 rounded text-xs font-medium',
                mcp.success_rate >= 0.95
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : mcp.success_rate >= 0.8
                  ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
              ]"
            >
              {{ Math.round(mcp.success_rate * 100) }}%
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
