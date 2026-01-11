# Understanding Claude Code, Agent SDK, and the AI Developer Ecosystem

> A comprehensive guide comparing Claude Code, the Claude Agent SDK, and similar tools from Google and OpenAI.

## Table of Contents
1. [The Big Picture: An Analogy](#the-big-picture-an-analogy)
2. [Claude Ecosystem Breakdown](#claude-ecosystem-breakdown)
3. [Comparison Tables](#comparison-tables)
4. [Google Gemini Ecosystem](#google-gemini-ecosystem)
5. [OpenAI Ecosystem](#openai-ecosystem)
6. [When to Use What](#when-to-use-what)
7. [Timeline of Releases](#timeline-of-releases)
8. [Sources](#sources)

---

## The Big Picture: An Analogy

Think of it like different ways to get a car:

| Product | Analogy | What You Do |
|---------|---------|-------------|
| **Claude.ai (Chat)** | Taking an Uber | You tell the driver where to go, they handle everything. Convenient but you have limited control. |
| **Claude Desktop** | Renting a car with GPS | You're driving, but you get turn-by-turn guidance. More control, still user-friendly. |
| **Claude Code (CLI)** | Having a skilled co-pilot mechanic | They can drive, navigate, AND fix the engine while moving. You're both in the car together. |
| **Claude Agent SDK** | Building your own self-driving car fleet | You design the cars, program their routes, and deploy them. They run 24/7 without you in the car. |

Another way to think about it:

| Product | Restaurant Analogy |
|---------|-------------------|
| **Claude.ai Chat** | Ordering food from a menu - you pick what you want, chef makes it |
| **Claude Desktop** | Cooking with a personal chef beside you - collaborative, you're involved |
| **Claude Code** | The chef works in YOUR kitchen, using YOUR ingredients, with YOUR recipes |
| **Agent SDK** | You BUILD the restaurant and hire AI chefs that work autonomously |

---

## Claude Ecosystem Breakdown

### 1. Claude.ai (Web Chat Interface)

**What it is:** The web-based chat interface at claude.ai

**How you access it:** Browser at https://claude.ai

**Best for:**
- General questions and conversations
- Writing assistance
- Quick code snippets
- Learning and exploration
- People who don't need file/system access

**Limitations:**
- No direct access to your files
- No command execution
- No persistent memory across sessions (unless using Projects)
- Limited context (copy/paste only)

---

### 2. Claude Desktop App

**What it is:** A native desktop application for macOS/Windows

**How you access it:** Download from Anthropic, runs as a desktop app

**Best for:**
- Extended conversations with better UX than browser
- MCP (Model Context Protocol) integrations
- File attachments and document analysis
- Users who prefer a dedicated app over browser

**Key Features:**
- Native app experience
- MCP support for connecting external tools
- Better file handling
- Projects for persistent context

**vs Claude.ai Chat:**
- Same underlying model
- Better desktop integration
- MCP support for extensibility

---

### 3. Claude Code (CLI)

**What it is:** An interactive command-line tool you run in your terminal

**Released:** Early 2025, major updates throughout the year

**How you access it:** `npm install -g @anthropic-ai/claude-code` then run `claude`

**Best for:**
- Software development
- Working with existing codebases
- File editing and code generation
- Running commands and tests
- Anyone comfortable with terminals

**Key Features:**
- **Direct file access:** Reads/writes files in your project
- **Command execution:** Runs bash commands, tests, builds
- **Codebase understanding:** Understands your entire project context
- **Tool ecosystem:** Glob, Grep, Read, Edit, Write, Bash, etc.
- **MCP integration:** Connect external tools and services
- **Skills/Hooks:** Extensible with custom commands
- **Human-in-the-loop:** You approve changes before they happen

**The Experience:**
```
You: "Fix the bug in the authentication module"
Claude Code: *reads files* *understands context* *proposes fix*
You: "Yes, apply that"
Claude Code: *edits file* *runs tests* "Done, tests pass"
```

**Cost Model:** Pay-per-use based on tokens (API usage)

---

### 4. Claude Agent SDK

**What it is:** A programmatic framework for building autonomous AI agents

**Released:** September 29, 2025 (alongside Claude Sonnet 4.5)

**How you access it:**
- Python: `pip install claude-agent-sdk`
- TypeScript/Node: `npm install @anthropic-ai/claude-agent-sdk`

**Best for:**
- Building autonomous applications
- CI/CD automation (auto-review PRs, run tests)
- Background workers and services
- Multi-agent orchestration
- Production deployments

**Key Difference from Claude Code:**
- **Claude Code:** Interactive, you're in the loop
- **Agent SDK:** Programmatic, runs without you

**Example Use Cases:**
- Nightly code review bot
- Automated documentation generator
- Customer support agent
- Research assistant that runs in background
- CI pipeline that auto-fixes failing tests

**Code Example:**
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

options = ClaudeAgentOptions(
    system_prompt="You are a code reviewer...",
    model='claude-sonnet-4-5-20250929',
    allowed_tools=['Read', 'Write', 'Bash'],
    permission_mode='acceptEdits',
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Review all Python files for security issues")
    async for message in client.receive_response():
        print(message)  # Agent works autonomously
```

**Why It Was Renamed:**
Originally called "Claude Code SDK" - but Anthropic realized the engine was so robust they used it for non-coding tasks: research, data synthesis, knowledge management, video/image creation. So they renamed it to "Agent SDK" to reflect its broader purpose.

---

### 5. Claude API (Raw)

**What it is:** The underlying REST API for Claude models

**How you access it:** Direct HTTP calls or via `anthropic` Python/TS package

**Best for:**
- Building custom applications
- Integration into existing systems
- When you need full control over the interaction
- Embedding Claude in products

**Relationship to Agent SDK:**
- API = raw model access
- Agent SDK = higher-level framework that uses the API + adds tools, hooks, sessions

---

## Comparison Tables

### Claude Products At a Glance

| Feature | Claude.ai | Desktop | Claude Code | Agent SDK |
|---------|-----------|---------|-------------|-----------|
| **Interface** | Browser | Desktop App | Terminal (CLI) | Code/API |
| **Interaction** | Chat | Chat | Interactive CLI | Programmatic |
| **File Access** | Upload only | MCP | Direct | Direct |
| **Command Execution** | No | Via MCP | Yes | Yes |
| **Human Approval** | N/A | N/A | Yes (default) | Optional |
| **Autonomous Operation** | No | No | No | Yes |
| **Best For** | General use | Power users | Developers | Automation |
| **Cost** | Subscription | Subscription | API usage | API usage |
| **Learning Curve** | Low | Low | Medium | High |

### Interactive vs Autonomous

| Aspect | Claude Code | Agent SDK |
|--------|-------------|-----------|
| **You're present?** | Yes, in terminal | No, runs in background |
| **Approval required?** | Yes, you review changes | Optional, can be fully autonomous |
| **Session type** | Interactive conversation | Programmatic execution |
| **Deployment** | Your terminal | CI/CD, Lambda, Docker, services |
| **State management** | Single conversation | Multi-turn with checkpointing |
| **Use case** | "Help me code this" | "Run this every night" |

---

## Google Gemini Ecosystem

### How Google's Stack Compares

| Anthropic | Google Equivalent | Notes |
|-----------|-------------------|-------|
| Claude.ai | Gemini (gemini.google.com) | Web chat interface |
| Claude Desktop | Gemini app (mobile/desktop) | Native apps |
| Claude Code | **Gemini CLI** | Terminal-based, open source |
| Agent SDK | **Agent Development Kit (ADK)** | Framework for building agents |
| MCP | MCP (Gemini CLI supports it) | Same protocol! |

### Gemini CLI

**Released:** June 2025

**What it is:** Open-source AI agent in your terminal

**Key Features:**
- Free tier: 60 requests/min, 1000/day with personal Google account
- Access to Gemini 2.5 Pro with 1M token context
- ReAct (reason and act) loop for complex tasks
- MCP support for external tools
- GUI-like rendering in terminal (Oct 2025 update)

**Similarity to Claude Code:**
- Both are terminal-based
- Both can read/write files, run commands
- Both support MCP
- Both are interactive (human-in-the-loop)

**Differences:**
- Gemini CLI is open source
- Gemini CLI has generous free tier
- Different underlying models

### Agent Development Kit (ADK)

**Released:** Google Cloud NEXT 2025

**What it is:** Framework for building multi-agent systems

**Languages:** Python and TypeScript

**Equivalent to:** Claude Agent SDK

**Key Features:**
- Same framework powering Google's internal agents (Agentspace, Customer Engagement Suite)
- Model-agnostic (works with Gemini, but also others)
- Optimized for Gemini 3 Pro and Flash
- Multi-agent orchestration

**Compatible Frameworks:**
- LangGraph/LangChain
- CrewAI
- LlamaIndex
- Pydantic AI
- Agno (formerly Phidata)

---

## OpenAI Ecosystem

### How OpenAI's Stack Compares

| Anthropic | OpenAI Equivalent | Notes |
|-----------|-------------------|-------|
| Claude.ai | ChatGPT | Web chat interface |
| Claude Desktop | ChatGPT Desktop | Native apps |
| Claude Code | **Codex CLI** (or ChatGPT code interpreter) | Less CLI-focused |
| Agent SDK | **OpenAI Agents SDK** | Framework for building agents |
| Projects | Custom GPTs | Persistent configurations |

### OpenAI Agents SDK

**Released:** March 2025

**What it is:** Lightweight Python framework for multi-agent workflows

**Key Features:**
- Evolved from "Swarm" (their experimental agents project)
- Provider-agnostic (works with 100+ LLMs, not just OpenAI)
- Built-in primitives: Agents, Handoffs, Guardrails, Sessions
- Built-in tracing for debugging
- Temporal integration for durable, long-running workflows

### Responses API

OpenAI introduced the Responses API in 2025 - a new API designed specifically for agents:
- Combines Chat Completions simplicity with Assistants API tool-use
- Built-in tools: web search, file search, computer use
- Better suited for agent workflows than the older APIs

### Custom GPTs vs Agent SDK

| Custom GPTs | Agent SDK |
|-------------|-----------|
| No-code configuration | Code-based |
| Runs in ChatGPT interface | Runs anywhere |
| Limited to web chat | Deployable as services |
| Good for simple assistants | Good for complex automation |

---

## When to Use What

### Decision Tree

```
Do you need to write code?
├─ No → Use Claude.ai or Gemini chat
└─ Yes
   └─ Are you comfortable with terminals?
      ├─ No → Use Claude Desktop with MCP
      └─ Yes
         └─ Do you need autonomous operation?
            ├─ No → Use Claude Code (or Gemini CLI)
            └─ Yes → Use Agent SDK (or ADK/OpenAI Agents SDK)
```

### By Use Case

| Use Case | Recommended Tool |
|----------|-----------------|
| Quick questions, writing | Claude.ai / ChatGPT / Gemini |
| Document analysis | Claude Desktop / ChatGPT |
| Coding with AI assistance | Claude Code / Gemini CLI |
| Automated code reviews | Agent SDK / OpenAI Agents SDK |
| CI/CD automation | Agent SDK / ADK |
| Multi-agent workflows | Agent SDK / ADK / OpenAI Agents SDK |
| Building AI-powered apps | API + Agent SDK |
| Learning AI development | Claude Code (see everything happen) |

### By Expertise Level

| Level | Anthropic | Google | OpenAI |
|-------|-----------|--------|--------|
| Beginner | Claude.ai, Desktop | Gemini chat | ChatGPT |
| Intermediate | Claude Code | Gemini CLI | ChatGPT + Code Interpreter |
| Advanced | Agent SDK | ADK | Agents SDK |
| Expert | Custom agents + API | Custom ADK agents | Custom agents + API |

---

## Timeline of Releases

| Date | Product | Company | Notes |
|------|---------|---------|-------|
| 2023 | ChatGPT | OpenAI | Chat interface launched |
| 2023 | Claude.ai | Anthropic | Web chat launched |
| 2023 | Gemini (Bard) | Google | Rebranded from Bard |
| Early 2025 | Claude Code | Anthropic | Terminal-based coding assistant |
| March 2025 | OpenAI Agents SDK | OpenAI | Evolution of Swarm |
| April 2025 | Agent Development Kit | Google | Announced at Cloud NEXT |
| June 2025 | Gemini CLI | Google | Open source terminal tool |
| **Sept 29, 2025** | **Claude Agent SDK** | **Anthropic** | Released with Sonnet 4.5 |
| Oct 2025 | Gemini CLI GUI update | Google | Enhanced terminal rendering |
| Late 2025 | Claude Code Desktop | Anthropic | Git worktrees, multi-session |

---

## ADWs: Building on Top of Agent SDK

### What Are ADWs?

**ADW = Agentic Development Workflow**

ADWs are custom automation workflows you build USING the Agent SDK. Think of it like this:

| Layer | What It Is | Example |
|-------|------------|---------|
| **Agent SDK** | The framework/library | Django, React |
| **ADWs** | Applications you build with it | Your Django app, your React site |

### The Relationship

```
Your ADWs (adw_plan.py, adw_build.py, etc.)
         │ uses
         ▼
Claude Agent SDK (ClaudeSDKClient)
         │ calls
         ▼
Claude API
         │ runs
         ▼
Claude Models (Sonnet, Opus, Haiku)
```

### ADW Patterns from IndyDevDan

IndyDevDan pioneered several ADW patterns in his TAC (The Agentic Coder) series:

| Pattern | Description | Trigger |
|---------|-------------|---------|
| **Local ADWs** | Run via `uv run adws/adw_plan.py "task"` | Terminal command |
| **GitHub @claude** | Tag `@claude` in issues/PRs | GitHub comment |
| **Database-Driven** | PostgreSQL + WebSocket + Dashboard | API/Webhook |

### Real Example: tac-6 Issue #5

The [AllCytes/tac-6#5](https://github.com/AllCytes/tac-6/issues/5) issue demonstrates database-driven ADWs:

1. User creates GitHub issue
2. Webhook triggers backend API
3. Backend creates `ai_developer_workflows` DB record
4. Backend spawns: `uv run adws/adw_plan_build.py --adw-id {uuid}`
5. ADW uses Agent SDK internally to run Claude
6. Real-time WebSocket updates to dashboard
7. Bot posts status comments to GitHub issue
8. PR created automatically

### ADW Code Example

```python
# adws/adw_modules/agent.py - uses Agent SDK

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

options = ClaudeAgentOptions(
    model="claude-sonnet-4-5-20250929",
    allowed_tools=["Read", "Write", "Edit", "Bash", "Skill"],
    permission_mode="acceptEdits",
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Execute /quick-plan with: Add dark mode")
    async for message in client.receive_response():
        # Process TextBlock, ToolUseBlock, ResultMessage
        ...
```

### Full Documentation

See [ADW-Guide.md](./ADW-Guide.md) for complete documentation on:
- Local ADW execution
- GitHub integration
- Database-driven patterns
- Example prompts

---

## Key Takeaways

1. **Claude Code = Interactive pair programming in your terminal**
   - You're always in the loop
   - Great for learning and daily development

2. **Agent SDK = Autonomous AI workers**
   - They run without you
   - Great for automation and production systems

3. **ADWs = Custom workflows built on Agent SDK**
   - Your automation patterns
   - Can be triggered locally, via GitHub, or via API

4. **All three major players have similar stacks:**
   - Chat interface (Claude.ai, ChatGPT, Gemini)
   - CLI tool (Claude Code, Gemini CLI)
   - Agent framework (Agent SDK, OpenAI Agents SDK, ADK)

5. **MCP is becoming a standard**
   - Both Claude Code and Gemini CLI support MCP
   - Allows tools to work across different AI systems

6. **The trend is toward autonomous agents**
   - All companies released agent SDKs in 2025
   - Focus on multi-agent orchestration
   - Provider-agnostic frameworks emerging

---

## Sources

### Anthropic (Claude)
- [Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Claude Agent SDK on npm](https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk)
- [Claude Agent SDK Python releases](https://github.com/anthropics/claude-agent-sdk-python/releases)
- [Claude, Claude API, and Claude Code: What's the Difference?](https://eval.16x.engineer/blog/claude-vs-claude-api-vs-claude-code)
- [Claude Desktop vs Claude Code comparison](https://www.arsturn.com/blog/claude-desktop-vs-claude-code-which-ai-tool-is-right-for-you)
- [Giving Claude a Terminal: Inside the Claude Agent SDK](https://medium.com/spillwave-solutions/giving-claude-a-terminal-inside-the-claude-agent-sdk-49a5f01dcce5)

### Google (Gemini)
- [Introducing Gemini CLI](https://blog.google/technology/developers/introducing-gemini-cli-open-source-ai-agent/)
- [Gemini CLI on GitHub](https://github.com/google-gemini/gemini-cli)
- [Agent Development Kit documentation](https://google.github.io/adk-docs/)
- [Building AI Agents with Gemini 3](https://developers.googleblog.com/building-ai-agents-with-google-gemini-3-and-open-source-frameworks/)
- [ADK for TypeScript announcement](https://developers.googleblog.com/introducing-agent-development-kit-for-typescript-build-ai-agents-with-the-power-of-a-code-first-approach/)

### OpenAI
- [OpenAI Agents SDK documentation](https://platform.openai.com/docs/guides/agents-sdk)
- [OpenAI Agents SDK on PyPI](https://pypi.org/project/openai-agents/)
- [OpenAI Agents SDK on GitHub](https://github.com/openai/openai-agents-python)
- [New tools for building agents](https://openai.com/index/new-tools-for-building-agents/)
- [OpenAI for Developers in 2025](https://developers.openai.com/blog/openai-for-developers-2025)

---

*Document created: January 10, 2026*
*For: Understanding the AI developer ecosystem*
