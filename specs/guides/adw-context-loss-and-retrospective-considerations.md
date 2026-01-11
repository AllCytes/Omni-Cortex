# ADW Context Loss and Retrospective Considerations

## The Problem You Identified

**Question**: If each phase gets a fresh context, won't the retrospective lose valuable information about errors and snags that occurred during build?

**Answer**: YES. This is a real tradeoff. Let me explain exactly what's lost.

---

## What the Build Output JSONL Captures

Looking at your actual `build_output.jsonl` from the Quick Capture Widget ADW:

```jsonl
{"type": "text", "content": "I'll execute the /build skill...", "timestamp": "..."}
{"type": "tool_use", "tool_name": "Skill", "tool_input": {...}, "timestamp": "..."}
{"type": "tool_use", "tool_name": "Read", "tool_input": {"file_path": "..."}, "timestamp": "..."}
{"type": "tool_use", "tool_name": "Edit", "tool_input": {...}, "timestamp": "..."}
{"type": "result", "session_id": "...", "usage": {...}, "timestamp": "..."}
```

### What IS Captured:
| Data | Example |
|------|---------|
| Claude's explanations | "Good! There's already a create_memory function" |
| Tool names called | "Read", "Edit", "Grep", "Bash" |
| Tool inputs | File paths, search patterns, edit content |
| Thinking blocks | Claude's reasoning (if extended thinking enabled) |
| Final result | Session ID, token usage |

### What is NOT Captured:
| Data | Why It Matters |
|------|----------------|
| **Tool RESULTS** | What came back from Read, Grep, Edit |
| **Error messages** | "File not found", "Edit failed" |
| **Bash stderr** | Build errors, test failures |
| **Recovery attempts** | "That didn't work, trying X instead" |
| **File diffs** | Before/after of edits |

---

## The Impact on Retrospective

### In Same Terminal (Manual Workflow)

When you run `/build` then `/retrospective` in the SAME terminal:

```
Terminal Session:
├── /build
│   ├── Tries to edit file → ERROR: old_string not found
│   ├── Reads file again to understand
│   ├── Fixes the edit → SUCCESS
│   └── All of this is IN CONTEXT
├── /retrospective
│   └── Can see the ENTIRE journey:
│       ├── "We tried X but it failed because Y"
│       ├── "The error message was: ..."
│       ├── "We recovered by doing Z"
│       └── Creates rich lessons-learned document
```

### In Separate Contexts (ADW Workflow)

When ADW runs build then retrospective in SEPARATE contexts:

```
Phase 2: BUILD (Context Window A)
├── Tries to edit file → ERROR: old_string not found
├── Reads file again to understand
├── Fixes the edit → SUCCESS
└── Context DISCARDED (including all error info!)

Phase 4: RETROSPECTIVE (Context Window B)
└── Starts fresh, can only see:
    ├── Final state of files (SUCCESS)
    ├── build_output.jsonl (tool names and inputs only)
    ├── NO error messages from failed attempts
    └── Cannot reconstruct the recovery journey
```

**Result**: Retrospective might say "Build completed successfully" without capturing the valuable lessons from the errors that occurred.

---

## Real Example from Your ADW

In your Quick Capture Widget build, there was a TypeScript error:

```
# During VALIDATE phase, this was discovered:
QuickCaptureModal.vue:231 - error TS2349:
  This expression is not callable.
  Type 'Number' has no call signatures.
```

The issue: `@blur="setTimeout(() => showSuggestions = false, 200)"` - using `setTimeout` directly in Vue template.

### What Happened:
1. **BUILD** created the component with this bug
2. **VALIDATE** found the TypeScript error
3. The error was in VALIDATE's context, not BUILD's

### What RETROSPECTIVE Could Miss:
- If retrospective ran after BUILD but before VALIDATE, it wouldn't know about the TS error
- The error message and stack trace were only in VALIDATE's context
- Retrospective would need to RE-RUN the TypeScript check to see it

---

## Solutions to Preserve Error Context

### Solution 1: Store Errors in Cortex During Build

Modify build to use `cortex_remember` when errors occur:

```python
# In build phase, when an error happens:
if error_occurred:
    await cortex_remember({
        "content": f"Build Error: {error_message}\nContext: {context}\nResolution: {how_fixed}",
        "type": "troubleshooting",
        "tags": ["build-error", "adw", adw_id],
        "importance": 85
    })
```

**Retrospective** then uses `cortex_recall("build-error adw_{id}")` to find these.

### Solution 2: Enhanced JSONL Output

Modify `agent.py` to capture tool results:

```python
# Currently only captures:
entry = {"type": "tool_use", "tool_name": block.name, "tool_input": block.input}

# Should also capture:
entry = {
    "type": "tool_result",
    "tool_name": tool_name,
    "result": tool_result,  # Add this!
    "success": success,      # Add this!
    "error": error_message   # Add this!
}
```

**Retrospective** then reads and analyzes the enhanced JSONL.

### Solution 3: Combine Build + Retrospective (Context Sharing)

For cases where you NEED the full journey:

```python
# adw_build_with_retro.py
async def run_build_and_retro(state):
    """Run build and retrospective in SAME context."""

    # Single ClaudeSDKClient for both
    async with ClaudeSDKClient(options) as client:
        # Phase 1: Build
        await client.query(build_prompt)
        async for message in client.receive_response():
            # Capture build output...

        # Phase 2: Retrospective (SAME context!)
        await client.query(retro_prompt)
        async for message in client.receive_response():
            # Capture retro output...
            # This HAS access to all build errors!
```

**Tradeoff**: Larger context window used, but richer retrospective.

### Solution 4: Structured Error Log File

Write errors to a dedicated file during build:

```python
# In build phase:
error_log_path = phase_dir / "errors.log"
with open(error_log_path, "a") as f:
    f.write(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "error": error_message,
        "context": what_we_were_doing,
        "resolution": how_we_fixed_it
    }) + "\n")
```

**Retrospective** reads `errors.log` at the start.

---

## Recommended Approach

For your workflow, I recommend a **hybrid approach**:

### For Simple/Successful Builds
Use separate contexts (current ADW approach):
- Build phase completes without issues
- Retrospective focuses on what was built, not how
- Faster execution, lower token usage

### For Complex/Error-Prone Builds
Combine build + retrospective in same context:
- Use `adw_build_with_retro.py` orchestrator
- Retrospective has full access to the journey
- Richer lessons-learned document

### Always Do
1. **cortex_remember during build** for significant errors/decisions
2. **Read build_output.jsonl in retrospective** to see what tools were called
3. **Run TypeScript/linting BEFORE retrospective** so errors are known

---

## Updated Workflow Recommendations

### Recipe: Standard Feature (Separate Contexts)

```
Plan    → Fresh context
Build   → Fresh context (store errors via cortex_remember)
Validate → Fresh context (finds TS errors, stores them)
Security → Fresh context
Review  → Fresh context
Retro   → Fresh context (uses cortex_recall to get errors from all phases)
Release → Fresh context
```

### Recipe: Learning-Focused (Combined for Key Phases)

```
Plan    → Fresh context
Build   → COMBINED
Retro   → COMBINED ← Same context, sees all build errors!
Validate → Fresh context
Security → Fresh context
Review  → Fresh context
Release → Fresh context
```

---

## Comparison: Context Isolation vs. Context Sharing

| Aspect | Separate Contexts | Combined Build+Retro |
|--------|-------------------|----------------------|
| Error visibility | LOW (only via cortex/JSONL) | HIGH (full journey) |
| Context usage | EFFICIENT (~30-50 calls each) | HIGHER (~80-100 calls total) |
| Speed | FASTER (parallel-capable) | SLOWER (sequential) |
| Retro quality | Good (focuses on outcome) | Excellent (captures journey) |
| Token cost | LOWER | HIGHER |
| Recommended for | Simple features, bug fixes | Complex features, learning |

---

## Implementation: cortex_remember for Errors

Here's how to modify the build phase to preserve errors:

```python
# In adws/adw_modules/agent.py

async def run_claude_code(...):
    # ... existing code ...

    # Add error tracking
    errors_encountered = []

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        # Check for error patterns
                        if any(word in block.text.lower() for word in ['error', 'failed', 'fix', 'retry']):
                            errors_encountered.append({
                                "timestamp": datetime.now().isoformat(),
                                "context": block.text[:500]
                            })

    # Store errors in cortex for retrospective
    if errors_encountered:
        # This would require adding cortex_remember call
        # For now, write to errors.log
        error_log = phase_dir / "errors_and_recovery.log"
        with open(error_log, "w") as f:
            json.dump(errors_encountered, f, indent=2)

    return success, output, str(output_file)
```

---

## Summary

### The Tradeoff is Real
- Separate contexts = some journey information lost
- Combined contexts = richer retrospective but higher cost

### Mitigations
1. **cortex_remember** during build for significant errors
2. **Enhanced JSONL** to capture tool results
3. **Combine build+retro** for complex features
4. **Read error logs** in retrospective

### My Recommendation
- Use separate contexts (efficiency)
- Enhance build to store errors via `cortex_remember`
- Have retrospective check `cortex_recall("error OR snag OR fix")` at start
- For critical learning opportunities, combine build+retro

Would you like me to implement the enhanced error tracking in `agent.py`?
