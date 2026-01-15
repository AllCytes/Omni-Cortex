# Omni Cortex MCP - Session Handoff

**Date:** January 15, 2026
**Project:** D:\Projects\omni-cortex
**GitHub:** https://github.com/AllCytes/Omni-Cortex
**PyPI:** https://pypi.org/project/omni-cortex/

---

## Current Status: v1.12.1 VERIFIED WORKING ✅ (Published to PyPI)

The MCP is **live on PyPI and GitHub**. Users can install with:
```bash
pip install omni-cortex
omni-cortex-setup
```

With semantic search:
```bash
pip install omni-cortex[semantic]
omni-cortex-setup
```

---

## Completed Phases

### Phase 1: Core Foundation ✅
- Database layer (SQLite + FTS5)
- Configuration system
- Utility functions
- Auto-categorization
- Basic models
- Core memory tools (6 tools)
- FastMCP server

### Phase 2: Activity Logging ✅
- Hook scripts (pre_tool_use, post_tool_use, stop, subagent_stop)
- Activity tools (3 tools)
- Auto-initialize database in hooks (out-of-box experience)
- `omni-cortex-setup` command for automatic configuration
- **v1.0.1**: Fixed hooks format for Claude Code update (matcher + hooks array)

### Phase 3: Semantic Search ✅
- `embeddings/local.py` (sentence-transformers, all-MiniLM-L6-v2, 384 dims)
- `search/semantic.py` (vector similarity with cosine similarity)
- `search/hybrid.py` (keyword + semantic combined)
- `cortex_recall` supports all search modes (keyword, semantic, hybrid)
- `cortex_remember` generates embeddings automatically

### Phase 4: Session Continuity ✅
- Session management tools (3 tools)
- Session summaries
- Context retrieval

---

## All 15 Tools Working

| Tool | Status |
|------|--------|
| `cortex_remember` | ✅ + auto-embeddings |
| `cortex_recall` | ✅ keyword/semantic/hybrid |
| `cortex_list_memories` | ✅ |
| `cortex_update_memory` | ✅ + re-generates embeddings |
| `cortex_forget` | ✅ |
| `cortex_link_memories` | ✅ |
| `cortex_log_activity` | ✅ |
| `cortex_get_activities` | ✅ |
| `cortex_get_timeline` | ✅ |
| `cortex_start_session` | ✅ |
| `cortex_end_session` | ✅ |
| `cortex_get_session_context` | ✅ |
| `cortex_list_tags` | ✅ |
| `cortex_review_memories` | ✅ |
| `cortex_export` | ✅ |

---

## Remaining Work (from TODO.md)

### Phase 3 - Optional
- [ ] API Fallback (`embeddings/api_fallback.py` for Claude/OpenAI)

### Phase 5: Global Index & Polish
- [x] Global index sync across projects (database/sync.py + 3 new tools)
- [x] SQLite dump export format (added to cortex_export)

### Phase 6: Testing & Documentation
- [x] `test_embeddings.py` (7 tests including security validation)
- [x] Integration tests (9 end-to-end workflow tests)
- [x] Document all 15 tools with examples (docs/TOOLS.md)
- [x] Document configuration options (docs/CONFIGURATION.md)
- [x] Document hook setup instructions (in CONFIGURATION.md)
- [x] Troubleshooting guide (in CONFIGURATION.md)
- [x] Code review for security
- [x] Performance profiling (test_performance.py with 6 benchmarks)

## Recently Completed (Jan 12, 2026 session - v1.11.2)

### Dashboard Global Index Duplication Warning (v1.11.2)
- [x] Added duplication warning banner when Global Index + individual projects are selected
- [x] Shows estimated overlap count with amber/yellow styling
- [x] Provides quick action buttons: "View Global Only" and "View Projects Only"
- [x] Dismissible with X button, reappears on selection changes
- [x] New component: `DuplicationWarningBanner.vue`
- [x] Added store actions: `selectGlobalOnly()` and `selectProjectsOnly()`
- [x] Smooth Vue transitions for banner appearance/disappearance

### Dashboard Multi-Project Selector Fixes (v1.11.0)

### Dashboard Multi-Project Selector Fixes
- [x] Fixed click-to-toggle behavior - dropdown now properly opens/closes on trigger click
- [x] Fixed memory count display reactivity - shows correct total across selected projects
- [x] Improved click-outside detection to exclude trigger button
- [x] Replaced array mutations with immutable operations for better Vue 3 reactivity

### ADW Enhancements
- [x] Added `cleanup_dashboard_ports()` utility to prevent 'address already in use' errors
- [x] Improved error handling across apply_learnings, retrospective, review, security, security_fix, and validate ADWs
- [x] Enhanced validation and subprocess management in ADW utilities

### Bug Fixes (Jan 7, 2026 session)
- [x] Fixed Session bug in `cortex_start_session` - was passing Session objects to formatting function that expected dicts
- [x] Fixed FK constraint in `create_activity` - agent upsert must happen BEFORE activity insert
- [x] **REBUILT** semantic search from scratch - uses subprocess with 60s timeout (can actually be killed)

### Semantic Search Status
**Embeddings DISABLED by default** - The sentence-transformers model loading is unreliable on Windows (hangs during first-time model download). Until a better solution is found:
- Default: `embedding_enabled: false` in config.py
- Keyword search works perfectly
- To enable: set `embedding_enabled: true` in `.omni-cortex/config.yaml` (may hang on first use)

### New Features
- [x] Added `cortex://tags` MCP resource
- [x] Added `cortex://sessions/recent` MCP resource
- [x] Added related memories display in recall results

### Tests
- [x] Created `test_activities.py` (8 tests)
- [x] Created `test_search.py` (11 tests)
- [x] Created `test_sessions.py` (13 tests)
- [x] Created `test_embeddings.py` (7 tests) - includes model name validation security tests
- Total: **66 tests passing**

### Security Review (completed Jan 7, 2026)
- [x] All SQL queries use parameterized statements (no SQL injection)
- [x] FTS5 queries properly escape special characters
- [x] Input validation via Pydantic models with constraints
- [x] YAML loading uses `safe_load()` (no code execution)
- [x] **Fixed: Model name validation** - prevents code injection via config file
  - Added `_validate_model_name()` function to `embeddings/local.py`
  - Only allows alphanumeric, hyphens, underscores, forward slashes
  - Blocks quotes, semicolons, backticks, and shell metacharacters

### Important: Restart Required
After these fixes, you must **restart Claude Code** to pick up the changes. The MCP server runs as a subprocess and won't see code changes until restarted.

---

## Key Files

| File | Purpose |
|------|---------|
| `src/omni_cortex/server.py` | FastMCP entry point |
| `src/omni_cortex/tools/memories.py` | Memory tools |
| `src/omni_cortex/tools/activities.py` | Activity logging tools |
| `src/omni_cortex/tools/sessions.py` | Session management tools |
| `src/omni_cortex/embeddings/local.py` | Sentence-transformers integration |
| `src/omni_cortex/search/hybrid.py` | Unified search |
| `src/omni_cortex/setup.py` | Auto-configuration script |
| `hooks/*.py` | Claude Code activity logging hooks |

---

## Continuation Prompt

Copy this to start a new session:

```
d:\Projects\omni-cortex\HANDOFF.md

Continue building Omni Cortex MCP at D:\Projects\omni-cortex.

Status: v1.11.2 - 66 tests passing, 18 tools, all phases complete.
Embeddings DISABLED by default (keyword search only) - model loading hangs on Windows.

Recent updates (v1.11.2):
- Dashboard duplication warning banner for Global Index overlap
- Improved UX for multi-project memory viewing
- All changes released to PyPI and GitHub

All planned features complete. Optional future work:
- API fallback for embeddings (Claude/OpenAI)
- Performance optimizations based on profiling results
```

---
