"""Claude Code agent execution for ADW."""

import subprocess
import os
import json
from typing import Optional, Tuple


# Get Claude Code CLI path
CLAUDE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")


def execute_slash_command(
    slash_command: str,
    args: list[str],
    adw_id: str,
    agent_name: str,
    working_dir: Optional[str] = None,
    timeout_seconds: int = 600,
) -> Tuple[bool, str]:
    """Execute a slash command via Claude Code CLI.

    Args:
        slash_command: The slash command to execute (e.g., "/build")
        args: Arguments to pass to the command
        adw_id: The ADW identifier for organizing output
        agent_name: Name for the agent directory (e.g., "planner", "builder")
        working_dir: Working directory for execution (defaults to project root)
        timeout_seconds: Maximum execution time in seconds

    Returns:
        Tuple of (success: bool, output: str)
    """
    # Build prompt
    prompt = f"{slash_command} {' '.join(args)}"

    # Create output directory
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    output_dir = os.path.join(project_root, "agents", adw_id, agent_name)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "raw_output.jsonl")

    # Build command
    cmd = [
        CLAUDE_PATH,
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--dangerously-skip-permissions",
        "--verbose",
    ]

    # Execute
    cwd = working_dir or project_root

    try:
        with open(output_file, "w") as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                timeout=timeout_seconds,
            )

        # Parse result from JSONL
        output_text = ""
        with open(output_file, "r") as f:
            lines = f.readlines()

        for line in reversed(lines):
            try:
                data = json.loads(line.strip())
                if data.get("type") == "result":
                    return not data.get("is_error", False), data.get("result", "")
                # Collect assistant messages for output
                if data.get("type") == "assistant" and data.get("message"):
                    msg = data["message"]
                    if isinstance(msg, dict) and msg.get("content"):
                        for block in msg["content"]:
                            if block.get("type") == "text":
                                output_text = block.get("text", "")
            except json.JSONDecodeError:
                continue

        # If no result found, check return code
        if result.returncode == 0:
            return True, output_text or "Command completed successfully"
        else:
            return False, result.stderr or "Command failed with no error message"

    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout_seconds} seconds"
    except FileNotFoundError:
        return False, f"Claude Code CLI not found at: {CLAUDE_PATH}"
    except Exception as e:
        return False, str(e)


def get_claude_path() -> str:
    """Get the path to Claude Code CLI."""
    return CLAUDE_PATH


def check_claude_available() -> bool:
    """Check if Claude Code CLI is available."""
    try:
        result = subprocess.run(
            [CLAUDE_PATH, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
