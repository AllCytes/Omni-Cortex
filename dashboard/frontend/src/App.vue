<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { useWebSocket } from '@/composables/useWebSocket'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import AppHeader from '@/components/AppHeader.vue'
import FilterPanel from '@/components/FilterPanel.vue'
import MemoryBrowser from '@/components/MemoryBrowser.vue'
import MemoryDetail from '@/components/MemoryDetail.vue'
import StatsPanel from '@/components/StatsPanel.vue'

const store = useDashboardStore()
const { connect } = useWebSocket()
useKeyboardShortcuts()

const showFilters = ref(true)
const activeTab = ref<'memories' | 'stats'>('memories')

onMounted(async () => {
  await store.loadProjects()
  connect()
})

function toggleFilters() {
  showFilters.value = !showFilters.value
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <AppHeader @toggle-filters="toggleFilters" />

    <main class="container mx-auto px-4 py-6">
      <!-- Tab Navigation -->
      <div class="flex gap-2 mb-6">
        <button
          @click="activeTab = 'memories'"
          :class="[
            'px-4 py-2 rounded-lg font-medium transition-colors',
            activeTab === 'memories'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
          ]"
        >
          Memories
        </button>
        <button
          @click="activeTab = 'stats'"
          :class="[
            'px-4 py-2 rounded-lg font-medium transition-colors',
            activeTab === 'stats'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
          ]"
        >
          Statistics
        </button>
      </div>

      <!-- Content Area -->
      <div v-if="activeTab === 'memories'" class="flex gap-6">
        <!-- Filter Panel (collapsible) -->
        <aside
          v-if="showFilters"
          class="w-64 flex-shrink-0 animate-fade-in"
        >
          <FilterPanel />
        </aside>

        <!-- Memory List -->
        <div class="flex-1 min-w-0">
          <MemoryBrowser />
        </div>

        <!-- Memory Detail Panel -->
        <aside
          v-if="store.selectedMemory"
          class="w-96 flex-shrink-0 animate-fade-in"
        >
          <MemoryDetail :memory="store.selectedMemory" @close="store.clearSelection" />
        </aside>
      </div>

      <!-- Stats Tab -->
      <div v-else-if="activeTab === 'stats'">
        <StatsPanel />
      </div>
    </main>
  </div>
</template>
