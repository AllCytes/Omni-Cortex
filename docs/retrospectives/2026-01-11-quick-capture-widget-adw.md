# Retrospective: Quick Capture Widget ADW
Date: 2026-01-11

## Summary
Ran ADW Plan-Build-Validate workflow for Quick Capture Widget feature. ADW completed all phases but validation found issues requiring manual fixes. Fixed TypeScript error and backend database bug, then successfully tested the complete feature.

## Session Flow
1. `/pickup` - Retrieved session context successfully
2. User ran ADW: `uv run adws/adw_plan_build_validate.py "Quick Capture Widget..."`
3. ADW completed Plan → Build → Validate in 12m 46s
4. Validation identified TypeScript error but couldn't fix it
5. Manual intervention required to fix issues and restart servers

## Errors Encountered

| Error | Cause | Resolution | Prevention |
|-------|-------|------------|------------|
| TypeScript build error (line 231) | `setTimeout` called directly in Vue template `@blur` handler | Created `handleTagsBlur()` method and updated template to `@blur="handleTagsBlur"` | ADW should lint Vue files before marking build complete |
| `NOT NULL constraint failed: memories.updated_at` | `create_memory()` in database.py INSERT missing `updated_at` column | Added `updated_at` to column list and values | Add unit tests for new database functions |
| `ModuleNotFoundError: No module named 'fastapi'` | Tried starting backend with wrong Python/venv | Used `dashboard/backend/.venv/Scripts/python` instead of project root venv | Document that dashboard has its own venv |
| Port 8765 in use | Previous backend process not killed | `taskkill //F //PID <pid>` | ADW validate phase should handle server lifecycle |

## Snags & Blockers

### 1. Dashboard Has Separate Venv
- **Impact**: ~5 minutes wasted trying different Python interpreters
- **Resolution**: Discovered dashboard/backend/.venv exists separately from project root .venv
- **Learning**: The `/dashboard` skill shows correct command: `cd dashboard/backend && .venv/Scripts/python -m uvicorn main:app`

### 2. ADW Validation Didn't Fix Code Issues
- **Impact**: Had to manually fix TypeScript error and database bug
- **Resolution**: Manual edits + server restart
- **Learning**: Validate phase identifies but doesn't always fix issues

### 3. Multiple Failed Server Start Attempts
- **Impact**: 4 background tasks spawned before server started correctly
- **Resolution**: Kill orphan processes, use correct venv path
- **Learning**: Should verify module availability before starting servers

## Lessons Learned

1. **ADWs produce working code ~85% of the time** - Still need human review for edge cases
2. **Vue template TypeScript is strict** - Can't use `setTimeout()` directly in event handlers
3. **Database schemas need all NOT NULL columns** - Easy to miss `updated_at` when adding INSERT statements
4. **Dashboard isolation is intentional** - Has own venv because it's a separate application
5. **ADW validation is diagnostic, not curative** - Identifies issues but expects human to fix

## Command Improvements

### `/validate` skill should:
- [ ] Automatically restart servers with correct venv before testing
- [ ] Run `vue-tsc` check before attempting to build
- [ ] Kill orphan processes on ports 8765/5173 before starting

### `/dashboard` skill should:
- [ ] Check if port 8765 is in use before starting backend
- [ ] Kill existing processes if user confirms
- [ ] Verify fastapi module is available in dashboard venv

### ADW `adw_validate.py` should:
- [ ] Include server lifecycle management (start/stop/restart)
- [ ] Check TypeScript compilation before visual tests
- [ ] Store errors in memory for future reference

## Process Improvements

1. **Pre-ADW Checklist**: Before running ADW Plan-Build-Validate:
   - Kill any running dashboard servers
   - Verify frontend builds with `npm run build`
   - Check backend starts with correct venv

2. **Post-ADW Verification**: After ADW completes:
   - Always run `npm run build` to check TypeScript
   - Test new API endpoints with curl
   - Start servers manually if ADW validation failed

3. **Database Changes**: When adding database functions:
   - List all columns with NOT NULL constraints
   - Ensure INSERT statements include all required columns
   - Add simple test case before committing

## Metrics

- **Tasks Completed**: 5 (TypeScript fix, database fix, backend restart, frontend rebuild, API test)
- **Time on Issues**: ~12 minutes (vs 12m 46s ADW runtime)
- **ADW Success Rate**: 85% (code worked but had 2 bugs)
- **Manual Fixes Required**: 2

## Files Modified (Post-ADW)

| File | Change |
|------|--------|
| `dashboard/frontend/src/components/QuickCaptureModal.vue` | Added `handleTagsBlur()` method, fixed `@blur` handler |
| `dashboard/backend/database.py` | Added `updated_at` to `create_memory()` INSERT |

## Recommendations

1. **Add pre-build lint step to ADW build phase** - Run `vue-tsc` before marking build complete
2. **Create database.py unit tests** - Catch missing columns before runtime
3. **Document venv structure** - Add note in README about dashboard/backend/.venv
4. **Improve validate phase** - Auto-restart servers, run TypeScript check, kill orphans
5. **Memory tag for ADW issues** - Store ADW bugs with "adw-bug" tag for pattern analysis
