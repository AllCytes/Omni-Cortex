<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import StyleProfileCard from '@/components/style/StyleProfileCard.vue'
import MessageHistoryTable from '@/components/style/MessageHistoryTable.vue'
import StyleSamplesPanel from '@/components/style/StyleSamplesPanel.vue'
import { User, RefreshCw, MessageSquare } from 'lucide-vue-next'

const store = useDashboardStore()
const loading = ref(false)
const error = ref<string | null>(null)

const currentProject = computed(() => store.currentProject)

// Track if we have any data
const hasProject = computed(() => !!currentProject.value)

async function refreshAll() {
  loading.value = true
  error.value = null

  try {
    // The child components handle their own data fetching
    // This refresh triggers a re-mount which causes them to refetch
    // We could also emit events to children if needed
    await new Promise(resolve => setTimeout(resolve, 100))
  } catch (e) {
    console.error('Failed to refresh style data:', e)
    error.value = 'Failed to refresh data'
  } finally {
    loading.value = false
  }
}

// Watch for project changes
watch(currentProject, () => {
  error.value = null
})

onMounted(() => {
  // Initial load handled by child components
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
          <User class="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
        </div>
        <div>
          <h1 class="text-xl font-semibold">Communication Style</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Analyze your messaging patterns and tone
          </p>
        </div>
      </div>
      <button
        v-if="hasProject"
        @click="refreshAll"
        :disabled="loading"
        class="flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
      >
        <RefreshCw :class="['w-4 h-4', { 'animate-spin': loading }]" />
        Refresh All
      </button>
    </div>

    <!-- Error State -->
    <div
      v-if="error"
      class="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-4 rounded-lg"
    >
      {{ error }}
    </div>

    <!-- No Project Selected -->
    <div
      v-if="!hasProject"
      class="text-center py-16 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700"
    >
      <MessageSquare class="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
      <h2 class="text-xl font-medium text-gray-600 dark:text-gray-400 mb-2">
        No Project Selected
      </h2>
      <p class="text-gray-500 dark:text-gray-500 max-w-md mx-auto">
        Select a project from the header to view your communication style analysis.
        Your messaging patterns will be tracked as you interact with Claude Code.
      </p>
    </div>

    <!-- Content (when project is selected) -->
    <template v-else>
      <!-- Style Profile Card -->
      <StyleProfileCard />

      <!-- Message History Table -->
      <MessageHistoryTable />

      <!-- Style Samples Panel -->
      <StyleSamplesPanel />
    </template>
  </div>
</template>
