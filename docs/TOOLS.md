# Omni Cortex MCP - Tool Reference

Complete documentation for all 15 Omni Cortex tools.

---

## Memory Tools

### cortex_remember

Store important information with auto-categorization and tagging.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| content | string | Yes | The information to remember (min 1 char) |
| context | string | No | Additional context about the memory |
| tags | string[] | No | Tags for categorization |
| type | string | No | Memory type (auto-detected if not specified) |
| importance | int | No | Importance score 1-100 |
| related_memory_ids | string[] | No | IDs of related memories |

**Example:**

```
cortex_remember({
  content: "SQLite FTS5 requires special escaping for quotes and parentheses",
  context: "Found while debugging search failures",
  tags: ["sqlite", "fts5", "debugging"],
  importance: 75
})
```

**Response:**
```
Remembered: mem_1767828231983_5c83106d
Type: troubleshooting
Tags: sqlite, fts5, debugging, database
Importance: 75/100
Search: no embedding
```

---

### cortex_recall

Search memories by keyword or semantic similarity.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Search query (min 1 char) |
| search_mode | string | No | `keyword`, `semantic`, or `hybrid` (default: keyword) |
| type_filter | string | No | Filter by memory type |
| tags_filter | string[] | No | Filter by tags |
| status_filter | string | No | Filter by status |
| min_importance | int | No | Minimum importance (0-100) |
| include_archived | bool | No | Include archived memories (default: false) |
| limit | int | No | Maximum results 1-50 (default: 10) |

**Example:**

```
cortex_recall({
  query: "FTS5 escaping",
  search_mode: "keyword",
  limit: 5
})
```

**Response:**
```markdown
# Memories (2)

## [troubleshooting] mem_1767828231983_5c83106d

SQLite FTS5 requires special escaping for quotes and parentheses

---
**Tags:** sqlite, fts5, debugging, database
**Context:** Found while debugging search failures
**Created:** 5 minutes ago
**Importance:** 75/100
```

---

### cortex_list_memories

List memories with filtering and pagination.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| type_filter | string | No | Filter by memory type |
| tags_filter | string[] | No | Filter by tags |
| status_filter | string | No | Filter by status |
| sort_by | string | No | `last_accessed`, `created_at`, `importance_score` |
| sort_order | string | No | `asc` or `desc` (default: desc) |
| limit | int | No | Maximum results 1-100 (default: 20) |
| offset | int | No | Pagination offset (default: 0) |

**Example:**

```
cortex_list_memories({
  type_filter: "solution",
  sort_by: "importance_score",
  limit: 10
})
```

---

### cortex_update_memory

Update an existing memory.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Memory ID to update |
| content | string | No | New content |
| context | string | No | New context |
| tags | string[] | No | Replace all tags |
| add_tags | string[] | No | Tags to add |
| remove_tags | string[] | No | Tags to remove |
| status | string | No | New status (`fresh`, `needs_review`, `outdated`, `archived`) |
| importance | int | No | New importance (1-100) |

**Example:**

```
cortex_update_memory({
  id: "mem_1767828231983_5c83106d",
  add_tags: ["verified"],
  importance: 90
})
```

---

### cortex_forget

Permanently delete a memory.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Memory ID to delete |
| confirm | bool | Yes | Must be `true` to confirm deletion |

**Example:**

```
cortex_forget({
  id: "mem_1767828231983_5c83106d",
  confirm: true
})
```

**Response:**
```
Memory deleted: mem_1767828231983_5c83106d
```

---

### cortex_link_memories

Create a relationship between two memories.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| source_id | string | Yes | Source memory ID |
| target_id | string | Yes | Target memory ID |
| relationship_type | string | Yes | Type: `related_to`, `supersedes`, `derived_from`, `contradicts` |
| strength | float | No | Relationship strength 0-1 (default: 1.0) |

**Relationship Types:**

- `related_to` - General association
- `supersedes` - New memory replaces old
- `derived_from` - New memory based on old
- `contradicts` - Memories conflict

**Example:**

```
cortex_link_memories({
  source_id: "mem_abc123",
  target_id: "mem_xyz789",
  relationship_type: "supersedes"
})
```

**Response:**
```
Linked: mem_abc123 --[supersedes]--> mem_xyz789
```

---

## Activity Tools

### cortex_log_activity

Manually log a tool call, decision, or observation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| event_type | string | Yes | `pre_tool_use`, `post_tool_use`, `decision`, `observation` |
| tool_name | string | No | Tool name if applicable |
| tool_input | string | No | Tool input (JSON string) |
| tool_output | string | No | Tool output (JSON string) |
| duration_ms | int | No | Duration in milliseconds |
| success | bool | No | Whether operation succeeded (default: true) |
| error_message | string | No | Error message if failed |
| file_path | string | No | Relevant file path |
| agent_id | string | No | Agent ID |

**Example:**

```
cortex_log_activity({
  event_type: "decision",
  tool_name: "architecture",
  tool_input: "{\"decision\": \"Use SQLite over PostgreSQL\"}",
  success: true
})
```

**Note:** Most activity logging is done automatically via hooks. This tool is for manual logging of decisions and observations.

---

### cortex_get_activities

Query the activity log with filters.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | No | Filter by session ID |
| agent_id | string | No | Filter by agent ID |
| event_type | string | No | Filter by event type |
| tool_name | string | No | Filter by tool name |
| since | string | No | Start time (ISO 8601) |
| until | string | No | End time (ISO 8601) |
| limit | int | No | Maximum results 1-200 (default: 50) |
| offset | int | No | Pagination offset (default: 0) |

**Example:**

```
cortex_get_activities({
  tool_name: "Edit",
  since: "2026-01-07T00:00:00Z",
  limit: 20
})
```

---

### cortex_get_timeline

Get a chronological timeline of activities and memories.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| hours | int | No | Hours to look back 1-168 (default: 24) |
| include_activities | bool | No | Include activities (default: true) |
| include_memories | bool | No | Include memories (default: true) |
| group_by | string | No | Group by: `hour`, `day`, or `session` |

**Example:**

```
cortex_get_timeline({
  hours: 8,
  group_by: "hour"
})
```

---

## Session Tools

### cortex_start_session

Start a new session and optionally get context from previous sessions.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | No | Custom session ID (auto-generated if not provided) |
| project_path | string | No | Project path (uses current directory if not provided) |
| provide_context | bool | No | Return context from previous sessions (default: true) |
| context_depth | int | No | Number of past sessions to summarize 1-10 (default: 3) |

**Example:**

```
cortex_start_session({
  provide_context: true,
  context_depth: 5
})
```

**Response:**
```markdown
# Session Started: sess_1767828223112_9de1a644
Project: D:\Projects\my-app
Started: 2026-01-07T23:23:43.112702+00:00

## Previous Sessions

### Session 1 (2 hours ago)
- Fixed authentication bug in login.py
- Added rate limiting to API endpoints
- Key decision: Use JWT instead of sessions
```

---

### cortex_end_session

End a session and generate summary statistics.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | Session ID to end |
| summary | string | No | Manual summary (auto-generated if not provided) |
| key_learnings | string[] | No | Key learnings from the session |

**Example:**

```
cortex_end_session({
  session_id: "sess_1767828223112_9de1a644",
  key_learnings: [
    "SQLite FTS5 needs special character escaping",
    "Subprocess timeout prevents embedding hangs"
  ]
})
```

---

### cortex_get_session_context

Get context from previous sessions for continuity.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| project_path | string | No | Filter by project path |
| session_count | int | No | Number of past sessions 1-20 (default: 5) |
| include_decisions | bool | No | Include key decisions (default: true) |
| include_errors | bool | No | Include errors encountered (default: true) |
| include_learnings | bool | No | Include key learnings (default: true) |

**Example:**

```
cortex_get_session_context({
  session_count: 3,
  include_decisions: true
})
```

**Response:**
```markdown
# Session Context

## Last Session (2 hours ago)
**Focus:** Bug fixes and API improvements
**Files Modified:** login.py, api.py, tests/test_auth.py
**Key Decisions:**
- Use JWT tokens for stateless auth
- Rate limit to 100 req/min per user
```

---

## Utility Tools

### cortex_list_tags

List all tags used in memories with usage counts.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| min_count | int | No | Minimum usage count (default: 1) |
| limit | int | No | Maximum tags to return 1-200 (default: 50) |

**Example:**

```
cortex_list_tags({
  min_count: 3
})
```

**Response:**
```markdown
# Tags (15)

| Tag | Count |
|-----|-------|
| python | 42 |
| debugging | 28 |
| api | 15 |
...
```

---

### cortex_review_memories

Review and update memory freshness status.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| action | string | Yes | `list`, `mark_fresh`, `mark_outdated`, `mark_archived` |
| days_threshold | int | No | Review memories older than this (default: 30) |
| memory_ids | string[] | No | Memory IDs to update (for mark actions) |
| limit | int | No | Maximum memories to list 1-100 (default: 20) |

**Example - List stale memories:**

```
cortex_review_memories({
  action: "list",
  days_threshold: 14
})
```

**Example - Mark memories as fresh:**

```
cortex_review_memories({
  action: "mark_fresh",
  memory_ids: ["mem_abc123", "mem_xyz789"]
})
```

---

### cortex_global_search

Search memories across all projects via the global index.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Search query (min 1 char) |
| type_filter | string | No | Filter by memory type |
| tags_filter | string[] | No | Filter by tags |
| project_filter | string | No | Filter by project path (substring match) |
| limit | int | No | Maximum results 1-100 (default: 20) |

**Example:**

```
cortex_global_search({
  query: "authentication pattern",
  project_filter: "my-api",
  limit: 10
})
```

**Response:**
```markdown
# Global Search Results (3)

## Project: D:\Projects\my-api

### [solution] mem_abc123
Implemented JWT authentication with refresh tokens...
**Tags:** auth, jwt, security
**Score:** 8.50
```

---

### cortex_global_stats

Get statistics from the global memory index.

**Parameters:** None

**Example:**

```
cortex_global_stats()
```

**Response:**
```markdown
# Global Index Statistics

**Total Memories:** 142

## By Project
- D:\Projects\my-api: 45
- D:\Projects\my-frontend: 38
- D:\Projects\shared-lib: 59

## By Type
- solution: 42
- troubleshooting: 35
- concept: 28
```

---

### cortex_sync_to_global

Manually sync project memories to the global index.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| full_sync | bool | No | Set to true to sync all project memories (default: false) |

**Example:**

```
cortex_sync_to_global({
  full_sync: true
})
```

**Response:**
```
Synced 42 memories to global index.
```

**Note:** Memories are automatically synced on create/update when `global_sync_enabled: true` in config.

---

### cortex_export

Export memories and activities to various formats.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| format | string | No | Export format: `markdown` or `json` (default: markdown) |
| include_memories | bool | No | Include memories (default: true) |
| include_activities | bool | No | Include activities (default: true) |
| since | string | No | Export data since this date (ISO 8601) |
| output_path | string | No | File path to save export |

**Example:**

```
cortex_export({
  format: "markdown",
  include_memories: true,
  include_activities: false
})
```

---

## Memory Types Reference

| Type | Description | Auto-detected Keywords |
|------|-------------|------------------------|
| `general` | General notes | (default) |
| `warning` | Cautions, things to avoid | "warning", "caution", "avoid", "never" |
| `tip` | Tips, tricks, best practices | "tip", "trick", "best practice" |
| `config` | Configuration and settings | "config", "setting", "environment" |
| `troubleshooting` | Debugging and problem-solving | "debug", "troubleshoot", "investigate" |
| `code` | Code snippets and algorithms | "function", "class", "algorithm" |
| `error` | Error messages and failures | "error", "exception", "failed" |
| `solution` | Solutions to problems | "solution", "fix", "resolved" |
| `command` | CLI commands | "run", "execute", "command" |
| `concept` | Definitions and explanations | "concept", "definition", "what is" |
| `decision` | Architectural decisions | "decided", "chose", "architecture" |

---

## Memory Status Reference

| Status | Description |
|--------|-------------|
| `fresh` | Recently created or verified |
| `needs_review` | May be outdated, needs verification |
| `outdated` | Confirmed outdated but kept for reference |
| `archived` | No longer relevant, excluded from search by default |

---

## Search Modes

| Mode | Description | Best For |
|------|-------------|----------|
| `keyword` | SQLite FTS5 full-text search with BM25 ranking | Exact matches, specific terms |
| `semantic` | AI-powered embedding similarity (requires sentence-transformers) | Conceptual similarity, natural language |
| `hybrid` | Combines keyword + semantic scores | Best overall results |

**Note:** Semantic search requires `pip install omni-cortex[semantic]` and may be slow on first use while downloading the model (~90MB).
