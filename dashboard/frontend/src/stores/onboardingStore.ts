import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface OnboardingStep {
  id: string
  target: string // CSS selector
  title: string
  description: string
  position: 'top' | 'bottom' | 'left' | 'right'
}

const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    id: 'welcome',
    target: '.app-header',
    title: 'Welcome to Omni-Cortex Dashboard!',
    description: 'Your AI memory management system. Let\'s take a quick tour of the main features.',
    position: 'bottom'
  },
  {
    id: 'project-switcher',
    target: '.project-switcher',
    title: 'Project Switcher',
    description: 'Switch between different projects to view their memories. Each project has its own memory database.',
    position: 'bottom'
  },
  {
    id: 'search',
    target: '.search-input',
    title: 'Search Memories',
    description: 'Search through your memories using keywords. Press / to focus, Enter to search, Esc to clear.',
    position: 'bottom'
  },
  {
    id: 'live-status',
    target: '.live-status',
    title: 'Live Status',
    description: 'Shows real-time connection status and when data was last updated. Updates automatically every second.',
    position: 'left'
  },
  {
    id: 'tabs',
    target: '.tab-navigation',
    title: 'Dashboard Tabs',
    description: 'Navigate between Memories, Activity timeline, Statistics, Review panel, Relationship Graph, and AI Chat.',
    position: 'bottom'
  },
  {
    id: 'memory-browser',
    target: '.memory-browser',
    title: 'Memory Browser',
    description: 'Browse, filter, and manage your memories. Click any memory to view details. Use j/k keys to navigate.',
    position: 'right'
  },
  {
    id: 'keyboard-shortcuts',
    target: '.help-button',
    title: 'Need Help?',
    description: 'Click here anytime to see keyboard shortcuts, replay this tour, or get help. Press ? for quick access.',
    position: 'left'
  }
]

export const useOnboardingStore = defineStore('onboarding', () => {
  const hasCompletedOnboarding = ref(localStorage.getItem('onboarding_completed') === 'true')
  const isOnboarding = ref(false)
  const currentStepIndex = ref(0)

  const currentStep = computed(() =>
    isOnboarding.value ? ONBOARDING_STEPS[currentStepIndex.value] : null
  )

  const totalSteps = computed(() => ONBOARDING_STEPS.length)
  const progress = computed(() => ((currentStepIndex.value + 1) / totalSteps.value) * 100)

  function startOnboarding() {
    isOnboarding.value = true
    currentStepIndex.value = 0
  }

  function nextStep() {
    if (currentStepIndex.value < ONBOARDING_STEPS.length - 1) {
      currentStepIndex.value++
    } else {
      completeOnboarding()
    }
  }

  function previousStep() {
    if (currentStepIndex.value > 0) {
      currentStepIndex.value--
    }
  }

  function skipOnboarding() {
    completeOnboarding()
  }

  function completeOnboarding() {
    isOnboarding.value = false
    hasCompletedOnboarding.value = true
    localStorage.setItem('onboarding_completed', 'true')
  }

  function resetOnboarding() {
    localStorage.removeItem('onboarding_completed')
    hasCompletedOnboarding.value = false
  }

  return {
    hasCompletedOnboarding,
    isOnboarding,
    currentStep,
    currentStepIndex,
    totalSteps,
    progress,
    startOnboarding,
    nextStep,
    previousStep,
    skipOnboarding,
    completeOnboarding,
    resetOnboarding
  }
})
