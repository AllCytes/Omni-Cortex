# Fix Multi-Project Selector Bugs

## Problem Statement

The MultiProjectSelector component has two UI bugs:

1. **Memory Count Display Bug**: The dropdown trigger shows "0 memories" instead of the actual total count when projects are selected. The per-project counts in the dropdown list show correctly, confirming data fetching works - the issue is in display logic.

2. **Click Toggle Bug**: Clicking the dropdown trigger only opens the dropdown - it doesn't toggle closed. Users must click outside to close. Expected behavior is click-to-toggle open/closed.

## Technical Analysis

### Bug 1: Memory Count Shows 0

**Location**: `AppHeader.vue` lines 106-108

```vue
<span class="text-sm text-gray-500 dark:text-gray-400">
  ({{ totalMemories }} memories)
</span>
```

**Root Cause**: `totalMemories` is computed from `store.stats?.total_count ?? 0`. The issue is a race condition - when `toggleProjectSelection()` is called:
1. It mutates `selectedProjects` via `splice/push`
2. Then calls `loadAggregateData()` which is async
3. The `stats.value` isn't updated until the API call completes

**BUT** - the user reported tags filter updates correctly, so API calls ARE succeeding. The likely issue is that `splice()` on line 87 doesn't trigger Vue reactivity properly for arrays in some cases, or the stats value is being set but not reflected in the computed.

**Actual Root Cause Found**: Looking at `clearProjectSelection()` - it sets `stats.value = null` but there's no similar reset logic in toggle. The issue is likely that when switching from single to multi-project or vice versa, there's a mismatch. Let me trace further:
- `loadAggregateStats()` does: `stats.value = await api.getAggregateStats(selectedDbPaths.value)`
- This should work, but the API might be returning a different structure

**Real Issue**: After async `loadAggregateData()`, the stats ARE being fetched correctly. The computed `totalMemories` uses `store.stats?.total_count ?? 0`. If stats is null or total_count is undefined, it shows 0. Need to verify the API response structure matches expectations.

### Bug 2: Click Toggle Not Working

**Location**:
- `AppHeader.vue` line 91: `@click="showProjectSwitcher = !showProjectSwitcher"`
- `MultiProjectSelector.vue` lines 33-46: Click outside handler

**Root Cause**: The `handleClickOutside` listener uses `capture: true` (third argument is `true`):
```js
document.addEventListener('click', handleClickOutside, true)
```

Event flow with capture:
1. Click on trigger button
2. Capture phase fires FIRST - `handleClickOutside` runs
3. The check `!target.closest('.multi-project-selector')` passes (button is outside the dropdown)
4. `emit('close')` fires, setting `showProjectSwitcher = false`
5. Bubbling phase - button click handler runs, toggles `false` to `true`
6. Result: dropdown opens (appears like it didn't close)

**Fix**: The click outside handler needs to also exclude the trigger button. The trigger button is in `.project-switcher` container.

## Implementation Plan

### Step 1: Fix Click Toggle Bug

**File**: `dashboard/frontend/src/components/MultiProjectSelector.vue`

**Change**: Modify `handleClickOutside` to also exclude clicks on the parent trigger container.

```diff
function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
-  if (!target.closest('.multi-project-selector')) {
+  // Exclude both the dropdown itself AND the trigger button in .project-switcher
+  if (!target.closest('.multi-project-selector') && !target.closest('.project-switcher')) {
    emit('close')
  }
}
```

**Rationale**: This allows the toggle logic in `AppHeader.vue` to handle the click instead of the outside handler pre-empting it.

### Step 2: Verify Memory Count Bug

**File**: `dashboard/frontend/src/components/AppHeader.vue`

First, add console logging to verify stats are being received:
- Check if `store.stats` is populated after project selection
- Check if `total_count` property exists

If stats are correct but display is wrong, the issue may be Vue reactivity with the `.splice()` mutation.

### Step 3: Fix Reactivity if Needed

**File**: `dashboard/frontend/src/stores/dashboardStore.ts`

**Potential Fix**: Replace `splice()` with immutable array operations for better Vue 3 reactivity:

```diff
function toggleProjectSelection(project: Project) {
  const index = selectedProjects.value.findIndex(p => p.db_path === project.db_path)
  if (index >= 0) {
-    selectedProjects.value.splice(index, 1)
+    selectedProjects.value = selectedProjects.value.filter(p => p.db_path !== project.db_path)
  } else {
-    selectedProjects.value.push(project)
+    selectedProjects.value = [...selectedProjects.value, project]
  }
  loadAggregateData()
}
```

**Rationale**: While Vue 3's reactivity system should track array mutations, replacing the entire array guarantees computed properties recalculate.

## Testing Strategy

### Manual Tests

1. **Toggle Test**:
   - Open dropdown by clicking trigger
   - Click trigger again - should close
   - Click trigger again - should open
   - Click outside - should close

2. **Memory Count Test**:
   - Select one project - verify count matches that project
   - Select additional project - verify count is sum of both
   - Use "Select All" - verify total across all projects
   - Use "Clear" - verify shows 0 or placeholder

3. **Integration Test**:
   - Select projects, verify tags panel updates (existing behavior)
   - Verify memories list updates with project badges
   - Verify stats panel reflects aggregate data

### Console Verification

Add temporary logging:
```js
watch(stats, (newVal) => {
  console.log('Stats updated:', newVal?.total_count)
})
```

## Files to Modify

1. `dashboard/frontend/src/components/MultiProjectSelector.vue` - Fix click outside handler
2. `dashboard/frontend/src/stores/dashboardStore.ts` - Improve array reactivity (if needed)
3. `dashboard/frontend/src/components/AppHeader.vue` - No changes expected, but verify

## Success Criteria

- [ ] Clicking dropdown trigger toggles open/closed (not just opens)
- [ ] Memory count in trigger reflects actual total across selected projects
- [ ] Memory count updates immediately when selection changes
- [ ] Tags filter continues to work correctly
- [ ] No console errors
- [ ] Build passes without TypeScript errors

## Estimated Time

30-45 minutes (simple UI bug fixes)

## Notes

- The dropdown uses capture phase event listener which is unusual - consider switching to bubbling phase
- Vue 3 Composition API with `ref()` should handle array mutations, but immutable patterns are safer
- Tags filter working confirms API endpoints are functional
