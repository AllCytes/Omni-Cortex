<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { MEMORY_TYPES, MEMORY_STATUSES, TYPE_COLORS } from '@/types'
import { RotateCcw, ChevronDown, ChevronUp } from 'lucide-vue-next'

const store = useDashboardStore()

const showTypes = ref(true)
const showStatuses = ref(true)
const showTags = ref(true)
const showImportance = ref(false)

const selectedType = computed({
  get: () => store.filters.memory_type,
  set: (val) => store.applyFilters({ memory_type: val })
})

const selectedStatus = computed({
  get: () => store.filters.status,
  set: (val) => store.applyFilters({ status: val })
})

const selectedTags = computed({
  get: () => store.filters.tags,
  set: (val) => store.applyFilters({ tags: val })
})

const minImportance = computed({
  get: () => store.filters.min_importance ?? 0,
  set: (val) => store.applyFilters({ min_importance: val || null })
})

const maxImportance = computed({
  get: () => store.filters.max_importance ?? 100,
  set: (val) => store.applyFilters({ max_importance: val === 100 ? null : val })
})

function toggleTag(tag: string) {
  const current = [...selectedTags.value]
  const index = current.indexOf(tag)
  if (index === -1) {
    current.push(tag)
  } else {
    current.splice(index, 1)
  }
  selectedTags.value = current
}

function getTypeColor(type: string): string {
  return TYPE_COLORS[type] || 'bg-gray-500'
}
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h2 class="font-semibold">Filters</h2>
      <button
        @click="store.resetFilters"
        class="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
      >
        <RotateCcw class="w-4 h-4" />
        Reset
      </button>
    </div>

    <!-- Type Filter -->
    <div class="mb-4">
      <button
        @click="showTypes = !showTypes"
        class="flex items-center justify-between w-full text-sm font-medium mb-2"
      >
        <span>Memory Type</span>
        <ChevronDown v-if="!showTypes" class="w-4 h-4" />
        <ChevronUp v-else class="w-4 h-4" />
      </button>
      <div v-if="showTypes" class="space-y-1">
        <button
          @click="selectedType = null"
          :class="[
            'w-full px-2 py-1 rounded text-sm text-left transition-colors',
            selectedType === null
              ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
              : 'hover:bg-gray-100 dark:hover:bg-gray-700'
          ]"
        >
          All Types
        </button>
        <button
          v-for="type in MEMORY_TYPES"
          :key="type"
          @click="selectedType = type"
          :class="[
            'w-full px-2 py-1 rounded text-sm text-left transition-colors flex items-center gap-2',
            selectedType === type
              ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
              : 'hover:bg-gray-100 dark:hover:bg-gray-700'
          ]"
        >
          <span :class="['w-2 h-2 rounded-full', getTypeColor(type)]"></span>
          <span class="capitalize">{{ type }}</span>
        </button>
      </div>
    </div>

    <!-- Status Filter -->
    <div class="mb-4">
      <button
        @click="showStatuses = !showStatuses"
        class="flex items-center justify-between w-full text-sm font-medium mb-2"
      >
        <span>Status</span>
        <ChevronDown v-if="!showStatuses" class="w-4 h-4" />
        <ChevronUp v-else class="w-4 h-4" />
      </button>
      <div v-if="showStatuses" class="space-y-1">
        <button
          @click="selectedStatus = null"
          :class="[
            'w-full px-2 py-1 rounded text-sm text-left transition-colors',
            selectedStatus === null
              ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
              : 'hover:bg-gray-100 dark:hover:bg-gray-700'
          ]"
        >
          All Statuses
        </button>
        <button
          v-for="status in MEMORY_STATUSES"
          :key="status"
          @click="selectedStatus = status"
          :class="[
            'w-full px-2 py-1 rounded text-sm text-left transition-colors capitalize',
            selectedStatus === status
              ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
              : 'hover:bg-gray-100 dark:hover:bg-gray-700'
          ]"
        >
          {{ status.replace('_', ' ') }}
        </button>
      </div>
    </div>

    <!-- Tags Filter -->
    <div class="mb-4">
      <button
        @click="showTags = !showTags"
        class="flex items-center justify-between w-full text-sm font-medium mb-2"
      >
        <span>Tags</span>
        <ChevronDown v-if="!showTags" class="w-4 h-4" />
        <ChevronUp v-else class="w-4 h-4" />
      </button>
      <div v-if="showTags" class="flex flex-wrap gap-1 max-h-40 overflow-y-auto">
        <button
          v-for="tag in store.tags.slice(0, 20)"
          :key="tag.name"
          @click="toggleTag(tag.name)"
          :class="[
            'px-2 py-0.5 rounded-full text-xs transition-colors',
            selectedTags.includes(tag.name)
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
          ]"
        >
          {{ tag.name }} ({{ tag.count }})
        </button>
      </div>
    </div>

    <!-- Importance Filter -->
    <div class="mb-4">
      <button
        @click="showImportance = !showImportance"
        class="flex items-center justify-between w-full text-sm font-medium mb-2"
      >
        <span>Importance</span>
        <ChevronDown v-if="!showImportance" class="w-4 h-4" />
        <ChevronUp v-else class="w-4 h-4" />
      </button>
      <div v-if="showImportance" class="space-y-2">
        <div class="flex items-center gap-2">
          <span class="text-xs w-8">Min:</span>
          <input
            v-model.number="minImportance"
            type="range"
            min="0"
            max="100"
            class="flex-1"
          />
          <span class="text-xs w-8">{{ minImportance }}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs w-8">Max:</span>
          <input
            v-model.number="maxImportance"
            type="range"
            min="0"
            max="100"
            class="flex-1"
          />
          <span class="text-xs w-8">{{ maxImportance }}</span>
        </div>
      </div>
    </div>

    <!-- Sort -->
    <div>
      <div class="text-sm font-medium mb-2">Sort By</div>
      <select
        v-model="store.filters.sort_by"
        @change="store.applyFilters({ sort_by: store.filters.sort_by })"
        class="w-full px-2 py-1.5 bg-gray-100 dark:bg-gray-700 rounded border-none text-sm"
      >
        <option value="last_accessed">Last Accessed</option>
        <option value="created_at">Created</option>
        <option value="importance_score">Importance</option>
        <option value="access_count">Access Count</option>
      </select>
      <div class="flex gap-2 mt-2">
        <button
          @click="store.applyFilters({ sort_order: 'desc' })"
          :class="[
            'flex-1 px-2 py-1 rounded text-sm transition-colors',
            store.filters.sort_order === 'desc'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 dark:bg-gray-700'
          ]"
        >
          Desc
        </button>
        <button
          @click="store.applyFilters({ sort_order: 'asc' })"
          :class="[
            'flex-1 px-2 py-1 rounded text-sm transition-colors',
            store.filters.sort_order === 'asc'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 dark:bg-gray-700'
          ]"
        >
          Asc
        </button>
      </div>
    </div>
  </div>
</template>
