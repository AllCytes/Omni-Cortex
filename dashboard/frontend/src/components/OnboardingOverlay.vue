<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useOnboardingStore } from '@/stores/onboardingStore'
import { ChevronLeft, ChevronRight, X } from 'lucide-vue-next'

const store = useOnboardingStore()

// Target element positioning
const targetRect = ref<DOMRect | null>(null)

// Calculate spotlight style based on target element
const spotlightStyle = computed(() => {
  if (!targetRect.value) return {}
  const padding = 8
  return {
    top: `${targetRect.value.top - padding}px`,
    left: `${targetRect.value.left - padding}px`,
    width: `${targetRect.value.width + padding * 2}px`,
    height: `${targetRect.value.height + padding * 2}px`
  }
})

// Calculate tooltip position based on step position preference
const tooltipStyle = computed(() => {
  if (!targetRect.value || !store.currentStep) return {}

  const rect = targetRect.value
  const tooltipWidth = 380
  const tooltipHeight = 200
  const gap = 16
  const position = store.currentStep.position

  let top = 0
  let left = 0

  switch (position) {
    case 'bottom':
      top = rect.bottom + gap
      left = rect.left + (rect.width / 2) - (tooltipWidth / 2)
      break
    case 'top':
      top = rect.top - tooltipHeight - gap
      left = rect.left + (rect.width / 2) - (tooltipWidth / 2)
      break
    case 'left':
      top = rect.top + (rect.height / 2) - (tooltipHeight / 2)
      left = rect.left - tooltipWidth - gap
      break
    case 'right':
      top = rect.top + (rect.height / 2) - (tooltipHeight / 2)
      left = rect.right + gap
      break
  }

  // Keep within viewport bounds
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  if (left < 16) left = 16
  if (left + tooltipWidth > viewportWidth - 16) left = viewportWidth - tooltipWidth - 16
  if (top < 16) top = 16
  if (top + tooltipHeight > viewportHeight - 16) top = viewportHeight - tooltipHeight - 16

  return {
    top: `${top}px`,
    left: `${left}px`,
    width: `${tooltipWidth}px`
  }
})

// Update target element position
function updateTargetPosition() {
  if (!store.currentStep) {
    targetRect.value = null
    return
  }

  const element = document.querySelector(store.currentStep.target)
  if (element) {
    targetRect.value = element.getBoundingClientRect()
    // Scroll element into view if needed
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
  } else {
    // Skip to next step if element not found
    console.warn(`Onboarding: Element not found for selector "${store.currentStep.target}"`)
    targetRect.value = null
  }
}

// Watch for step changes and update position
watch(() => store.currentStepIndex, async () => {
  await nextTick()
  updateTargetPosition()
}, { immediate: true })

// Handle window resize
function handleResize() {
  updateTargetPosition()
}

// Handle escape key to skip
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    store.skipOnboarding()
  } else if (e.key === 'ArrowRight' || e.key === 'Enter') {
    store.nextStep()
  } else if (e.key === 'ArrowLeft') {
    store.previousStep()
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeydown)
  updateTargetPosition()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport to="body">
    <div v-if="store.isOnboarding" class="fixed inset-0 z-[100]">
      <!-- Backdrop with spotlight cutout -->
      <div class="absolute inset-0 bg-black/70 transition-opacity duration-300" />

      <!-- Spotlight highlight -->
      <div
        v-if="targetRect"
        class="absolute bg-white/10 ring-4 ring-blue-500 rounded-lg transition-all duration-300 pointer-events-none"
        :style="spotlightStyle"
      />

      <!-- Tooltip -->
      <div
        v-if="store.currentStep"
        class="absolute bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 transition-all duration-300"
        :style="tooltipStyle"
      >
        <div class="flex items-start justify-between mb-3">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white">
            {{ store.currentStep.title }}
          </h3>
          <button
            @click="store.skipOnboarding"
            class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Skip tour (Esc)"
          >
            <X class="w-4 h-4 text-gray-500" />
          </button>
        </div>

        <p class="text-gray-600 dark:text-gray-300 mb-5 leading-relaxed">
          {{ store.currentStep.description }}
        </p>

        <!-- Progress bar -->
        <div class="flex items-center gap-3 mb-4">
          <div class="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full bg-blue-500 transition-all duration-300"
              :style="{ width: `${store.progress}%` }"
            />
          </div>
          <span class="text-sm text-gray-500 dark:text-gray-400 font-medium whitespace-nowrap">
            {{ store.currentStepIndex + 1 }} / {{ store.totalSteps }}
          </span>
        </div>

        <!-- Actions -->
        <div class="flex items-center justify-between">
          <button
            v-if="store.currentStepIndex > 0"
            @click="store.previousStep"
            class="flex items-center gap-1 px-3 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
          >
            <ChevronLeft class="w-4 h-4" />
            Back
          </button>
          <div v-else class="flex-1" />

          <div class="flex items-center gap-2">
            <button
              @click="store.skipOnboarding"
              class="px-4 py-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
            >
              Skip
            </button>
            <button
              @click="store.nextStep"
              class="flex items-center gap-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              {{ store.currentStepIndex === store.totalSteps - 1 ? 'Finish' : 'Next' }}
              <ChevronRight v-if="store.currentStepIndex < store.totalSteps - 1" class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
