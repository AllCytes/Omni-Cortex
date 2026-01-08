<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { Download, FileJson, FileText, Table, X, Check } from 'lucide-vue-next'

const emit = defineEmits<{
  (e: 'close'): void
}>()

const store = useDashboardStore()
const format = ref<'json' | 'markdown' | 'csv'>('json')
const includeRelationships = ref(true)
const exporting = ref(false)
const success = ref(false)

const formatOptions = [
  { value: 'json', label: 'JSON', icon: FileJson, description: 'Full data with relationships, importable' },
  { value: 'markdown', label: 'Markdown', icon: FileText, description: 'Human-readable documentation' },
  { value: 'csv', label: 'CSV', icon: Table, description: 'Spreadsheet compatible' },
]

const exportUrl = computed(() => {
  if (!store.currentProject) return ''
  const params = new URLSearchParams({
    project: store.currentProject.db_path,
    format: format.value,
    include_relationships: includeRelationships.value.toString(),
  })
  return `/api/export?${params}`
})

async function handleExport() {
  if (!store.currentProject) return

  exporting.value = true

  try {
    // Create a link and trigger download
    const link = document.createElement('a')
    link.href = exportUrl.value
    link.download = `memories_export.${format.value}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    success.value = true
    setTimeout(() => {
      success.value = false
    }, 3000)
  } catch (e) {
    console.error('Export failed:', e)
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="emit('close')">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full mx-4 overflow-hidden">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h2 class="text-lg font-semibold flex items-center gap-2">
          <Download class="w-5 h-5 text-blue-500" />
          Export Memories
        </h2>
        <button
          @click="emit('close')"
          class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Content -->
      <div class="p-6 space-y-6">
        <!-- Format Selection -->
        <div>
          <label class="block text-sm font-medium mb-3">Export Format</label>
          <div class="space-y-2">
            <label
              v-for="option in formatOptions"
              :key="option.value"
              :class="[
                'flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-colors',
                format === option.value
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              ]"
            >
              <input
                type="radio"
                :value="option.value"
                v-model="format"
                class="sr-only"
              />
              <component :is="option.icon" :class="[
                'w-5 h-5',
                format === option.value ? 'text-blue-500' : 'text-gray-400'
              ]" />
              <div class="flex-1">
                <div class="font-medium">{{ option.label }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">{{ option.description }}</div>
              </div>
              <div
                v-if="format === option.value"
                class="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center"
              >
                <Check class="w-3 h-3 text-white" />
              </div>
            </label>
          </div>
        </div>

        <!-- Options -->
        <div>
          <label class="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              v-model="includeRelationships"
              :disabled="format === 'csv'"
              class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span :class="format === 'csv' ? 'text-gray-400' : ''">
              Include memory relationships
            </span>
          </label>
          <p v-if="format === 'csv'" class="mt-1 text-xs text-gray-500">
            CSV format doesn't support relationships
          </p>
        </div>

        <!-- Stats -->
        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
          <div class="text-sm text-gray-600 dark:text-gray-400">
            <p>Exporting from: <span class="font-medium text-gray-900 dark:text-gray-100">{{ store.currentProject?.name }}</span></p>
            <p class="mt-1">Total memories: <span class="font-medium text-gray-900 dark:text-gray-100">{{ store.stats?.total_count ?? 0 }}</span></p>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 bg-gray-50 dark:bg-gray-700/30 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
        <button
          @click="emit('close')"
          class="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
        >
          Cancel
        </button>
        <button
          @click="handleExport"
          :disabled="exporting || !store.currentProject"
          :class="[
            'px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors',
            success
              ? 'bg-green-600 text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed'
          ]"
        >
          <Check v-if="success" class="w-4 h-4" />
          <Download v-else :class="['w-4 h-4', exporting && 'animate-bounce']" />
          {{ success ? 'Downloaded!' : exporting ? 'Exporting...' : 'Export' }}
        </button>
      </div>
    </div>
  </div>
</template>
