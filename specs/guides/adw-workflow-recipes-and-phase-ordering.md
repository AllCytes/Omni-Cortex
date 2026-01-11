# ADW Workflow Recipes and Phase Ordering Guide

## Your Questions Answered

1. **Should /handoff and /pickup be integrated between ADW phases?**
2. **What's the optimal order for phases 4-7?**
3. **Does the order matter? What are the tradeoffs?**

---

## Part 1: Handoff/Pickup in ADWs - Do We Need Them?

### Understanding What Each Provides

| Mechanism | What It Captures | Where It's Stored | Retrieval |
|-----------|------------------|-------------------|-----------|
| **Spec File** | Implementation plan | `specs/todo/*.md` | Read file directly |
| **ADW State** | adw_id, spec path, completed phases | `agents/{id}/adw_state.json` | Passed in Python |
| **cortex_remember** | Decisions, discoveries during phase | Omni-Cortex DB | `cortex_recall` |
| **/handoff** | Rich structured summary: CONTEXT, COMPLETED, IN PROGRESS, NEXT STEPS, KEY FILES, BLOCKERS | Omni-Cortex DB (importance: 90-95) | `cortex_recall "handoff"` |
| **/pickup** | Retrieves handoff, creates TodoWrite | N/A (retrieval only) | N/A |

### The Key Question: Is /handoff Between Phases Redundant?

**Current ADW Flow:**
```
Plan Phase
  └── Uses cortex_remember to store important decisions
  └── Creates spec file
  └── ADW state updated
  └── Context DISCARDED

Build Phase
  └── Uses cortex_recall to get relevant context
  └── Reads spec file
  └── Knows adw_id from state
  └── Works fine without /handoff memory
```

**With /handoff Between Phases:**
```
Plan Phase
  └── Same as above...
  └── PLUS: Runs /handoff (20-30 tool calls)
        └── Creates rich structured memory
  └── Context DISCARDED

Build Phase
  └── Runs /pickup (10-15 tool calls)
  └── Gets structured CONTEXT, COMPLETED, NEXT STEPS
  └── THEN also reads spec file
  └── More context, but slower
```

### Recommendation: WHERE to Use Handoff/Pickup

| Scenario | Use Handoff/Pickup? | Why |
|----------|---------------------|-----|
| **Between ADW phases** | **NO** | Overkill - spec file + cortex_recall is sufficient. Adds 30-45 tool calls per phase transition. |
| **At END of full ADW workflow** | **YES** | Captures the complete session state for future manual sessions |
| **If ADW FAILS mid-workflow** | **YES** | Enable manual resume with full context |
| **Manual multi-terminal workflow** | **YES** | Essential for human-operated terminal switching |

### The Math

Adding /handoff + /pickup between each phase:

```
ADW with 7 phases:
- 6 phase transitions
- ~35 extra tool calls per transition
- = 210 extra tool calls total
- = ~3-5 minutes added runtime
- = Marginal benefit (spec file already sufficient)
```

**Verdict**: The spec file already serves as the "handoff document." Adding /handoff between phases is over-engineering.

### When /handoff IS Valuable in ADWs

1. **At workflow END** - Capture everything for future sessions
2. **Before risky phases** - E.g., before /release, capture state in case of failure
3. **After critical discoveries** - If build phase finds a major issue

### Implementation Recommendation

```python
# adw_full_sdlc.py - Optimal handoff placement

async def run_full_sdlc(task: str):
    # Phases 1-3: No handoff needed
    await run_plan(task, adw_id)      # Creates spec file
    await run_build(state)             # Reads spec, implements
    await run_validate(state)          # Validates

    # Phases 4-6: Still no handoff between
    await run_retrospective(state)     # Documents lessons
    await run_security(state)          # Audits
    await run_review(state)            # Compares to spec

    # BEFORE RELEASE: Consider handoff (if release might fail)
    if not skip_release:
        await run_handoff_checkpoint(state)  # Optional safety
        await run_release(state)

    # AT VERY END: Always handoff
    await run_final_handoff(state)    # Full session summary
```

---

## Part 2: Phase Ordering (Phases 4-7)

### The Fixed Part (Phases 1-3)

These MUST be in order:

```
1. PLAN ──────► 2. BUILD ──────► 3. VALIDATE
   │                │                │
   Creates spec     Implements       Verifies it works
```

**Why fixed**: Build needs the spec. Validate needs the implementation.

### The Flexible Part (Phases 4-7)

These can be reordered:

```
4. RETROSPECTIVE - Documents lessons learned
5. SECURITY      - Audits for vulnerabilities
6. REVIEW        - Compares implementation to spec
7. RELEASE       - Commits, pushes, publishes
```

**Constraint**: RELEASE must always be LAST.

### Dependency Analysis

| Phase | Depends On | Can Run After |
|-------|------------|---------------|
| **Retrospective** | Validate results (to know what worked/failed) | Validate |
| **Security** | Complete code (to audit) | Build or Validate |
| **Review** | Complete implementation | Build or Validate |
| **Release** | Everything passing | All other phases |

### Phase Ordering Comparison Matrix

| Order | Phases 4-6 Sequence | Pros | Cons | Best For |
|-------|---------------------|------|------|----------|
| **A** | Retro → Security → Review | Lessons captured while fresh; Security issues found before review | Security fixes might need re-review | Most common/balanced |
| **B** | Security → Retro → Review | Critical issues found first; Retro includes security findings | Retro waits for security | Security-first projects |
| **C** | Security → Review → Retro | Security + Review are "checks", Retro is final documentation | Retro might feel redundant after review | Formal projects |
| **D** | Review → Security → Retro | Spec compliance verified first; Security audits verified code | Might find spec issues that security also catches | Spec-critical projects |
| **E** | Review → Retro → Security | Review confirms spec, Retro documents, Security is final check | Security findings come late | NOT recommended |
| **F** | Retro → Review → Security | Lessons first, spec check, security last | Security issues discovered late | NOT recommended |

### Efficiency/Success Rate Comparison

| Order | Efficiency | Issue Discovery | Rework Risk | Overall Score |
|-------|------------|-----------------|-------------|---------------|
| **A: Retro → Security → Review** | 85% | Good | Medium | ★★★★☆ |
| **B: Security → Retro → Review** | 90% | Best | Low | ★★★★★ |
| **C: Security → Review → Retro** | 88% | Best | Low | ★★★★☆ |
| **D: Review → Security → Retro** | 80% | Good | Medium | ★★★☆☆ |
| **E: Review → Retro → Security** | 70% | Late | High | ★★☆☆☆ |
| **F: Retro → Review → Security** | 65% | Late | High | ★☆☆☆☆ |

### Why Security Should Be Early

```
Scenario: Security finds SQL injection vulnerability

If Security runs FIRST (Order B/C):
├── Security finds issue
├── You decide: Fix now or document and continue
├── If fix: Re-run build, validate, THEN continue
├── If document: Review knows about it, Release can be blocked
└── Result: Issue addressed early

If Security runs LAST (Order E/F):
├── Retro already written (doesn't include security issue)
├── Review already done (doesn't catch security issue)
├── Security finds issue
├── Now what? Re-run retro? Re-run review?
└── Result: Wasted work or incomplete documentation
```

### The Recommended Order

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDED WORKFLOW                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Phase 1: PLAN                                                       │
│      └── /quick-plan "task description"                             │
│      └── Output: specs/todo/feature.md                              │
│                                                                      │
│  Phase 2: BUILD                                                      │
│      └── /build specs/todo/feature.md                               │
│      └── Output: Implementation                                      │
│                                                                      │
│  Phase 3: VALIDATE                                                   │
│      └── /validate                                                   │
│      └── Output: Validation report, screenshots                     │
│                                                                      │
│  ═══════════════ FIRST HALF COMPLETE ═══════════════                │
│                                                                      │
│  Phase 4: SECURITY (Run early to find critical issues)              │
│      └── /security                                                   │
│      └── Output: Security audit report                              │
│      └── Decision point: Fix issues now or document for later?      │
│                                                                      │
│  Phase 5: REVIEW (Check spec compliance)                             │
│      └── /review or /adw-review                                      │
│      └── Output: Spec compliance report                             │
│      └── Note: Includes awareness of any security findings          │
│                                                                      │
│  Phase 6: RETROSPECTIVE (Document everything)                        │
│      └── /retrospective                                              │
│      └── Output: docs/retrospectives/YYYY-MM-DD-*.md                │
│      └── Includes: Build lessons, validation results, security      │
│                    findings, review outcomes                         │
│                                                                      │
│  Phase 7: RELEASE (Always last)                                      │
│      └── /omni                                                       │
│      └── Output: Git commit, push, PyPI publish                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Workflow Recipes

### Recipe 1: Quick Feature (No Security Audit)

**When to use**: Small features, internal tools, low-risk changes

```
/quick-plan "Add button to X"
/build specs/todo/add-button.md
/validate
/review
/omni
```

**Phases**: 1 → 2 → 3 → 6 → 7
**Skipped**: Security, Retrospective
**Time**: ~15-20 minutes

### Recipe 2: Standard Feature (7 Phases)

**When to use**: Most features, external-facing code

```
/quick-plan "Add feature X"
/build specs/todo/feature-x.md
/validate
/security
/review
/retrospective
/omni
```

**Phases**: 1 → 2 → 3 → 4 → 5 → 6 → 7
**Time**: ~30-45 minutes

### Recipe 3: Complete SDLC with Fix Phases (9 Phases) ⭐ NEW

**When to use**: Production features, learning-focused development, security-critical code

```
Phase 1: /quick-plan "Add authentication"
Phase 2: /build specs/todo/auth.md
Phase 3: /validate
Phase 4: /security
Phase 5: /security-fix  ← NEW: Execute security recommendations
Phase 6: /review
Phase 7: /retrospective
Phase 8: /apply-learnings  ← NEW: Implement retro recommendations
Phase 9: /omni
```

**Phases**: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9
**Time**: ~60-90 minutes

**Why 9 phases?**
- Security audit creates recommendations → Phase 5 executes them
- Retrospective identifies improvements → Phase 8 implements them
- No manual terminal switching for fixes

### Recipe 3a: Security-Critical Feature (with Re-validation)

**When to use**: Auth, payments, data handling, API endpoints

```
Phase 1: /quick-plan "Add authentication"
Phase 2: /build
Phase 3: /validate
Phase 4: /security
Phase 5: /security-fix (execute fixes)
Phase 6: /validate (re-validate after security fixes)
Phase 7: /review
Phase 8: /retrospective
Phase 9: /apply-learnings
Phase 10: /omni
```

**Phases**: 1 → 2 → 3 → 4 → 5 → 3 → 6 → 7 → 8 → 9
**Time**: ~75-100 minutes

### Recipe 4: Bug Fix (Minimal)

**When to use**: Simple bug fixes

```
/quick-plan "Fix bug in X"
/build specs/todo/fix-bug.md
/validate
/omni
```

**Phases**: 1 → 2 → 3 → 7
**Skipped**: Security, Review, Retrospective
**Time**: ~10-15 minutes

### Recipe 5: Refactoring (Documentation Heavy)

**When to use**: Major refactors, architectural changes

```
/quick-plan "Refactor module X"
/build specs/todo/refactor-x.md
/validate
/review (critical for refactors)
/security
/retrospective (important for lessons)
/omni
```

**Phases**: 1 → 2 → 3 → 6 → 5 → 4 → 7
**Time**: ~40-50 minutes

---

## Part 4: Decision Flowchart

```
                            START
                              │
                              ▼
                    ┌─────────────────┐
                    │ /quick-plan     │
                    │ /build          │
                    │ /validate       │
                    └────────┬────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │ Is this security-sensitive?  │
              │ (auth, payments, user data)  │
              └──────────────┬───────────────┘
                    │                │
                   YES              NO
                    │                │
                    ▼                ▼
            ┌───────────┐    ┌───────────────────┐
            │ /security │    │ Skip to next step │
            └─────┬─────┘    └─────────┬─────────┘
                  │                    │
                  ▼                    │
         ┌────────────────┐            │
         │ Issues found?  │            │
         └───────┬────────┘            │
            │         │                │
           YES        NO               │
            │         │                │
            ▼         │                │
     ┌──────────┐     │                │
     │ Fix now? │     │                │
     └────┬─────┘     │                │
      │       │       │                │
     YES      NO      │                │
      │       │       │                │
      ▼       ▼       ▼                │
  ┌──────┐  ┌──────────────────┐       │
  │/build│  │ Document in      │       │
  │/valid│  │ retrospective    │       │
  └──┬───┘  └────────┬─────────┘       │
     │               │                 │
     └───────────────┼─────────────────┘
                     │
                     ▼
              ┌────────────┐
              │ /review    │
              │ (optional  │
              │ for simple │
              │ changes)   │
              └─────┬──────┘
                    │
                    ▼
         ┌────────────────────┐
         │ Is this a learning │
         │ opportunity?       │
         └─────────┬──────────┘
               │        │
              YES       NO
               │        │
               ▼        │
        ┌──────────┐    │
        │/retrospe-│    │
        │ ctive    │    │
        └────┬─────┘    │
             │          │
             └────┬─────┘
                  │
                  ▼
           ┌───────────┐
           │ /omni     │
           │ (release) │
           └───────────┘
```

---

## Part 5: Quick Reference - What Order Works

### Does Order Matter for Phases 4-6?

**Short answer**: Security should be early. Otherwise, flexible.

| If you run... | Then... |
|---------------|---------|
| Security FIRST | Find critical issues early, can fix before documenting |
| Security LAST | Risk wasting work on retro/review that needs updating |
| Review before Retro | Retro can include review findings (more complete) |
| Retro before Review | Review catches issues retro missed (double-check) |

### The "It Doesn't Really Matter" Cases

For **simple, non-security-sensitive** changes:
- Order of retro/review doesn't significantly impact outcome
- Pick whichever feels natural
- Both work fine

For **complex, security-sensitive** changes:
- Order DOES matter
- Security should be phases 4 or 5 (early)
- Review should be before release

---

## Part 6: ADW Implementation

Based on this analysis, here's the recommended ADW structure:

### adw_standard_feature.py
```
Plan → Build → Validate → Security → Review → Retrospective → Release
```

### adw_quick_fix.py
```
Plan → Build → Validate → Release
```

### adw_security_critical.py
```
Plan → Build → Validate → Security → [decision point] → Review → Retrospective → Release
```

---

## Summary

### Handoff/Pickup
- **Between phases**: NOT needed (spec file is sufficient)
- **At workflow end**: YES (capture full session)
- **On failure**: YES (enable resume)

### Phase Ordering
- **Fixed**: Plan → Build → Validate (always first)
- **Fixed**: Release (always last)
- **Flexible**: Security, Review, Retrospective (can reorder)
- **Recommended**: Security early, Retrospective late
- **Best order**: Security → Review → Retrospective → Release

### The Simple Rule
1. Build it (Plan, Build, Validate)
2. Check it (Security, Review)
3. Document it (Retrospective)
4. Ship it (Release)

---

## Important: Context Loss Tradeoff

**Note**: Fresh contexts per phase means retrospective cannot see build errors unless they're stored.

### For Rich Retrospectives (Learning Focus)
Consider combining build+retrospective in the same context:
- Retrospective sees all errors, recovery attempts
- Higher token cost but richer lessons-learned
- Use for complex features or when learning is the goal

### For Efficient Retrospectives (Standard)
Keep separate contexts but:
- Use `cortex_remember` during build for significant errors
- Have retrospective use `cortex_recall("error OR snag OR fix")`
- Read `build_output.jsonl` for tool history

**See Also**: `specs/guides/adw-context-loss-and-retrospective-considerations.md` for full analysis.

---

## Part 6: The Complete 9-Phase Workflow

### Visual Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE 9-PHASE SDLC WORKFLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────── CORE DEVELOPMENT ────────────────────┐               │
│  │                                                           │               │
│  │  Phase 1: PLAN          Phase 2: BUILD      Phase 3: VALIDATE            │
│  │  /quick-plan ──────────► /build ──────────► /validate                    │
│  │  Creates spec           Implements          Verifies works               │
│  │                                                           │               │
│  └───────────────────────────────────────────────────────────┘               │
│                               │                                              │
│                               ▼                                              │
│  ┌──────────────────── SECURITY CYCLE ──────────────────────┐               │
│  │                                                           │               │
│  │  Phase 4: SECURITY                Phase 5: SECURITY-FIX                  │
│  │  /security ─────────────────────► /security-fix                          │
│  │  Audits for vulnerabilities       Executes recommended fixes             │
│  │  Creates: security-audit.md       Reads audit, applies fixes             │
│  │                                                           │               │
│  └───────────────────────────────────────────────────────────┘               │
│                               │                                              │
│                               ▼                                              │
│  ┌──────────────────── REVIEW & DOCUMENTATION ──────────────┐               │
│  │                                                           │               │
│  │  Phase 6: REVIEW                                                         │
│  │  /review or /adw-review                                                  │
│  │  Compares implementation to spec                                         │
│  │                                                           │               │
│  └───────────────────────────────────────────────────────────┘               │
│                               │                                              │
│                               ▼                                              │
│  ┌──────────────────── LEARNING CYCLE ──────────────────────┐               │
│  │                                                           │               │
│  │  Phase 7: RETROSPECTIVE           Phase 8: APPLY-LEARNINGS               │
│  │  /retrospective ────────────────► /apply-learnings                       │
│  │  Documents lessons learned        Implements improvements:               │
│  │  Creates: retrospective.md        - Update commands/skills               │
│  │  Identifies improvements          - Add documentation                    │
│  │                                   - Create templates                     │
│  │                                                           │               │
│  └───────────────────────────────────────────────────────────┘               │
│                               │                                              │
│                               ▼                                              │
│  ┌──────────────────── RELEASE ─────────────────────────────┐               │
│  │                                                           │               │
│  │  Phase 9: RELEASE                                                        │
│  │  /omni                                                                   │
│  │  Git commit, push, tag, PyPI publish                                    │
│  │                                                           │               │
│  └───────────────────────────────────────────────────────────┘               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase Details for Fix Phases

#### Phase 5: Security Fix (`/security-fix`)

**Purpose**: Execute the recommendations from the security audit

**Inputs**:
- Security audit report (e.g., `docs/security/security-audit-YYYY-MM-DD.md`)
- Original spec file

**What it does**:
1. Reads the security audit report
2. Extracts HIGH and CRITICAL severity items
3. Creates a todo list of fixes
4. Implements each fix
5. Re-runs affected tests
6. Updates the audit report with "FIXED" status

**Outputs**:
- Fixed code
- Updated security audit with resolution notes

**New Command**: `.claude/commands/security-fix.md`

#### Phase 8: Apply Learnings (`/apply-learnings`)

**Purpose**: Implement the improvements identified in retrospective

**Inputs**:
- Retrospective report (e.g., `docs/retrospectives/YYYY-MM-DD-*.md`)
- Current commands/skills

**What it does**:
1. Reads the retrospective
2. Identifies actionable improvements (not just observations)
3. Categories:
   - **Command updates**: Improve existing /commands
   - **New templates**: Create reusable patterns
   - **Documentation**: Add missing docs
   - **Process improvements**: Update CLAUDE.md or workflows

**Outputs**:
- Updated/new commands in `.claude/commands/`
- New documentation
- Updated templates

**New Command**: `.claude/commands/apply-learnings.md`

---

## Part 7: Loop Detection and Retry Limits

### The Problem

You experienced Claude getting stuck in an infinite loop trying to fix a 500 error. This wastes tokens and time.

### Solution: Retry Limits and Graceful Failure

```python
# In agent.py or ADW orchestrator

MAX_RETRIES = 3  # Maximum attempts for any single fix
MAX_CONSECUTIVE_ERRORS = 5  # Stop if 5 errors in a row

class ADWExecutionConfig:
    max_retries_per_fix: int = 3
    max_consecutive_errors: int = 5
    max_phase_duration_minutes: int = 30
    store_failures_in_cortex: bool = True
```

### When to Stop and Store

```
┌─────────────────────────────────────────────────────────────┐
│                 LOOP DETECTION LOGIC                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  FOR each fix attempt:                                       │
│      │                                                       │
│      ├── Attempt 1: Try to fix                              │
│      │   └── Failed? → Increment retry_count                │
│      │                                                       │
│      ├── Attempt 2: Try different approach                  │
│      │   └── Failed? → Increment retry_count                │
│      │                                                       │
│      ├── Attempt 3: Try simplified fix                      │
│      │   └── Failed? → STOP, store in cortex:               │
│      │                                                       │
│      │       cortex_remember({                              │
│      │         "content": "UNRESOLVED: {error}",            │
│      │         "type": "troubleshooting",                   │
│      │         "tags": ["unresolved", "needs-human"],       │
│      │         "importance": 95                             │
│      │       })                                              │
│      │                                                       │
│      └── Move to next issue (don't block workflow)          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### What Gets Stored on Failure

```json
{
  "content": "UNRESOLVED ISSUE: 500 Error in /api/memories endpoint\n\nAttempted fixes:\n1. Checked database connection - OK\n2. Verified schema - OK\n3. Added try/catch - Still failing\n\nError: TypeError: 'NoneType' object is not subscriptable\nFile: dashboard/backend/main.py:245\n\nNeeds human investigation: Possible race condition or missing null check.",
  "type": "troubleshooting",
  "tags": ["unresolved", "needs-human", "500-error", "api", "adw_xyz"],
  "importance": 95
}
```

### Benefits

1. **No infinite loops** - Hard limit on retries
2. **Preserved context** - Error details stored for later
3. **Workflow continues** - Other issues still get fixed
4. **Human handoff** - Clear flag for what needs attention

---

## Part 8: Enhanced Error Tracking (cortex_remember)

### What Gets Tracked

During BUILD and FIX phases, automatically store:

| Event | Importance | Tags |
|-------|------------|------|
| Error encountered | 80 | error, build, adw_id |
| Error fixed | 75 | resolved, build, adw_id |
| Error UNRESOLVED (after retries) | 95 | unresolved, needs-human, adw_id |
| Significant decision | 70 | decision, architecture, adw_id |
| Workaround used | 85 | workaround, technical-debt, adw_id |

### How Retrospective Uses This

```python
# In retrospective phase:

# 1. Get all errors from this ADW
errors = await cortex_recall(f"error adw_{adw_id}", limit=20)

# 2. Get all unresolved issues
unresolved = await cortex_recall("unresolved needs-human", limit=10)

# 3. Generate retrospective with full context
retrospective_prompt = f"""
Analyze this build session:

ERRORS ENCOUNTERED:
{format_errors(errors)}

UNRESOLVED ISSUES (need human attention):
{format_unresolved(unresolved)}

SPEC FILE:
{spec_content}

Generate a retrospective document that includes:
1. What worked well
2. What didn't work (include errors above)
3. Lessons learned
4. Actionable improvements
5. HUMAN ATTENTION REQUIRED section (for unresolved issues)
"""
```

---

## Summary: Complete 9-Phase Workflow

| Phase | Command | Purpose | Outputs |
|-------|---------|---------|---------|
| 1 | /quick-plan | Create spec | specs/todo/*.md |
| 2 | /build | Implement | Code changes |
| 3 | /validate | Verify | Validation report |
| 4 | /security | Audit | Security report |
| 5 | /security-fix | Fix security issues | Fixed code |
| 6 | /review | Check spec compliance | Review report |
| 7 | /retrospective | Document lessons | Retrospective doc |
| 8 | /apply-learnings | Implement improvements | Updated commands/docs |
| 9 | /omni | Release | Git push, PyPI |

### Error Handling Throughout

- **cortex_remember** stores errors during phases 2, 5, 8
- **Retry limits** (3 attempts) prevent infinite loops
- **Unresolved issues** flagged with `needs-human` tag
- **Retrospective** (phase 7) sees ALL errors via cortex_recall
