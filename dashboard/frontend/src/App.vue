<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { useOnboardingStore } from '@/stores/onboardingStore'
import { useWebSocket } from '@/composables/useWebSocket'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import AppHeader from '@/components/AppHeader.vue'
import FilterPanel from '@/components/FilterPanel.vue'
import MemoryBrowser from '@/components/MemoryBrowser.vue'
import MemoryDetail from '@/components/MemoryDetail.vue'
import StatsPanel from '@/components/StatsPanel.vue'
import ActivityTimeline from '@/components/ActivityTimeline.vue'
import ChatPanel from '@/components/ChatPanel.vue'
import SessionContextViewer from '@/components/SessionContextViewer.vue'
import FreshnessReviewPanel from '@/components/FreshnessReviewPanel.vue'
import RelationshipGraph from '@/components/RelationshipGraph.vue'
import StyleTab from '@/components/StyleTab.vue'
import OnboardingOverlay from '@/components/OnboardingOverlay.vue'
import QuickCaptureModal from '@/components/QuickCaptureModal.vue'
import { Plus, Check } from 'lucide-vue-next'

const store = useDashboardStore()
const onboardingStore = useOnboardingStore()
const { connect } = useWebSocket()
useKeyboardShortcuts()

const showFilters = ref(true)
const activeTab = ref<'memories' | 'activity' | 'stats' | 'style' | 'review' | 'graph' | 'chat'>('memories')
const showQuickCapture = ref(false)
const toast = ref({ show: false, message: '' })

onMounted(async () => {
  await store.loadProjects()
  connect()

  // Start onboarding for first-time users
  if (!onboardingStore.hasCompletedOnboarding) {
    // Small delay to ensure UI is rendered
    setTimeout(() => {
      onboardingStore.startOnboarding()
    }, 500)
  }

  // Listen for quick capture keyboard shortcut
  window.addEventListener('show-quick-capture', () => {
    showQuickCapture.value = true
  })
})

function toggleFilters() {
  showFilters.value = !showFilters.value
}

function handleNavigateToMemory(_memoryId: string) {
  // Switch to memories tab when navigating from chat
  activeTab.value = 'memories'
}

function showToast(message: string, duration = 3000) {
  toast.value = { show: true, message }
  setTimeout(() => {
    toast.value.show = false
  }, duration)
}

function handleQuickCaptureSuccess(memory: { id: string; content: string }) {
  const preview = memory.content.slice(0, 30) + (memory.content.length > 30 ? '...' : '')
  showToast(`Memory created: "${preview}"`)
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <AppHeader @toggle-filters="toggleFilters" />

    <main class="container mx-auto px-4 py-6">
      <!-- Session Context (collapsible) -->
      <div v-if="store.currentProject" class="mb-6">
        <SessionContextViewer />
      </div>

      <!-- Tab Navigation -->
      <div class="tab-navigation flex gap-2 mb-6">
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
          @click="activeTab = 'activity'"
          :class="[
            'px-4 py-2 rounded-lg font-medium transition-colors',
            activeTab === 'activity'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
          ]"
        >
          Activity
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
        <button
          @click="activeTab = 'style'"
          :class="[
            'px-4 py-2 rounded-lg font-medium transition-colors',
            activeTab === 'style'
              ? 'bg-indigo-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
          ]"
        >
          Style
        </button>
        <button
          @click="activeTab = 'review'"
          :class="[
            'px-4 py-2 rounded-lg font-medium transition-colors',
            activeTab === 'review'
              ? 'bg-amber-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
          ]"
        >
          Review
        </button>
        <button
          @click="activeTab = 'graph'"
          :class="[
            'px-4 py-2 rounded-lg font-medium transition-colors',
            activeTab === 'graph'
              ? 'bg-purple-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
          ]"
        >
          Graph
        </button>
        <button
          @click="activeTab = 'chat'"
          :class="[
            'px-4 py-2 rounded-lg font-medium transition-colors',
            activeTab === 'chat'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
          ]"
        >
          Ask AI
        </button>
      </div>

      <!-- Memories Tab -->
      <div v-if="activeTab === 'memories'" class="flex gap-6">
        <!-- Filter Panel (collapsible) -->
        <aside
          v-if="showFilters"
          class="w-64 flex-shrink-0 animate-fade-in"
        >
          <FilterPanel />
        </aside>

        <!-- Memory List -->
        <div class="memory-browser flex-1 min-w-0">
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

      <!-- Activity Tab -->
      <div v-else-if="activeTab === 'activity'">
        <ActivityTimeline />
      </div>

      <!-- Stats Tab -->
      <div v-else-if="activeTab === 'stats'">
        <StatsPanel />
      </div>

      <!-- Style Tab -->
      <div v-else-if="activeTab === 'style'" class="max-w-6xl mx-auto">
        <StyleTab />
      </div>

      <!-- Review Tab -->
      <div v-else-if="activeTab === 'review'" class="max-w-4xl mx-auto">
        <FreshnessReviewPanel />
      </div>

      <!-- Graph Tab -->
      <div v-else-if="activeTab === 'graph'">
        <RelationshipGraph />
      </div>

      <!-- Chat Tab -->
      <div v-else-if="activeTab === 'chat'" class="max-w-6xl mx-auto h-[calc(100vh-200px)]">
        <ChatPanel @navigate-to-memory="handleNavigateToMemory" />
      </div>
    </main>

    <!-- Onboarding Overlay -->
    <OnboardingOverlay />

    <!-- Floating Action Button -->
    <button
      @click="showQuickCapture = true"
      class="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center z-40 group"
      title="Quick Capture (Ctrl+Shift+N)"
    >
      <Plus class="w-6 h-6 group-hover:rotate-90 transition-transform duration-200" />
    </button>

    <!-- Quick Capture Modal -->
    <QuickCaptureModal
      :is-open="showQuickCapture"
      @close="showQuickCapture = false"
      @success="handleQuickCaptureSuccess"
    />

    <!-- Toast Notification -->
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      leave-active-class="transition-all duration-200 ease-in"
      enter-from-class="opacity-0 translate-y-2"
      leave-to-class="opacity-0 translate-y-2"
    >
      <div
        v-if="toast.show"
        class="fixed bottom-24 right-6 bg-green-600 text-white px-4 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2"
      >
        <Check class="w-5 h-5" />
        <span>{{ toast.message }}</span>
      </div>
    </Transition>
  </div>
</template>
