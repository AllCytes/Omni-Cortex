<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getActivityHeatmap, type ActivityHeatmapEntry } from '@/services/api'
import { Flame } from 'lucide-vue-next'

const store = useDashboardStore()
const data = ref<ActivityHeatmapEntry[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// Generate dates for the last 90 days organized by weeks
const calendarData = computed(() => {
  const today = new Date()
  const weeks: Array<Array<{ date: string; count: number; dayOfWeek: number }>> = []

  // Create a map of date -> count
  const countMap = new Map(data.value.map(d => [d.date, d.count]))

  // Generate 13 weeks (91 days) of data
  let currentWeek: Array<{ date: string; count: number; dayOfWeek: number }> = []

  for (let i = 90; i >= 0; i--) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    const dateStr = date.toISOString().split('T')[0]
    const dayOfWeek = date.getDay()

    currentWeek.push({
      date: dateStr,
      count: countMap.get(dateStr) || 0,
      dayOfWeek
    })

    if (dayOfWeek === 6 || i === 0) {
      weeks.push(currentWeek)
      currentWeek = []
    }
  }

  return weeks
})

const maxCount = computed(() => {
  return Math.max(...data.value.map(d => d.count), 1)
})

function getIntensityClass(count: number): string {
  if (count === 0) return 'bg-gray-100 dark:bg-gray-700'
  const ratio = count / maxCount.value
  if (ratio <= 0.25) return 'bg-green-200 dark:bg-green-900'
  if (ratio <= 0.5) return 'bg-green-400 dark:bg-green-700'
  if (ratio <= 0.75) return 'bg-green-500 dark:bg-green-500'
  return 'bg-green-600 dark:bg-green-400'
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

async function loadData() {
  if (!store.currentProject) return

  loading.value = true
  error.value = null

  try {
    data.value = await getActivityHeatmap(store.currentProject.db_path, 90)
  } catch (e) {
    error.value = 'Failed to load activity data'
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
      <Flame class="w-5 h-5 text-orange-500" />
      Activity Heatmap
    </h2>

    <div v-if="loading" class="flex items-center justify-center h-24">
      <div class="animate-pulse text-gray-500">Loading...</div>
    </div>

    <div v-else-if="error" class="text-red-500 text-sm">{{ error }}</div>

    <div v-else class="overflow-x-auto">
      <!-- Days of week labels -->
      <div class="flex items-start gap-1 mb-1">
        <div class="w-8 flex-shrink-0"></div>
        <div class="text-xs text-gray-400 h-3">S</div>
        <div class="text-xs text-gray-400 h-3">M</div>
        <div class="text-xs text-gray-400 h-3">T</div>
        <div class="text-xs text-gray-400 h-3">W</div>
        <div class="text-xs text-gray-400 h-3">T</div>
        <div class="text-xs text-gray-400 h-3">F</div>
        <div class="text-xs text-gray-400 h-3">S</div>
      </div>

      <!-- Calendar grid -->
      <div class="flex gap-1">
        <div
          v-for="(week, weekIndex) in calendarData"
          :key="weekIndex"
          class="flex flex-col gap-1"
        >
          <div
            v-for="day in week"
            :key="day.date"
            :class="[
              'w-3 h-3 rounded-sm cursor-pointer transition-colors',
              getIntensityClass(day.count)
            ]"
            :title="`${formatDate(day.date)}: ${day.count} activities`"
          ></div>
        </div>
      </div>

      <!-- Legend -->
      <div class="flex items-center gap-2 mt-4 text-xs text-gray-500">
        <span>Less</span>
        <div class="w-3 h-3 rounded-sm bg-gray-100 dark:bg-gray-700"></div>
        <div class="w-3 h-3 rounded-sm bg-green-200 dark:bg-green-900"></div>
        <div class="w-3 h-3 rounded-sm bg-green-400 dark:bg-green-700"></div>
        <div class="w-3 h-3 rounded-sm bg-green-500 dark:bg-green-500"></div>
        <div class="w-3 h-3 rounded-sm bg-green-600 dark:bg-green-400"></div>
        <span>More</span>
      </div>

      <!-- Summary -->
      <div class="mt-4 text-sm text-gray-600 dark:text-gray-400">
        {{ data.reduce((sum, d) => sum + d.count, 0) }} activities in the last 90 days
      </div>
    </div>
  </div>
</template>
