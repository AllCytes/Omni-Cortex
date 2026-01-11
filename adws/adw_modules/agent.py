"""Claude Agent SDK execution wrapper for ADWs.

Includes error tracking via Omni-Cortex for retrospective context preservation.
"""

import asyncio
import json
import os
import subprocess
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

# Error tracking configuration
MAX_RETRIES = 3  # Maximum attempts for any single fix
MAX_CONSECUTIVE_ERRORS = 5  # Stop if N errors in a row


def store_in_cortex(content: str, tags: list[str], importance: int = 80, memory_type: str = "troubleshooting") -> bool:
    """Store information in Omni-Cortex for retrospective access.

    Uses the cortex CLI to store memories directly, enabling retrospective
    phases to access build errors and decisions.

    Args:
        content: The content to remember
        tags: List of tags for categorization
        importance: 1-100 importance score
        memory_type: Type of memory (troubleshooting, decision, etc.)

    Returns:
        True if stored successfully, False otherwise
    """
    try:
        # Use cortex CLI to store the memory
        cmd = [
            "cortex", "remember",
            "--content", content,
            "--tags", ",".join(tags),
            "--importance", str(importance),
            "--type", memory_type,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(project_root),
        )
        if result.returncode == 0:
            return True
        else:
            # Silently fail - don't block ADW execution for memory storage issues
            print(f"[ADW] Warning: Could not store to Cortex: {result.stderr[:100]}")
            return False
    except Exception as e:
        # Silently fail - memory storage is best-effort
        print(f"[ADW] Warning: Cortex storage failed: {e}")
        return False


def track_error(
    error_msg: str,
    adw_id: str,
    phase: str,
    agent_name: str,
    attempt: int = 1,
    is_resolved: bool = False,
    is_unresolved_final: bool = False,
) -> None:
    """Track an error in Omni-Cortex for retrospective visibility.

    Args:
        error_msg: The error message or description
        adw_id: The ADW ID for correlation
        phase: Current phase (build, security-fix, etc.)
        agent_name: Name of the agent that encountered the error
        attempt: Which retry attempt this is (1-3)
        is_resolved: True if the error was successfully fixed
        is_unresolved_final: True if this is the final attempt and still unresolved
    """
    if is_unresolved_final:
        # High importance - needs human attention
        content = f"""UNRESOLVED ISSUE (after {MAX_RETRIES} attempts): {error_msg}

ADW: {adw_id}
Phase: {phase}
Agent: {agent_name}
Timestamp: {datetime.now().isoformat()}

This issue could not be resolved automatically and requires human investigation."""
        tags = ["unresolved", "needs-human", phase, f"adw_{adw_id}"]
        importance = 95
    elif is_resolved:
        content = f"""RESOLVED ERROR: {error_msg}

ADW: {adw_id}
Phase: {phase}
Agent: {agent_name}
Resolved at: {datetime.now().isoformat()}"""
        tags = ["resolved", phase, f"adw_{adw_id}"]
        importance = 75
    else:
        # Error encountered but not yet resolved
        content = f"""ERROR (attempt {attempt}/{MAX_RETRIES}): {error_msg}

ADW: {adw_id}
Phase: {phase}
Agent: {agent_name}
Timestamp: {datetime.now().isoformat()}"""
        tags = ["error", phase, f"adw_{adw_id}"]
        importance = 80

    store_in_cortex(content, tags, importance, "troubleshooting")


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
        setting_sources=["project", "user"],  # Load project + user commands/skills
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

        # Track the error in Omni-Cortex for retrospective visibility
        track_error(
            error_msg=str(e),
            adw_id=adw_id,
            phase=phase,
            agent_name=agent_name,
            attempt=1,  # First attempt failure tracked
            is_unresolved_final=True,  # SDK errors are typically fatal
        )

        print(f"\n{'='*60}")
        print(f"[ADW] Phase {phase} FAILED")
        print(f"[ADW] Error stored in Cortex for retrospective")
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
