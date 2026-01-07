# Omni Cortex MCP - Session Handoff

**Date:** January 7, 2026
**Project:** D:\Projects\omni-cortex
**GitHub:** https://github.com/AllCytes/Omni-Cortex
**PyPI:** https://pypi.org/project/omni-cortex/

---

## Current Status: v1.0.2 VERIFIED WORKING ✅

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
- [ ] Global index sync across projects
- [ ] SQLite dump export format

### Phase 6: Testing & Documentation
- [ ] `test_embeddings.py`
- [ ] Integration tests
- [ ] Document all 15 tools with examples
- [ ] Document configuration options
- [ ] Document hook setup instructions
- [ ] Troubleshooting guide
- [ ] Code review for security
- [ ] Performance profiling

## Recently Completed (Jan 7, 2026 session)

### Bug Fixes (resolves MCP "stuck" issues)
- [x] Fixed Session bug in `cortex_start_session` - was passing Session objects to formatting function that expected dicts (caused `'Session' object has no attribute 'get'` error)
- [x] Fixed FK constraint in `create_activity` - agent upsert must happen BEFORE activity insert (caused `FOREIGN KEY constraint failed` error)
- [x] Fixed embedding model hang in `cortex_remember` - added 30s timeout to model loading, checks `embedding_enabled` config before attempting

### Workaround: Disable Embeddings
If `cortex_remember` still hangs, disable embeddings by creating `.omni-cortex/config.yaml`:
```yaml
embedding_enabled: false
```

### New Features
- [x] Added `cortex://tags` MCP resource
- [x] Added `cortex://sessions/recent` MCP resource
- [x] Added related memories display in recall results

### Tests
- [x] Created `test_activities.py` (8 tests)
- [x] Created `test_search.py` (11 tests)
- [x] Created `test_sessions.py` (13 tests)
- Total: **41 tests passing**

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

Status: v1.0.2 VERIFIED - 41 tests passing, all 15 tools working.
Embeddings currently DISABLED via .omni-cortex/config.yaml (prevents hang issue).

Remaining tasks:
1. Global index sync across projects
2. SQLite dump export format
3. Integration tests
4. Documentation (all 15 tools with examples)
5. Code review for security
6. Performance profiling

To re-enable semantic search: set embedding_enabled: true in .omni-cortex/config.yaml
```

---
