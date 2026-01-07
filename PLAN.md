# Omni Cortex MCP - Implementation Plan

## Executive Summary

**Omni Cortex MCP** is a universal memory system for Claude Code that combines:
- **Ken You Remember MCP**: Smart storage, auto-categorization, multi-factor ranking, freshness lifecycle
- **IndyDevDan's Philosophy**: Hook-based logging, timestamps everywhere, session/agent attribution
- **Unique Innovations**: Semantic search, memory decay, session continuity, multi-agent tracking

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OMNI CORTEX MCP                          │
├─────────────────────────────────────────────────────────────┤
│  LAYER 1: ACTIVITY LOG                                      │
│  - Every tool call, agent action, decision                  │
│  - ISO 8601 timestamps with timezone                        │
│  - Session ID + Agent ID attribution                        │
│  - Project/directory context                                │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: KNOWLEDGE STORE                                   │
│  - Distilled insights, solutions, learnings                 │
│  - Auto-categorization (11 types)                           │
│  - Multi-factor ranking + AI semantic search                │
│  - Freshness lifecycle + importance scoring                 │
│  - Links to activities and other memories                   │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: GLOBAL INDEX                                      │
│  - Full sync of all project memories                        │
│  - Cross-project search                                     │
│  - Session continuity data                                  │
└─────────────────────────────────────────────────────────────┘
```

### Storage Strategy
- **Per-project**: `.omni-cortex/cortex.db` (SQLite)
- **Global**: `~/.omni-cortex/global.db` (SQLite with full sync)

---

## Database Schema

```sql
-- ============================================
-- OMNI CORTEX MCP DATABASE SCHEMA v1.0
-- ============================================

-- Sessions Table
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,                          -- sess_{timestamp}_{random}
    project_path TEXT NOT NULL,
    started_at TEXT NOT NULL,                     -- ISO 8601
    ended_at TEXT,
    summary TEXT,
    tags TEXT,                                    -- JSON array
    metadata TEXT                                 -- JSON object
);

-- Agents Table
CREATE TABLE agents (
    id TEXT PRIMARY KEY,                          -- Agent ID from Claude Code
    name TEXT,
    type TEXT NOT NULL DEFAULT 'main',            -- main, subagent, tool
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    total_activities INTEGER DEFAULT 0,
    metadata TEXT
);

-- Activities Table (Layer 1)
CREATE TABLE activities (
    id TEXT PRIMARY KEY,                          -- act_{timestamp}_{random}
    session_id TEXT NOT NULL,
    agent_id TEXT,
    timestamp TEXT NOT NULL,                      -- ISO 8601 with timezone
    event_type TEXT NOT NULL,                     -- pre_tool_use, post_tool_use, etc.
    tool_name TEXT,
    tool_input TEXT,                              -- JSON (truncated to 10KB)
    tool_output TEXT,                             -- JSON (truncated to 10KB)
    duration_ms INTEGER,
    success INTEGER DEFAULT 1,
    error_message TEXT,
    project_path TEXT,
    file_path TEXT,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Memories Table (Layer 2)
CREATE TABLE memories (
    id TEXT PRIMARY KEY,                          -- mem_{timestamp}_{random}
    content TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'general',
    tags TEXT,                                    -- JSON array
    context TEXT,

    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_accessed TEXT NOT NULL,
    last_verified TEXT,

    -- Usage
    access_count INTEGER DEFAULT 0,

    -- Importance/Decay
    importance_score REAL DEFAULT 50.0,           -- 0-100
    manual_importance INTEGER,                    -- User override

    -- Freshness
    status TEXT DEFAULT 'fresh',                  -- fresh, needs_review, outdated, archived

    -- Attribution
    source_session_id TEXT,
    source_agent_id TEXT,
    source_activity_id TEXT,

    -- Project
    project_path TEXT,
    file_context TEXT,                            -- JSON array

    -- Embedding
    has_embedding INTEGER DEFAULT 0,

    metadata TEXT,

    FOREIGN KEY (source_session_id) REFERENCES sessions(id),
    FOREIGN KEY (source_agent_id) REFERENCES agents(id),
    FOREIGN KEY (source_activity_id) REFERENCES activities(id)
);

-- FTS5 for Full-Text Search
CREATE VIRTUAL TABLE memories_fts USING fts5(
    content, context, tags,
    content=memories,
    content_rowid=rowid,
    tokenize='porter unicode61'
);

-- Memory Relationships
CREATE TABLE memory_relationships (
    id TEXT PRIMARY KEY,
    source_memory_id TEXT NOT NULL,
    target_memory_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,              -- related_to, supersedes, derived_from, contradicts
    strength REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (source_memory_id) REFERENCES memories(id) ON DELETE CASCADE,
    FOREIGN KEY (target_memory_id) REFERENCES memories(id) ON DELETE CASCADE,
    UNIQUE(source_memory_id, target_memory_id, relationship_type)
);

-- Activity-Memory Links
CREATE TABLE activity_memory_links (
    activity_id TEXT NOT NULL,
    memory_id TEXT NOT NULL,
    link_type TEXT NOT NULL,                      -- created, accessed, updated, referenced
    created_at TEXT NOT NULL,
    PRIMARY KEY (activity_id, memory_id, link_type),
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

-- Embeddings
CREATE TABLE embeddings (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL UNIQUE,
    model_name TEXT NOT NULL,                     -- 'all-MiniLM-L6-v2'
    vector BLOB NOT NULL,                         -- float32 array
    dimensions INTEGER NOT NULL,                  -- 384
    created_at TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

-- Session Summaries
CREATE TABLE session_summaries (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    key_learnings TEXT,                           -- JSON array
    key_decisions TEXT,                           -- JSON array
    key_errors TEXT,                              -- JSON array
    files_modified TEXT,                          -- JSON array
    tools_used TEXT,                              -- JSON object
    total_activities INTEGER DEFAULT 0,
    total_memories_created INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Configuration
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Indexes
CREATE INDEX idx_activities_session ON activities(session_id);
CREATE INDEX idx_activities_agent ON activities(agent_id);
CREATE INDEX idx_activities_timestamp ON activities(timestamp DESC);
CREATE INDEX idx_activities_tool ON activities(tool_name);
CREATE INDEX idx_memories_type ON memories(type);
CREATE INDEX idx_memories_status ON memories(status);
CREATE INDEX idx_memories_project ON memories(project_path);
CREATE INDEX idx_memories_importance ON memories(importance_score DESC);
CREATE INDEX idx_memories_accessed ON memories(last_accessed DESC);
```

---

## Tool API (15 Tools)

### Activity Logging Tools

#### `cortex_log_activity`
```python
class LogActivityInput(BaseModel):
    event_type: str          # pre_tool_use, post_tool_use, decision, observation
    tool_name: Optional[str]
    tool_input: Optional[str]
    tool_output: Optional[str]
    duration_ms: Optional[int]
    success: bool = True
    error_message: Optional[str]
    file_path: Optional[str]
    agent_id: Optional[str]
```

#### `cortex_get_activities`
```python
class GetActivitiesInput(BaseModel):
    session_id: Optional[str]
    agent_id: Optional[str]
    event_type: Optional[str]
    tool_name: Optional[str]
    since: Optional[str]      # ISO 8601
    until: Optional[str]      # ISO 8601
    limit: int = 50
    offset: int = 0
```

#### `cortex_get_timeline`
```python
class TimelineInput(BaseModel):
    hours: int = 24           # Hours to look back
    include_activities: bool = True
    include_memories: bool = True
    group_by: str = "hour"    # hour, day, session
```

### Memory Storage Tools

#### `cortex_remember`
```python
class RememberInput(BaseModel):
    content: str
    context: Optional[str]
    tags: Optional[List[str]]
    type: Optional[str]       # Override auto-detect
    importance: Optional[int] # 1-100
    related_activity_id: Optional[str]
    related_memory_ids: Optional[List[str]]
```

#### `cortex_recall`
```python
class RecallInput(BaseModel):
    query: str
    search_mode: str = "hybrid"  # keyword, semantic, hybrid
    type_filter: Optional[str]
    tags_filter: Optional[List[str]]
    status_filter: Optional[str]
    min_importance: Optional[int]
    include_archived: bool = False
    limit: int = 10
```

#### `cortex_list_memories`
```python
class ListMemoriesInput(BaseModel):
    type_filter: Optional[str]
    tags_filter: Optional[List[str]]
    status_filter: Optional[str]
    sort_by: str = "last_accessed"
    sort_order: str = "desc"
    limit: int = 20
    offset: int = 0
```

#### `cortex_update_memory`
```python
class UpdateMemoryInput(BaseModel):
    id: str
    content: Optional[str]
    context: Optional[str]
    tags: Optional[List[str]]
    add_tags: Optional[List[str]]
    remove_tags: Optional[List[str]]
    status: Optional[str]
    importance: Optional[int]
```

#### `cortex_forget`
```python
class ForgetInput(BaseModel):
    id: str
    confirm: bool             # Must be True
```

#### `cortex_link_memories`
```python
class LinkMemoriesInput(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str    # related_to, supersedes, derived_from, contradicts
    strength: float = 1.0
```

### Session Continuity Tools

#### `cortex_start_session`
```python
class StartSessionInput(BaseModel):
    session_id: Optional[str]
    project_path: str
    provide_context: bool = True
    context_depth: int = 3    # Past sessions to summarize
```

#### `cortex_end_session`
```python
class EndSessionInput(BaseModel):
    session_id: str
    summary: Optional[str]    # Manual override
    key_learnings: Optional[List[str]]
```

#### `cortex_get_session_context`
```python
class SessionContextInput(BaseModel):
    project_path: Optional[str]
    session_count: int = 5
    include_learnings: bool = True
    include_decisions: bool = True
    include_errors: bool = True
```

### Utility Tools

#### `cortex_list_tags`
```python
class ListTagsInput(BaseModel):
    min_count: int = 1
    limit: int = 50
```

#### `cortex_review_memories`
```python
class ReviewMemoriesInput(BaseModel):
    action: str               # list, mark_fresh, mark_outdated, mark_archived
    days_threshold: int = 30
    memory_ids: Optional[List[str]]
    limit: int = 20
```

#### `cortex_export`
```python
class ExportInput(BaseModel):
    format: str = "markdown"  # markdown, json, sqlite
    include_activities: bool = True
    include_memories: bool = True
    since: Optional[str]
    output_path: Optional[str]
```

---

## Hook Scripts

### `hooks/pre_tool_use.py`
```python
#!/usr/bin/env python3
"""PreToolUse hook - logs tool call before execution."""
import json, sys, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROJECT_PATH = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
DB_PATH = Path(PROJECT_PATH) / '.omni-cortex' / 'cortex.db'

def main():
    try:
        input_data = json.load(sys.stdin)

        if DB_PATH.exists():
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO activities (id, session_id, agent_id, timestamp,
                    event_type, tool_name, tool_input, project_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"act_{int(datetime.now().timestamp()*1000)}_{os.urandom(4).hex()}",
                os.environ.get('CLAUDE_SESSION_ID'),
                input_data.get('agent_id'),
                datetime.now(timezone.utc).isoformat(),
                'pre_tool_use',
                input_data.get('tool_name'),
                json.dumps(input_data.get('tool_input', {}))[:10000],
                PROJECT_PATH
            ))
            conn.commit()
            conn.close()

        print(json.dumps({}))
    except Exception as e:
        print(json.dumps({"systemMessage": f"Cortex: {e}"}))
    sys.exit(0)

if __name__ == '__main__':
    main()
```

### Similar patterns for:
- `hooks/post_tool_use.py` - Captures tool output, duration, success/error
- `hooks/stop.py` - Ends session, triggers summary generation
- `hooks/subagent_stop.py` - Logs subagent completion

---

## File Structure

```
omni-cortex/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── omni_cortex/
│       ├── __init__.py
│       ├── server.py                 # FastMCP entry point
│       ├── config.py                 # Configuration management
│       │
│       ├── database/
│       │   ├── __init__.py
│       │   ├── schema.py             # SQL schema definitions
│       │   ├── connection.py         # SQLite connection pool
│       │   ├── migrations.py         # Schema versioning
│       │   └── sync.py               # Global index sync
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── activity.py
│       │   ├── memory.py
│       │   ├── session.py
│       │   ├── agent.py
│       │   └── relationship.py
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── activities.py         # 3 activity tools
│       │   ├── memories.py           # 6 memory tools
│       │   ├── sessions.py           # 3 session tools
│       │   └── utilities.py          # 3 utility tools
│       │
│       ├── search/
│       │   ├── __init__.py
│       │   ├── keyword.py            # FTS5 search
│       │   ├── semantic.py           # Vector search
│       │   ├── hybrid.py             # Combined search
│       │   └── ranking.py            # Multi-factor ranking
│       │
│       ├── embeddings/
│       │   ├── __init__.py
│       │   ├── local.py              # sentence-transformers
│       │   └── api_fallback.py       # Claude/OpenAI API
│       │
│       ├── categorization/
│       │   ├── __init__.py
│       │   ├── auto_type.py          # Type detection
│       │   └── auto_tags.py          # Tag suggestion
│       │
│       ├── decay/
│       │   ├── __init__.py
│       │   └── importance.py         # Decay algorithm
│       │
│       ├── resources/
│       │   ├── __init__.py
│       │   └── read_only.py          # MCP resources
│       │
│       └── utils/
│           ├── __init__.py
│           ├── ids.py
│           ├── timestamps.py
│           ├── formatting.py
│           └── truncation.py
│
├── hooks/
│   ├── pre_tool_use.py
│   ├── post_tool_use.py
│   ├── stop.py
│   └── subagent_stop.py
│
├── scripts/
│   ├── init_db.py
│   ├── migrate.py
│   └── sync_global.py
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_database.py
    ├── test_memories.py
    ├── test_activities.py
    ├── test_search.py
    └── test_embeddings.py
```

---

## Key Algorithms

### Smart Ranking (search/ranking.py)
```python
def calculate_relevance_score(memory, query, keyword_score, semantic_score):
    score = 0.0

    # Base scores (40% each)
    score += keyword_score * 0.4
    score += semantic_score * 0.4

    # Access frequency (log scale, max +20)
    score += min(20, math.log1p(memory.access_count) * 5)

    # Recency (exponential decay over 30 days, max +15)
    days = (now - memory.last_accessed).days
    score += max(0, 15 * math.exp(-days / 30))

    # Freshness status
    freshness_bonus = {'fresh': 10, 'needs_review': 0, 'outdated': -10, 'archived': -30}
    score += freshness_bonus.get(memory.status, 0)

    # Importance (0-100 scaled to 0-15)
    score += memory.importance_score * 0.15

    return score
```

### Importance Decay (decay/importance.py)
```python
def calculate_decayed_importance(base, last_accessed, access_count, manual=None):
    if manual is not None:
        return float(manual)

    days = (datetime.now(timezone.utc) - last_accessed).days
    decay_rate = 0.5  # Points lost per day

    decayed = base - (days * decay_rate)
    access_boost = math.log1p(access_count) * 5

    return max(0.0, min(100.0, decayed + access_boost))
```

### Auto-Categorization (categorization/auto_type.py)
```python
TYPE_PATTERNS = {
    'warning': [r'\b(warning|caution|don\'t|avoid|never)\b'],
    'tip': [r'\b(tip|trick|best practice|recommend)\b'],
    'config': [r'\b(config|setting|setup|environment)\b'],
    'troubleshooting': [r'\b(fix|solve|debug|troubleshoot)\b'],
    'code': [r'```', r'\b(function|class|def)\s+\w+'],
    'error': [r'\b(error|exception|failed)\b'],
    'solution': [r'\b(solution|solved|fixed)\b'],
    'command': [r'^\s*[$>]', r'\b(npm|pip|git)\s+'],
    'concept': [r'\b(is|means|defined as)\b'],
    'decision': [r'\b(decided|decision|approach)\b'],
}
```

---

## Dependencies

```toml
[project]
name = "omni-cortex"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
    "httpx>=0.25.0",
    "sentence-transformers>=2.2.0",
    "numpy>=1.24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

---

## Configuration

### Per-Project Config (`.omni-cortex/config.yaml`)
```yaml
schema_version: "1.0"
embedding_model: "all-MiniLM-L6-v2"
decay_rate_per_day: 0.5
freshness_review_days: 30
max_output_truncation: 10000
auto_provide_context: true
context_depth: 3
```

### Global Config (`~/.omni-cortex/config.yaml`)
```yaml
global_sync_enabled: true
api_fallback_enabled: false
api_key: ""  # For Claude/OpenAI embeddings
default_search_mode: "hybrid"
```

---

## Build Phases

| Phase | Focus | Deliverables |
|-------|-------|--------------|
| 1 | Core Foundation | Database, basic memory tools, auto-categorization |
| 2 | Activity Logging | Hook scripts, activity tools, timeline |
| 3 | Semantic Search | Embeddings, hybrid search, ranking |
| 4 | Session Continuity | Session tools, context retrieval |
| 5 | Global Index | Cross-project sync, decay, relationships |
| 6 | Polish | Tests, docs, error handling |

---

## Reference Files

- **FastMCP patterns**: `C:\Users\Tony\.claude\skills\mcp-builder\reference\python_mcp_server.md`
- **MCP best practices**: `C:\Users\Tony\.claude\skills\mcp-builder\reference\mcp_best_practices.md`
- **Hook examples**: `C:\Users\Tony\.claude\plugins\marketplaces\claude-plugins-official\plugins\hookify\hooks\`
- **Ken You Remember source**: `C:\Users\Tony\AppData\Local\npm-cache\_npx\...\ken-you-remember`
- **IndyDevDan patterns**: `D:\Projects\TAC`
