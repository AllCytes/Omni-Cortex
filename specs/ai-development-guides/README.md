# AI Development Guides

This folder contains comprehensive documentation for understanding and using AI-powered development workflows.

## Reading Order

Read these guides in order for the best learning experience:

### 01 - Understanding Claude Code, Agent SDK, and Ecosystem
**File:** `01-understanding-claude-code-agent-sdk-ecosystem.md`

**What you'll learn:**
- Difference between Claude.ai, Claude Desktop, Claude Code, and Agent SDK
- How each product fits into the AI development ecosystem
- Comparisons with Google (Gemini CLI, ADK) and OpenAI (Agents SDK)
- Analogies to help understand the relationships
- When to use each tool

**Read this first** to understand the foundational concepts.

---

### 02 - ADW (Agentic Development Workflow) Guide
**File:** `02-adw-guide.md`

**What you'll learn:**
- How ADWs relate to the Agent SDK
- Three ways to invoke Claude autonomously (local, @claude, database-driven)
- How to run ADWs locally
- GitHub + Claude integration
- IndyDevDan's orchestrator pattern
- Environment variables and infrastructure (webhooks, tunnels, sandboxes)

**Read this second** to understand ADW architecture and usage.

---

### 03 - Phone-Anywhere ADWs and @claude GitHub Integration
**File:** `03-phone-anywhere-adws-and-github.md`

**What you'll learn:**
- How to trigger Claude from your phone
- Setting up @claude in GitHub (easy)
- Setting up E2B cloud sandboxes (powerful)
- Step-by-step setup instructions
- Example prompts and workflows
- When to use each approach

**Read this third** for practical setup instructions.

---

### 04 - @claude vs ADWs Decision Guide
**File:** `04-claude-vs-adws-decision-guide.md`

**What you'll learn:**
- Detailed pros/cons comparison with visual indicators
- Reliability and consistency ratings
- Cost analysis
- Scoring by use case
- When to use @claude vs ADWs
- The hybrid approach (recommended)
- Whether to continue building ADWs

**Read this last** to make informed decisions about your workflow.

---

## Quick Reference

| Question | See Guide |
|----------|-----------|
| "What is the Agent SDK?" | 01 |
| "How do I run an ADW?" | 02 |
| "How do I trigger from my phone?" | 03 |
| "Should I use @claude or ADWs?" | 04 |

## TL;DR Summary

- **@claude** = Easy, quick tasks, runs on GitHub's servers
- **ADWs** = Powerful, multi-phase workflows, more setup required
- **Hybrid** = Use @claude for simple tasks, ADWs for complex ones
- **Phone trigger** = @claude works immediately, ADWs need E2B or local webhook

---

*Last updated: January 2026*
