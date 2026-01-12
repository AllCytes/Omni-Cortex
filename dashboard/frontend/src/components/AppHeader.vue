<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { useTheme } from '@/composables/useTheme'
import { useElapsedTime } from '@/composables/useElapsedTime'
import { Search, Filter, Wifi, WifiOff, Database, Sun, Moon, Monitor, Download, HelpCircle, Settings, Layers } from 'lucide-vue-next'
import MultiProjectSelector from './MultiProjectSelector.vue'
import ExportPanel from './ExportPanel.vue'
import HelpModal from './HelpModal.vue'
import ProjectManagementModal from './ProjectManagementModal.vue'
import SettingsModal from './SettingsModal.vue'

const emit = defineEmits<{
  (e: 'toggle-filters'): void
}>()

const store = useDashboardStore()
const { theme, toggleTheme } = useTheme()

const searchQuery = ref('')
const showProjectSwitcher = ref(false)
const showExportPanel = ref(false)
const showHelp = ref(false)
const showProjectManagement = ref(false)
const showSettings = ref(false)

// Live elapsed time since last update
const { formattedElapsed: lastUpdatedText } = useElapsedTime(
  () => store.lastUpdated
)

const totalMemories = computed(() => store.stats?.total_count ?? 0)

const themeIcon = computed(() => {
  if (theme.value === 'light') return Sun
  if (theme.value === 'dark') return Moon
  return Monitor
})

const themeLabel = computed(() => {
  if (theme.value === 'light') return 'Light'
  if (theme.value === 'dark') return 'Dark'
  return 'System'
})

function handleSearch() {
  store.search(searchQuery.value)
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    searchQuery.value = ''
    store.search('')
  }
}

function openProjectManagement() {
  showProjectSwitcher.value = false
  showProjectManagement.value = true
}

// Listen for help modal trigger from keyboard shortcuts
function handleShowHelp() {
  showHelp.value = true
}

onMounted(() => {
  window.addEventListener('show-help', handleShowHelp)
})

onUnmounted(() => {
  window.removeEventListener('show-help', handleShowHelp)
})
</script>

<template>
  <header class="app-header bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
    <div class="container mx-auto px-4 py-3">
      <div class="flex items-center justify-between gap-4">
        <!-- Logo & Title -->
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg flex items-center justify-center">
            <Database class="w-5 h-5 text-white" />
          </div>
          <h1 class="text-xl font-bold">Omni-Cortex</h1>
        </div>

        <!-- Multi-Project Selector -->
        <div class="project-switcher relative">
          <button
            @click="showProjectSwitcher = !showProjectSwitcher"
            :class="[
              'flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors',
              store.isMultiProject
                ? 'bg-gradient-to-r from-blue-100 to-purple-100 dark:from-blue-900/30 dark:to-purple-900/30'
                : 'bg-gray-100 dark:bg-gray-700'
            ]"
          >
            <Layers v-if="store.isMultiProject" class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <span class="font-medium truncate max-w-[200px]">
              {{ store.isMultiProject
                ? `${store.selectedProjects.length} Projects`
                : (store.currentProject?.name ?? 'Select Project')
              }}
            </span>
            <span class="text-sm text-gray-500 dark:text-gray-400">
              ({{ totalMemories }} memories)
            </span>
          </button>
          <MultiProjectSelector
            v-if="showProjectSwitcher"
            @close="showProjectSwitcher = false"
            @openManagement="openProjectManagement"
          />
        </div>

        <!-- Search Bar -->
        <div class="flex-1 max-w-xl">
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              v-model="searchQuery"
              @keyup.enter="handleSearch"
              @keydown="handleKeydown"
              type="text"
              placeholder="Search memories... (Enter to search, Esc to clear)"
              class="search-input w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg border-none focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2">
          <!-- Export Button -->
          <button
            @click="showExportPanel = true"
            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Export memories"
          >
            <Download class="w-5 h-5" />
          </button>

          <!-- Filter Toggle -->
          <button
            @click="emit('toggle-filters')"
            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Toggle Filters"
          >
            <Filter class="w-5 h-5" />
          </button>

          <!-- Settings Button -->
          <button
            @click="showSettings = true"
            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Settings & API Keys"
          >
            <Settings class="w-5 h-5" />
          </button>

          <!-- Theme Toggle -->
          <button
            @click="toggleTheme"
            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-1"
            :title="`Theme: ${themeLabel} (click to toggle)`"
          >
            <component :is="themeIcon" class="w-5 h-5" />
          </button>

          <!-- Help Button -->
          <button
            @click="showHelp = true"
            class="help-button p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Help & Shortcuts (?)"
          >
            <HelpCircle class="w-5 h-5" />
          </button>

          <!-- Connection Status -->
          <div
            class="live-status"
            :class="[
              'flex items-center gap-1 px-2 py-1 rounded-full text-sm',
              store.isConnected
                ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
                : 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300'
            ]"
            :title="lastUpdatedText ? `Last updated: ${lastUpdatedText}` : ''"
          >
            <!-- Pulsing dot when connected -->
            <span v-if="store.isConnected" class="relative flex h-2 w-2 mr-1">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            <Wifi v-if="store.isConnected" class="w-4 h-4" />
            <WifiOff v-else class="w-4 h-4" />
            <span>{{ store.isConnected ? 'Live' : 'Offline' }}</span>
            <span v-if="lastUpdatedText && store.isConnected" class="text-xs opacity-75">
              · {{ lastUpdatedText }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Export Panel Modal -->
    <ExportPanel v-if="showExportPanel" @close="showExportPanel = false" />

    <!-- Help Modal -->
    <HelpModal v-if="showHelp" @close="showHelp = false" />

    <!-- Project Management Modal -->
    <ProjectManagementModal v-if="showProjectManagement" @close="showProjectManagement = false" />

    <!-- Settings Modal -->
    <SettingsModal v-if="showSettings" @close="showSettings = false" />
  </header>
</template>
