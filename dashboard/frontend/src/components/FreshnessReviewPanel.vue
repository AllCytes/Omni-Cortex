<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getMemoriesNeedingReview, bulkUpdateMemoryStatus } from '@/services/api'
import type { Memory } from '@/types'
import { CheckCircle, XCircle, Archive, RefreshCw, Clock, Filter } from 'lucide-vue-next'

const store = useDashboardStore()
const memories = ref<Memory[]>([])
const selectedIds = ref<Set<string>>(new Set())
const loading = ref(false)
const updating = ref(false)
const error = ref<string | null>(null)
const daysThreshold = ref(30)

const allSelected = computed(() =>
  memories.value.length > 0 && selectedIds.value.size === memories.value.length
)

const someSelected = computed(() =>
  selectedIds.value.size > 0 && selectedIds.value.size < memories.value.length
)

const selectedCount = computed(() => selectedIds.value.size)

const reviewProgress = computed(() => {
  if (!store.stats) return { reviewed: 0, total: 0, percentage: 0 }
  const total = store.stats.total_count
  const needsReview = store.stats.by_status['needs_review'] || 0
  const outdated = store.stats.by_status['outdated'] || 0
  const reviewed = total - needsReview - outdated
  return {
    reviewed,
    total,
    percentage: total > 0 ? Math.round((reviewed / total) * 100) : 100
  }
})

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value.clear()
  } else {
    selectedIds.value = new Set(memories.value.map(m => m.id))
  }
}

function toggleSelect(id: string) {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  } else {
    selectedIds.value.add(id)
  }
  // Force reactivity
  selectedIds.value = new Set(selectedIds.value)
}

function formatRelativeTime(dateStr: string | null): string {
  if (!dateStr) return 'Never accessed'
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffDays < 1) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`
  return `${Math.floor(diffDays / 365)} years ago`
}

async function loadData() {
  if (!store.currentProject) return

  loading.value = true
  error.value = null
  selectedIds.value.clear()

  try {
    memories.value = await getMemoriesNeedingReview(
      store.currentProject.db_path,
      daysThreshold.value,
      50
    )
  } catch (e) {
    error.value = 'Failed to load memories'
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function bulkUpdate(status: string) {
  if (!store.currentProject || selectedIds.value.size === 0) return

  updating.value = true
  error.value = null

  try {
    await bulkUpdateMemoryStatus(
      store.currentProject.db_path,
      Array.from(selectedIds.value),
      status
    )

    // Remove updated memories from list
    memories.value = memories.value.filter(m => !selectedIds.value.has(m.id))
    selectedIds.value.clear()

    // Refresh stats
    store.loadStats()
  } catch (e) {
    error.value = 'Failed to update memories'
    console.error(e)
  } finally {
    updating.value = false
  }
}

onMounted(loadData)

watch(() => store.currentProject, loadData)
watch(daysThreshold, loadData)
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
    <!-- Header -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold flex items-center gap-2">
          <RefreshCw class="w-5 h-5 text-amber-500" />
          Freshness Review
        </h2>
        <button
          @click="loadData"
          :disabled="loading"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          title="Refresh"
        >
          <RefreshCw :class="['w-4 h-4', loading && 'animate-spin']" />
        </button>
      </div>

      <!-- Progress Bar -->
      <div class="mb-4">
        <div class="flex items-center justify-between text-sm mb-1">
          <span class="text-gray-600 dark:text-gray-400">Review Progress</span>
          <span class="font-medium">{{ reviewProgress.percentage }}%</span>
        </div>
        <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            class="h-full bg-green-500 transition-all duration-500"
            :style="{ width: `${reviewProgress.percentage}%` }"
          ></div>
        </div>
        <div class="text-xs text-gray-500 mt-1">
          {{ reviewProgress.reviewed }} of {{ reviewProgress.total }} memories reviewed
        </div>
      </div>

      <!-- Days Filter -->
      <div class="flex items-center gap-2">
        <Filter class="w-4 h-4 text-gray-400" />
        <span class="text-sm text-gray-600 dark:text-gray-400">Show memories not accessed in</span>
        <select
          v-model="daysThreshold"
          class="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-sm border-none focus:ring-2 focus:ring-blue-500"
        >
          <option :value="7">7 days</option>
          <option :value="14">14 days</option>
          <option :value="30">30 days</option>
          <option :value="60">60 days</option>
          <option :value="90">90 days</option>
        </select>
      </div>
    </div>

    <!-- Action Bar -->
    <div
      v-if="memories.length > 0"
      class="px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700 flex items-center gap-4"
    >
      <!-- Select All -->
      <label class="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          :checked="allSelected"
          :indeterminate="someSelected"
          @change="toggleSelectAll"
          class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <span class="text-sm text-gray-600 dark:text-gray-400">
          {{ selectedCount }} selected
        </span>
      </label>

      <!-- Bulk Actions -->
      <div v-if="selectedCount > 0" class="flex items-center gap-2 ml-auto">
        <button
          @click="bulkUpdate('fresh')"
          :disabled="updating"
          class="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          <CheckCircle class="w-4 h-4" />
          Mark Fresh
        </button>
        <button
          @click="bulkUpdate('outdated')"
          :disabled="updating"
          class="flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          <XCircle class="w-4 h-4" />
          Mark Outdated
        </button>
        <button
          @click="bulkUpdate('archived')"
          :disabled="updating"
          class="flex items-center gap-1.5 px-3 py-1.5 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          <Archive class="w-4 h-4" />
          Archive
        </button>
      </div>
    </div>

    <!-- Content -->
    <div v-if="loading" class="p-8 text-center">
      <div class="animate-pulse text-gray-500">Loading memories...</div>
    </div>

    <div v-else-if="error" class="p-8 text-center text-red-500">{{ error }}</div>

    <div v-else-if="memories.length === 0" class="p-8 text-center text-gray-500">
      <CheckCircle class="w-12 h-12 mx-auto mb-2 text-green-500" />
      <p class="font-medium">All caught up!</p>
      <p class="text-sm">No memories need review within the selected timeframe.</p>
    </div>

    <div v-else class="divide-y divide-gray-100 dark:divide-gray-700 max-h-96 overflow-y-auto">
      <div
        v-for="memory in memories"
        :key="memory.id"
        class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors cursor-pointer"
        @click="toggleSelect(memory.id)"
      >
        <div class="flex items-start gap-3">
          <input
            type="checkbox"
            :checked="selectedIds.has(memory.id)"
            @click.stop
            @change="toggleSelect(memory.id)"
            class="mt-1 w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <div class="flex-1 min-w-0">
            <p class="text-sm text-gray-900 dark:text-gray-100 line-clamp-2">
              {{ memory.content }}
            </p>
            <div class="mt-1 flex items-center gap-3 text-xs text-gray-500">
              <span
                :class="[
                  'px-2 py-0.5 rounded-full capitalize',
                  memory.memory_type === 'decision' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                  memory.memory_type === 'solution' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                  memory.memory_type === 'error' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                  'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
                ]"
              >
                {{ memory.memory_type }}
              </span>
              <span class="flex items-center gap-1">
                <Clock class="w-3 h-3" />
                {{ formatRelativeTime(memory.last_accessed) }}
              </span>
              <span v-if="memory.importance_score" class="text-amber-600 dark:text-amber-400">
                Importance: {{ memory.importance_score }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
