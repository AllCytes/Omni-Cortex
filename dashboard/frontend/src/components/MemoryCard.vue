<script setup lang="ts">
import { computed } from 'vue'
import type { Memory } from '@/types'
import { TYPE_COLORS, TYPE_BORDER_COLORS } from '@/types'
import { truncateWithHighlight } from '@/utils/highlight'
import { Clock, Eye } from 'lucide-vue-next'

const props = defineProps<{
  memory: Memory
  selected?: boolean
  searchTerm?: string
}>()

const typeColor = computed(() => TYPE_COLORS[props.memory.memory_type] || 'bg-gray-500')
const borderColor = computed(() => TYPE_BORDER_COLORS[props.memory.memory_type] || 'border-l-gray-500')

const contentPreview = computed(() => {
  return truncateWithHighlight(props.memory.content, props.searchTerm || '', 200)
})

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Never'
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}
</script>

<template>
  <div
    :class="[
      'p-4 rounded-lg cursor-pointer transition-all hover:shadow-md border-l-4',
      borderColor,
      selected
        ? 'border-r border-t border-b border-r-blue-500 border-t-blue-500 border-b-blue-500 bg-blue-50 dark:bg-blue-900/20'
        : 'border-r border-t border-b border-r-gray-200 border-t-gray-200 border-b-gray-200 dark:border-r-gray-700 dark:border-t-gray-700 dark:border-b-gray-700 bg-white dark:bg-gray-800 hover:border-r-gray-300 hover:border-t-gray-300 hover:border-b-gray-300 dark:hover:border-r-gray-600 dark:hover:border-t-gray-600 dark:hover:border-b-gray-600'
    ]"
  >
    <!-- Header -->
    <div class="flex items-start justify-between gap-2 mb-2">
      <div class="flex items-center gap-2">
        <!-- Type Badge -->
        <span :class="['px-2 py-0.5 rounded-full text-xs font-medium text-white', typeColor]">
          {{ memory.memory_type }}
        </span>
        <!-- Status -->
        <span
          v-if="memory.status !== 'fresh'"
          :class="[
            'px-2 py-0.5 rounded-full text-xs',
            memory.status === 'needs_review' && 'bg-yellow-100 text-yellow-700',
            memory.status === 'outdated' && 'bg-red-100 text-red-700',
            memory.status === 'archived' && 'bg-gray-100 text-gray-600'
          ]"
        >
          {{ memory.status.replace('_', ' ') }}
        </span>
      </div>

      <!-- Importance -->
      <div class="flex items-center gap-1">
        <div class="w-16 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            :class="['h-full rounded-full', typeColor]"
            :style="{ width: `${memory.importance_score}%` }"
          ></div>
        </div>
        <span class="text-xs text-gray-500">{{ memory.importance_score }}</span>
      </div>
    </div>

    <!-- Content Preview -->
    <p
      class="text-sm text-gray-700 dark:text-gray-300 mb-3 whitespace-pre-wrap break-words"
      v-html="contentPreview"
    ></p>

    <!-- Tags -->
    <div v-if="memory.tags.length > 0" class="flex flex-wrap gap-1 mb-3">
      <span
        v-for="tag in memory.tags.slice(0, 5)"
        :key="tag"
        class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded-full text-xs text-gray-600 dark:text-gray-400"
      >
        {{ tag }}
      </span>
      <span
        v-if="memory.tags.length > 5"
        class="px-2 py-0.5 text-xs text-gray-500"
      >
        +{{ memory.tags.length - 5 }} more
      </span>
    </div>

    <!-- Footer -->
    <div class="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
      <span class="flex items-center gap-1">
        <Clock class="w-3 h-3" />
        {{ formatDate(memory.last_accessed) }}
      </span>
      <span class="flex items-center gap-1">
        <Eye class="w-3 h-3" />
        {{ memory.access_count }} views
      </span>
    </div>
  </div>
</template>
