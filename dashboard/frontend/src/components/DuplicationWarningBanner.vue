<script setup lang="ts">
import { ref, watch } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { AlertTriangle, X, Globe, Folder } from 'lucide-vue-next'

const store = useDashboardStore()
const isDismissed = ref(false)

function dismiss() {
  isDismissed.value = true
}

function handleViewGlobalOnly() {
  store.selectGlobalOnly()
  isDismissed.value = false  // Reset dismissal for future selections
}

function handleViewProjectsOnly() {
  store.selectProjectsOnly()
  isDismissed.value = false
}

// Reset dismissal when going from false to true (new warning condition)
watch(() => store.showDuplicationWarning, (newVal, oldVal) => {
  if (newVal && !oldVal) {
    isDismissed.value = false
  }
})
</script>

<template>
  <Transition
    enter-active-class="transition-all duration-200 ease-out"
    leave-active-class="transition-all duration-150 ease-in"
    enter-from-class="opacity-0 -translate-y-2"
    leave-to-class="opacity-0 -translate-y-2"
  >
    <div
      v-if="store.showDuplicationWarning && !isDismissed"
      class="bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700 rounded-lg p-4 mb-4"
    >
      <div class="flex items-start gap-3">
        <!-- Warning Icon -->
        <AlertTriangle class="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <h4 class="font-medium text-amber-800 dark:text-amber-200">
            Duplicate Counting Detected
          </h4>
          <p class="text-sm text-amber-700 dark:text-amber-300 mt-1">
            Global Index contains memories from all projects. Selecting both
            causes ~{{ store.estimatedOverlapCount }} memories to be counted twice.
          </p>

          <!-- Action Buttons -->
          <div class="flex gap-2 mt-3">
            <button
              @click="handleViewGlobalOnly"
              class="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md
                     bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200
                     hover:bg-amber-300 dark:hover:bg-amber-700 transition-colors"
            >
              <Globe class="w-4 h-4" />
              View Global Only
            </button>
            <button
              @click="handleViewProjectsOnly"
              class="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md
                     bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200
                     hover:bg-amber-300 dark:hover:bg-amber-700 transition-colors"
            >
              <Folder class="w-4 h-4" />
              View Projects Only
            </button>
          </div>
        </div>

        <!-- Dismiss Button -->
        <button
          @click="dismiss"
          class="flex-shrink-0 p-1 rounded-md text-amber-600 dark:text-amber-400
                 hover:bg-amber-200 dark:hover:bg-amber-800 transition-colors"
          title="Dismiss"
        >
          <X class="w-4 h-4" />
        </button>
      </div>
    </div>
  </Transition>
</template>
