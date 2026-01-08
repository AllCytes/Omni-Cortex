<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getToolUsage, type ToolUsageEntry } from '@/services/api'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Wrench } from 'lucide-vue-next'

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const store = useDashboardStore()
const data = ref<ToolUsageEntry[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const chartData = computed(() => ({
  labels: data.value.map(d => d.tool_name),
  datasets: [
    {
      label: 'Usage Count',
      data: data.value.map(d => d.count),
      backgroundColor: 'rgba(59, 130, 246, 0.7)',
      borderColor: 'rgba(59, 130, 246, 1)',
      borderWidth: 1,
      borderRadius: 4,
    }
  ]
}))

const chartOptions = computed(() => ({
  indexAxis: 'y' as const,
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      callbacks: {
        afterLabel: (context: { dataIndex: number }) => {
          const entry = data.value[context.dataIndex]
          return `Success rate: ${Math.round(entry.success_rate * 100)}%`
        }
      }
    }
  },
  scales: {
    x: {
      beginAtZero: true,
      grid: {
        display: false
      },
      ticks: {
        color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280'
      }
    },
    y: {
      grid: {
        display: false
      },
      ticks: {
        color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280'
      }
    }
  }
}))

async function loadData() {
  if (!store.currentProject) return

  loading.value = true
  error.value = null

  try {
    data.value = await getToolUsage(store.currentProject.db_path, 10)
  } catch (e) {
    error.value = 'Failed to load tool usage data'
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
      <Wrench class="w-5 h-5 text-blue-500" />
      Tool Usage
    </h2>

    <div v-if="loading" class="flex items-center justify-center h-48">
      <div class="animate-pulse text-gray-500">Loading...</div>
    </div>

    <div v-else-if="error" class="text-red-500 text-sm">{{ error }}</div>

    <div v-else-if="data.length === 0" class="text-gray-500 text-center py-8">
      No tool usage data available
    </div>

    <div v-else class="h-64">
      <Bar :data="chartData" :options="chartOptions" />
    </div>

    <!-- Success rate indicators -->
    <div v-if="data.length > 0" class="mt-4 grid grid-cols-2 gap-2 text-sm">
      <div
        v-for="tool in data.slice(0, 4)"
        :key="tool.tool_name"
        class="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded"
      >
        <span class="truncate">{{ tool.tool_name }}</span>
        <span
          :class="[
            'px-2 py-0.5 rounded text-xs font-medium',
            tool.success_rate >= 0.95
              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
              : tool.success_rate >= 0.8
              ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
              : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
          ]"
        >
          {{ Math.round(tool.success_rate * 100) }}%
        </span>
      </div>
    </div>
  </div>
</template>
