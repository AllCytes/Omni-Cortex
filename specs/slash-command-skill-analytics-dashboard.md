# Slash Command & Skill Analytics Dashboard Enhancement

## Overview

Enhance the OmniCortex dashboard to provide detailed analytics for slash commands and skills, including usage frequency, scope differentiation (universal vs. project-specific), MCP tool source tracking, and expandable activity details.

## Problem Statement

Currently, the OmniCortex dashboard tracks tool usage but lacks:
1. **Slash command/skill-specific analytics** - No way to see how often specific commands like `/commit`, `/build`, etc. are used
2. **Scope differentiation** - Can't distinguish between universal commands (from `~/.claude/commands/`) and project-specific commands
3. **MCP source tracking** - When viewing tool activity, no visibility into which MCP server provided the tool
4. **Activity detail expansion** - The activity timeline shows basic info but doesn't allow drilling down into full tool input/output

## Objectives

1. Track and display slash command/skill usage analytics
2. Differentiate between universal and project-specific commands
3. Add MCP server source tracking to activity display
4. Implement expandable activity details with full input/output viewing
5. Add command/skill-specific filtering in the dashboard

---

## Technical Approach

### Phase 1: Backend - Enhanced Activity Logging

#### 1.1 Database Schema Updates

**File:** `src/omni_cortex/database/schema.py`

Add new columns to the `activities` table:

```sql
-- New columns for activities table
ALTER TABLE activities ADD COLUMN command_name TEXT;        -- e.g., "commit", "build"
ALTER TABLE activities ADD COLUMN command_scope TEXT;       -- "universal" or "project"
ALTER TABLE activities ADD COLUMN mcp_server TEXT;          -- e.g., "grep-mcp", "claude-in-chrome"
ALTER TABLE activities ADD COLUMN skill_name TEXT;          -- Parsed skill name from Skill tool
```

Create new migration file: `src/omni_cortex/database/migrations/004_command_analytics.py`

#### 1.2 Activity Model Updates

**File:** `src/omni_cortex/models/activity.py`

Extend `ActivityCreate` and `Activity` models:

```python
class ActivityCreate(BaseModel):
    # ... existing fields ...
    command_name: Optional[str] = None
    command_scope: Optional[str] = None  # "universal" | "project"
    mcp_server: Optional[str] = None
    skill_name: Optional[str] = None
```

#### 1.3 Activity Logging Tool Enhancement

**File:** `src/omni_cortex/tools/activities.py`

Update `cortex_log_activity` to:
1. Auto-detect Skill tool calls and extract skill name from `tool_input`
2. Accept optional `mcp_server` parameter
3. Parse command scope from file path patterns

```python
def extract_skill_info(tool_name: str, tool_input: str) -> tuple[str, str]:
    """Extract skill name and scope from Skill tool calls."""
    if tool_name != "Skill":
        return None, None

    try:
        input_data = json.loads(tool_input)
        skill_name = input_data.get("skill", "")
        # Scope detection logic based on skill registry
        return skill_name, detect_scope(skill_name)
    except:
        return None, None
```

#### 1.4 New Analytics API Endpoints

**File:** `dashboard/backend/main.py`

Add new endpoints:

```python
@app.get("/api/stats/command-usage")
async def get_command_usage(
    project: str = Query(...),
    scope: Optional[str] = Query(None),  # "universal", "project", or None for all
    days: int = Query(30)
) -> list[CommandUsageEntry]:
    """Get slash command usage statistics."""
    pass

@app.get("/api/stats/skill-usage")
async def get_skill_usage(
    project: str = Query(...),
    scope: Optional[str] = Query(None),
    days: int = Query(30)
) -> list[SkillUsageEntry]:
    """Get skill usage statistics."""
    pass

@app.get("/api/stats/mcp-usage")
async def get_mcp_usage(
    project: str = Query(...),
    days: int = Query(30)
) -> list[MCPUsageEntry]:
    """Get MCP server usage statistics."""
    pass

@app.get("/api/activities/{activity_id}")
async def get_activity_detail(
    activity_id: str,
    project: str = Query(...)
) -> ActivityDetail:
    """Get full activity details including complete input/output."""
    pass
```

**File:** `dashboard/backend/database.py`

Add query functions:

```python
def get_command_usage(db_path: str, scope: str = None, days: int = 30) -> list:
    """Query command usage aggregated by command_name."""
    query = """
        SELECT
            command_name,
            command_scope,
            COUNT(*) as count,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate,
            AVG(duration_ms) as avg_duration_ms
        FROM activities
        WHERE command_name IS NOT NULL
          AND timestamp >= datetime('now', ?)
        GROUP BY command_name, command_scope
        ORDER BY count DESC
    """
    # ... implementation
```

---

### Phase 2: Frontend - Dashboard Enhancements

#### 2.1 New Types

**File:** `dashboard/frontend/src/types/index.ts`

```typescript
interface CommandUsageEntry {
  command_name: string
  command_scope: 'universal' | 'project'
  count: number
  success_rate: number
  avg_duration_ms: number
}

interface SkillUsageEntry {
  skill_name: string
  skill_scope: 'universal' | 'project'
  count: number
  success_rate: number
  avg_duration_ms: number
}

interface MCPUsageEntry {
  mcp_server: string
  tool_count: number
  total_calls: number
  success_rate: number
}

interface ActivityDetail extends Activity {
  tool_input_full: string  // Full JSON, not truncated
  tool_output_full: string
  mcp_server: string | null
  command_name: string | null
  command_scope: string | null
}
```

#### 2.2 Command Analytics Component

**File:** `dashboard/frontend/src/components/charts/CommandUsageChart.vue`

New component showing:
- Bar chart of command usage frequency
- Toggle between universal/project scope view
- Success rate indicators
- Trend over time option

#### 2.3 Skill Analytics Component

**File:** `dashboard/frontend/src/components/charts/SkillUsageChart.vue`

Similar to command analytics but for skills:
- Skill usage frequency
- Scope indicators (universal vs project)
- Success rates

#### 2.4 MCP Server Analytics

**File:** `dashboard/frontend/src/components/charts/MCPUsageChart.vue`

- Shows which MCP servers are being used
- Tool distribution per MCP
- Call volume and success rates

#### 2.5 Enhanced Activity Timeline

**File:** `dashboard/frontend/src/components/ActivityTimeline.vue`

Modify to add:

1. **Expandable rows** - Click to expand and see full tool input/output:

```vue
<div
  v-for="activity in items"
  :key="activity.id"
  class="..."
  @click="toggleExpanded(activity.id)"
>
  <!-- Existing content -->

  <!-- Expandable detail section -->
  <div v-if="expandedIds.has(activity.id)" class="mt-4 border-t pt-4">
    <div class="grid grid-cols-2 gap-4">
      <div>
        <h4 class="font-medium mb-2">Input</h4>
        <pre class="text-xs bg-gray-100 p-2 rounded overflow-auto max-h-64">
          {{ formatJson(activity.tool_input_full) }}
        </pre>
      </div>
      <div>
        <h4 class="font-medium mb-2">Output</h4>
        <pre class="text-xs bg-gray-100 p-2 rounded overflow-auto max-h-64">
          {{ formatJson(activity.tool_output_full) }}
        </pre>
      </div>
    </div>
  </div>
</div>
```

2. **MCP server badge** - Show source MCP:

```vue
<span v-if="activity.mcp_server" class="text-xs px-2 py-0.5 bg-purple-100 rounded">
  {{ activity.mcp_server }}
</span>
```

3. **Command/skill filter** - New filter in the filter bar:

```vue
<div>
  <label>Command/Skill</label>
  <input
    v-model="filterCommandName"
    type="text"
    placeholder="Filter by command..."
    class="..."
  />
</div>
```

#### 2.6 New Statistics Tab Section

**File:** `dashboard/frontend/src/views/StatisticsView.vue`

Add new sections:
- Command Usage Analytics panel
- Skill Usage Analytics panel
- MCP Distribution panel

---

### Phase 3: Data Collection Integration

#### 3.1 Claude Code Hooks Enhancement

The current hook system (`PreToolUse`, `PostToolUse`) already captures tool calls. We need to ensure:

1. **Skill tool detection** - When `tool_name === "Skill"`, parse the skill name from input
2. **MCP tool detection** - Extract MCP server name from tool metadata if available
3. **Command detection** - For ReadSkillFile or similar, detect command invocations

**Hook enhancement pattern:**

```javascript
// In PostToolUse hook, extract additional metadata
if (tool_name === "Skill") {
  const skillName = JSON.parse(tool_input).skill;
  // Log with skill_name field
}

// For MCP tools, the tool name format is often: mcp__servername__toolname
if (tool_name.startsWith("mcp__")) {
  const [_, serverName, actualTool] = tool_name.split("__");
  // Log with mcp_server = serverName
}
```

#### 3.2 Skill Registry Tracking

Create a skill registry that maps skill names to their scope:

**File:** `src/omni_cortex/tools/skill_registry.py`

```python
def get_skill_scope(skill_name: str, project_path: str) -> str:
    """Determine if skill is universal or project-specific."""
    universal_path = Path.home() / ".claude" / "commands" / f"{skill_name}.md"
    project_path = Path(project_path) / ".claude" / "commands" / f"{skill_name}.md"

    if project_path.exists():
        return "project"
    elif universal_path.exists():
        return "universal"
    return "unknown"
```

---

## Implementation Steps

### Step 1: Database Migration
1. Create migration file `004_command_analytics.py`
2. Add new columns: `command_name`, `command_scope`, `mcp_server`, `skill_name`
3. Create indexes for new columns
4. Run migration on existing databases

### Step 2: Backend Model Updates
1. Update `ActivityCreate` model with new fields
2. Update `Activity` model for API responses
3. Add `ActivityDetail` model for full activity data

### Step 3: Activity Logging Enhancement
1. Update `cortex_log_activity` to accept new fields
2. Add skill name extraction from Skill tool calls
3. Add MCP server detection from tool names
4. Implement auto-scope detection

### Step 4: New API Endpoints
1. Implement `/api/stats/command-usage`
2. Implement `/api/stats/skill-usage`
3. Implement `/api/stats/mcp-usage`
4. Implement `/api/activities/{id}` for full details

### Step 5: Frontend Type Updates
1. Add new TypeScript interfaces
2. Update API service with new endpoints
3. Add Pinia store actions for new data

### Step 6: Command Analytics Component
1. Create `CommandUsageChart.vue`
2. Add scope toggle (universal/project/all)
3. Add trend visualization
4. Integrate into Statistics tab

### Step 7: Skill Analytics Component
1. Create `SkillUsageChart.vue`
2. Mirror command analytics structure
3. Add skill-specific icons/colors

### Step 8: MCP Analytics Component
1. Create `MCPUsageChart.vue`
2. Show tool distribution per server
3. Add success rate indicators

### Step 9: Activity Timeline Enhancement
1. Add expandable row functionality
2. Implement full input/output fetching
3. Add MCP server badge display
4. Add command/skill text filter

### Step 10: Integration Testing
1. Verify data collection works for Skill tool
2. Test MCP tool name parsing
3. Validate scope detection accuracy
4. Test expandable activity details

---

## Potential Challenges & Solutions

### Challenge 1: Parsing Historical Data
**Problem:** Existing activities don't have the new fields populated.
**Solution:**
- Run a backfill script that parses `tool_input` for Skill entries
- Parse `tool_name` for MCP server extraction
- Mark historical data with `command_scope = "unknown"` if indeterminate

### Challenge 2: MCP Tool Name Variations
**Problem:** Not all MCP tools follow the `mcp__server__tool` naming convention.
**Solution:**
- Maintain a mapping of known tool names to MCP servers
- Use heuristics for common patterns
- Allow manual override via config

### Challenge 3: Large Input/Output Data
**Problem:** Full tool input/output can be very large.
**Solution:**
- Lazy load full data only when row is expanded
- Implement virtual scrolling for large JSON
- Add "copy to clipboard" functionality

### Challenge 4: Skill Scope Detection
**Problem:** Determining if a skill is universal vs project-specific requires filesystem access.
**Solution:**
- Cache skill scope in the activity record at logging time
- For existing data, infer from project_path + known universal skills

---

## Testing Strategy

### Unit Tests
- Test skill name extraction from tool_input JSON
- Test MCP server parsing from tool names
- Test scope detection logic
- Test new database queries

### Integration Tests
- Log activity with skill data, verify storage
- Query command usage, verify aggregation
- Expand activity, verify full data fetch

### E2E Tests
- Filter activities by command name
- Toggle scope filter, verify chart updates
- Expand activity row, verify input/output display

---

## Success Criteria

1. **Command Analytics:** Dashboard shows command usage frequency with scope differentiation
2. **Skill Analytics:** Dashboard shows skill usage with universal/project breakdown
3. **MCP Visibility:** Activity timeline shows MCP server source for each tool call
4. **Expandable Details:** Clicking an activity reveals full input/output
5. **Filtering:** Can filter activities by specific command/skill name
6. **Cross-Project View:** Can see global command usage across all projects
7. **Historical Data:** Backfill works for existing activities where possible

---

## Files to Create/Modify

### New Files
- `src/omni_cortex/database/migrations/004_command_analytics.py`
- `src/omni_cortex/tools/skill_registry.py`
- `dashboard/frontend/src/components/charts/CommandUsageChart.vue`
- `dashboard/frontend/src/components/charts/SkillUsageChart.vue`
- `dashboard/frontend/src/components/charts/MCPUsageChart.vue`
- `dashboard/frontend/src/components/ActivityDetailModal.vue`

### Modified Files
- `src/omni_cortex/database/schema.py` - Add new columns
- `src/omni_cortex/models/activity.py` - Extend models
- `src/omni_cortex/tools/activities.py` - Enhanced logging
- `dashboard/backend/main.py` - New endpoints
- `dashboard/backend/database.py` - New queries
- `dashboard/backend/models.py` - New response models
- `dashboard/frontend/src/types/index.ts` - New interfaces
- `dashboard/frontend/src/services/api.ts` - New API calls
- `dashboard/frontend/src/components/ActivityTimeline.vue` - Expandable rows, filters
- `dashboard/frontend/src/views/StatisticsView.vue` - New chart sections

---

## Estimated Complexity

- **Phase 1 (Backend):** Medium - Schema changes, new endpoints
- **Phase 2 (Frontend):** Medium - New components, timeline enhancement
- **Phase 3 (Integration):** Low-Medium - Parsing logic, backfill

Total: ~15-20 discrete implementation tasks across 3 phases
