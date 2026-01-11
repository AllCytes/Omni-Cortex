# Dashboard UX Enhancements Implementation Plan

## Overview

Three major UX enhancements for the Omni-Cortex web dashboard:

1. **Live Update Timer** - Real-time elapsed time display showing when data was last refreshed
2. **Onboarding Flow** - First-time user guided tour with step-by-step feature introduction
3. **Help Guide System** - Persistent help button with feature overview and ability to replay onboarding

## Current State Analysis

### Existing Infrastructure
- **AppHeader.vue** (lines 35-42): Has `lastUpdatedText` computed property with static text ("Just now", "5s ago", etc.)
- **dashboardStore.ts** (line 31): Has `lastUpdated` ref (timestamp in milliseconds)
- **App.vue**: Main layout with tab navigation (Memories, Activity, Stats, Review, Graph, Ask AI)
- **useKeyboardShortcuts.ts**: Already has `?` mapped to show help

### Gap Analysis
1. Timer doesn't auto-update (only recalculates on component re-render)
2. No onboarding system exists
3. No help modal/guide exists (keyboard shortcut `?` is wired but implementation unclear)

---

## Feature 1: Live Update Timer

### Problem
The current `lastUpdatedText` only updates when the component re-renders. Users can't see real-time elapsed time since last data refresh.

### Solution
Create a reactive timer that updates every second, showing elapsed time since `lastUpdated`.

### Implementation Steps

#### Step 1.1: Create useElapsedTime Composable
**File:** `dashboard/frontend/src/composables/useElapsedTime.ts`

```typescript
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

export function useElapsedTime(timestampRef: () => number | null, updateIntervalMs = 1000) {
  const elapsed = ref(0)
  let intervalId: ReturnType<typeof setInterval> | null = null

  function formatElapsed(ms: number): string {
    if (ms < 5000) return 'Just now'
    if (ms < 60000) return `${Math.floor(ms / 1000)}s ago`
    if (ms < 3600000) return `${Math.floor(ms / 60000)}m ago`
    if (ms < 86400000) return `${Math.floor(ms / 3600000)}h ago`
    return new Date(Date.now() - ms).toLocaleString()
  }

  const formattedElapsed = computed(() => {
    const timestamp = timestampRef()
    if (!timestamp) return ''
    return formatElapsed(elapsed.value)
  })

  function startTimer() {
    if (intervalId) clearInterval(intervalId)
    intervalId = setInterval(() => {
      const timestamp = timestampRef()
      if (timestamp) {
        elapsed.value = Date.now() - timestamp
      }
    }, updateIntervalMs)
  }

  function stopTimer() {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  onMounted(startTimer)
  onUnmounted(stopTimer)

  // Restart timer when timestamp changes
  watch(timestampRef, (newVal) => {
    if (newVal) {
      elapsed.value = Date.now() - newVal
    }
  })

  return { elapsed, formattedElapsed }
}
```

#### Step 1.2: Update AppHeader.vue
Replace the static `lastUpdatedText` computed with the composable:

```vue
// Add import
import { useElapsedTime } from '@/composables/useElapsedTime'

// Replace lastUpdatedText computed with:
const { formattedElapsed: lastUpdatedText } = useElapsedTime(
  () => store.lastUpdated
)
```

#### Step 1.3: Visual Enhancement
Add a pulsing dot indicator next to "Live" status when connected and receiving real-time updates.

---

## Feature 2: Onboarding Flow

### Problem
New users have no guided introduction to dashboard features.

### Solution
Create a step-by-step onboarding tour using a spotlight/overlay pattern that highlights each feature area.

### Implementation Steps

#### Step 2.1: Create Onboarding Store
**File:** `dashboard/frontend/src/stores/onboardingStore.ts`

```typescript
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
    description: 'Shows real-time connection status and when data was last updated. Updates automatically.',
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
    description: 'Browse, filter, and manage your memories. Click any memory to view details.',
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
```

#### Step 2.2: Create OnboardingOverlay Component
**File:** `dashboard/frontend/src/components/OnboardingOverlay.vue`

Key features:
- Full-screen overlay with spotlight cutout on target element
- Tooltip positioned relative to target
- Progress indicator (step X of Y)
- Next/Previous/Skip buttons
- Smooth animations between steps
- Click outside to dismiss (with confirmation)

```vue
<template>
  <Teleport to="body">
    <div v-if="store.isOnboarding" class="fixed inset-0 z-[100]">
      <!-- Backdrop with spotlight cutout -->
      <div class="absolute inset-0 bg-black/70 transition-opacity" />

      <!-- Spotlight highlight -->
      <div
        v-if="targetRect"
        class="absolute bg-white/10 ring-4 ring-blue-500 rounded-lg transition-all duration-300"
        :style="spotlightStyle"
      />

      <!-- Tooltip -->
      <div
        v-if="store.currentStep"
        class="absolute bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 max-w-md transition-all duration-300"
        :style="tooltipStyle"
      >
        <h3 class="text-lg font-bold mb-2">{{ store.currentStep.title }}</h3>
        <p class="text-gray-600 dark:text-gray-300 mb-4">{{ store.currentStep.description }}</p>

        <!-- Progress -->
        <div class="flex items-center gap-2 mb-4">
          <div class="flex-1 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full bg-blue-500 transition-all duration-300"
              :style="{ width: `${store.progress}%` }"
            />
          </div>
          <span class="text-sm text-gray-500">
            {{ store.currentStepIndex + 1 }} / {{ store.totalSteps }}
          </span>
        </div>

        <!-- Actions -->
        <div class="flex items-center justify-between">
          <button
            v-if="store.currentStepIndex > 0"
            @click="store.previousStep"
            class="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Back
          </button>
          <div class="flex-1" />
          <button
            @click="store.skipOnboarding"
            class="px-4 py-2 text-gray-500 hover:text-gray-700 mr-2"
          >
            Skip
          </button>
          <button
            @click="store.nextStep"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {{ store.currentStepIndex === store.totalSteps - 1 ? 'Finish' : 'Next' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
```

#### Step 2.3: Auto-trigger on First Visit
In App.vue `onMounted`:

```typescript
import { useOnboardingStore } from '@/stores/onboardingStore'

const onboardingStore = useOnboardingStore()

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
})
```

#### Step 2.4: Add CSS Classes for Targeting
Add identifying classes to target elements in relevant components:
- `.app-header` on header
- `.project-switcher` on project dropdown
- `.search-input` on search field
- `.live-status` on connection indicator
- `.tab-navigation` on tab buttons container
- `.memory-browser` on memory list
- `.help-button` on help icon

---

## Feature 3: Help Guide System

### Problem
No persistent help access or way to review features after onboarding.

### Solution
Add a help button in the header that opens a modal with:
- Keyboard shortcuts reference
- Feature overview
- "Replay Tour" button to restart onboarding
- Links to documentation

### Implementation Steps

#### Step 3.1: Create HelpModal Component
**File:** `dashboard/frontend/src/components/HelpModal.vue`

Structure:
```
HelpModal
├── Tabs: [Shortcuts, Features, About]
├── Shortcuts Tab
│   ├── Navigation shortcuts (/, Esc, j/k, 1-9)
│   ├── Action shortcuts (r, ?)
│   └── Tab shortcuts (if added)
├── Features Tab
│   ├── Feature cards with icons
│   ├── Brief descriptions
│   └── "Take Tour" button
└── About Tab
    ├── Version info
    ├── Documentation links
    └── Support info
```

```vue
<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/50" @click="$emit('close')" />

      <!-- Modal -->
      <div class="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b dark:border-gray-700">
          <h2 class="text-xl font-bold">Help & Shortcuts</h2>
          <button @click="$emit('close')" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Tab Navigation -->
        <div class="flex border-b dark:border-gray-700">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'px-6 py-3 font-medium transition-colors',
              activeTab === tab.id
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            ]"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Content -->
        <div class="p-6 overflow-y-auto max-h-[50vh]">
          <!-- Shortcuts Tab -->
          <div v-if="activeTab === 'shortcuts'" class="space-y-4">
            <ShortcutGroup title="Navigation">
              <ShortcutItem key="/" description="Focus search" />
              <ShortcutItem key="Esc" description="Clear selection/filters" />
              <ShortcutItem key="j/k" description="Navigate memories" />
              <ShortcutItem key="r" description="Refresh data" />
              <ShortcutItem key="?" description="Show this help" />
              <ShortcutItem key="1-9" description="Quick filter by type" />
            </ShortcutGroup>
          </div>

          <!-- Features Tab -->
          <div v-else-if="activeTab === 'features'" class="space-y-4">
            <FeatureCard
              v-for="feature in features"
              :key="feature.id"
              :icon="feature.icon"
              :title="feature.title"
              :description="feature.description"
            />
            <button
              @click="startTour"
              class="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Take the Tour Again
            </button>
          </div>

          <!-- About Tab -->
          <div v-else-if="activeTab === 'about'" class="space-y-4">
            <p>Omni-Cortex Dashboard v1.0</p>
            <p>Your AI memory management system.</p>
            <a href="/docs" class="text-blue-600 hover:underline">Documentation</a>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
```

#### Step 3.2: Add Help Button to AppHeader
Add HelpCircle icon button next to theme toggle:

```vue
<button
  @click="showHelp = true"
  class="help-button p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
  title="Help & Shortcuts (?)"
>
  <HelpCircle class="w-5 h-5" />
</button>

<HelpModal v-if="showHelp" @close="showHelp = false" />
```

#### Step 3.3: Connect Keyboard Shortcut
In useKeyboardShortcuts.ts, emit event or directly control help modal visibility:

```typescript
// Add to keyboard shortcuts
case '?':
  // Emit global event or use store
  window.dispatchEvent(new CustomEvent('show-help'))
  break
```

In AppHeader.vue:
```typescript
onMounted(() => {
  window.addEventListener('show-help', () => showHelp.value = true)
})
onUnmounted(() => {
  window.removeEventListener('show-help', () => {})
})
```

---

## File Structure

```
dashboard/frontend/src/
├── composables/
│   ├── useElapsedTime.ts      # NEW - Live timer composable
│   ├── useKeyboardShortcuts.ts # UPDATE - Add help trigger
│   └── ...
├── stores/
│   ├── onboardingStore.ts     # NEW - Onboarding state management
│   └── dashboardStore.ts      # EXISTING
├── components/
│   ├── OnboardingOverlay.vue  # NEW - Tour overlay
│   ├── HelpModal.vue          # NEW - Help/shortcuts modal
│   ├── AppHeader.vue          # UPDATE - Add help button, live timer
│   └── ...
└── App.vue                    # UPDATE - Add onboarding trigger
```

---

## Testing Strategy

### Unit Tests
1. **useElapsedTime**: Test formatting at various intervals (seconds, minutes, hours)
2. **onboardingStore**: Test step navigation, completion persistence, reset
3. **HelpModal**: Test tab switching, tour restart

### Integration Tests
1. First-time user sees onboarding automatically
2. Onboarding can be skipped and persists
3. Help modal opens with ? key
4. Timer updates every second
5. Tour can be replayed from help modal

### E2E Tests
1. Complete onboarding flow end-to-end
2. Verify all spotlight targets are visible during tour
3. Timer accuracy over 5+ minutes

---

## Potential Challenges

### Challenge 1: Element Positioning During Tour
**Problem:** Target elements may be off-screen or dynamically rendered.
**Solution:**
- Use `getBoundingClientRect()` with scroll-into-view
- Re-calculate positions on window resize
- Skip steps for elements that don't exist

### Challenge 2: Timer Performance
**Problem:** setInterval running every second could impact performance.
**Solution:**
- Only run timer when tab is visible (use Page Visibility API)
- Throttle updates when tab is hidden
- Clean up interval on unmount

### Challenge 3: Onboarding State Persistence
**Problem:** localStorage might not persist across browser sessions.
**Solution:**
- Use both localStorage and IndexedDB as fallback
- Consider syncing with user preferences API

---

## Success Criteria

1. **Live Timer**
   - [ ] Timer updates every second
   - [ ] Displays "Just now" for < 5s
   - [ ] Displays seconds for < 60s
   - [ ] Displays minutes for < 60m
   - [ ] Stops updating when tab is hidden

2. **Onboarding**
   - [ ] Auto-starts for first-time users
   - [ ] All 7 steps complete without errors
   - [ ] Skip works and persists
   - [ ] Can be replayed from help modal
   - [ ] Spotlight correctly highlights each element

3. **Help Guide**
   - [ ] Opens with ? keyboard shortcut
   - [ ] Opens with help button click
   - [ ] Shows all keyboard shortcuts
   - [ ] Shows feature overview
   - [ ] "Take Tour" button works

---

## Implementation Order

1. **Phase 1**: Live Update Timer (simplest, immediate value)
2. **Phase 2**: Help Modal (foundation for onboarding)
3. **Phase 3**: Onboarding Flow (depends on help modal for replay)

Estimated total: 4-6 focused development sessions
