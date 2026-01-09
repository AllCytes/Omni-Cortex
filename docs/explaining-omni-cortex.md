# Explaining Omni-Cortex

## For the AI Expert

Omni-Cortex is a **dual-layer persistent context system** for Claude Code that combines:

1. **Activity Audit Layer** - Automatic tool call logging via Claude Code hooks (PreToolUse/PostToolUse), capturing inputs, outputs, duration, and error states with full session traceability
2. **Knowledge Layer** - Curated memories with auto-categorization (11 types via regex pattern matching), hybrid search (FTS5 keyword + optional sentence-transformer embeddings), and importance scoring with temporal decay + access frequency boosting

**Key architectural differentiators:**
- **Session continuity** - Multi-session context restoration via summarized session history
- **Memory relationship graph** - `supersedes`, `derived_from`, `contradicts` relationships for knowledge evolution tracking
- **Cross-project global index** - Unified semantic search across all project databases
- **Real-time dashboard** - FastAPI + Vue 3 with WebSocket sync for memory/activity visualization

It's not purely RAG—it's more accurately described as a **context-aware knowledge management system with activity provenance tracking**.

**Analogy:** Think of it like **Git + Elasticsearch + a knowledge graph, but for AI context**. Git tracks what changed and when, Elasticsearch provides hybrid retrieval, and the knowledge graph tracks how information relates and evolves. The activity layer is your commit history; the memory layer is your searchable documentation that auto-organizes itself.

---

## For Someone Who Knows Some AI

Omni-Cortex solves the "amnesia problem" in Claude Code—where the AI forgets everything between sessions.

**What it does:**
- **Remembers automatically** - Every action Claude takes gets logged (what tool, what inputs, did it work?)
- **Stores knowledge smartly** - When you tell it to remember something, it auto-categorizes it (is this a bug fix? a config tip? a decision?)
- **Finds relevant context** - Uses both keyword matching AND meaning-based search (embeddings) to find what's relevant
- **Tracks importance** - Memories you use often become more important; old unused ones fade away
- **Works across projects** - Search your learnings from one project while working on another

**Analogy:** Imagine a **senior developer's brain** after working at a company for years. They remember:
- What they tried before (activity log)
- What worked and what didn't (memories with importance)
- How different solutions relate ("we tried X but Y superseded it")
- Context from similar projects ("oh, we solved this in Project A")

Basic memory solutions are like sticky notes. Omni-Cortex is like having that experienced developer's institutional knowledge—searchable, organized, and always available.

---

## For a Non-Technical Person

Imagine you have an incredibly smart assistant who helps you with work, but every morning they wake up with complete amnesia—they don't remember yesterday's conversations, what worked, what failed, or any decisions you made together.

**Omni-Cortex is like giving that assistant a perfect memory.**

- **It remembers what happened** - Every task, every solution, every mistake
- **It organizes automatically** - No need to manually file things, it figures out what type of information it is
- **It finds things when needed** - Ask a question and it pulls up relevant past experiences
- **It gets smarter over time** - The more you use it, the better it knows what's important to you
- **You can see it all** - A visual dashboard shows your entire work history

**The result:** Instead of re-explaining your project every session, your AI assistant already knows the context and can pick up right where you left off.

**Analogy:** Think of it like the difference between:

| Without Omni-Cortex | With Omni-Cortex |
|---------------------|------------------|
| A new temp worker every day who needs full training each morning | A trusted employee who's been with you for years |
| Sticky notes scattered everywhere that you have to search through manually | A personal assistant who files everything and hands you exactly what you need |
| Starting from scratch every conversation | Picking up mid-conversation like no time passed |

It's like giving your AI a **perfect memory, a filing system, and a work journal**—all rolled into one.

---

## Comparison: Memory Solutions for Claude Code

| Feature | Claude Code (Basic) | CLAUDE.md Files | Basic MCP Memory | Omni-Cortex |
|---------|:------------------:|:---------------:|:----------------:|:-----------:|
| **Persists between sessions** | ❌ | ✅ | ✅ | ✅ |
| **Auto-logs all activity** | ❌ | ❌ | ❌ | ✅ |
| **Smart search (meaning-based)** | ❌ | ❌ | ✅ | ✅ |
| **Keyword + semantic hybrid search** | ❌ | ❌ | ❌ | ✅ |
| **Auto-categorizes memories** | ❌ | ❌ | ❌ | ✅ |
| **Importance decay over time** | ❌ | ❌ | ❌ | ✅ |
| **Frequently-used items rank higher** | ❌ | ❌ | ❌ | ✅ |
| **Session history & context** | ❌ | ❌ | ❌ | ✅ |
| **Memory relationships (supersedes, contradicts)** | ❌ | ❌ | ❌ | ✅ |
| **Cross-project search** | ❌ | ❌ | ❌ | ✅ |
| **Visual dashboard** | ❌ | ❌ | ❌ | ✅ |
| **Real-time sync** | ❌ | ❌ | ❌ | ✅ |
| **Activity timeline & heatmaps** | ❌ | ❌ | ❌ | ✅ |
| **Works without manual maintenance** | ❌ | ❌ | ✅ | ✅ |

### What Each Solution Is

| Solution | What It Is | Limitation |
|----------|-----------|------------|
| **Claude Code (Basic)** | No memory at all—context resets each session | Complete amnesia |
| **CLAUDE.md Files** | Static markdown files loaded at startup | Manual updates, no search, no activity tracking |
| **Basic MCP Memory** | Simple key-value or embedding-based storage | No activity logging, no categorization, no relationships |
| **Omni-Cortex** | Full knowledge management + activity audit system | Requires setup (but automated via CLI) |

---

## The One-Liner Pitch

> **For experts:** "A dual-layer context system with activity provenance, hybrid semantic search, and temporal importance decay."

> **For tech-savvy folks:** "It gives Claude Code a persistent, searchable memory that auto-logs everything and gets smarter over time."

> **For everyone:** "It makes your AI assistant actually remember things."

---

## Quick Analogies Reference

| Audience | Analogy |
|----------|---------|
| **Expert** | Git + Elasticsearch + Knowledge Graph for AI context. Activity layer = commit history; Memory layer = self-organizing searchable docs. |
| **Intermediate** | A senior developer's brain—institutional knowledge that's searchable, tracks what worked/failed, and remembers context across projects. |
| **Beginner** | A trusted long-term employee vs. a new temp worker every day. Perfect memory + filing system + work journal for your AI. |

---

## Sources & Related Projects

Other memory solutions in the ecosystem:
- [mcp-memory-service](https://github.com/doobidoo/mcp-memory-service) - Semantic search memory
- [mcp-memory-keeper](https://github.com/mkreyman/mcp-memory-keeper) - Persistent context management
- [episodic-memory](https://blog.fsck.com/2025/10/23/episodic-memory/) - Conversation archiving with vector search
- [claude-mem](https://github.com/thedotmack/claude-mem) - Session compression and injection
- [Official CLAUDE.md docs](https://code.claude.com/docs/en/memory) - Built-in memory files
