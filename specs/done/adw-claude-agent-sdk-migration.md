# ADW Migration: Subprocess to claude-agent-sdk

## Problem Statement

The current ADW (AI Developer Workflow) system uses subprocess calls to `claude -p` for agent execution. This approach has a critical limitation: **skills cannot be invoked programmatically**. When the subprocess runs `claude -p "Run /quick-plan"`, Claude treats the input as a conversation prompt rather than a command, and cannot actually invoke the Skill tool.

**Current Flow (Broken):**
```
run_skill("quick-plan", args)
  → subprocess.Popen(["claude", "-p", prompt])
  → Claude receives prompt as text, can't invoke skills
  → Skills never execute
```

**Desired Flow (Fixed):**
```
run_skill("quick-plan", args)
  → ClaudeSDKClient.query(prompt)
  → Claude receives command with full tool access
  → Skills execute correctly via Skill tool
```

## Objectives

1. Replace subprocess-based agent execution with `claude-agent-sdk`
2. Enable proper skill invocation in ADW workflows
3. Maintain existing ADW structure (plan/build/validate phases)
4. Preserve Windows compatibility and .env loading
5. Add async/await pattern throughout the execution layer

## Technical Approach

### Reference Implementation

The reference implementation from IndyDevDan's orchestrator shows the correct SDK usage pattern:

**Location:** `D:\Projects\TAC\multi-agent-orchestration\apps\orchestrator_3_stream\backend\modules\agent_manager.py`

### SDK Usage Pattern

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ResultMessage,
    HookMatcher,
)

# Configure options
options = ClaudeAgentOptions(
    system_prompt=prompt,
    model='claude-sonnet-4-5-20250929',
    cwd=working_dir,
    allowed_tools=['Read', 'Write', 'Edit', 'Bash', 'Skill', ...],
    permission_mode='acceptEdits',
)

# Execute agent
async with ClaudeSDKClient(options=options) as client:
    await client.query(command)
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"[Tool] {block.name}")
        elif isinstance(message, ResultMessage):
            session_id = message.session_id
```

## Implementation Steps

### Step 1: Add Dependency

**File:** `pyproject.toml`

Add `claude-agent-sdk` to dependencies:

```toml
dependencies = [
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
    "httpx>=0.25.0",
    "pyyaml>=6.0.0",
    "python-dotenv>=1.0.0",
    "claude-agent-sdk>=0.1.0",  # ADD THIS
]
```

After editing, run:
```bash
uv sync
# or
pip install -e .
```

### Step 2: Rewrite agent.py

**File:** `adws/adw_modules/agent.py`

Complete rewrite to use async SDK instead of subprocess.

**Key Changes:**
- `run_claude_code()` becomes `async def run_claude_code()`
- `run_skill()` becomes `async def run_skill()`
- Replace subprocess.Popen with ClaudeSDKClient
- Add proper message type handling
- Stream output to console and JSONL file

**New Implementation:**

```python
"""Claude Agent SDK execution wrapper for ADWs."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ResultMessage,
)

from .utils import get_phase_dir


# Model aliases for convenience
MODEL_ALIASES = {
    "sonnet": "claude-sonnet-4-5-20250929",
    "haiku": "claude-haiku-4-5-20251001",
    "opus": "claude-opus-4-5-20251101",
}


async def run_claude_code(
    prompt: str,
    adw_id: str,
    phase: str,
    agent_name: str = "main",
    model: str = "sonnet",
    max_turns: int = 50,
    cwd: Optional[str] = None,
    capture_output: bool = True,
) -> tuple[bool, str, Optional[str]]:
    """Execute Claude via SDK with a prompt.

    Args:
        prompt: The prompt to send to Claude
        adw_id: The ADW ID for output organization
        phase: The phase name (plan, build, validate, etc.)
        agent_name: Name for this agent instance
        model: Model to use (sonnet, opus, haiku)
        max_turns: Maximum agentic turns
        cwd: Working directory (defaults to current)
        capture_output: Whether to capture and save output

    Returns:
        Tuple of (success, output, output_file_path)
    """
    # Resolve model alias
    resolved_model = MODEL_ALIASES.get(model.lower(), model)

    # Prepare output directory
    phase_dir = get_phase_dir(adw_id, phase)
    output_file = phase_dir / f"{agent_name}_output.jsonl"

    working_dir = cwd or str(Path.cwd())

    print(f"\n{'='*60}")
    print(f"[ADW] Phase: {phase} | Agent: {agent_name}")
    print(f"[ADW] Model: {resolved_model} | Max turns: {max_turns}")
    print(f"[ADW] Working dir: {working_dir}")
    print(f"{'='*60}\n")

    # Default allowed tools for ADW execution
    allowed_tools = [
        "Read", "Write", "Edit", "Bash", "Glob", "Grep",
        "Task", "WebFetch", "WebSearch", "TodoWrite",
        "Skill", "AskUserQuestion",
    ]

    # Pass ANTHROPIC_API_KEY to subprocess
    env_vars = {}
    if "ANTHROPIC_API_KEY" in os.environ:
        env_vars["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]

    options = ClaudeAgentOptions(
        model=resolved_model,
        cwd=working_dir,
        max_turns=max_turns,
        allowed_tools=allowed_tools,
        permission_mode="acceptEdits",
        env=env_vars,
        setting_sources=["project"],  # Load CLAUDE.md and skills
    )

    output_lines = []
    final_result = ""
    success = True

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            with open(output_file, "w", encoding="utf-8") as f:
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                print(block.text)
                                final_result += block.text + "\n"
                                entry = {
                                    "type": "text",
                                    "content": block.text,
                                    "timestamp": datetime.now().isoformat(),
                                }
                                output_lines.append(entry)
                                f.write(json.dumps(entry) + "\n")

                            elif isinstance(block, ThinkingBlock):
                                # Log thinking but don't print
                                entry = {
                                    "type": "thinking",
                                    "content": block.thinking,
                                    "timestamp": datetime.now().isoformat(),
                                }
                                output_lines.append(entry)
                                f.write(json.dumps(entry) + "\n")

                            elif isinstance(block, ToolUseBlock):
                                print(f"[Tool] {block.name}")
                                entry = {
                                    "type": "tool_use",
                                    "tool_name": block.name,
                                    "tool_input": block.input,
                                    "timestamp": datetime.now().isoformat(),
                                }
                                output_lines.append(entry)
                                f.write(json.dumps(entry) + "\n")

                    elif isinstance(message, ResultMessage):
                        # Capture final result and usage
                        entry = {
                            "type": "result",
                            "session_id": message.session_id,
                            "usage": message.usage if hasattr(message, 'usage') else None,
                            "timestamp": datetime.now().isoformat(),
                        }
                        output_lines.append(entry)
                        f.write(json.dumps(entry) + "\n")

        print(f"\n{'='*60}")
        print(f"[ADW] Phase {phase} COMPLETED")
        print(f"[ADW] Output saved to: {output_file}")
        print(f"{'='*60}\n")

        return True, final_result, str(output_file)

    except Exception as e:
        error_msg = f"Error running Claude SDK: {e}"
        print(f"[ADW ERROR] {error_msg}")

        print(f"\n{'='*60}")
        print(f"[ADW] Phase {phase} FAILED")
        print(f"{'='*60}\n")

        return False, error_msg, None


async def run_skill(
    skill_name: str,
    args: str,
    adw_id: str,
    phase: str,
    **kwargs,
) -> tuple[bool, str, Optional[str]]:
    """Execute a slash command/skill via Claude SDK.

    This wraps run_claude_code with a skill invocation prompt.

    Args:
        skill_name: The skill to run (e.g., "quick-plan", "build")
        args: Arguments to pass to the skill
        adw_id: The ADW ID
        phase: The phase name
        **kwargs: Additional args passed to run_claude_code

    Returns:
        Tuple of (success, output, output_file_path)
    """
    # Build prompt that invokes the skill
    # With SDK, Claude can actually use the Skill tool
    prompt = f"""Execute the /{skill_name} skill with these arguments: {args}

This is an automated ADW (Agentic Development Workflow) execution.
Run the skill immediately and complete the task autonomously."""

    return await run_claude_code(
        prompt=prompt,
        adw_id=adw_id,
        phase=phase,
        agent_name=skill_name.replace("-", "_"),
        **kwargs,
    )
```

### Step 3: Update adw_plan.py

**File:** `adws/adw_plan.py`

Make the phase runner async:

```python
#!/usr/bin/env python3
"""ADW Plan Phase - Creates a spec using /quick-plan."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.state import ADWState
from adw_modules.agent import run_skill  # Now async
from adw_modules.utils import generate_adw_id, get_project_root


async def run_plan(task_description: str, adw_id: str = None) -> tuple[bool, ADWState]:
    """Execute the plan phase.

    Args:
        task_description: What to plan
        adw_id: Existing ADW ID or None to generate new

    Returns:
        Tuple of (success, state)
    """
    if adw_id is None:
        adw_id = generate_adw_id()

    state = ADWState(
        adw_id=adw_id,
        task_description=task_description,
        project_path=str(get_project_root()),
    )

    print(f"\n[ADW Plan] Starting plan phase")
    print(f"[ADW Plan] ID: {adw_id}")
    print(f"[ADW Plan] Task: {task_description}")

    state.start_phase(ADWPhase.PLAN)

    # Run /quick-plan skill (now async)
    success, output, output_file = await run_skill(
        skill_name="quick-plan",
        args=task_description,
        adw_id=adw_id,
        phase="plan",
    )

    if success:
        specs_dir = get_project_root() / "specs"
        if specs_dir.exists():
            spec_files = sorted(specs_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            if spec_files:
                state.set_spec_file(str(spec_files[0]))
                print(f"[ADW Plan] Spec file: {spec_files[0]}")

        state.complete_phase(ADWPhase.PLAN, success=True, output_file=output_file)
        print("[ADW Plan] Phase completed successfully")
    else:
        state.complete_phase(ADWPhase.PLAN, success=False, error_message=output)
        print(f"[ADW Plan] Phase failed: {output}")

    return success, state


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python adw_plan.py <task_description>")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    success, state = asyncio.run(run_plan(task))

    if success:
        print(f"\nPlan phase completed. ADW ID: {state.adw_id}")
        if state.spec:
            print(f"Spec file: {state.spec}")
    else:
        print("\nPlan phase failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Step 4: Update adw_build.py

**File:** `adws/adw_build.py`

Same pattern - make async:

```python
#!/usr/bin/env python3
"""ADW Build Phase - Implements the plan using /build."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.state import ADWState
from adw_modules.agent import run_skill


async def run_build(state: ADWState) -> bool:
    """Execute the build phase.

    Args:
        state: ADW state with spec file from plan phase

    Returns:
        True if successful
    """
    print(f"\n[ADW Build] Starting build phase")
    print(f"[ADW Build] Spec: {state.spec}")

    state.start_phase(ADWPhase.BUILD)

    if not state.spec:
        error = "No spec file found. Run plan phase first."
        print(f"[ADW Build] Error: {error}")
        state.complete_phase(ADWPhase.BUILD, success=False, error_message=error)
        return False

    # Run /build skill with spec file
    success, output, output_file = await run_skill(
        skill_name="build",
        args=state.spec,
        adw_id=state.adw_id,
        phase="build",
    )

    if success:
        state.complete_phase(ADWPhase.BUILD, success=True, output_file=output_file)
        print("[ADW Build] Phase completed successfully")
    else:
        state.complete_phase(ADWPhase.BUILD, success=False, error_message=output)
        print(f"[ADW Build] Phase failed: {output}")

    return success


def main():
    """CLI entry point - requires existing state."""
    # For standalone testing, would need to load state from file
    print("Build phase requires state from plan phase.")
    print("Use adw_plan_build_validate.py for full workflow.")
    sys.exit(1)


if __name__ == "__main__":
    main()
```

### Step 5: Update adw_validate.py

**File:** `adws/adw_validate.py`

Same async pattern:

```python
#!/usr/bin/env python3
"""ADW Validate Phase - Validates implementation using /validate."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.state import ADWState
from adw_modules.agent import run_skill


async def run_validate(state: ADWState) -> bool:
    """Execute the validate phase.

    Args:
        state: ADW state from previous phases

    Returns:
        True if successful
    """
    print(f"\n[ADW Validate] Starting validate phase")
    print(f"[ADW Validate] Spec: {state.spec}")

    state.start_phase(ADWPhase.VALIDATE)

    if not state.spec:
        error = "No spec file found. Run plan phase first."
        print(f"[ADW Validate] Error: {error}")
        state.complete_phase(ADWPhase.VALIDATE, success=False, error_message=error)
        return False

    # Run /validate skill with spec file
    success, output, output_file = await run_skill(
        skill_name="validate",
        args=state.spec,
        adw_id=state.adw_id,
        phase="validate",
    )

    if success:
        state.complete_phase(ADWPhase.VALIDATE, success=True, output_file=output_file)
        print("[ADW Validate] Phase completed successfully")
    else:
        state.complete_phase(ADWPhase.VALIDATE, success=False, error_message=output)
        print(f"[ADW Validate] Phase failed: {output}")

    return success


def main():
    """CLI entry point - requires existing state."""
    print("Validate phase requires state from previous phases.")
    print("Use adw_plan_build_validate.py for full workflow.")
    sys.exit(1)


if __name__ == "__main__":
    main()
```

### Step 6: Update adw_plan_build_validate.py

**File:** `adws/adw_plan_build_validate.py`

Make the orchestrator async:

```python
#!/usr/bin/env python3
"""ADW Orchestrator: Plan -> Build -> Validate.

Usage:
    uv run adws/adw_plan_build_validate.py "Your task description"
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.utils import generate_adw_id, format_duration
from adw_plan import run_plan
from adw_build import run_build
from adw_validate import run_validate


async def run_plan_build_validate(task_description: str) -> bool:
    """Execute the complete Plan -> Build -> Validate workflow.

    Args:
        task_description: What to implement

    Returns:
        True if all phases successful
    """
    start_time = time.time()
    adw_id = generate_adw_id()

    print("\n" + "=" * 70)
    print("ADW ORCHESTRATOR: Plan -> Build -> Validate")
    print("=" * 70)
    print(f"ADW ID: {adw_id}")
    print(f"Task: {task_description}")
    print("=" * 70 + "\n")

    # Phase 1: PLAN
    print("\n" + "-" * 50)
    print("PHASE 1/3: PLAN")
    print("-" * 50)

    plan_success, state = await run_plan(task_description, adw_id)

    if not plan_success:
        print("\n[ORCHESTRATOR] Plan phase failed. Stopping workflow.")
        state.mark_failed("Plan phase failed")
        return False

    print(f"\n[ORCHESTRATOR] Plan complete. Spec: {state.spec}")

    # Phase 2: BUILD
    print("\n" + "-" * 50)
    print("PHASE 2/3: BUILD")
    print("-" * 50)

    build_success = await run_build(state)

    if not build_success:
        print("\n[ORCHESTRATOR] Build phase failed. Stopping workflow.")
        state.mark_failed("Build phase failed")
        return False

    print("\n[ORCHESTRATOR] Build complete.")

    # Phase 3: VALIDATE
    print("\n" + "-" * 50)
    print("PHASE 3/3: VALIDATE")
    print("-" * 50)

    validate_success = await run_validate(state)

    if not validate_success:
        print("\n[ORCHESTRATOR] Validate phase failed.")
        state.mark_failed("Validate phase failed")
        return False

    # All phases complete
    state.mark_completed()
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("ADW WORKFLOW COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"ADW ID: {adw_id}")
    print(f"Duration: {format_duration(elapsed)}")
    print(f"Phases completed: {len(state.data.completed_phases)}")
    print(f"State file: agents/{adw_id}/adw_state.json")
    if state.spec:
        print(f"Spec file: {state.spec}")
    print("=" * 70 + "\n")

    return True


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("ADW Orchestrator: Plan -> Build -> Validate")
        print()
        print("Usage:")
        print("  uv run adws/adw_plan_build_validate.py <task_description>")
        print()
        print("Examples:")
        print('  uv run adws/adw_plan_build_validate.py "Add dark mode toggle"')
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    success = asyncio.run(run_plan_build_validate(task))

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## Potential Challenges and Solutions

### Challenge 1: API Key Propagation
**Problem:** SDK subprocess may not have access to ANTHROPIC_API_KEY.
**Solution:** Explicitly pass env vars in ClaudeAgentOptions:
```python
env_vars = {"ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"]}
options = ClaudeAgentOptions(..., env=env_vars)
```

### Challenge 2: Windows Compatibility
**Problem:** Previous subprocess approach had Windows-specific handling for .cmd files.
**Solution:** claude-agent-sdk handles this internally. No special Windows handling needed.

### Challenge 3: Session Management
**Problem:** Maintaining context across turns within a phase.
**Solution:** SDK handles sessions automatically. Use `resume=session_id` if resuming existing session.

### Challenge 4: Skill Not Found
**Problem:** /quick-plan, /build, /validate skills may not be available.
**Solution:** Ensure `setting_sources=["project"]` is set to load `.claude/commands/` skills.

## Testing Strategy

### Test 1: SDK Connection
```bash
# Test basic SDK connection
cd D:\Projects\omni-cortex
uv run python -c "from claude_agent_sdk import ClaudeSDKClient; print('SDK loaded')"
```

### Test 2: Single Phase
```bash
# Test plan phase alone
uv run adws/adw_plan.py "Add a simple logging utility"
```

### Test 3: Full Workflow
```bash
# Test complete workflow
uv run adws/adw_plan_build_validate.py "Add a hello world endpoint"
```

### Test 4: Verify Skill Invocation
Check the output JSONL file for `tool_use` entries with `Skill` as the tool name:
```json
{"type": "tool_use", "tool_name": "Skill", "tool_input": {"skill": "quick-plan", ...}}
```

## Success Criteria

1. **Skill Invocation Works:** JSONL output shows Skill tool calls with actual execution
2. **Phases Complete:** All three phases (plan, build, validate) complete successfully
3. **Spec File Generated:** /quick-plan creates spec file in specs/
4. **No Subprocess:** No more `claude -p` subprocess calls in agent.py
5. **Windows Compatible:** Works on Windows without special handling
6. **Async Throughout:** All phase functions are async with proper await

## Files Modified

| File | Change |
|------|--------|
| `pyproject.toml` | Add claude-agent-sdk dependency |
| `adws/adw_modules/agent.py` | Complete rewrite to async SDK |
| `adws/adw_plan.py` | Convert to async |
| `adws/adw_build.py` | Convert to async |
| `adws/adw_validate.py` | Convert to async |
| `adws/adw_plan_build_validate.py` | Convert to async |

## Post-Migration Cleanup

1. Remove `find_claude_cli()` function (no longer needed)
2. Remove subprocess-related imports
3. Update any tests that mock subprocess
4. Document SDK version requirements in README
