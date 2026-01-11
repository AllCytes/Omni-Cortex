# Dashboard Activity Enhancements v4

## Overview

Address multiple issues with the dashboard activity tracking system and add new natural language summary features.

## Problem Statement

### Issue 1: Missing Database Columns
The activities table is missing the command analytics columns that were defined in migration v1.1:
- `command_name`
- `command_scope`
- `mcp_server`
- `skill_name`

The migration exists in `src/omni_cortex/database/migrations.py` but hasn't been applied to existing databases.

### Issue 2: Backend Not Returning Command Analytics Fields
Even if columns existed, `dashboard/backend/database.py::get_activities()` doesn't return the command analytics fields. It only returns basic activity fields.

### Issue 3: Backend Activity Model Missing Fields
The `Activity` model in `dashboard/backend/models.py` lacks command analytics fields.

### Issue 4: Output Fields Showing Null
Many `tool_output` values are null/empty. This is partially expected behavior since:
- Pre-tool-use events log before output exists
- Post-tool-use hooks may not always capture output
- Some tools don't produce output

### Issue 5: No Natural Language Summaries
User requests 12-20 word collapsed view with expanded detailed description for each activity.

### Issue 6: User Prompt Tracking
User wants to track user prompts in the activity log.

---

## Technical Approach

### Phase 1: Fix Database Schema

#### 1.1 Apply Missing Migration

The migration already exists but needs to be triggered. Create a utility to apply migrations on dashboard startup.

**File:** `dashboard/backend/database.py`

Add migration check at startup:

```python
def ensure_migrations(db_path: str) -> None:
    """Ensure database has latest migrations applied."""
    conn = get_write_connection(db_path)

    # Check if command analytics columns exist
    columns = conn.execute("PRAGMA table_info(activities)").fetchall()
    column_names = [col[1] for col in columns]

    if "command_name" not in column_names:
        # Apply migration v1.1
        conn.executescript("""
            ALTER TABLE activities ADD COLUMN command_name TEXT;
            ALTER TABLE activities ADD COLUMN command_scope TEXT;
            ALTER TABLE activities ADD COLUMN mcp_server TEXT;
            ALTER TABLE activities ADD COLUMN skill_name TEXT;

            CREATE INDEX IF NOT EXISTS idx_activities_command ON activities(command_name);
            CREATE INDEX IF NOT EXISTS idx_activities_mcp ON activities(mcp_server);
            CREATE INDEX IF NOT EXISTS idx_activities_skill ON activities(skill_name);
        """)
        conn.commit()

    conn.close()
```

#### 1.2 Add Summary Column

Add new column for natural language summaries:

```sql
ALTER TABLE activities ADD COLUMN summary TEXT;
ALTER TABLE activities ADD COLUMN summary_detail TEXT;
```

---

### Phase 2: Fix Backend Models & Queries

#### 2.1 Update Activity Model

**File:** `dashboard/backend/models.py`

```python
class Activity(BaseModel):
    """Activity log record."""
    id: str
    session_id: Optional[str] = None
    event_type: str
    tool_name: Optional[str] = None
    tool_input: Optional[str] = None
    tool_output: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    file_path: Optional[str] = None
    timestamp: datetime
    # Command analytics fields
    command_name: Optional[str] = None
    command_scope: Optional[str] = None
    mcp_server: Optional[str] = None
    skill_name: Optional[str] = None
    # Natural language summary fields
    summary: Optional[str] = None
    summary_detail: Optional[str] = None
```

#### 2.2 Update get_activities Query

**File:** `dashboard/backend/database.py`

Update `get_activities()` to include new fields with backward compatibility:

```python
def get_activities(
    db_path: str,
    event_type: Optional[str] = None,
    tool_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Activity]:
    """Get activity log entries."""
    conn = get_connection(db_path)

    # Check available columns
    columns = conn.execute("PRAGMA table_info(activities)").fetchall()
    column_names = {col[1] for col in columns}

    query = "SELECT * FROM activities WHERE 1=1"
    params: list = []

    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)

    if tool_name:
        query += " AND tool_name = ?"
        params.append(tool_name)

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = conn.execute(query, params)
    activities = []

    for row in cursor.fetchall():
        ts_str = row["timestamp"]
        try:
            ts = datetime.fromisoformat(ts_str)
        except ValueError:
            ts = datetime.now()

        activity_data = {
            "id": row["id"],
            "session_id": row["session_id"],
            "event_type": row["event_type"],
            "tool_name": row["tool_name"],
            "tool_input": row["tool_input"],
            "tool_output": row["tool_output"],
            "success": bool(row["success"]),
            "error_message": row["error_message"],
            "duration_ms": row["duration_ms"],
            "file_path": row["file_path"],
            "timestamp": ts,
        }

        # Add command analytics fields if available
        if "command_name" in column_names:
            activity_data["command_name"] = row["command_name"]
        if "command_scope" in column_names:
            activity_data["command_scope"] = row["command_scope"]
        if "mcp_server" in column_names:
            activity_data["mcp_server"] = row["mcp_server"]
        if "skill_name" in column_names:
            activity_data["skill_name"] = row["skill_name"]
        if "summary" in column_names:
            activity_data["summary"] = row["summary"]
        if "summary_detail" in column_names:
            activity_data["summary_detail"] = row["summary_detail"]

        activities.append(Activity(**activity_data))

    conn.close()
    return activities
```

---

### Phase 3: Natural Language Summary Generation

#### 3.1 Summary Generation Logic

**File:** `src/omni_cortex/tools/activities.py`

Add summary generation function:

```python
def generate_activity_summary(
    tool_name: str,
    tool_input: Optional[str],
    success: bool,
    file_path: Optional[str],
    event_type: str
) -> tuple[str, str]:
    """Generate natural language summary for an activity.

    Returns:
        tuple of (short_summary, detailed_summary)
        - short_summary: 12-20 words, shown in collapsed view
        - detailed_summary: Expanded description with more context
    """
    short = ""
    detail = ""

    # Parse tool input if available
    input_data = {}
    if tool_input:
        try:
            input_data = json.loads(tool_input)
        except:
            pass

    # Generate summaries based on tool type
    if tool_name == "Read":
        path = input_data.get("file_path", file_path or "unknown file")
        filename = Path(path).name if path else "file"
        short = f"Read file: {filename}"
        detail = f"Reading contents of {path}"

    elif tool_name == "Write":
        path = input_data.get("file_path", file_path or "unknown file")
        filename = Path(path).name if path else "file"
        short = f"Write file: {filename}"
        detail = f"Writing/creating file at {path}"

    elif tool_name == "Edit":
        path = input_data.get("file_path", file_path or "unknown file")
        filename = Path(path).name if path else "file"
        short = f"Edit file: {filename}"
        detail = f"Editing {path} - replacing text content"

    elif tool_name == "Bash":
        cmd = input_data.get("command", "")[:50]
        short = f"Run command: {cmd}..."
        detail = f"Executing bash command: {input_data.get('command', 'unknown')}"

    elif tool_name == "Grep":
        pattern = input_data.get("pattern", "")
        short = f"Search for: {pattern[:30]}"
        detail = f"Searching codebase for pattern: {pattern}"

    elif tool_name == "Glob":
        pattern = input_data.get("pattern", "")
        short = f"Find files: {pattern[:30]}"
        detail = f"Finding files matching pattern: {pattern}"

    elif tool_name == "Skill":
        skill = input_data.get("skill", "unknown")
        short = f"Run skill: /{skill}"
        detail = f"Executing slash command /{skill}"

    elif tool_name == "Task":
        desc = input_data.get("description", "task")
        short = f"Spawn agent: {desc[:30]}"
        detail = f"Launching sub-agent for: {input_data.get('prompt', desc)[:100]}"

    elif tool_name and tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        server = parts[1] if len(parts) > 1 else "unknown"
        tool = parts[2] if len(parts) > 2 else tool_name
        short = f"MCP call: {server}/{tool}"
        detail = f"Calling {tool} tool from MCP server {server}"

    elif tool_name == "cortex_remember":
        content = input_data.get("params", {}).get("content", "")[:40]
        short = f"Store memory: {content}..."
        detail = f"Saving to memory system: {content}"

    elif tool_name == "cortex_recall":
        query = input_data.get("params", {}).get("query", "")
        short = f"Recall: {query[:30]}"
        detail = f"Searching memories for: {query}"

    else:
        short = f"{event_type}: {tool_name or 'unknown'}"
        detail = f"Activity type {event_type} with tool {tool_name}"

    # Add status suffix
    if not success:
        short = f"[FAILED] {short}"
        detail = f"[FAILED] {detail}"

    return short, detail
```

#### 3.2 Backfill Existing Activities

Create a utility to generate summaries for existing activities:

**File:** `dashboard/backend/backfill_summaries.py`

```python
def backfill_activity_summaries(db_path: str) -> int:
    """Generate summaries for activities that don't have them."""
    conn = get_write_connection(db_path)

    cursor = conn.execute("""
        SELECT id, tool_name, tool_input, success, file_path, event_type
        FROM activities
        WHERE summary IS NULL OR summary = ''
    """)

    count = 0
    for row in cursor.fetchall():
        short, detail = generate_activity_summary(
            row["tool_name"],
            row["tool_input"],
            bool(row["success"]),
            row["file_path"],
            row["event_type"]
        )

        conn.execute("""
            UPDATE activities
            SET summary = ?, summary_detail = ?
            WHERE id = ?
        """, (short, detail, row["id"]))
        count += 1

        if count % 100 == 0:
            conn.commit()

    conn.commit()
    conn.close()
    return count
```

---

### Phase 4: Frontend Activity Display Updates

#### 4.1 Update ActivityTimeline.vue

Add summary display in collapsed view:

```vue
<!-- In activity item, before expand button -->
<div class="flex-1 min-w-0">
  <div class="flex items-center gap-2 flex-wrap">
    <span class="font-medium">{{ activity.tool_name || 'Unknown' }}</span>
    <!-- ... existing badges ... -->
  </div>

  <!-- NEW: Natural language summary (collapsed view) -->
  <p v-if="activity.summary" class="text-sm text-gray-600 dark:text-gray-300 mt-1">
    {{ activity.summary }}
  </p>
</div>
```

In expanded section, add detailed summary:

```vue
<!-- Expanded detail section -->
<div v-if="expandedIds.has(activity.id)" class="...">
  <!-- NEW: Detailed summary -->
  <div v-if="activityDetails.get(activity.id)?.summary_detail" class="mb-4">
    <h4 class="font-medium text-sm mb-1">What happened:</h4>
    <p class="text-sm text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 p-2 rounded">
      {{ activityDetails.get(activity.id)?.summary_detail }}
    </p>
  </div>

  <!-- Existing Input/Output panels -->
  ...
</div>
```

#### 4.2 Update TypeScript Types

**File:** `dashboard/frontend/src/types/index.ts`

```typescript
export interface Activity {
  // ... existing fields ...

  // Command analytics fields
  command_name: string | null
  command_scope: string | null
  mcp_server: string | null
  skill_name: string | null

  // Natural language summaries
  summary: string | null
  summary_detail: string | null
}

export interface ActivityDetail extends Activity {
  tool_input_full: string | null
  tool_output_full: string | null
}
```

---

### Phase 5: Enhanced Tool Call Tracking

The existing hook system captures PreToolUse and PostToolUse events. We need to ensure proper metadata extraction:

**Tool-specific summary generation:**

```python
TOOL_DESCRIPTIONS = {
    "Read": "Reading file contents",
    "Write": "Creating/writing file",
    "Edit": "Editing file content",
    "Bash": "Executing shell command",
    "Grep": "Searching file contents",
    "Glob": "Finding files by pattern",
    "WebSearch": "Searching the web",
    "WebFetch": "Fetching web page content",
    "Task": "Spawning sub-agent",
    "Skill": "Running slash command/skill",
    "TodoWrite": "Managing todo list",
    "AskUserQuestion": "Asking user for input",
    "NotebookEdit": "Editing Jupyter notebook",
}

def get_tool_description(tool_name: str, tool_input: dict) -> str:
    """Get human-readable description of tool action."""
    base_desc = TOOL_DESCRIPTIONS.get(tool_name, f"Using {tool_name}")

    # Add specifics based on input
    if tool_name == "Read" and "file_path" in tool_input:
        return f"{base_desc}: {Path(tool_input['file_path']).name}"
    elif tool_name == "Bash" and "command" in tool_input:
        cmd = tool_input["command"][:50]
        return f"{base_desc}: {cmd}..."
    elif tool_name == "Grep" and "pattern" in tool_input:
        return f"{base_desc} for: {tool_input['pattern'][:30]}"
    elif tool_name == "WebSearch" and "query" in tool_input:
        return f"{base_desc}: {tool_input['query'][:40]}"
    elif tool_name == "Skill" and "skill" in tool_input:
        return f"Running /{tool_input['skill']} skill"
    elif tool_name == "Task" and "description" in tool_input:
        return f"{base_desc}: {tool_input['description'][:30]}"

    return base_desc
```

#### 5.1 Activity Types for Dashboard

The Activity Timeline should show different activity types with appropriate icons:

| Activity Type | Icon | Description |
|--------------|------|-------------|
| pre_tool_use | Play | Tool execution starting |
| post_tool_use | CheckCircle | Tool execution completed |
| skill_execution | Zap | Skill being executed (via Skill tool) |
| web_search | Search | Web search performed |
| file_read | FileText | File being read |
| file_write | FilePlus | File being written |
| bash_command | Terminal | Shell command executed |
| mcp_call | Server | MCP server tool called |
| sub_agent | Users | Sub-agent spawned |

#### 5.2 Dashboard Activity Stream View

Update ActivityTimeline to show Claude Code-style activity stream:

```vue
<template>
  <div class="activity-stream">
    <!-- Each activity shows: -->
    <!-- [icon] [tool/action] [summary] [timestamp] -->
    <!-- Click to expand for full details -->

    <div v-for="activity in activities" :key="activity.id" class="activity-item">
      <!-- Icon based on tool type -->
      <component :is="getActivityIcon(activity)" class="icon" />

      <!-- Tool/Action name -->
      <span class="tool-name">{{ activity.tool_name || activity.event_type }}</span>

      <!-- Natural language summary -->
      <span class="summary">{{ activity.summary }}</span>

      <!-- Badges -->
      <span v-if="activity.mcp_server" class="badge mcp">{{ activity.mcp_server }}</span>
      <span v-if="activity.skill_name" class="badge skill">{{ activity.skill_name }}</span>
      <span v-if="activity.command_name" class="badge command">/{{ activity.command_name }}</span>

      <!-- Status indicator -->
      <CheckCircle v-if="activity.success" class="status success" />
      <XCircle v-else class="status error" />

      <!-- Timestamp -->
      <span class="timestamp">{{ formatTime(activity.timestamp) }}</span>
    </div>
  </div>
</template>
```

---

### Phase 6: MCP Server Data Population

#### 6.1 Auto-Extract MCP Server

The MCP server extraction already exists in `activities.py::_extract_mcp_server()`. Ensure it's being called:

```python
# In cortex_log_activity
if params.tool_name and params.tool_name.startswith("mcp__"):
    extracted_mcp = _extract_mcp_server(params.tool_name)
    mcp_server = mcp_server or extracted_mcp
```

#### 6.2 Backfill MCP Server Data

Create backfill for existing activities:

```python
def backfill_mcp_servers(db_path: str) -> int:
    """Extract and populate mcp_server for existing activities."""
    conn = get_write_connection(db_path)

    cursor = conn.execute("""
        SELECT id, tool_name FROM activities
        WHERE tool_name LIKE 'mcp__%'
          AND (mcp_server IS NULL OR mcp_server = '')
    """)

    count = 0
    for row in cursor.fetchall():
        parts = row["tool_name"].split("__")
        if len(parts) >= 2:
            server = parts[1]
            conn.execute(
                "UPDATE activities SET mcp_server = ? WHERE id = ?",
                (server, row["id"])
            )
            count += 1

    conn.commit()
    conn.close()
    return count
```

---

## Implementation Steps

### Step 1: Database Migration (Priority: Critical)
1. Add `ensure_migrations()` function to `dashboard/backend/database.py`
2. Call migration check on dashboard startup
3. Add columns: `command_name`, `command_scope`, `mcp_server`, `skill_name`, `summary`, `summary_detail`
4. Test migration on existing database

### Step 2: Backend Model Updates (Priority: High)
1. Update `Activity` model in `models.py` with all new fields
2. Update `get_activities()` query with backward-compatible column checking
3. Update `get_activity_detail()` to include summary fields
4. Test API responses include new fields

### Step 3: Summary Generation (Priority: High)
1. Implement `generate_activity_summary()` function
2. Integrate into `cortex_log_activity` for new activities
3. Create backfill script for existing activities
4. Test summary quality for common tools

### Step 4: Frontend Updates (Priority: Medium)
1. Update TypeScript interfaces
2. Add summary display in ActivityTimeline collapsed view
3. Add detailed summary in expanded view
4. Style summary text appropriately

### Step 5: MCP/Command Backfill (Priority: Medium)
1. Run MCP server backfill for existing data
2. Run skill/command name backfill where possible
3. Verify charts now show data

---

## Success Criteria

1. **Database columns exist:** All new columns present (command_name, skill_name, mcp_server, summary, summary_detail)
2. **API returns analytics fields:** GET /api/activities includes command_name, skill_name, mcp_server
3. **Charts show data:** Command usage, skill usage, MCP usage charts display actual data
4. **Summaries visible:** Activity items show 12-20 word summary in collapsed view
5. **Expanded detail:** Clicking activity shows detailed summary + full I/O
6. **Backfill works:** Existing activities have summaries and MCP data populated
7. **Skill tracking works:** Skill tool invocations show skill_name in activity timeline

---

## Files to Modify

### Backend
- `dashboard/backend/database.py` - Migration, query updates
- `dashboard/backend/models.py` - Activity model fields
- `src/omni_cortex/tools/activities.py` - Summary generation, logging
- `src/omni_cortex/models/activity.py` - ActivityCreate model

### Frontend
- `dashboard/frontend/src/types/index.ts` - Activity interface
- `dashboard/frontend/src/components/ActivityTimeline.vue` - Summary display

### New Files
- `dashboard/backend/backfill_summaries.py` - Backfill utility
