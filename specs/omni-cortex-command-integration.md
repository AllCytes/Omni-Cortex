# Omni Cortex MCP Integration Plan

## Problem Statement

Claude Code commands across three project paths need to be updated to utilize the Omni Cortex MCP for persistent memory, context preservation, and cross-session learning. Currently, only 11 of 28+ commands/skills use Omni Cortex, leaving significant potential for improved context continuity unexploited.

## Objectives

1. Integrate Omni Cortex MCP tools into 17+ commands
2. Integrate Omni Cortex MCP tools into 6 skills
3. Standardize integration patterns for consistency
4. Enable cross-project pattern recognition
5. Preserve session context for future reference

## Paths to Update

| Path | Type | Commands/Skills |
|------|------|-----------------|
| `C:\Users\Tony\.claude\commands\` | Global Commands | 17 commands |
| `C:\Users\Tony\.claude\skills\` | Global Skills | 6 skills |
| `D:\Projects\Project-Management\.claude\commands\` | Project Commands | 1 command |

---

## Omni Cortex Tools Reference

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `cortex_recall` | Search memories | Start of workflow - check previous context |
| `cortex_remember` | Store memories | End of workflow - store results/decisions |
| `cortex_get_session_context` | Get previous session context | For session-aware commands |
| `cortex_global_search` | Cross-project search | For pattern discovery across projects |
| `cortex_log_activity` | Log significant events | For audit trail on important operations |

---

## Integration Patterns

### Pattern A: Recall-Execute-Remember (Standard)
```yaml
allowed-tools: [...existing..., mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember]

Workflow:
  1. cortex_recall: Check for previous patterns/issues
  2. Execute main workflow
  3. cortex_remember: Store results with tags
```

### Pattern B: Session-Aware (For Daily/Ongoing Tasks)
```yaml
allowed-tools: [...existing..., mcp__omni-cortex__cortex_get_session_context, mcp__omni-cortex__cortex_remember]

Workflow:
  1. cortex_get_session_context: Get continuity from previous sessions
  2. Execute main workflow
  3. cortex_remember: Store session outcomes
```

### Pattern C: Cross-Project (For Pattern Discovery)
```yaml
allowed-tools: [...existing..., mcp__omni-cortex__cortex_global_search, mcp__omni-cortex__cortex_remember]

Workflow:
  1. cortex_global_search: Find patterns across all projects
  2. Execute main workflow
  3. cortex_remember: Store with global-relevant tags
```

---

## Phase 1: High-Priority Commands (Critical Path)

### 1.1 build.md
**Path:** `C:\Users\Tony\.claude\commands\build.md`
**Pattern:** A (Recall-Execute-Remember)

**Changes:**
```yaml
# Add to allowed-tools:
allowed-tools: Read, Write, Bash, mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember

# Add to Workflow (before implementation):
- Recall previous build issues: `cortex_recall: "build errors {project_name}"`
- Check for known solutions: `cortex_recall: "build fix"`

# Add to Workflow (after completion):
- Store build outcome: `cortex_remember`
  - Content: Build result summary (success/failure, key changes)
  - Tags: ["build", "{project_name}", "success|failure"]
  - Type: "progress" or "troubleshooting"
```

**Memory Examples:**
- Success: "Build succeeded for omni-cortex: 5 files changed, tests passing"
- Failure: "Build failed: TypeScript error in dashboard/App.vue - missing import"

---

### 1.2 prime.md
**Path:** `C:\Users\Tony\.claude\commands\prime.md`
**Pattern:** B (Session-Aware)

**Changes:**
```yaml
# Add to allowed-tools:
allowed-tools: Bash, Read, mcp__omni-cortex__cortex_get_session_context, mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember

# Add to Workflow (before exploration):
- Check for previous priming: `cortex_recall: "prime {project_name}"`
- Get session context: `cortex_get_session_context`
  - If previous priming exists, offer to show summary or re-prime

# Add to Workflow (after completion):
- Store priming result: `cortex_remember`
  - Content: Project structure summary, key files, architecture notes
  - Tags: ["prime", "{project_name}", "codebase-understanding"]
  - Type: "knowledge"
  - Importance: 80 (high - frequently needed)
```

**Memory Example:**
```
Project: omni-cortex
Type: Python MCP Server + Vue Dashboard
Key Files: src/omni_cortex/server.py, dashboard/frontend/src/App.vue
Architecture: FastMCP backend, SQLite storage, Vue 3 frontend
Entry Points: omni-cortex (CLI), omni-cortex-dashboard
```

---

### 1.3 test.md
**Path:** `C:\Users\Tony\.claude\commands\test.md`
**Pattern:** A (Recall-Execute-Remember)

**Changes:**
```yaml
# Add to allowed-tools:
allowed-tools: Bash, Read, mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember

# Add to Workflow (before tests):
- Recall test patterns: `cortex_recall: "test failure {project_name}"`
- Check for flaky tests: `cortex_recall: "flaky test"`

# Add to Workflow (after completion):
- Store test results: `cortex_remember`
  - Content: Test summary (passed/failed, failure details)
  - Tags: ["test", "{project_name}", "passed|failed"]
  - Type: "progress" or "troubleshooting"
```

---

### 1.4 commit.md
**Path:** `C:\Users\Tony\.claude\commands\commit.md`
**Pattern:** A (Recall-Execute-Remember)

**Changes:**
```yaml
# Add to allowed-tools:
allowed-tools: Bash, mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember

# Add to Workflow (before commit):
- Recall commit style: `cortex_recall: "commit message {project_name}"`
  - Use to maintain consistent messaging

# Add to Workflow (after completion):
- Store significant commits: `cortex_remember`
  - Content: Commit hash + message summary
  - Tags: ["commit", "{project_name}", "{feature_area}"]
  - Type: "progress"
  - Importance: 30 (low - only for major changes)
```

---

### 1.5 quick-plan.md
**Path:** `C:\Users\Tony\.claude\commands\quick-plan.md`
**Pattern:** C (Cross-Project)

**Changes:**
```yaml
# Add to allowed-tools:
allowed-tools: Read, Write, Edit, Glob, Grep, MultiEdit, mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_global_search, mcp__omni-cortex__cortex_remember

# Add to Workflow (before planning):
- Search for similar plans: `cortex_recall: "plan {feature_keywords}"`
- Cross-project patterns: `cortex_global_search: "{architecture_keywords}"`

# Add to Workflow (after completion):
- Store plan reference: `cortex_remember`
  - Content: Plan summary + file path + key decisions
  - Tags: ["plan", "{project_name}", "{feature_area}"]
  - Type: "decision"
  - Importance: 70
```

---

## Phase 2: Supporting Commands

### 2.1 question.md
**Path:** `C:\Users\Tony\.claude\commands\question.md`
**Pattern:** C (Cross-Project)

**Changes:**
```yaml
allowed-tools: Bash(git ls-files:*), Read, mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_global_search, mcp__omni-cortex__cortex_remember

# Before answering:
- Check if question asked before: `cortex_recall: "{question_keywords}"`
- Check cross-project: `cortex_global_search: "{question_keywords}"`

# After answering:
- Store Q&A: `cortex_remember`
  - Tags: ["question", "{project_name}", "{topic}"]
  - Type: "knowledge"
```

---

### 2.2 docs.md
**Path:** `C:\Users\Tony\.claude\commands\docs.md`
**Pattern:** A (Recall-Execute-Remember)

**Changes:**
```yaml
allowed-tools: [...existing..., mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember]

# Before creating docs:
- Recall doc patterns: `cortex_recall: "documentation {project_name}"`

# After completion:
- Store doc update: `cortex_remember`
  - Tags: ["docs", "{project_name}", "{doc_type}"]
  - Type: "progress"
```

---

### 2.3 deploy.md
**Path:** `C:\Users\Tony\.claude\commands\deploy.md`
**Pattern:** A + Log Activity

**Changes:**
```yaml
allowed-tools: [...existing..., mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember, mcp__omni-cortex__cortex_log_activity]

# Before deploy:
- Recall deployment issues: `cortex_recall: "deploy {project_name} error"`

# After completion:
- Log deployment: `cortex_log_activity`
  - event_type: "decision"
  - tool_name: "deploy"
- Store outcome: `cortex_remember`
  - Tags: ["deploy", "{project_name}", "{environment}", "success|failure"]
  - Type: "progress"
  - Importance: 85 (high - critical operations)
```

---

### 2.4 migrate.md
**Path:** `C:\Users\Tony\.claude\commands\migrate.md`
**Pattern:** A + Log Activity

**Changes:**
```yaml
allowed-tools: [...existing..., mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember, mcp__omni-cortex__cortex_log_activity]

# Before migration:
- Recall migration patterns: `cortex_recall: "migration {project_name}"`

# After completion:
- Log migration: `cortex_log_activity`
- Store migration record: `cortex_remember`
  - Tags: ["migration", "{project_name}", "{migration_type}"]
  - Type: "decision"
  - Importance: 90 (critical - data operations)
```

---

### 2.5 coverage.md
**Path:** `C:\Users\Tony\.claude\commands\coverage.md`
**Pattern:** A (Recall-Execute-Remember)

**Changes:**
```yaml
allowed-tools: [...existing..., mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember]

# Before analysis:
- Recall coverage history: `cortex_recall: "coverage {project_name}"`

# After completion:
- Store coverage progress: `cortex_remember`
  - Content: Coverage percentage, files improved
  - Tags: ["coverage", "{project_name}", "{percentage}%"]
  - Type: "progress"
```

---

### 2.6 clean.md
**Path:** `C:\Users\Tony\.claude\commands\clean.md`
**Pattern:** A (Recall-Execute-Remember)

**Changes:**
```yaml
allowed-tools: [...existing..., mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember]

# Before cleanup:
- Recall previous cleanups: `cortex_recall: "cleanup {project_name}"`

# After completion:
- Store cleanup results: `cortex_remember`
  - Tags: ["cleanup", "{project_name}"]
  - Type: "progress"
```

---

### 2.7 api.md
**Path:** `C:\Users\Tony\.claude\commands\api.md`
**Pattern:** C (Cross-Project)

**Changes:**
```yaml
allowed-tools: [...existing..., mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_global_search, mcp__omni-cortex__cortex_remember]

# Before API work:
- Recall API patterns: `cortex_recall: "api {project_name}"`
- Cross-project API patterns: `cortex_global_search: "api design"`

# After completion:
- Store API decisions: `cortex_remember`
  - Tags: ["api", "{project_name}", "{endpoint_type}"]
  - Type: "decision"
```

---

### 2.8 analyze-history.md ✅ COMPLETED
**Path:** `C:\Users\Tony\.claude\commands\analyze-history.md`
**Pattern:** B + C (Session-Aware + Cross-Project) - **FULLY INTEGRATED**
**Status:** Completed on 2026-01-07

**Integrated Tools (8 total):**
- `cortex_global_search` - Cross-project pattern mining
- `cortex_get_activities` - Activity log analysis with date filtering
- `cortex_get_timeline` - Temporal pattern analysis
- `cortex_list_tags` - Existing pattern categories
- `cortex_list_memories` - Memory retrieval
- `cortex_global_stats` - Global memory statistics
- `cortex_link_memories` - Connect related findings
- `cortex_remember` - Store analysis results

**Date Filter Feature Added:**
```yaml
argument-hint: [session-name] [--date YYYY-MM-DD | --today | --range 24h|7d|30d]

# Examples:
/analyze-history --today                    # Just today
/analyze-history --date 2026-01-07          # Specific date
/analyze-history --range 24h                # Last 24 hours
/analyze-history --range 7d                 # Last 7 days
/analyze-history omni-cortex --today        # Named session + date
```

**3-Phase Workflow:**
1. Phase 0: Parse date filter arguments
2. Phase 1: Omni-Cortex Intelligence Gathering (with date filtering)
3. Phase 2: History.jsonl Deep Dive (filtered by date)
4. Phase 3: Synthesis and Output with enhanced memory storage

---

### 2.9 merge-worktrees.md
**Path:** `C:\Users\Tony\.claude\commands\merge-worktrees.md`
**Pattern:** A + Log Activity

**Changes:**
```yaml
allowed-tools: [...existing..., mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember, mcp__omni-cortex__cortex_log_activity]

# Before merge:
- Recall merge conflicts: `cortex_recall: "merge conflict {project_name}"`

# After completion:
- Log merge activity: `cortex_log_activity`
- Store merge result: `cortex_remember`
  - Tags: ["merge", "{project_name}", "worktree"]
  - Type: "progress"
```

---

### 2.10 orchestrate.md
**Path:** `C:\Users\Tony\.claude\commands\orchestrate.md`
**Pattern:** A (Recall-Execute-Remember)

**Changes:**
```yaml
allowed-tools: [...existing..., mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember]

# Before orchestration:
- Recall orchestration patterns: `cortex_recall: "orchestrate {project_name}"`

# After completion:
- Store orchestration results: `cortex_remember`
  - Tags: ["orchestrate", "{project_name}", "parallel-execution"]
  - Type: "progress"
```

---

### 2.11 parallel_subagents.md
**Path:** `C:\Users\Tony\.claude\commands\parallel_subagents.md`
**Pattern:** A (Recall-Execute-Remember)

**Changes:**
```yaml
allowed-tools: [...existing..., mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember]

# Before spawning:
- Recall agent patterns: `cortex_recall: "subagent {task_type}"`

# After completion:
- Store execution results: `cortex_remember`
  - Tags: ["subagents", "{project_name}", "parallel"]
  - Type: "progress"
```

---

### 2.12 prime_cc.md
**Path:** `C:\Users\Tony\.claude\commands\prime_cc.md`
**Pattern:** B (Session-Aware)

**Changes:**
```yaml
allowed-tools: [...existing..., mcp__omni-cortex__cortex_get_session_context, mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember]

# Before exploration:
- Get session context: `cortex_get_session_context`
- Recall previous CC findings: `cortex_recall: "claude code improvement"`

# After completion:
- Store findings: `cortex_remember`
  - Tags: ["prime", "claude-code", "improvement-ideas"]
  - Type: "knowledge"
  - Importance: 80
```

---

## Phase 3: Project Management Commands

### 3.1 eisenhower.md
**Path:** `D:\Projects\Project-Management\.claude\commands\eisenhower.md`
**Pattern:** A (Recall-Execute-Remember)

**Changes:**
```yaml
# Add to allowed-tools:
allowed-tools: mcp__ticktick__*, mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember

# Add to Workflow (after matrix display):
- Store snapshot: `cortex_remember`
  - Content: Distribution summary (Q1: X, Q2: Y, Q3: Z, Q4: W)
  - Tags: ["eisenhower", "task-distribution", "{date}"]
  - Type: "progress"
  - Context: Used for trend analysis over time
```

---

### 3.2 reflect.md ✅ COMPLETED
**Path:** `D:\Projects\Project-Management\.claude\commands\reflect.md`
**Pattern:** B + C (Session-Aware + Cross-Project) - **FULLY INTEGRATED**
**Status:** Completed on 2026-01-08

**Enhancement:** Added comprehensive cross-project activity analysis as Step 0.

**Integrated Tools (5 new):**
- `cortex_get_activities` - Query today's tool usage across all projects
- `cortex_get_timeline` - 24-hour temporal pattern analysis
- `cortex_list_memories` - Today's decisions/progress/knowledge
- `cortex_global_search` - Cross-project pattern discovery
- `cortex_remember` - Store reflection insights (already existed)

**New Step 0: Cross-Project Activity Analysis:**
```yaml
argument-hint: [--skip-analysis]

# Skip with: /reflect --skip-analysis

Workflow additions:
  0.1: Query today's activities (cortex_get_activities with since: today)
  0.2: Get timeline view (cortex_get_timeline hours: 24)
  0.3: Query today's memories (cortex_list_memories sorted by created_at)
  0.4: Cross-project search (cortex_global_search)
  0.5: Present activity summary before reflection prompts
  0.6: Use activity data to inform productivity scoring
```

**8-Step Workflow:**
1. Step 0: Cross-Project Activity Analysis (NEW)
2. Step 1: Validate Yesterday's Prediction
3. Step 2: Three Wins Prompts
4. Step 3: Gap Analysis
5. Step 4: Productivity Scoring (now informed by actual activity)
6. Step 5: Tomorrow's Priorities
7. Step 6: Satisfaction Prediction & Burnout Assessment
8. Step 7: Write to Supabase
9. Step 8: Store Insights in Memory

---

## Phase 4: Skills Integration

### 4.1 git-worktrees/skill.md
**Path:** `C:\Users\Tony\.claude\skills\git-worktrees\skill.md`
**Pattern:** A (Recall-Execute-Remember)

**Add to SKILL.md header:**
```yaml
tools:
  - mcp__omni-cortex__cortex_recall
  - mcp__omni-cortex__cortex_remember
```

**Add to workflow:**
- Before creating worktrees: `cortex_recall: "worktree {project_name}"`
- After completion: `cortex_remember` with tags ["worktree", "{project_name}", "parallel-dev"]

---

### 4.2 file-factory/SKILL.md
**Path:** `C:\Users\Tony\.claude\skills\file-factory\SKILL.md`
**Pattern:** C (Cross-Project)

**Add to workflow:**
- Before creating: `cortex_global_search: "{document_type} template"`
- After completion: `cortex_remember` with tags ["file-factory", "{output_type}", "{theme}"]

---

### 4.3 waverunner-orchestration/SKILL.md
**Path:** `C:\Users\Tony\.claude\skills\waverunner-orchestration\SKILL.md`
**Pattern:** A (Recall-Execute-Remember)

**Add to workflow:**
- Before orchestration: `cortex_recall: "waverunner {batch_type}"`
- After completion: `cortex_remember` with tags ["waverunner", "batch", "{result}"]

---

### 4.4 skill-creator/SKILL.md
**Path:** `C:\Users\Tony\.claude\skills\skill-creator\SKILL.md`
**Pattern:** C (Cross-Project)

**Add to workflow:**
- Before creation: `cortex_global_search: "skill {skill_type}"`
- After completion: `cortex_remember` with tags ["skill-creator", "{skill_name}"]

---

### 4.5 mcp-builder/SKILL.md
**Path:** `C:\Users\Tony\.claude\skills\mcp-builder\SKILL.md`
**Pattern:** C (Cross-Project)

**Add to workflow:**
- Before building: `cortex_global_search: "mcp server {capability}"`
- After completion: `cortex_remember` with tags ["mcp-builder", "{server_name}"]

---

### 4.6 video-transcript-extractor/SKILL.md
**Path:** `C:\Users\Tony\.claude\skills\video-transcript-extractor\SKILL.md`
**Pattern:** A (Recall-Execute-Remember)

**Add to workflow:**
- Before extraction: `cortex_recall: "transcript {topic}"`
- After completion: `cortex_remember` with tags ["transcript", "{video_topic}", "extraction"]

---

## Implementation Checklist

### Phase 1: High-Priority (5 commands)
- [x] build.md - Add recall/remember for build issues
- [x] prime.md - Add session context + codebase storage
- [x] test.md - Add recall/remember for test patterns
- [x] commit.md - Add commit style recall
- [x] quick-plan.md - Add cross-project plan search

### Phase 2: Supporting (7 commands)
- [x] question.md - Add Q&A storage
- [x] docs.md - Add doc pattern recall
- [x] deploy.md - Add deployment logging
- [x] migrate.md - Add migration logging
- [x] coverage.md - Add coverage tracking
- [x] clean.md - Add cleanup recall
- [x] api.md - Add API pattern search

### Phase 3: Workflow (5 commands)
- [x] analyze-history.md - COMPLETED: Full integration + date filter (8 tools, 3-phase workflow)
- [x] merge-worktrees.md - Add merge logging
- [x] orchestrate.md - Add orchestration recall
- [x] parallel_subagents.md - Add agent recall
- [x] prime_cc.md - Add CC improvement tracking

### Phase 4: Project Management (2 commands)
- [x] eisenhower.md - Add trend snapshot storage
- [x] reflect.md - COMPLETED: Cross-project activity analysis + 8-step workflow (5 tools)

### Phase 5: Skills (6 skills)
- [x] git-worktrees - Add worktree tracking
- [x] file-factory - Add template search
- [x] waverunner-orchestration - Add batch tracking
- [x] skill-creator - Add skill pattern search
- [x] mcp-builder - Add MCP pattern search
- [x] video-transcript-extractor - Add extraction storage

---

## Testing Strategy

### Per-Command Testing
1. Run command with integration
2. Verify cortex_recall is called first
3. Verify cortex_remember is called with correct tags
4. Check memory was stored: `cortex_list_memories` with tag filter

### Integration Testing
1. Run prime.md on a project
2. Close session
3. Open new session, run prime.md again
4. Verify previous priming is recalled

### Cross-Project Testing
1. Run quick-plan.md with similar feature
2. Verify cortex_global_search finds relevant plans from other projects

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Commands integrated | 18/18 (100%) |
| Skills integrated | 6/6 (100%) |
| Recall on start | All commands check previous context |
| Remember on complete | All commands store outcomes |
| Cross-project search | 5+ commands use global_search |
| Session continuity | 3+ commands use get_session_context |

---

## Rollback Plan

If issues occur:
1. Each command change is isolated - can be reverted individually
2. Git commit after each phase for easy rollback
3. Original files backed up before modification

---

## Estimated Effort

| Phase | Commands | Est. Time |
|-------|----------|-----------|
| Phase 1 | 5 | 15 min |
| Phase 2 | 7 | 20 min |
| Phase 3 | 5 | 15 min |
| Phase 4 | 1 | 5 min |
| Phase 5 | 6 | 20 min |
| Testing | All | 15 min |
| **Total** | **24** | **~90 min** |

---

## Prompt for Next Session

```
Execute the Omni Cortex integration plan at specs/omni-cortex-command-integration.md using /build.

Work through the phases in order:
1. Phase 1: High-priority commands (build, prime, test, commit, quick-plan)
2. Phase 2: Supporting commands (question, docs, deploy, migrate, coverage, clean, api)
3. Phase 3: Workflow commands (analyze-history, merge-worktrees, orchestrate, parallel_subagents, prime_cc)
4. Phase 4: Project Management (eisenhower)
5. Phase 5: Skills (git-worktrees, file-factory, waverunner-orchestration, skill-creator, mcp-builder, video-transcript-extractor)

For each file:
1. Read the current content
2. Add the Omni Cortex tools to allowed-tools
3. Add the workflow steps for cortex_recall and cortex_remember
4. Test by running the command once

Commit after each phase with message: "Integrate Omni Cortex into Phase X commands"
```
