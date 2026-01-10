<script setup lang="ts">
import type { ChatSource } from '@/services/api'

interface Props {
  source: ChatSource
  position: { x: number; y: number }
}

defineProps<Props>()

const TYPE_COLORS: Record<string, string> = {
  decision: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  solution: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
  error: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  fact: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  preference: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  progress: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
  conversation: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
  troubleshooting: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  other: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
}

function getTypeColorClass(type: string): string {
  return TYPE_COLORS[type] || TYPE_COLORS.other
}
</script>

<template>
  <div
    class="fixed z-50 w-80 p-3 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-600 pointer-events-none"
    :style="{ top: position.y + 'px', left: position.x + 'px' }"
  >
    <div class="flex items-center gap-2 mb-2">
      <span
        :class="[getTypeColorClass(source.type), 'px-2 py-0.5 text-xs rounded font-medium']"
      >
        {{ source.type }}
      </span>
      <span class="text-xs text-gray-500 dark:text-gray-400 font-mono">
        {{ source.id.slice(0, 16) }}...
      </span>
    </div>
    <p class="text-sm text-gray-700 dark:text-gray-300 line-clamp-4">
      {{ source.content_preview }}
    </p>
    <div v-if="source.tags?.length" class="mt-2 flex flex-wrap gap-1">
      <span
        v-for="tag in source.tags.slice(0, 5)"
        :key="tag"
        class="text-xs px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded"
      >
        {{ tag }}
      </span>
      <span
        v-if="source.tags.length > 5"
        class="text-xs px-1.5 py-0.5 text-gray-500 dark:text-gray-400"
      >
        +{{ source.tags.length - 5 }} more
      </span>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
