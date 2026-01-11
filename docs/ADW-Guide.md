# ADW (Agentic Development Workflow) Guide

This guide covers how to run ADWs locally, integrate with GitHub for automation, and leverage Claude as an AI teammate.

---

## Table of Contents

1. [Local ADW Execution](#local-adw-execution)
2. [GitHub + Claude Integration](#github--claude-integration)
3. [IndyDevDan's Orchestrator Pattern](#indydevdans-orchestrator-pattern)
4. [Recommended Approach](#recommended-approach)
5. [Example Prompts](#example-prompts)

---

## Local ADW Execution

### Quick Start

Run the plan-build-validate workflow:

```bash
# Using uv (recommended)
uv run adws/adw_plan_build_validate.py "Your task description"

# Using Python directly
python adws/adw_plan_build_validate.py "Your task description"
```

### Available Workflows

| Workflow | Command | Description |
|----------|---------|-------------|
| Plan Only | `uv run adws/adw_plan.py "task"` | Creates spec via /quick-plan |
| Build Only | `uv run adws/adw_build.py <adw_id>` | Implements from existing spec |
| Validate Only | `uv run adws/adw_validate.py <adw_id>` | Visual validation with screenshots |
| Plan → Build → Validate | `uv run adws/adw_plan_build_validate.py "task"` | Full workflow |

### How It Works

1. **Each phase runs Claude Code as a subprocess** (separate terminal session)
2. **State persists in** `agents/{adw_id}/adw_state.json`
3. **Output saved as JSONL** in `agents/{adw_id}/{phase}/`
4. **Phases run sequentially** - each must complete before the next starts

### Directory Structure

```
agents/
└── adw_1736545200_a1b2c3d4/
    ├── adw_state.json           # Workflow state
    ├── plan/
    │   └── quick_plan_output.jsonl
    ├── build/
    │   └── build_output.jsonl
    └── validate/
        ├── validate_output.jsonl
        └── screenshots/
            └── *.png
```

### Example Usage

```bash
# Fix a bug
uv run adws/adw_plan_build_validate.py "Fix dashboard stats not showing command/skill usage data"

# Add a feature
uv run adws/adw_plan_build_validate.py "Add dark mode toggle to settings page"

# Refactor code
uv run adws/adw_plan_build_validate.py "Refactor authentication module to use JWT tokens"
```

---

## GitHub + Claude Integration

### What It Does

- **Tag @claude in any issue or PR** and Claude will respond
- **Automatically creates PRs** for implementation tasks
- **Reviews code** and suggests improvements
- **Implements features** directly from issue descriptions

### Setup (One Command)

```bash
# Run in your terminal
claude
/install-github-app
```

This will:
- Guide you through GitHub app installation
- Set up required secrets automatically
- Configure repository authentication

### Requirements

- Repository admin access
- `ANTHROPIC_API_KEY` in repository secrets

### Manual Setup (Alternative)

1. **Create workflow file** `.github/workflows/claude.yml`:

```yaml
name: Claude Code Action

on:
  issue_comment:
    types: [created, edited]
  pull_request_review_comment:
    types: [created, edited]
  issues:
    types: [opened, assigned]
  pull_request:
    types: [opened, synchronize]

jobs:
  claude:
    if: |
      github.event_name == 'issues' ||
      github.event_name == 'pull_request' ||
      contains(github.event.comment.body, '@claude')
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          claude_args: |
            {
              "model": "claude-sonnet-4-20250514"
            }
```

2. **Add secret** in GitHub: Settings → Secrets → Actions → `ANTHROPIC_API_KEY`

### How to Use

#### Ask Questions in Issues

```markdown
@claude What is the best way to implement caching in this codebase?
```

#### Request Implementation

```markdown
@claude Please implement a user authentication system with JWT tokens.
Include:
- Login/logout endpoints
- Token refresh mechanism
- Protected route middleware
```

#### Code Review

```markdown
@claude Review this PR for:
- Security vulnerabilities
- Performance issues
- Best practices compliance
```

#### Fix Issues

```markdown
@claude Fix the bug described in this issue and create a PR with the solution.
```

### Trigger Modes

| Trigger | What Happens |
|---------|--------------|
| `@claude` in issue comment | Claude responds with analysis/guidance |
| `@claude` in PR comment | Claude reviews code or implements changes |
| Issue assigned to bot | Claude auto-executes the issue description |
| PR opened | Can auto-run code review if configured |

---

## IndyDevDan's Orchestrator Pattern

IndyDevDan's approach uses a **database-driven orchestrator** with PostgreSQL, WebSockets, and a visual dashboard.

### Architecture

```
User Request
    → API creates ai_developer_workflows record (UUID)
    → Backend spawns: uv run adws/adw_{type}.py --adw-id {uuid}
    → Workflow fetches config from DB via adw_id
    → Real-time updates via WebSocket
    → UI shows swimlane visualization
```

### Key Differences from Simple ADWs

| Feature | Simple ADWs | IndyDevDan Pattern |
|---------|-------------|-------------------|
| State Storage | JSON files | PostgreSQL |
| Real-time Updates | Console output | WebSocket broadcasts |
| Visualization | None | Swimlane dashboard |
| Triggering | CLI only | API + CLI + GitHub |
| Scaling | Sequential | Parallel via workers |

### Workflow Types (Composable)

1. **plan_build** (2 steps): `/plan` → `/build`
2. **plan_build_review** (3 steps): `/plan` → `/build` → `/review`
3. **plan_build_review_fix** (4 steps): `/plan` → `/build` → `/review` → `/fix`

### GitHub Integration Pattern

From his `tac-5` implementation:

```python
# adw_plan.py fetches issue, classifies, creates branch, generates plan
# adw_build.py picks up from state file, implements, creates PR

class ADWState:
    # Persists to .adw_state/{adw_id}.json
    issue_number: int
    branch_name: str
    plan_file: str
    issue_class: str  # bug, feature, refactor
    pr_url: str
```

This allows **handoff between phases** - `adw_plan.py` creates state, `adw_build.py` resumes from it.

---

## Recommended Approach

### For Quick Tasks: GitHub @claude

**Best for:**
- Bug fixes
- Small features
- Code reviews
- Quick questions

**How:**
```markdown
@claude Fix the login button not working on mobile.
Create a PR with the fix.
```

### For Complex Features: Local ADWs

**Best for:**
- Multi-file implementations
- Features requiring visual validation
- Work that needs iteration

**How:**
```bash
uv run adws/adw_plan_build_validate.py "Implement user dashboard with analytics charts"
```

### For Team Workflows: GitHub + ADWs Combined

**Pattern 1: Issue-Triggered ADW**

1. Create detailed GitHub issue
2. Tag `@claude` with ADW instruction:

```markdown
@claude Run the plan-build-validate workflow for this issue:

1. Create a detailed implementation plan
2. Implement all items in the plan
3. Validate with visual testing
4. Create a PR with the changes

Use the /quick-plan command first, then /build, then /validate.
```

**Pattern 2: Batch Processing**

```markdown
@claude For each of the following features, create separate branches and PRs:

1. Add dark mode toggle
2. Implement search functionality
3. Add export to CSV feature

Tag @claude in each PR for implementation.
```

### My Recommendation

**Start with GitHub @claude** for these reasons:

1. **Lowest friction** - just tag @claude in an issue
2. **Runs in background** - check back when done
3. **Creates PRs automatically** - easy to review and merge
4. **Parallel execution** - run multiple tasks simultaneously
5. **No local resources needed** - runs on GitHub's infrastructure

**Use local ADWs when:**
- You need visual validation (Chrome MCP screenshots)
- You want detailed JSONL logs for debugging
- You're iterating on a complex feature
- You need to watch execution in real-time

---

## Example Prompts

### Simple Bug Fix (GitHub Issue)

```markdown
# Issue Title: Login button doesn't work on Safari

@claude Please investigate and fix this bug:

**Steps to reproduce:**
1. Open the app in Safari
2. Click the login button
3. Nothing happens

**Expected behavior:**
Login modal should appear

Please create a PR with the fix.
```

### Feature Implementation (GitHub Issue)

```markdown
# Issue Title: Add user profile page

@claude Implement a user profile page with the following requirements:

**Features:**
- Display user avatar, name, email
- Show account creation date
- Allow editing display name
- Add profile picture upload

**Technical requirements:**
- Use existing auth system
- Store images in S3
- Add appropriate API endpoints

Create a detailed plan first, then implement and create a PR.
```

### Code Review (PR Comment)

```markdown
@claude Please review this PR for:

1. **Security**: Any vulnerabilities or unsafe practices
2. **Performance**: N+1 queries, unnecessary re-renders
3. **Best Practices**: Code style, naming, architecture
4. **Testing**: Are there adequate tests?

Provide specific line-by-line feedback.
```

### ADW-Style Workflow (GitHub Issue)

```markdown
# Issue Title: Implement analytics dashboard

@claude Execute this as a multi-phase workflow:

## Phase 1: Plan
- Analyze the codebase for existing patterns
- Create detailed spec in `specs/analytics-dashboard.md`
- Include component structure, API endpoints, data models

## Phase 2: Build
- Implement all items from the spec
- Follow existing code conventions
- Add unit tests for new components

## Phase 3: Review
- Self-review the implementation against the spec
- Check for security issues, performance problems
- List any items that weren't fully implemented

## Phase 4: Fix
- Address any issues found in review
- Ensure all spec items are complete

Create a PR when all phases are complete.
```

### Batch Implementation (GitHub Issue)

```markdown
@claude I need you to implement these 5 features as separate PRs:

1. **Dark mode**: Add theme toggle in settings
2. **Export CSV**: Allow exporting data tables
3. **Keyboard shortcuts**: Add common shortcuts (Cmd+K, etc.)
4. **Search**: Global search across all entities
5. **Notifications**: In-app notification system

For each feature:
1. Create a branch: `feature/{name}`
2. Implement the feature
3. Create a PR with description
4. Tag @claude in the PR for final review

Start with feature 1 and proceed sequentially.
```

---

## Troubleshooting

### Claude Not Responding in GitHub

1. **Check app installation**: Settings → GitHub Apps → Verify Claude is installed
2. **Check workflows**: Actions tab → Ensure workflows are enabled
3. **Check secrets**: Settings → Secrets → Verify `ANTHROPIC_API_KEY` exists
4. **Syntax**: Use `@claude` (not `/claude` or `claude`)

### Local ADW Failures

```bash
# Check the state file
cat agents/{adw_id}/adw_state.json

# Check the output logs
cat agents/{adw_id}/{phase}/*_output.jsonl

# Re-run a specific phase
uv run adws/adw_build.py {adw_id}
```

---

## Resources

- [Claude Code Action (GitHub)](https://github.com/anthropics/claude-code-action)
- [Claude Code Docs](https://code.claude.com/docs)
- [IndyDevDan TAC Repositories](https://github.com/indydevdan) - Orchestrator patterns
- [Claude Code GitHub Marketplace](https://github.com/marketplace/actions/claude-code-action-official)

---

*Last updated: January 2026*
