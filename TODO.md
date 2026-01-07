# Omni Cortex MCP - Implementation TODO

## Phase 1: Core Foundation ✅ COMPLETE

### Project Setup ✅
- [x] Create `pyproject.toml` with dependencies
- [x] Create `README.md` placeholder
- [x] Set up `src/omni_cortex/` package structure
- [x] Create `__init__.py` files for all modules
- [x] Test basic package can be imported

### Database Layer ✅
- [x] Create `database/schema.py` with full SQL schema
- [x] Create `database/connection.py` for SQLite connection management
- [x] Implement `database/migrations.py` for schema versioning
- [x] Create `database/__init__.py` with exports
- [x] Test: Database initializes correctly with all tables

### Configuration ✅
- [x] Create `config.py` with settings management
- [x] Support per-project config in `.omni-cortex/config.yaml`
- [x] Support global config in `~/.omni-cortex/config.yaml`
- [x] Define default values for all settings

### Utility Functions ✅
- [x] Create `utils/ids.py` - ID generation (mem_, act_, sess_, etc.)
- [x] Create `utils/timestamps.py` - ISO 8601 helpers with timezone
- [x] Create `utils/formatting.py` - Markdown/JSON formatters
- [x] Create `utils/truncation.py` - Output truncation logic

### Auto-Categorization ✅
- [x] Create `categorization/auto_type.py` - Memory type detection
- [x] Define regex patterns for all 11 types
- [x] Create `categorization/auto_tags.py` - Tag suggestion
- [x] Define patterns for languages, frameworks, concepts
- [x] Test: Types correctly detected from sample content

### Basic Models ✅
- [x] Create `models/memory.py` - Memory dataclass + CRUD
- [x] Create `models/activity.py` - Activity dataclass + CRUD
- [x] Create `models/session.py` - Session dataclass + CRUD
- [x] Create `models/agent.py` - Agent dataclass + CRUD
- [x] Create `models/relationship.py` - Relationship dataclass

### Core Memory Tools ✅
- [x] Create `tools/memories.py`
- [x] Implement `cortex_remember` tool
- [x] Implement `cortex_list_memories` tool
- [x] Implement `cortex_update_memory` tool
- [x] Implement `cortex_forget` tool
- [x] Test: Can create, list, update, delete memories

### Basic Search (Keyword Only) ✅
- [x] Create `search/keyword.py` - FTS5-based search
- [x] Implement basic `cortex_recall` (keyword mode only)
- [x] Test: Can search memories by keywords

### FastMCP Server ✅
- [x] Create `server.py` - FastMCP entry point
- [x] Register all Phase 1 tools
- [x] Test: Server starts and responds to tool calls

---

## Phase 2: Activity Logging ✅ COMPLETE

### Hook Scripts ✅
- [x] Create `hooks/pre_tool_use.py`
- [x] Create `hooks/post_tool_use.py`
- [x] Create `hooks/stop.py`
- [x] Create `hooks/subagent_stop.py`
- [x] Create hook configuration template for settings.json
- [x] Auto-initialize database if not exists (out-of-box experience)
- [x] Create `omni-cortex-setup` command for automatic configuration
- [x] Test: Hooks log to database correctly

### Activity Tools ✅
- [x] Create `tools/activities.py`
- [x] Implement `cortex_log_activity` tool
- [x] Implement `cortex_get_activities` tool
- [x] Implement `cortex_get_timeline` tool
- [x] Test: Can log and query activities

### Activity-Memory Linking ✅
- [x] Add linking logic when memories reference activities
- [x] Add linking logic when activities create memories
- [x] Display links in recall/list results
- [x] Test: Links created and displayed correctly

---

## Phase 3: Semantic Search ✅ COMPLETE

### Embeddings Infrastructure ✅
- [x] Create `embeddings/__init__.py`
- [x] Create `embeddings/local.py` - sentence-transformers integration
- [x] Implement embedding generation function
- [x] Implement vector storage (BLOB in SQLite)
- [x] Implement vector retrieval and similarity calculation
- [x] Test: Can generate and store embeddings

### API Fallback (Optional)
- [ ] Create `embeddings/api_fallback.py`
- [ ] Implement Claude/OpenAI embedding API calls
- [ ] Add configuration for API keys
- [ ] Implement fallback logic (local first, API if needed)

### Hybrid Search ✅
- [x] Create `search/semantic.py` - Vector similarity search
- [x] Create `search/hybrid.py` - Combined keyword + semantic
- [x] Update `cortex_recall` to support all search modes
- [x] Test: Semantic search finds conceptually similar content

### Ranking Algorithm ✅
- [x] Create `search/ranking.py` - Multi-factor ranking
- [x] Implement access frequency bonus
- [x] Implement recency bonus
- [x] Implement freshness status bonus
- [x] Implement importance score bonus
- [x] Test: Results ranked correctly by multiple factors

### Background Embedding Generation ✅
- [x] Generate embeddings on `cortex_remember`
- [x] Batch process existing memories without embeddings
- [x] Lazy loading for large memory stores
- [x] Test: Embeddings generated without blocking

---

## Phase 4: Session Continuity ✅ COMPLETE

### Session Management ✅
- [x] Create `tools/sessions.py`
- [x] Implement `cortex_start_session` tool
- [x] Implement `cortex_end_session` tool
- [x] Auto-detect session from environment variables
- [ ] Test: Sessions created and tracked correctly

### Session Summaries ✅
- [x] Implement auto-summary generation on session end
- [x] Track key learnings per session
- [x] Track key decisions per session
- [x] Track errors encountered per session
- [x] Track files modified per session
- [ ] Test: Summaries capture important session data

### Context Retrieval ✅
- [x] Implement `cortex_get_session_context` tool
- [x] Generate "Last time you..." context message
- [ ] Auto-provide context on first tool call (configurable)
- [ ] Test: Context accurately reflects past work

---

## Phase 5: Global Index & Polish

### Global Index Sync
- [ ] Create `database/sync.py` - Sync logic
- [x] Create global database at `~/.omni-cortex/global.db`
- [ ] Implement sync from project to global on memory create/update
- [ ] Implement cross-project search via global index
- [ ] Test: Memories searchable across projects

### Importance Decay ✅
- [x] Create `decay/importance.py`
- [x] Implement decay calculation formula
- [x] Support manual importance override
- [ ] Run decay on access (lazy update)
- [ ] Test: Importance scores decay over time

### Memory Relationships ✅
- [x] Implement `cortex_link_memories` tool
- [x] Support relationship types: related_to, supersedes, derived_from, contradicts
- [x] Display related memories in recall results
- [x] Test: Relationships created and displayed

### Export & Utilities ✅
- [x] Create `tools/utilities.py`
- [x] Implement `cortex_list_tags` tool
- [x] Implement `cortex_review_memories` tool
- [x] Implement `cortex_export` tool (markdown format)
- [x] Implement `cortex_export` tool (JSON format)
- [ ] Implement `cortex_export` tool (SQLite dump)
- [ ] Test: All export formats work correctly

### MCP Resources ✅
- [x] Create `resources/read_only.py` (in server.py)
- [x] Implement `cortex://stats` resource
- [x] Implement `cortex://types` resource
- [x] Implement `cortex://tags` resource
- [x] Implement `cortex://sessions/recent` resource
- [x] Implement `cortex://config` resource
- [x] Test: Resources return expected data

---

## Phase 6: Testing & Documentation

### Unit Tests ✅
- [x] Create `tests/conftest.py` with fixtures
- [x] Create `tests/test_database.py`
- [x] Create `tests/test_memories.py`
- [x] Create `tests/test_activities.py`
- [x] Create `tests/test_search.py`
- [ ] Create `tests/test_embeddings.py`
- [x] Create `tests/test_sessions.py`
- [ ] Achieve >80% code coverage

### Integration Tests
- [ ] Test full workflow: start session → remember → recall → end session
- [ ] Test hook integration with mock Claude Code events
- [ ] Test global index sync across multiple project directories
- [ ] Test semantic search accuracy

### Documentation
- [x] Write comprehensive README.md
- [ ] Document all 15 tools with examples
- [ ] Document configuration options
- [ ] Document hook setup instructions
- [ ] Create troubleshooting guide

### Final Polish
- [ ] Code review for security issues
- [ ] Performance profiling for large memory stores
- [ ] Error handling and graceful degradation
- [ ] Logging for debugging

---

## Optional Enhancements (Post-MVP)

- [ ] Web dashboard for memory visualization
- [ ] Memory import from Ken You Remember
- [ ] Vector database backend (Chroma, Pinecone)
- [ ] Multi-user support with authentication
- [ ] Memory sharing between users/projects
- [ ] Scheduled cleanup of old activities
- [ ] Webhooks for external integrations
