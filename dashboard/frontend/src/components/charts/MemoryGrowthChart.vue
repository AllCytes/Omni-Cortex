<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getMemoryGrowth, type MemoryGrowthEntry } from '@/services/api'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { TrendingUp } from 'lucide-vue-next'

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const store = useDashboardStore()
const data = ref<MemoryGrowthEntry[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const chartData = computed(() => ({
  labels: data.value.map(d => {
    const date = new Date(d.date)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }),
  datasets: [
    {
      label: 'Cumulative Memories',
      data: data.value.map(d => d.cumulative),
      borderColor: 'rgba(139, 92, 246, 1)',
      backgroundColor: 'rgba(139, 92, 246, 0.2)',
      fill: true,
      tension: 0.4,
      pointRadius: 2,
      pointHoverRadius: 5,
    },
    {
      label: 'Daily New',
      data: data.value.map(d => d.count),
      borderColor: 'rgba(34, 197, 94, 1)',
      backgroundColor: 'rgba(34, 197, 94, 0.5)',
      fill: false,
      tension: 0.4,
      pointRadius: 3,
      pointHoverRadius: 6,
      yAxisID: 'y1',
    }
  ]
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index' as const,
    intersect: false,
  },
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280',
        usePointStyle: true,
        pointStyle: 'circle',
      }
    },
    tooltip: {
      backgroundColor: document.documentElement.classList.contains('dark') ? '#374151' : '#ffffff',
      titleColor: document.documentElement.classList.contains('dark') ? '#f3f4f6' : '#1f2937',
      bodyColor: document.documentElement.classList.contains('dark') ? '#d1d5db' : '#4b5563',
      borderColor: document.documentElement.classList.contains('dark') ? '#4b5563' : '#e5e7eb',
      borderWidth: 1,
    }
  },
  scales: {
    x: {
      grid: {
        display: false
      },
      ticks: {
        color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280',
        maxRotation: 45,
        minRotation: 45,
      }
    },
    y: {
      type: 'linear' as const,
      display: true,
      position: 'left' as const,
      title: {
        display: true,
        text: 'Cumulative',
        color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280',
      },
      grid: {
        color: document.documentElement.classList.contains('dark') ? '#374151' : '#e5e7eb',
      },
      ticks: {
        color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280',
      }
    },
    y1: {
      type: 'linear' as const,
      display: true,
      position: 'right' as const,
      title: {
        display: true,
        text: 'Daily',
        color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280',
      },
      grid: {
        drawOnChartArea: false,
      },
      ticks: {
        color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280',
      }
    },
  }
}))

const totalNew = computed(() => data.value.reduce((sum, d) => sum + d.count, 0))
const currentTotal = computed(() => data.value.length > 0 ? data.value[data.value.length - 1].cumulative : 0)

async function loadData() {
  if (!store.currentProject) return

  loading.value = true
  error.value = null

  try {
    data.value = await getMemoryGrowth(store.currentProject.db_path, 30)
  } catch (e) {
    error.value = 'Failed to load memory growth data'
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
      <TrendingUp class="w-5 h-5 text-purple-500" />
      Memory Growth
    </h2>

    <div v-if="loading" class="flex items-center justify-center h-48">
      <div class="animate-pulse text-gray-500">Loading...</div>
    </div>

    <div v-else-if="error" class="text-red-500 text-sm">{{ error }}</div>

    <div v-else-if="data.length === 0" class="text-gray-500 text-center py-8">
      No memory growth data available
    </div>

    <template v-else>
      <!-- Summary stats -->
      <div class="grid grid-cols-2 gap-4 mb-4">
        <div class="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">{{ currentTotal }}</div>
          <div class="text-xs text-purple-600/70 dark:text-purple-400/70">Total Memories</div>
        </div>
        <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
          <div class="text-2xl font-bold text-green-600 dark:text-green-400">+{{ totalNew }}</div>
          <div class="text-xs text-green-600/70 dark:text-green-400/70">Last 30 Days</div>
        </div>
      </div>

      <div class="h-56">
        <Line :data="chartData" :options="chartOptions" />
      </div>
    </template>
  </div>
</template>
