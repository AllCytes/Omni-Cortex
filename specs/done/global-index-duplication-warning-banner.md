# Global Index Duplication Warning Banner

## Problem Statement

When users select both the Global Index and individual projects simultaneously in the Multi-Project Selector, they see duplicate memory counts because:
1. The Global Index contains aggregated memories from ALL projects
2. Individual project databases contain the same memories
3. Combined selection results in the same memories appearing twice in counts/results

Users need a clear visual warning explaining this behavior and easy options to fix it.

## Objectives

1. Display an amber/yellow info banner when Global Index + other projects are selected
2. Explain the duplicate counting issue clearly
3. Show the estimated overlap count
4. Provide quick-action buttons to resolve the situation
5. Allow manual dismissal with X button

## Technical Approach

### Component Structure

Create a new dedicated component `DuplicationWarningBanner.vue` for:
- Clean separation of concerns
- Reusable warning pattern
- Easy testing

### Location in UI

The banner appears in the `MemoryBrowser.vue` component:
- Below the "Memories" header section
- Above the memory cards list
- Part of the memories tab only (main use case)

### State Management

Add computed properties to `dashboardStore.ts`:
```typescript
// Check if Global Index is selected
const hasGlobalSelected = computed(() =>
  selectedProjects.value.some(p => p.is_global)
)

// Check if non-global projects are selected
const hasNonGlobalSelected = computed(() =>
  selectedProjects.value.some(p => !p.is_global)
)

// Show duplication warning when both are selected
const showDuplicationWarning = computed(() =>
  hasGlobalSelected.value && hasNonGlobalSelected.value
)

// Estimate overlap count (sum of non-global project memory counts)
const estimatedOverlapCount = computed(() => {
  if (!showDuplicationWarning.value) return 0
  return selectedProjects.value
    .filter(p => !p.is_global)
    .reduce((sum, p) => sum + p.memory_count, 0)
})
```

### Store Actions

Add two new actions to resolve duplication:
```typescript
function selectGlobalOnly() {
  const globalProject = projects.value.find(p => p.is_global)
  if (globalProject) {
    selectedProjects.value = [globalProject]
    loadAggregateData()
  }
}

function selectProjectsOnly() {
  selectedProjects.value = selectedProjects.value.filter(p => !p.is_global)
  loadAggregateData()
}
```

## Implementation Steps

### Step 1: Update Dashboard Store

**File:** `dashboard/frontend/src/stores/dashboardStore.ts`

Add computed properties:
- `hasGlobalSelected`
- `hasNonGlobalSelected`
- `showDuplicationWarning`
- `estimatedOverlapCount`

Add actions:
- `selectGlobalOnly()`
- `selectProjectsOnly()`

### Step 2: Create Warning Banner Component

**File:** `dashboard/frontend/src/components/DuplicationWarningBanner.vue`

```vue
<script setup lang="ts">
import { ref } from 'vue'
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
```

### Step 3: Integrate Banner into MemoryBrowser

**File:** `dashboard/frontend/src/components/MemoryBrowser.vue`

```vue
<script setup lang="ts">
import DuplicationWarningBanner from './DuplicationWarningBanner.vue'
// ... existing imports
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border...">
    <!-- Header -->
    <div class="px-4 py-3 border-b...">
      <!-- existing header content -->
    </div>

    <!-- Duplication Warning Banner (NEW) -->
    <div class="px-4 pt-4">
      <DuplicationWarningBanner />
    </div>

    <!-- Memory List -->
    <div ref="listRef" @scroll="handleScroll" class="overflow-y-auto...">
      <!-- existing content -->
    </div>
  </div>
</template>
```

## Visual Design

### Color Scheme (Amber/Yellow)
- Background: `bg-amber-50` / `dark:bg-amber-900/30`
- Border: `border-amber-200` / `dark:border-amber-700`
- Text: `text-amber-700/800` / `dark:text-amber-200/300`
- Icon: `text-amber-500`
- Button Background: `bg-amber-200` / `dark:bg-amber-800`

### Layout
```
┌──────────────────────────────────────────────────────────────┐
│ ⚠️ Duplicate Counting Detected                           [X] │
│    Global Index contains memories from all projects.         │
│    Selecting both causes ~42 memories to be counted twice.   │
│                                                              │
│    [🌐 View Global Only]  [📁 View Projects Only]           │
└──────────────────────────────────────────────────────────────┘
```

## Potential Challenges and Solutions

### Challenge 1: Dismissal State Persistence
**Issue:** User dismisses banner, changes selection, banner should reappear
**Solution:** Reset `isDismissed` when action buttons are clicked; use `watch` on `showDuplicationWarning` to reset dismissal when conditions change

```typescript
watch(() => store.showDuplicationWarning, (newVal, oldVal) => {
  // Reset dismissal when going from false to true (new warning condition)
  if (newVal && !oldVal) {
    isDismissed.value = false
  }
})
```

### Challenge 2: Accurate Overlap Calculation
**Issue:** Exact overlap count requires querying both databases
**Solution:** Use estimated count (sum of individual project memory counts) with "~" prefix to indicate approximation. This avoids expensive database queries.

### Challenge 3: Animation Timing
**Issue:** Banner appearing/disappearing should feel smooth
**Solution:** Use Vue's `<Transition>` with appropriate duration and transform classes

## Testing Strategy

### Manual Testing Checklist
1. [ ] Select only Global Index → No banner shown
2. [ ] Select only individual projects → No banner shown
3. [ ] Select Global Index + 1 project → Banner shows with overlap count
4. [ ] Select Global Index + multiple projects → Banner shows combined overlap
5. [ ] Click "View Global Only" → Only Global Index selected, banner hides
6. [ ] Click "View Projects Only" → Global Index deselected, banner hides
7. [ ] Click X button → Banner hides
8. [ ] After X dismiss, select different combo → Banner reappears
9. [ ] Dark mode → Banner styled correctly with amber colors
10. [ ] Animation → Smooth enter/exit transitions

### Component Unit Tests (if time permits)
- Test `showDuplicationWarning` computed logic
- Test `estimatedOverlapCount` calculation
- Test `selectGlobalOnly` action
- Test `selectProjectsOnly` action

## Success Criteria

- [ ] Banner appears only when Global Index AND other projects selected
- [ ] Banner clearly explains the duplicate counting issue
- [ ] Overlap count is displayed with "~" approximation
- [ ] "View Global Only" button works correctly
- [ ] "View Projects Only" button works correctly
- [ ] X button dismisses banner
- [ ] Banner reappears when selection changes
- [ ] Amber/yellow color scheme applied
- [ ] Smooth animation transitions
- [ ] Works in both light and dark mode

## Files to Modify

1. `dashboard/frontend/src/stores/dashboardStore.ts` - Add computed properties and actions
2. `dashboard/frontend/src/components/DuplicationWarningBanner.vue` - New component (create)
3. `dashboard/frontend/src/components/MemoryBrowser.vue` - Integrate banner

## Dependencies

- `lucide-vue-next` icons (already installed): `AlertTriangle`, `X`, `Globe`, `Folder`
- Vue's `Transition` component (built-in)
- TailwindCSS amber color palette (already available)

## Estimated Implementation Time

- Store updates: 15 minutes
- Banner component: 30 minutes
- Integration: 10 minutes
- Testing: 20 minutes
- **Total: ~75 minutes**
