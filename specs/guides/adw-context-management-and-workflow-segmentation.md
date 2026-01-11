# ADW Context Management and Workflow Segmentation Guide

## Your Questions Answered

You asked:
1. How does context management work when ADWs run through each step?
2. Is each phase getting a fresh context window?
3. How should I break up my terminal sessions?

**Short Answer**: YES - each ADW phase gets a **completely fresh context window**. This is the primary advantage of ADWs over running multiple commands in a single terminal.

---

## Understanding Your Terminal Output

Let me annotate your ADW run to show exactly where context boundaries occur:

```
======================================================================
ADW ORCHESTRATOR: Plan -> Build -> Validate       <-- Python orchestrator starts
======================================================================
ADW ID: adw_1768119806_6cd2ebe5
Task: Quick Capture Widget...
======================================================================

--------------------------------------------------
PHASE 1/3: PLAN                                   <-- Phase 1 begins
--------------------------------------------------

[ADW Plan] Starting plan phase
[ADW Plan] ID: adw_1768119806_6cd2ebe5

============================================================
[ADW] Phase: plan | Agent: quick_plan
[ADW] Model: claude-sonnet-4-5-20250929 | Max turns: 50
[ADW] Working dir: D:\Projects\omni-cortex
============================================================
                                                  ↑
                                                  │
                       ╔══════════════════════════════════════════════╗
                       ║  NEW ClaudeSDKClient CREATED HERE            ║
                       ║  Context Window #1 starts (empty/fresh)      ║
                       ╚══════════════════════════════════════════════╝

I'll execute the /quick-plan skill...
[Tool] Skill
[Tool] mcp__omni-cortex__cortex_recall
[Tool] Glob
[Tool] Read
... (plan phase work happens)
[Tool] Write
[Tool] mcp__omni-cortex__cortex_remember

============================================================
[ADW] Phase plan COMPLETED
[ADW] Output saved to: .../plan/quick_plan_output.jsonl
============================================================
                                                  ↑
                                                  │
                       ╔══════════════════════════════════════════════╗
                       ║  ClaudeSDKClient CLOSED HERE                 ║
                       ║  Context Window #1 ends                      ║
                       ║  All context is DISCARDED                    ║
                       ╚══════════════════════════════════════════════╝

[ORCHESTRATOR] Plan complete. Spec: D:\Projects\omni-cortex\specs\todo\quick-capture-widget.md

--------------------------------------------------
PHASE 2/3: BUILD                                  <-- Phase 2 begins
--------------------------------------------------

[ADW Build] Starting build phase

============================================================
[ADW] Phase: build | Agent: build
[ADW] Model: claude-sonnet-4-5-20250929 | Max turns: 50
[ADW] Working dir: D:\Projects\omni-cortex
============================================================
                                                  ↑
                                                  │
                       ╔══════════════════════════════════════════════╗
                       ║  NEW ClaudeSDKClient CREATED HERE            ║
                       ║  Context Window #2 starts (empty/fresh)      ║
                       ║  ZERO knowledge of what Plan phase did       ║
                       ║  Only knows: spec file path (from state)     ║
                       ╚══════════════════════════════════════════════╝

I'll execute the /build skill...
[Tool] Skill
[Tool] mcp__omni-cortex__cortex_recall            <-- Must RE-READ context!
[Tool] Read                                       <-- Must RE-READ spec file!
[Tool] TodoWrite
... (build phase work happens)
[Tool] Edit
[Tool] Edit
[Tool] Edit

============================================================
[ADW] Phase build COMPLETED
[ADW] Output saved to: .../build/build_output.jsonl
============================================================
                                                  ↑
                                                  │
                       ╔══════════════════════════════════════════════╗
                       ║  ClaudeSDKClient CLOSED HERE                 ║
                       ║  Context Window #2 ends                      ║
                       ║  All context is DISCARDED                    ║
                       ╚══════════════════════════════════════════════╝

--------------------------------------------------
PHASE 3/3: VALIDATE                               <-- Phase 3 begins
--------------------------------------------------

============================================================
[ADW] Phase: validate | Agent: validate
[ADW] Model: claude-sonnet-4-5-20250929 | Max turns: 50
[ADW] Working dir: D:\Projects\omni-cortex
============================================================
                                                  ↑
                                                  │
                       ╔══════════════════════════════════════════════╗
                       ║  NEW ClaudeSDKClient CREATED HERE            ║
                       ║  Context Window #3 starts (empty/fresh)      ║
                       ║  ZERO knowledge of Plan or Build phases      ║
                       ╚══════════════════════════════════════════════╝

I'll execute the /validate skill...
[Tool] Skill
[Tool] mcp__omni-cortex__cortex_recall            <-- Must RE-READ context!
[Tool] Read                                       <-- Must RE-READ spec!
... (validate phase work happens)
[Tool] Bash
[Tool] Bash
[Tool] Grep

============================================================
[ADW] Phase validate COMPLETED
============================================================
                                                  ↑
                                                  │
                       ╔══════════════════════════════════════════════╗
                       ║  ClaudeSDKClient CLOSED HERE                 ║
                       ║  Context Window #3 ends                      ║
                       ╚══════════════════════════════════════════════╝

======================================================================
ADW WORKFLOW COMPLETED SUCCESSFULLY
======================================================================
Duration: 12m 46s
Phases completed: 3
======================================================================
```

---

## The Code That Creates Fresh Context

In `agent.py:106`:

```python
async with ClaudeSDKClient(options=options) as client:
    await client.query(prompt)

    async for message in client.receive_response():
        # Process messages...
```

This `async with` block:
1. **Creates** a new ClaudeSDKClient (fresh context)
2. **Runs** the prompt to completion
3. **Closes** the client when done (context discarded)

Each call to `run_skill()` or `run_claude_code()` creates a **completely new client**.

---

## What Persists Between Phases (vs. What Doesn't)

### What PERSISTS (via adw_state.json):
- ADW ID
- Task description
- Spec file path
- Which phases completed
- Phase timing/success status

### What DOES NOT PERSIST:
- Claude's "memory" of what it did
- Tool call history
- Reasoning/thinking
- Files it read (must re-read)
- Context about decisions made

**This is why you see `cortex_recall` and `Read` at the start of each phase** - Claude must re-establish context because it has no memory of the previous phase!

---

## Comparison: Manual Terminals vs. ADW

### Your Current Manual Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│ TERMINAL 1: /quick-plan "Add dark mode"                             │
│ └── Context Window A (ends when you close terminal or start fresh)  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ TERMINAL 2: /build specs/todo/dark-mode.md                          │
│             /validate                                                │
│             /retrospective                                           │
│ └── Context Window B (accumulates ALL of these commands!)           │
│     └── Build uses ~30-50 tool calls                                │
│         └── Validate adds ~20-30 more                               │
│             └── Retrospective adds ~10-20 more                      │
│                 └── TOTAL: 60-100 tool calls in ONE context!        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ TERMINAL 3: /security                                               │
│ └── Context Window C                                                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ TERMINAL 4: /review                                                 │
│             /omni                                                    │
│ └── Context Window D (accumulates both)                             │
└─────────────────────────────────────────────────────────────────────┘
```

**Problem with Terminal 2**: Running `/build` + `/validate` + `/retrospective` in the same terminal means:
- Build's 50+ tool calls are still in context
- Validate adds more on top
- Retrospective might hit context limits or have degraded quality

### ADW Approach

```
┌─────────────────────────────────────────────────────────────────────┐
│ SINGLE TERMINAL: uv run adws/adw_plan_build_validate.py "task"      │
│                                                                      │
│  Phase 1: PLAN                                                       │
│  └── Context Window A (fresh, ~15-30 tool calls)                    │
│      └── CLOSED after phase                                         │
│                                                                      │
│  Phase 2: BUILD                                                      │
│  └── Context Window B (fresh, ~30-50 tool calls)                    │
│      └── CLOSED after phase                                         │
│                                                                      │
│  Phase 3: VALIDATE                                                   │
│  └── Context Window C (fresh, ~20-30 tool calls)                    │
│      └── CLOSED after phase                                         │
└─────────────────────────────────────────────────────────────────────┘
```

**Each phase gets a FRESH context window automatically!**

---

## Recommended Workflow Segmentation

Based on context management principles, here's how to structure your workflow:

### Option A: Full ADW Automation (Recommended)

Create an ADW that handles your entire SDLC:

```python
# adw_full_sdlc.py
async def run_full_sdlc(task: str):
    adw_id = generate_adw_id()

    # Phase 1: PLAN (fresh context)
    await run_plan(task, adw_id)

    # Phase 2: BUILD (fresh context)
    await run_build(state)

    # Phase 3: VALIDATE (fresh context)
    await run_validate(state)

    # Phase 4: RETROSPECTIVE (fresh context)
    await run_retrospective(state)

    # Phase 5: SECURITY (fresh context)
    await run_security(state)

    # Phase 6: REVIEW (fresh context)
    await run_review(state)

    # Phase 7: RELEASE (fresh context) - optional
    if not skip_release:
        await run_release(state)
```

Each phase = fresh context = no pollution.

### Option B: Manual with Optimal Terminal Segmentation

If you prefer manual control, here's the optimal breakdown:

```
┌──────────────────────────────────────────────────────────────┐
│ TERMINAL 1: Planning                                          │
│ $ claude                                                      │
│ > /quick-plan "Add dark mode toggle"                         │
│ (Close terminal or start fresh conversation when done)        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ TERMINAL 2: Building (HEAVY - do this alone)                 │
│ $ claude                                                      │
│ > /build specs/todo/dark-mode.md                             │
│ (Close terminal when done - build uses most context)          │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ TERMINAL 3: Validation (MODERATE)                             │
│ $ claude                                                      │
│ > /validate                                                   │
│ (Can optionally add /retrospective here if not too heavy)     │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ TERMINAL 4: Security (MODERATE)                               │
│ $ claude                                                      │
│ > /security                                                   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ TERMINAL 5: Review & Release (LIGHT)                          │
│ $ claude                                                      │
│ > /review                                                     │
│ > /omni                                                       │
│ (These are lighter, can combine)                              │
└──────────────────────────────────────────────────────────────┘
```

### Context Load Estimates by Command

| Command | Context Load | Typical Tool Calls | Recommendation |
|---------|--------------|-------------------|----------------|
| `/quick-plan` | LIGHT | 10-20 | Alone or first |
| `/build` | HEAVY | 30-80 | **Always alone** |
| `/validate` | MODERATE | 20-40 | Alone or with light cmd |
| `/retrospective` | MODERATE | 15-30 | Alone or with light cmd |
| `/security` | MODERATE | 20-40 | Alone |
| `/review` | LIGHT | 10-25 | Can combine |
| `/omni` | LIGHT | 5-15 | Can combine |

---

## Why /build Should Always Be Alone

Looking at your terminal output, the BUILD phase made these tool calls:
- `cortex_recall` x2
- `Read` x8
- `TodoWrite` x6
- `Grep` x8
- `Edit` x12
- Plus internal processing

That's 36+ tool calls in a single phase. If you then run `/validate` in the same terminal, you're adding another 20-30 on top, which means:
- Slower responses (more context to process)
- Higher risk of context-related issues
- Claude may "forget" early context

**ADWs solve this automatically** - each phase starts fresh.

---

## The Secret Sauce: What Links Phases Together

If each phase has a fresh context, how does BUILD know what PLAN created?

### Answer: The State File + Spec File

```
agents/adw_1768119806_6cd2ebe5/
├── adw_state.json           <-- Links phases together
├── plan/
│   └── quick_plan_output.jsonl
├── build/
│   └── build_output.jsonl
└── validate/
    └── validate_output.jsonl
```

The `adw_state.json` contains:
```json
{
  "adw_id": "adw_1768119806_6cd2ebe5",
  "task_description": "Quick Capture Widget...",
  "spec": "D:\\Projects\\omni-cortex\\specs\\todo\\quick-capture-widget.md",
  "completed_phases": ["plan", "build", "validate"],
  "phase_results": {...}
}
```

When BUILD starts, it:
1. Gets the state object from the orchestrator
2. Reads the spec file path from state
3. Uses `cortex_recall` to check for relevant memories
4. Reads the actual spec file
5. Proceeds with implementation

**The spec file IS the handoff document between phases!**

---

## Optimal ADW Design for Your Workflow

Based on your described workflow, here's the ideal ADW structure:

### adw_full_development_cycle.py

```
PHASE 1: PLAN (/quick-plan)
    └── Fresh context
    └── Creates: specs/todo/feature.md
    └── Outputs: plan_output.jsonl

PHASE 2: BUILD (/build)
    └── Fresh context
    └── Reads: specs/todo/feature.md
    └── Outputs: build_output.jsonl

PHASE 3: VALIDATE (/validate)
    └── Fresh context
    └── Verifies: API, visual, integration
    └── Outputs: validate_output.jsonl

PHASE 4: RETROSPECTIVE (/retrospective)
    └── Fresh context
    └── Reads: All phase outputs
    └── Creates: docs/retrospectives/*.md

PHASE 5: SECURITY (/security)
    └── Fresh context
    └── Audits: All modified files
    └── Creates: docs/security/*.md

PHASE 6: REVIEW (/review or /adw-review)
    └── Fresh context
    └── Compares: Implementation vs. spec
    └── Reports: Discrepancies

PHASE 7: RELEASE (/omni) [Optional]
    └── Fresh context
    └── Git: commit, push, tag
    └── PyPI: publish
```

### Would You Like Me to Create This ADW?

I can create `adw_full_sdlc.py` that runs all 7 phases with fresh context for each. Just let me know!

---

## Key Takeaways

1. **Each ADW phase = fresh context window** (like opening a new terminal)
2. **The spec file is the handoff** between phases (not Claude's memory)
3. **`cortex_recall` at phase start** re-establishes relevant context
4. **BUILD should always be isolated** (heaviest context load)
5. **ADWs automatically segment** - no manual terminal juggling needed
6. **State file tracks progress** - resume if something fails
7. **12m 46s for 3 phases** is good - fresh contexts are efficient

---

## Important Tradeoff: Error Context Loss

**WARNING**: Fresh contexts have a downside - the retrospective phase cannot see errors that occurred during build!

### What's Lost:
- Error messages from failed tool calls
- Recovery attempts ("tried X, failed, then tried Y")
- Bash stderr output
- The "journey" of debugging

### Mitigations:
1. Use `cortex_remember` during build to store significant errors
2. Have retrospective read `build_output.jsonl` for tool history
3. For learning-focused builds, combine build+retro in same context

**See Also**: `specs/guides/adw-context-loss-and-retrospective-considerations.md` for full analysis and solutions.

---

## Your Workflow: ADW vs. Manual Comparison

| Your Current Manual Approach | Equivalent ADW Approach |
|------------------------------|-------------------------|
| Terminal 1: /quick-plan | Phase 1: run_plan() |
| Terminal 2: /build | Phase 2: run_build() |
| Terminal 2: /validate | Phase 3: run_validate() |
| Terminal 2: /retrospective | Phase 4: run_retrospective() |
| Terminal 3: /security | Phase 5: run_security() |
| Terminal 4: /review | Phase 6: run_review() |
| Terminal 4: /omni | Phase 7: run_release() |
| **4-5 terminals, manual switching** | **1 command, automatic context isolation** |

The ADW gives you the same context isolation as opening 7 separate terminals, but with a single command!
