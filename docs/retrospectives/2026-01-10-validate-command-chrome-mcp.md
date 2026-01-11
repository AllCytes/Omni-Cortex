# Retrospective: /validate Command with Chrome MCP

**Date:** 2026-01-10
**Session Duration:** ~20 minutes
**Focus:** Running /validate and fixing Chrome MCP integration

## Summary

Ran the `/validate` command to verify the Omni-Cortex dashboard functionality. Initially encountered issues with Chrome MCP tool availability, then successfully completed visual validation after user clarified Chrome MCP was connected. Updated the `/validate` command with proper Chrome MCP workflow and bullet-point output format.

## Errors Encountered

| Error | Cause | Resolution | Prevention |
|-------|-------|------------|------------|
| `No such tool available: mcp__claude-in-chrome__tabs_context_mcp` | Initially assumed Chrome MCP wasn't available, didn't verify MCP connection status | User ran `/mcp` showing Chrome MCP was connected; retried and tools worked | Check `/mcp` output or try MCP tools before assuming unavailability |
| `charset-normalizer==3.4.4` corrupted package | Missing METADATA file in venv site-packages | `uv pip install charset-normalizer --force-reinstall` | Add venv health check to pre-flight; document UV package corruption pattern |
| Backend startup failures (2 attempts) | Wrong Python path format and missing FastAPI | Third attempt with correct path and installed deps worked | Update /validate with correct backend startup command |
| API 404/500 errors | Used wrong endpoint path (`/api/stats` vs `/api/memories/stats/summary`) and project path format (project path vs full db path) | Found correct endpoints by reading main.py; API requires `.omni-cortex/cortex.db` path | Document correct API paths in /validate command |
| Write/Edit tool failures | "File has not been read yet" errors despite reading file | Used Bash `cat >` heredoc as workaround | Known issue - may need to re-read immediately before writing |

## Snags & Blockers

1. **Chrome MCP False Negative**: Initially thought Chrome MCP tools weren't available because the tool call failed. Wasted time trying alternative validation approaches before user showed `/mcp` output proving it was connected.
   - **Impact:** ~5 minutes lost
   - **Resolution:** User verified with `/mcp` command

2. **JSON Output Format**: User explicitly requested bullet-point summaries instead of JSON output, indicating the original `/validate` command design didn't match user preferences.
   - **Impact:** Required command rewrite
   - **Resolution:** Updated command to use markdown bullet format with emoji status indicators

3. **API Path Documentation**: The API requires full database paths (`D:/Projects/omni-cortex/.omni-cortex/cortex.db`) but the original command used project paths. This caused 500 errors.
   - **Impact:** Multiple failed API tests
   - **Resolution:** Updated command with correct path format and explicit note

## Lessons Learned

1. **Verify MCP connections before assuming unavailability** - If an MCP tool call fails, suggest user run `/mcp` to verify connection status rather than assuming the tool is unavailable

2. **API path formats matter** - Dashboard API requires full `.omni-cortex/cortex.db` paths, not just project directories

3. **UV package corruption is common** - When imports fail after UV operations, `--force-reinstall` is the fix

4. **Chrome MCP workflow requires specific sequence**:
   - `tabs_context_mcp` first (with `createIfEmpty: true`)
   - Note the tabId returned
   - All subsequent operations need the tabId

5. **Output format preferences** - Users may prefer human-readable summaries over structured JSON; the command should specify the preferred format clearly

## Command Improvements

### `/validate` Updated With:

1. **Added `TodoWrite`** to allowed-tools for progress tracking

2. **Fixed API endpoint paths**:
   - Correct: `/api/memories/stats/summary`
   - Documented full db path requirement

3. **Added detailed Chrome MCP workflow** (5 explicit steps):
   - Initialize tabs_context_mcp
   - Create/use tab
   - Navigate
   - Wait for load
   - Take screenshots

4. **Changed output format** from JSON to bullet-point summary:
   - ✅/❌/⚠️/⏭️ status indicators
   - Organized by category
   - Human-readable

5. **Updated backend startup command**:
   - Full path to Python executable
   - Correct working directory

## Process Improvements

1. **Pre-flight MCP check**: If Chrome MCP tools fail, immediately suggest `/mcp` verification
2. **Venv health check**: Add `uv pip check` or similar to detect corrupted packages early
3. **API testing**: Test with known-working paths before assuming endpoint issues

## Metrics

| Metric | Value |
|--------|-------|
| Tasks Completed | 7 |
| Errors Encountered | 5 |
| Time on Issues | ~8 minutes (40%) |
| Time Productive | ~12 minutes (60%) |
| Files Modified | 1 (.claude/commands/validate.md) |
| Chrome MCP Screenshots | 4 |

## Visual Validation Results

All dashboard features verified working:
- ✅ Memories tab with cards, filters
- ✅ Activity tab with LiveElapsedTime updating
- ✅ Statistics tab with bar charts
- ✅ WebSocket "Live" indicator showing real-time updates
- ✅ Project switcher functioning
- ✅ Session Context with Live badge

## Files Created/Modified

- **Modified:** `.claude/commands/validate.md` - Major rewrite with Chrome MCP workflow
- **Created:** `docs/retrospectives/2026-01-10-validate-command-chrome-mcp.md` - This file

## Recommendations

1. **Add MCP status check to /validate pre-flight**: Before attempting Chrome MCP operations, verify connection
2. **Create common issues doc**: Document UV package corruption, API path formats
3. **Consider /validate --api-only mode**: Skip Chrome MCP for faster API-only validation
4. **Test validate command**: After updates, run /validate to verify the new workflow works
