# Phone-Anywhere ADWs: E2B Cloud Setup & @claude GitHub Integration

> A complete guide to triggering autonomous AI development from anywhere - your phone, tablet, or any device with internet access.

## Table of Contents

1. [Overview: Three Approaches Compared](#overview-three-approaches-compared)
2. [Option 1: @claude in GitHub (Easiest)](#option-1-claude-in-github-easiest)
3. [Option 2: E2B Cloud Sandbox (Most Powerful)](#option-2-e2b-cloud-sandbox-most-powerful)
4. [Option 3: IndyDevDan's Local Webhook (Reference)](#option-3-indydevdans-local-webhook-reference)
5. [When to Use Each Approach](#when-to-use-each-approach)
6. [Practical Examples](#practical-examples)
7. [Sources](#sources)

---

## Overview: Three Approaches Compared

| Approach | Computer Required? | Setup Complexity | Best For |
|----------|-------------------|------------------|----------|
| **@claude in GitHub** | No | Low | Quick tasks, reviews, simple features |
| **E2B Cloud Sandbox** | No | High | Full ADW workflows, complex automation |
| **Local Webhook** | Yes (must be on) | Medium | Development, debugging, full control |

### Visual Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     @CLAUDE IN GITHUB (EASIEST)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  📱 Phone → GitHub Issue → "@claude fix this bug"                           │
│                    │                                                        │
│                    ▼                                                        │
│            GitHub Actions Runner (GitHub's servers)                         │
│                    │                                                        │
│                    ▼                                                        │
│            Claude Code runs → Creates PR                                    │
│                                                                             │
│  ✅ No computer needed                                                      │
│  ✅ Easy setup                                                              │
│  ⚠️  Limited to what GitHub Actions can do                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                     E2B CLOUD SANDBOX (MOST POWERFUL)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  📱 Phone → GitHub Issue → Triggers GitHub Action                           │
│                    │                                                        │
│                    ▼                                                        │
│            GitHub Action creates E2B Sandbox                                │
│                    │                                                        │
│                    ▼                                                        │
│            Full VM in cloud with Claude Code                                │
│            - Can run any command                                            │
│            - Full filesystem access                                         │
│            - Browser automation possible                                    │
│                    │                                                        │
│                    ▼                                                        │
│            Complete ADW workflow → Creates PR                               │
│                                                                             │
│  ✅ No computer needed                                                      │
│  ✅ Full power of ADWs                                                      │
│  ⚠️  E2B costs money                                                        │
│  ⚠️  More complex setup                                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                     LOCAL WEBHOOK (INDYDEVDAN)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  📱 Phone → GitHub Issue → Webhook via CloudFlare Tunnel                    │
│                    │                                                        │
│                    ▼                                                        │
│            Your Computer (MUST BE ON)                                       │
│            - trigger_webhook.py                                             │
│            - Claude Code local                                              │
│            - Full ADW workflow                                              │
│                    │                                                        │
│                    ▼                                                        │
│            Creates PR, posts status                                         │
│                                                                             │
│  ⚠️  Computer must be running                                               │
│  ✅ Free (no cloud costs)                                                   │
│  ✅ Full control and debugging                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Option 1: @claude in GitHub (Easiest)

This is the **simplest way** to trigger Claude from your phone. It uses GitHub Actions, which run on GitHub's servers - no computer required.

### Step 1: Install the GitHub App

Open Claude Code in your terminal and run:

```bash
claude
/install-github-app
```

This guided setup:
- Installs the Claude GitHub App
- Configures required secrets (`ANTHROPIC_API_KEY`)
- Creates the workflow file

### Step 2: Manual Setup (Alternative)

If you prefer manual setup:

**2a. Create workflow file** `.github/workflows/claude.yml`:

```yaml
name: Claude Code

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
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
```

**2b. Add secret**: Go to Settings → Secrets → Actions → Add `ANTHROPIC_API_KEY`

### Step 3: Use It From Your Phone

Now you can create issues or comments from anywhere:

```markdown
@claude Please fix the login button that's not working on mobile.
Create a PR with the fix.
```

Claude will:
1. Analyze the codebase
2. Implement a fix
3. Create a PR
4. Comment with what it did

### Effective @claude Prompts

#### Simple Bug Fix
```markdown
@claude The submit button on the contact form doesn't work.
Debug and fix it, then create a PR.
```

#### Feature Implementation
```markdown
@claude Implement a dark mode toggle in the settings page.

Requirements:
- Add toggle switch to settings
- Store preference in localStorage
- Apply theme on page load

Create a PR when done.
```

#### Code Review
```markdown
@claude Review this PR for:
1. Security vulnerabilities
2. Performance issues
3. Best practices violations

Provide specific line-by-line feedback.
```

#### ADW-Style Workflow
```markdown
@claude Execute this as a multi-phase workflow:

## Phase 1: Plan
- Analyze the codebase
- Create a spec file at specs/feature-name.md
- Include component structure, API changes, and tests needed

## Phase 2: Build
- Implement according to the spec
- Add unit tests
- Ensure all tests pass

## Phase 3: Review
- Self-review against the spec
- List any issues found

Create a PR when complete.
```

### Advanced Configuration

#### Custom Model and Settings
```yaml
- uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    claude_args: |
      {
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 16000,
        "thinking": {
          "type": "enabled",
          "budget_tokens": 5000
        }
      }
```

#### Restrict Tools for Security
```yaml
- uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    claude_args: '--allowed-tools "Read,Write,Edit,Bash(git:*),Bash(npm test:*)"'
```

#### Path-Specific Triggers
```yaml
on:
  pull_request:
    paths:
      - 'src/security/**'
      - 'src/auth/**'
```

---

## Option 2: E2B Cloud Sandbox (Most Powerful)

E2B provides cloud-based sandboxes where Claude Code can run with full system access - just like on your local machine, but in the cloud.

### What is E2B?

- **E2B = "Environment to Build"**
- Cloud-based code execution sandboxes
- Like a temporary virtual machine
- Full filesystem, network, and command access
- Supports browser automation, database access, etc.

### Step 1: Get E2B API Key

1. Go to [e2b.dev](https://e2b.dev)
2. Sign up for an account
3. Get your API key from the dashboard
4. Add it to your GitHub secrets as `E2B_API_KEY`

### Step 2: Create GitHub Workflow

Create `.github/workflows/adw-e2b.yml`:

```yaml
name: ADW via E2B Cloud

on:
  issues:
    types: [opened]
  issue_comment:
    types: [created]

jobs:
  run-adw:
    # Only run if issue body or comment contains "adw_"
    if: |
      contains(github.event.issue.body, 'adw_') ||
      contains(github.event.comment.body, 'adw_')
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install e2b-code-interpreter anthropic

      - name: Run ADW in E2B Sandbox
        env:
          E2B_API_KEY: ${{ secrets.E2B_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          ISSUE_BODY: ${{ github.event.issue.body }}
          REPO_NAME: ${{ github.repository }}
        run: python .github/scripts/run_adw_e2b.py
```

### Step 3: Create the E2B Runner Script

Create `.github/scripts/run_adw_e2b.py`:

```python
#!/usr/bin/env python3
"""
Run ADW workflow in E2B cloud sandbox.
Triggered by GitHub Actions when issue contains 'adw_'.
"""

import os
import json
from e2b_code_interpreter import Sandbox

# Get environment variables
e2b_api_key = os.environ["E2B_API_KEY"]
anthropic_api_key = os.environ["ANTHROPIC_API_KEY"]
github_token = os.environ["GITHUB_TOKEN"]
issue_number = os.environ["ISSUE_NUMBER"]
issue_body = os.environ["ISSUE_BODY"]
repo_name = os.environ["REPO_NAME"]

print(f"🚀 Starting E2B sandbox for issue #{issue_number}")
print(f"📋 Repository: {repo_name}")

# Extract workflow type from issue body
workflow = "adw_plan_build"  # default
if "adw_sdlc" in issue_body.lower():
    workflow = "adw_sdlc"
elif "adw_plan_build_review" in issue_body.lower():
    workflow = "adw_plan_build_review"
elif "adw_plan_build_test" in issue_body.lower():
    workflow = "adw_plan_build_test"

print(f"🔧 Detected workflow: {workflow}")

# Create sandbox with required environment variables
with Sandbox(
    api_key=e2b_api_key,
    envs={
        "ANTHROPIC_API_KEY": anthropic_api_key,
        "GITHUB_TOKEN": github_token,
        "GH_TOKEN": github_token,
    },
    timeout=600,  # 10 minute timeout
) as sandbox:
    print(f"✅ Sandbox created: {sandbox.sandbox_id}")

    # Install required tools
    print("📦 Installing Claude Code and GitHub CLI...")
    sandbox.commands.run("npm config set prefix ~/.npm-global", timeout=30000)
    sandbox.commands.run(
        "npm install -g @anthropic-ai/claude-code",
        timeout=120000
    )
    sandbox.commands.run(
        "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg",
        timeout=30000
    )
    sandbox.commands.run(
        'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null',
        timeout=30000
    )
    sandbox.commands.run("sudo apt update && sudo apt install gh -y", timeout=120000)

    # Clone the repository
    print(f"📥 Cloning {repo_name}...")
    sandbox.commands.run(
        f"gh repo clone {repo_name} /workspace",
        timeout=60000
    )

    # Run the ADW workflow
    print(f"🤖 Running {workflow}...")

    # Build the Claude prompt
    prompt = f"""You are running an automated ADW workflow for GitHub issue #{issue_number}.

Issue body:
{issue_body}

Execute the /{workflow.replace('adw_', '')} workflow:
1. Analyze the issue requirements
2. Create an implementation plan
3. Implement the solution
4. Commit changes
5. Create a pull request

Use `gh` CLI to interact with GitHub.
Working directory: /workspace
"""

    # Run Claude Code with the workflow
    result = sandbox.commands.run(
        f"cd /workspace && ~/.npm-global/bin/claude -p '{prompt}' --dangerously-skip-permissions < /dev/null",
        timeout=300000  # 5 minute timeout for Claude
    )

    print("📤 Claude Output:")
    print(result.stdout)

    if result.stderr:
        print("⚠️ Errors:")
        print(result.stderr)

    print(f"✅ Workflow complete for issue #{issue_number}")
```

### Step 4: Use From Your Phone

Create a GitHub issue with:

```markdown
# Add user analytics dashboard

adw_plan_build

## Requirements
- Track page views per user
- Show daily/weekly/monthly charts
- Export data as CSV
- Mobile responsive design

## Technical Notes
- Use Chart.js for visualization
- Store data in existing PostgreSQL
- Add new API endpoints under /api/analytics/
```

The E2B sandbox will:
1. Spin up a cloud VM
2. Clone your repo
3. Install Claude Code
4. Run the full ADW workflow
5. Create a PR with the implementation

### E2B Pricing

| Tier | Sandbox Hours | Price |
|------|---------------|-------|
| Free | 100 hours/month | $0 |
| Pro | 1000 hours/month | $50/month |
| Enterprise | Unlimited | Custom |

Each ADW run typically takes 5-15 minutes, so the free tier covers ~400-1200 runs/month.

---

## Option 3: IndyDevDan's Local Webhook (Reference)

This is what you used for tac-6 issue #5. Included here for comparison.

### Architecture

```
GitHub Issue → CloudFlare Tunnel → Your Computer → Claude Code
```

### Setup Requirements

1. **CloudFlare Tunnel Token** from [CloudFlare Zero Trust](https://one.dash.cloudflare.com/)
2. **trigger_webhook.py** running on your computer
3. **expose_webhook.sh** running CloudFlare tunnel

### Start the Services

```bash
# Terminal 1: Start webhook server
cd adws/
uv run adw_triggers/trigger_webhook.py

# Terminal 2: Start CloudFlare tunnel
./scripts/expose_webhook.sh
```

### Configure GitHub Webhook

1. Go to repo Settings → Webhooks
2. Add webhook:
   - Payload URL: `https://your-tunnel-url.trycloudflare.com/gh-webhook`
   - Content type: `application/json`
   - Events: Issues, Issue comments

### Trigger Patterns

In your GitHub issue:
```markdown
adw_plan_build

Implement a user settings page with profile editing.
```

---

## When to Use Each Approach

### Decision Matrix

| Scenario | Best Approach | Why |
|----------|---------------|-----|
| Quick bug fix from phone | @claude | Fast, simple, no setup |
| Simple feature from phone | @claude | Direct implementation |
| Complex multi-phase workflow | E2B | Full ADW power in cloud |
| Need browser automation | E2B | Sandbox has full system access |
| Debugging ADW issues | Local Webhook | Full control, real-time logs |
| No budget for cloud | Local Webhook | Free, but needs computer |
| Production automation | E2B or @claude | Reliable, no hardware dependency |

### Feature Comparison

| Feature | @claude | E2B | Local Webhook |
|---------|---------|-----|---------------|
| Phone trigger | ✅ | ✅ | ✅ (if computer on) |
| Computer required | ❌ | ❌ | ✅ |
| Full ADW phases | ⚠️ Limited | ✅ | ✅ |
| Browser automation | ❌ | ✅ | ✅ |
| Custom skills | ⚠️ Via prompt | ✅ | ✅ |
| Real-time logs | ❌ | ❌ | ✅ |
| Free tier | ✅ (API only) | ✅ (100 hrs) | ✅ |
| Setup complexity | Low | High | Medium |

---

## Practical Examples

### Example 1: Bug Fix from Phone (@claude)

You're at lunch and get a bug report. Open GitHub on your phone:

```markdown
@claude The login form shows "undefined" error when email is empty.

Debug the issue in src/components/LoginForm.tsx and fix it.
Add a test case to prevent regression.
Create a PR with the fix.
```

**Result:** PR created in ~5 minutes, reviewable when you're back at your desk.

### Example 2: Feature Implementation (E2B)

You want a full feature built while you sleep:

```markdown
# Implement email notification system

adw_sdlc

## Requirements
- Send welcome email on signup
- Send password reset emails
- Daily digest of activity
- Unsubscribe functionality

## Technical
- Use SendGrid API
- Store preferences in user settings
- Queue emails with background worker
```

**Result:** Full implementation with tests, review, and documentation by morning.

### Example 3: Code Review (Simple @claude)

Quick PR review:

```markdown
@claude Review this PR focusing on:
1. SQL injection vulnerabilities
2. Missing input validation
3. Performance issues with database queries

Provide specific line comments.
```

### Example 4: Scheduled Maintenance (@claude Workflow)

Create a scheduled workflow for weekly code quality:

```yaml
# .github/workflows/weekly-review.yml
name: Weekly Code Quality

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday 9am

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Perform a weekly code quality review:
            1. Check for TODO comments that should be addressed
            2. Identify functions over 100 lines that need refactoring
            3. Find unused imports and dead code
            4. Check for outdated dependencies

            Create an issue summarizing findings with priority levels.
```

---

## Comparison: @claude vs IndyDevDan ADWs

| Aspect | @claude GitHub | IndyDevDan ADWs |
|--------|----------------|-----------------|
| **Architecture** | Single GitHub Action | Multi-phase orchestrator |
| **State Management** | Stateless per run | Persistent state files |
| **Phases** | All in one prompt | Separate plan/build/test/review/document |
| **Customization** | Via prompt engineering | Via Python scripts |
| **Workflow Types** | Whatever you prompt | Predefined: adw_plan_build, adw_sdlc, etc. |
| **GitHub Integration** | Native (GitHub Action) | Via gh CLI + webhooks |
| **Skill Support** | Via SKILL.md files | Via .claude/commands/ |
| **Debugging** | GitHub Actions logs | Local logs + JSONL files |
| **Best For** | Quick tasks, reviews | Complex multi-step workflows |

### When IndyDevDan's Approach Wins

1. **Complex orchestration** - Need 5+ phases with handoffs
2. **Custom state** - Track data between phases
3. **Browser testing** - E2E tests with Playwright
4. **Screenshot reviews** - Visual validation with images
5. **Debugging** - Need detailed JSONL logs

### When @claude Wins

1. **Quick fixes** - Simple bugs, small features
2. **Code reviews** - Fast PR feedback
3. **No setup** - Works immediately
4. **Reliability** - GitHub's infrastructure
5. **Team use** - Everyone can trigger easily

---

## Sources

### E2B
- [E2B Official Site](https://e2b.dev/)
- [E2B Documentation](https://e2b.dev/docs)
- [E2B GitHub](https://github.com/e2b-dev/E2B)
- [E2B Code Interpreter](https://github.com/e2b-dev/code-interpreter)

### Claude Code Action
- [claude-code-action GitHub](https://github.com/anthropics/claude-code-action)
- [Claude Code GitHub Actions Docs](https://code.claude.com/docs/en/github-actions)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)

### Community Resources
- [Awesome Claude Code](https://github.com/hesreallyhim/awesome-claude-code)
- [Claude Code Showcase](https://github.com/ChrisWiles/claude-code-showcase)
- [Claude Code Guide](https://github.com/zebbern/claude-code-guide)

---

*Document created: January 2026*
*For: Phone-anywhere autonomous development workflows*
