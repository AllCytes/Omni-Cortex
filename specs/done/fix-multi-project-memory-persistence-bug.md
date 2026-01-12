# Fix Multi-Project Selector Memory Persistence Bug

## Problem Statement

When all projects are deselected in the multi-project selector, memories persist on the dashboard until the user explicitly clicks the "Clear" button. **Expected behavior**: When the last project is deselected, memories, stats, and tags should be cleared immediately.

## Root Cause Analysis

**Location**: `dashboard/frontend/src/stores/dashboardStore.ts`

**The Bug**: The `loadAggregateData()` function (lines 108-119) returns early when `selectedProjects.value.length === 0` **without clearing the data arrays**:

```typescript
async function loadAggregateData() {
  if (selectedProjects.value.length === 0) return  // <-- RETURNS WITHOUT CLEARING

  page.value = 0
  hasMore.value = true

  await Promise.all([
    loadAggregateMemories(),
    loadAggregateStats(),
    loadAggregateTags(),
  ])
}
```

**Why This Happens**: When `toggleProjectSelection()` is called to deselect the last project:
1. `selectedProjects` becomes an empty array
2. `loadAggregateData()` is called
3. It returns early because `selectedProjects.length === 0`
4. `memories`, `stats`, and `tags` retain their previous values
5. The UI continues showing stale data

**Correct Behavior Reference**: The `clearProjectSelection()` function (lines 101-106) correctly clears all arrays:

```typescript
function clearProjectSelection() {
  selectedProjects.value = []
  memories.value = []
  stats.value = null
  tags.value = []
}
```

## Implementation Plan

### Step 1: Clear Arrays Before Early Return

**File**: `dashboard/frontend/src/stores/dashboardStore.ts`

**Change**: Clear `memories`, `stats`, and `tags` before the early return in `loadAggregateData()`.

**Current Code** (lines 108-119):
```typescript
async function loadAggregateData() {
  if (selectedProjects.value.length === 0) return

  page.value = 0
  hasMore.value = true

  await Promise.all([
    loadAggregateMemories(),
    loadAggregateStats(),
    loadAggregateTags(),
  ])
}
```

**Fixed Code**:
```typescript
async function loadAggregateData() {
  if (selectedProjects.value.length === 0) {
    // Clear data when no projects selected (immediate feedback)
    memories.value = []
    stats.value = null
    tags.value = []
    return
  }

  page.value = 0
  hasMore.value = true

  await Promise.all([
    loadAggregateMemories(),
    loadAggregateStats(),
    loadAggregateTags(),
  ])
}
```

### Step 2: Verify Build

Run TypeScript check and Vite build:
```bash
cd dashboard/frontend
npx vue-tsc -b
npm run build
```

### Step 3: Visual Validation

Start dashboard and verify:
1. Select one or more projects
2. Deselect all projects one by one
3. When last project is deselected, memories/stats/tags should clear immediately
4. No need to click "Clear" button

## Testing Strategy

### Manual Tests

1. **Single Project Deselection**:
   - Select one project → verify memories load
   - Deselect that project → memories should clear immediately
   - Tags panel should show empty/default state
   - Stats should show 0 or placeholder

2. **Multiple Project Deselection**:
   - Select multiple projects → verify aggregated memories
   - Deselect projects one by one
   - When last project deselected → all data clears immediately

3. **Clear Button Still Works**:
   - Select projects
   - Click "Clear" button
   - Should still work as before (calls `clearProjectSelection()`)

4. **Re-selection After Clear**:
   - Deselect all projects (data clears)
   - Select a project again
   - Data should load correctly

### Console Verification

Check for any errors when deselecting last project - there should be none since we return early after clearing.

## Files to Modify

| File | Change |
|------|--------|
| `dashboard/frontend/src/stores/dashboardStore.ts` | Add array clearing before early return in `loadAggregateData()` |

## Success Criteria

- [ ] When last project is deselected, memories list clears immediately
- [ ] When last project is deselected, stats clear immediately
- [ ] When last project is deselected, tags panel clears immediately
- [ ] No console errors during deselection
- [ ] TypeScript build passes
- [ ] Vite build passes
- [ ] "Clear" button still works correctly
- [ ] Re-selecting projects after clear loads data correctly

## Estimated Time

10-15 minutes (simple 3-line fix)

## Risk Assessment

**Risk Level**: Low

- Change is additive (adding clear logic, not modifying existing)
- Mirrors existing `clearProjectSelection()` pattern
- No API calls affected
- No type changes required

## Notes

- This is a data consistency fix - UI should reflect state accurately
- The fix aligns `loadAggregateData()` behavior with `clearProjectSelection()` for empty selection case
- Consider adding a unit test for this edge case in future
