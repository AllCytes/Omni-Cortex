<script setup lang="ts">
import { ref } from 'vue'
import { useOnboardingStore } from '@/stores/onboardingStore'
import {
  X, Keyboard, Sparkles, Info,
  RefreshCw, HelpCircle,
  Database, Activity, BarChart3, FileCheck, GitBranch, MessageSquare
} from 'lucide-vue-next'

const emit = defineEmits<{
  (e: 'close'): void
}>()

const onboardingStore = useOnboardingStore()

type TabId = 'shortcuts' | 'features' | 'about'
const activeTab = ref<TabId>('shortcuts')

const tabs = [
  { id: 'shortcuts' as const, label: 'Shortcuts', icon: Keyboard },
  { id: 'features' as const, label: 'Features', icon: Sparkles },
  { id: 'about' as const, label: 'About', icon: Info }
]

const shortcuts = [
  { group: 'Navigation', items: [
    { key: '/', description: 'Focus search bar' },
    { key: 'Esc', description: 'Clear selection / filters' },
    { key: 'j / k', description: 'Navigate down / up through memories' },
    { key: 'Enter', description: 'Select first memory' },
    { key: '?', description: 'Open this help dialog' }
  ]},
  { group: 'Quick Filters', items: [
    { key: '1-9', description: 'Filter by memory type (decision, solution, etc.)' }
  ]}
]

const features = [
  { icon: Database, title: 'Memory Browser', description: 'Browse, search, and filter your AI memories with powerful search and filtering.' },
  { icon: Activity, title: 'Activity Timeline', description: 'View a chronological timeline of all activities and tool usage.' },
  { icon: BarChart3, title: 'Statistics', description: 'Visualize activity heatmaps, tool usage charts, and memory growth trends.' },
  { icon: FileCheck, title: 'Freshness Review', description: 'Review and update outdated memories to keep your knowledge fresh.' },
  { icon: GitBranch, title: 'Relationship Graph', description: 'Explore visual connections between related memories using D3.js.' },
  { icon: MessageSquare, title: 'Ask AI', description: 'Chat with AI about your memories using natural language queries.' }
]

function startTour() {
  emit('close')
  onboardingStore.resetOnboarding()
  onboardingStore.startOnboarding()
}

function handleBackdropClick(e: MouseEvent) {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('close')
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center"
      @click="handleBackdropClick"
      @keydown="handleKeydown"
    >
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/50 transition-opacity" />

      <!-- Modal -->
      <div class="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden animate-fade-in">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <HelpCircle class="w-6 h-6 text-blue-500" />
            Help & Shortcuts
          </h2>
          <button
            @click="emit('close')"
            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Close (Esc)"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Tab Navigation -->
        <div class="flex border-b border-gray-200 dark:border-gray-700">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'flex items-center gap-2 px-6 py-3 font-medium transition-colors',
              activeTab === tab.id
                ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            ]"
          >
            <component :is="tab.icon" class="w-4 h-4" />
            {{ tab.label }}
          </button>
        </div>

        <!-- Content -->
        <div class="p-6 overflow-y-auto max-h-[50vh]">
          <!-- Shortcuts Tab -->
          <div v-if="activeTab === 'shortcuts'" class="space-y-6">
            <div v-for="group in shortcuts" :key="group.group">
              <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                {{ group.group }}
              </h3>
              <div class="space-y-2">
                <div
                  v-for="shortcut in group.items"
                  :key="shortcut.key"
                  class="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                >
                  <span class="text-gray-700 dark:text-gray-300">{{ shortcut.description }}</span>
                  <kbd class="px-2 py-1 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 text-sm font-mono rounded">
                    {{ shortcut.key }}
                  </kbd>
                </div>
              </div>
            </div>
          </div>

          <!-- Features Tab -->
          <div v-else-if="activeTab === 'features'" class="space-y-4">
            <div
              v-for="feature in features"
              :key="feature.title"
              class="flex items-start gap-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl"
            >
              <div class="p-2 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
                <component :is="feature.icon" class="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h4 class="font-semibold text-gray-900 dark:text-white">{{ feature.title }}</h4>
                <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">{{ feature.description }}</p>
              </div>
            </div>

            <button
              @click="startTour"
              class="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center justify-center gap-2 mt-6"
            >
              <RefreshCw class="w-4 h-4" />
              Take the Tour Again
            </button>
          </div>

          <!-- About Tab -->
          <div v-else-if="activeTab === 'about'" class="space-y-6">
            <div class="flex items-center gap-4">
              <div class="w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-600 rounded-2xl flex items-center justify-center">
                <Database class="w-8 h-8 text-white" />
              </div>
              <div>
                <h3 class="text-xl font-bold text-gray-900 dark:text-white">Omni-Cortex Dashboard</h3>
                <p class="text-gray-500 dark:text-gray-400">Version 1.0</p>
              </div>
            </div>

            <p class="text-gray-600 dark:text-gray-300 leading-relaxed">
              Omni-Cortex is an AI memory management system that helps Claude Code and other AI assistants
              remember context, decisions, and solutions across sessions. This dashboard provides a visual
              interface to browse, search, and manage your AI memories.
            </p>

            <div class="space-y-3">
              <h4 class="font-semibold text-gray-900 dark:text-white">Resources</h4>
              <div class="space-y-2">
                <a
                  href="https://github.com/Anthropic/omni-cortex"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline"
                >
                  GitHub Repository
                </a>
                <a
                  href="https://pypi.org/project/omni-cortex/"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline"
                >
                  PyPI Package
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
