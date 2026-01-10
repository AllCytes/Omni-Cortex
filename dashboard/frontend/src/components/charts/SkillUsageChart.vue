<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getSkillUsage, type SkillUsageEntry } from '@/services/api'
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
import { Sparkles, Globe, FolderOpen } from 'lucide-vue-next'

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const store = useDashboardStore()
const data = ref<SkillUsageEntry[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const scopeFilter = ref<'all' | 'universal' | 'project'>('all')

const chartData = computed(() => ({
  labels: data.value.map(d => d.skill_name),
  datasets: [
    {
      label: 'Usage Count',
      data: data.value.map(d => d.count),
      backgroundColor: data.value.map(d =>
        d.skill_scope === 'universal'
          ? 'rgba(236, 72, 153, 0.7)'   // Pink for universal
          : d.skill_scope === 'project'
          ? 'rgba(14, 165, 233, 0.7)'   // Sky blue for project
          : 'rgba(156, 163, 175, 0.7)'  // Gray for unknown
      ),
      borderColor: data.value.map(d =>
        d.skill_scope === 'universal'
          ? 'rgba(236, 72, 153, 1)'
          : d.skill_scope === 'project'
          ? 'rgba(14, 165, 233, 1)'
          : 'rgba(156, 163, 175, 1)'
      ),
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
          return [
            `Success rate: ${Math.round(entry.success_rate * 100)}%`,
            `Scope: ${entry.skill_scope}`,
            entry.avg_duration_ms ? `Avg duration: ${entry.avg_duration_ms}ms` : ''
          ].filter(Boolean)
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
    const scope = scopeFilter.value === 'all' ? undefined : scopeFilter.value
    data.value = await getSkillUsage(store.currentProject.db_path, scope, 30)
  } catch (e) {
    error.value = 'Failed to load skill usage data'
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

watch(() => store.currentProject, loadData)
watch(scopeFilter, loadData)
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold flex items-center gap-2">
        <Sparkles class="w-5 h-5 text-pink-500" />
        Skill Usage
      </h2>

      <!-- Scope Filter -->
      <div class="flex items-center gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
        <button
          @click="scopeFilter = 'all'"
          :class="[
            'px-3 py-1 rounded text-sm transition-colors',
            scopeFilter === 'all'
              ? 'bg-white dark:bg-gray-600 shadow'
              : 'hover:bg-gray-200 dark:hover:bg-gray-600'
          ]"
        >
          All
        </button>
        <button
          @click="scopeFilter = 'universal'"
          :class="[
            'px-3 py-1 rounded text-sm transition-colors flex items-center gap-1',
            scopeFilter === 'universal'
              ? 'bg-white dark:bg-gray-600 shadow'
              : 'hover:bg-gray-200 dark:hover:bg-gray-600'
          ]"
        >
          <Globe class="w-3 h-3" />
          Universal
        </button>
        <button
          @click="scopeFilter = 'project'"
          :class="[
            'px-3 py-1 rounded text-sm transition-colors flex items-center gap-1',
            scopeFilter === 'project'
              ? 'bg-white dark:bg-gray-600 shadow'
              : 'hover:bg-gray-200 dark:hover:bg-gray-600'
          ]"
        >
          <FolderOpen class="w-3 h-3" />
          Project
        </button>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-48">
      <div class="animate-pulse text-gray-500">Loading...</div>
    </div>

    <div v-else-if="error" class="text-red-500 text-sm">{{ error }}</div>

    <div v-else-if="data.length === 0" class="text-gray-500 text-center py-8">
      No skill usage data available
    </div>

    <div v-else class="h-64">
      <Bar :data="chartData" :options="chartOptions" />
    </div>

    <!-- Legend -->
    <div v-if="data.length > 0" class="mt-4 flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded bg-pink-500"></span>
        Universal
      </div>
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded bg-sky-500"></span>
        Project
      </div>
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded bg-gray-400"></span>
        Unknown
      </div>
    </div>

    <!-- Top skills summary -->
    <div v-if="data.length > 0" class="mt-4 grid grid-cols-2 gap-2 text-sm">
      <div
        v-for="skill in data.slice(0, 4)"
        :key="skill.skill_name"
        class="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded"
      >
        <span class="truncate">{{ skill.skill_name }}</span>
        <span
          :class="[
            'px-2 py-0.5 rounded text-xs font-medium',
            skill.success_rate >= 0.95
              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
              : skill.success_rate >= 0.8
              ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
              : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
          ]"
        >
          {{ Math.round(skill.success_rate * 100) }}%
        </span>
      </div>
    </div>
  </div>
</template>
