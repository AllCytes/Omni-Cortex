# ADW (Agentic Development Workflow) Guide

This guide covers how to run ADWs locally, integrate with GitHub for automation, and leverage Claude as an AI teammate.

---

## Table of Contents

1. [How ADWs Relate to Agent SDK](#how-adws-relate-to-agent-sdk)
2. [Three Ways to Invoke Claude Autonomously](#three-ways-to-invoke-claude-autonomously)
3. [Local ADW Execution](#local-adw-execution)
4. [GitHub + Claude Integration](#github--claude-integration)
5. [IndyDevDan's Orchestrator Pattern](#indydevdans-orchestrator-pattern)
6. [Recommended Approach](#recommended-approach)
7. [Example Prompts](#example-prompts)
8. [Real-World Example: tac-6 Issue #5](#real-world-example-tac-6-issue-5)

---

## How ADWs Relate to Agent SDK

### The Relationship (Analogy)

Think of it like building a car:

| Component | What It Is | Analogy |
|-----------|------------|---------|
| **Claude API** | Raw access to Claude models | The engine |
| **Agent SDK** | Framework for building autonomous agents | The chassis + transmission |
| **ADWs** | Your custom workflow orchestrators | The complete car you built |
| **Claude Code** | Interactive CLI (what you use in terminal) | Driving the car manually |

**Key Insight:** ADWs are applications you BUILD using the Agent SDK. The Agent SDK is the underlying engine.

### Code Relationship

```
Your ADW Python Scripts (adw_plan.py, adw_build.py, etc.)
         │
         ▼
┌─────────────────────────────────────────┐
│       Claude Agent SDK                   │
│  (ClaudeSDKClient, ClaudeAgentOptions)  │
│  pip install claude-agent-sdk            │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│        Claude API (Anthropic)           │
│  (Raw model access, token processing)   │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│        Claude Models                     │
│  (Sonnet, Opus, Haiku)                  │
└─────────────────────────────────────────┘
```

### What the Agent SDK Provides

The `claude-agent-sdk` package gives you:

```python
from claude_agent_sdk import (
    ClaudeSDKClient,      # Main client for running agents
    ClaudeAgentOptions,   # Configuration (model, tools, permissions)
    AssistantMessage,     # Claude's responses
    TextBlock,            # Text content blocks
    ThinkingBlock,        # Extended thinking content
    ToolUseBlock,         # Tool invocation blocks
    ResultMessage,        # Final result with usage stats
)
```

### How ADWs Use the SDK

Your ADW code (in `adws/adw_modules/agent.py`) uses the SDK like this:

```python
# 1. Configure the agent
options = ClaudeAgentOptions(
    model="claude-sonnet-4-5-20250929",
    cwd=working_dir,
    max_turns=50,
    allowed_tools=["Read", "Write", "Edit", "Bash", "Skill", ...],
    permission_mode="acceptEdits",  # Auto-approve edits
)

# 2. Run the agent
async with ClaudeSDKClient(options=options) as client:
    await client.query("Execute the /quick-plan skill with: Add dark mode")

    # 3. Process responses as they stream in
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"[Tool] {block.name}")
```

### Why This Matters

| Without Agent SDK (Old Way) | With Agent SDK (Current) |
|-----------------------------|--------------------------|
| `subprocess.run(["claude", "-p", prompt])` | `ClaudeSDKClient(options).query(prompt)` |
| Skills don't work (treated as conversation) | Skills work correctly |
| No streaming, just final output | Real-time streaming responses |
| Can't access tool invocations | Full access to TextBlock, ToolUseBlock, etc. |
| Limited control | Full control over permissions, tools, model |

---

## Three Ways to Invoke Claude Autonomously

There are three distinct approaches, each with different setup and use cases:

### Comparison Table

| Method | Where It Runs | Trigger | Best For | Setup Effort |
|--------|---------------|---------|----------|--------------|
| **Local ADWs** | Your machine | Terminal command | Complex features, visual validation | Medium |
| **@claude (GitHub)** | GitHub Actions | `@claude` in issue/PR | Quick tasks, team collaboration | Low |
| **Database-Driven ADWs** | Backend server | API call or GitHub webhook | Production automation, dashboards | High |

### Visual Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL ADWs                                    │
│  You → Terminal → uv run adws/adw_plan.py "task"               │
│        → Agent SDK → Claude → Files modified locally            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    @CLAUDE (GITHUB)                              │
│  You → Create issue → @claude in comment                        │
│        → GitHub Action → claude-code-action → Claude            │
│        → PR created, comments posted                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│               DATABASE-DRIVEN ADWs (IndyDevDan)                 │
│  GitHub Issue → Webhook → API → PostgreSQL record created       │
│        → Backend spawns ADW process → Agent SDK → Claude        │
│        → WebSocket updates → Dashboard visualization            │
│        → Bot posts status to GitHub issue                       │
└─────────────────────────────────────────────────────────────────┘
```

### When You've Used Each

1. **Local ADWs**: When you run `uv run adws/adw_plan_build_validate.py "task"` in your terminal
2. **@claude**: When you tag `@claude` in a GitHub issue and it responds/creates PRs
3. **Database-Driven**: The tac-6 example where ADW-BOT posted status updates to issues

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

## Real-World Example: tac-6 Issue #5

This example shows the **Database-Driven ADW** pattern in action from IndyDevDan's tac-6 repository.

### The GitHub Issue

**Repository:** [AllCytes/tac-6](https://github.com/AllCytes/tac-6/issues/5)
**Title:** One-Click Table Exports v3
**Goal:** Implement CSV export functionality with download buttons in the UI

### What Happened (Automated Workflow)

1. **User creates issue** (Dec 25, 2025) - Manual step describing the feature

2. **ADW-BOT activates** - Automated bot picks up the issue

3. **Planning Phase:**
   - Bot classifies issue as `/feature`
   - Creates branch: `feature-issue-5-adw-358dea9a-one-click-table-exports`
   - Generates plan: `specs/issue-5-adw-358dea9a-sdlc_planner-one-click-table-exports.md`

4. **Status Updates Posted:**
   ```
   [21:27] ADW-BOT: Planning phase started...
   [21:35] ADW-BOT: Branch created, plan generated
   [21:42] ADW-BOT: Building phase started...
   [21:58] ADW-BOT: Implementation complete, PR ready
   ```

5. **PR Created** - With all implementation, tests, screenshots

### The Technical Flow

```
GitHub Issue Created
        │
        ▼ (Webhook)
Backend API receives event
        │
        ▼
Creates ai_developer_workflows DB record
  - adw_id: UUID generated
  - workflow_type: "plan_build"
  - input_data: {prompt: issue description, working_dir: repo}
  - status: "pending"
        │
        ▼
Backend spawns subprocess:
  uv run adws/adw_plan_build.py --adw-id {uuid}
        │
        ▼
ADW fetches config from DB via adw_id
        │
        ▼ (uses Agent SDK internally)
ClaudeSDKClient runs /quick-plan skill
        │
        ▼
Plan committed, status updated in DB
        │
        ▼
ClaudeSDKClient runs /build skill
        │
        ▼
Implementation committed, PR created
        │
        ▼ (WebSocket)
Real-time updates to dashboard
        │
        ▼ (GitHub API)
Bot posts status comments to issue
```

### Key Takeaways

1. **The issue triggered automation** - You didn't run a command manually
2. **ADW-BOT is the orchestrator** - Python code using Agent SDK
3. **State persisted in PostgreSQL** - Not local JSON files
4. **Real-time visibility** - WebSocket updates to dashboard
5. **Full audit trail** - Every step logged with timestamps

### How You Did It (Your Process)

Based on the tac-6 pattern, here's what you likely did:

1. **Created the GitHub issue** with detailed requirements
2. **The webhook triggered** the ADW system (already configured)
3. **Watched the bot work** via GitHub comments or the dashboard
4. **Reviewed the PR** when complete

OR (alternate flow):

1. **Created the GitHub issue** first
2. **Ran the ADW manually** from terminal: `uv run adws/adw_plan_build.py --issue 5`
3. **The ADW connected to GitHub**, fetched the issue, processed it

---

## Summary: The Three Invocation Methods

| When You... | Method Used | What Happens |
|-------------|-------------|--------------|
| Run `uv run adws/adw_plan.py "task"` | Local ADW | Agent SDK runs on your machine |
| Tag `@claude` in GitHub issue | GitHub Actions | claude-code-action runs in GitHub runner |
| Issue webhook triggers backend | Database-Driven ADW | Backend spawns ADW, uses Agent SDK |

**They all use the Agent SDK under the hood** - the difference is WHERE they run and HOW they're triggered.

---

## Infrastructure Deep Dive: Webhooks, Tunnels, and Cloud Sandboxes

This section explains the infrastructure required for automated GitHub-triggered ADWs.

### Environment Variables Explained

From a typical `.env.sample`:

| Variable | Purpose | When Needed |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Authenticates Claude Code with Anthropic | **Always required** |
| `GITHUB_PAT` | GitHub API access (if different from `gh auth login`) | Optional |
| `CLAUDE_CODE_PATH` | Path to Claude CLI binary | Optional (defaults to `claude`) |
| `E2B_API_KEY` | Cloud sandbox for remote code execution | Only for cloud deployment |
| `CLOUDFLARED_TUNNEL_TOKEN` | Exposes local webhook to internet | Only for local webhook |
| `CLOUDFLARE_R2_*` | Screenshot storage for GitHub comments | Optional (nice for reviews) |

### Two Deployment Models

#### Model 1: Local Webhook (Your Computer Must Be On)

```
GitHub Issue Created
        │
        ▼ (webhook to public URL)
CloudFlare Tunnel (expose_webhook.sh)
        │
        ▼ (forwards to localhost:8001)
Your Computer ◄─── MUST BE RUNNING
  ├── trigger_webhook.py (FastAPI server)
  └── Claude Code (Agent SDK)
        │
        ▼
Changes pushed to GitHub
```

**Setup steps:**
1. Get CloudFlare tunnel token from CloudFlare Zero Trust dashboard
2. Run: `./scripts/expose_webhook.sh` (starts tunnel)
3. Run: `uv run adws/adw_triggers/trigger_webhook.py` (starts server)
4. Configure GitHub webhook to point to your tunnel URL + `/gh-webhook`
5. Create GitHub issue with `adw_plan_build` in body/comment

**Pros:**
- Full control over execution
- No cloud costs
- Easy to debug

**Cons:**
- Computer must be on 24/7
- Depends on your internet connection

#### Model 2: GitHub Actions + E2B (Fully Cloud)

```
GitHub Issue Created
        │
        ▼ (native GitHub event)
GitHub Actions Workflow
        │
        ▼ (creates sandbox)
E2B Cloud Sandbox
  └── Claude Code runs in cloud
        │
        ▼
Changes pushed to GitHub
```

**What E2B is:**
- E2B = "Environment to Build"
- Cloud-based code execution sandbox
- Like a temporary virtual machine
- Claude Code gets installed and runs inside it

**Example from sandbox_poc.py:**
```python
from e2b_code_interpreter import Sandbox

with Sandbox(envs={"ANTHROPIC_API_KEY": api_key}) as sandbox:
    # Runs in CLOUD, not your computer
    sandbox.commands.run("npm install -g @anthropic-ai/claude-code")
    sandbox.commands.run("claude -p 'Hello' < /dev/null")
```

**Pros:**
- Computer doesn't need to be on
- Can trigger from phone anywhere
- More reliable for production

**Cons:**
- E2B costs money
- More complex setup
- Debugging is harder

### CloudFlare R2 (Screenshot Storage)

When ADW runs the `/review` phase, it takes screenshots. CloudFlare R2:
- Stores screenshots in cloud storage
- Provides public URLs for images
- GitHub comments can display the screenshots inline

Without R2, screenshots show as local file paths (not viewable in GitHub).

### "Can I Create Issues From My Phone?"

| Deployment | Phone Trigger? | Requirements |
|------------|----------------|--------------|
| Local Webhook | Yes, BUT... | Computer on + tunnel running + webhook running |
| GitHub Actions + E2B | Yes, truly | GitHub Action configured + E2B API key |
| GitHub @claude | Yes, truly | GitHub Action configured (no E2B needed) |

**Simplest "phone anywhere" option:** Use `@claude` in GitHub issues. This uses GitHub Actions (runs on GitHub's servers), not your computer.

---

## Resources

- [Claude Code Action (GitHub)](https://github.com/anthropics/claude-code-action)
- [Claude Code Docs](https://code.claude.com/docs)
- [Claude Agent SDK (npm)](https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk)
- [Claude Agent SDK (Python)](https://github.com/anthropics/claude-agent-sdk-python)
- [IndyDevDan TAC Repositories](https://github.com/indydevdan) - Orchestrator patterns
- [Claude Code GitHub Marketplace](https://github.com/marketplace/actions/claude-code-action-official)
- [Anthropic: Building Agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)

---

*Last updated: January 2026*
