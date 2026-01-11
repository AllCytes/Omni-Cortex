#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Plan Phase - Creates implementation spec using /quick-plan."""

import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.utils import generate_adw_id
from adw_modules.state import ADWState
from adw_modules.agent import execute_slash_command, check_claude_available
from adw_modules.data_types import ADWPhase


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_plan.py <request-or-spec-file> [adw-id]")
        print("\nExamples:")
        print('  uv run adw_plan.py "Add dark mode toggle"')
        print("  uv run adw_plan.py specs/existing-spec.md abc12345")
        sys.exit(1)

    request = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else generate_adw_id()

    print(f"{'=' * 50}")
    print(f"ADW PLAN PHASE")
    print(f"{'=' * 50}")
    print(f"ADW ID: {adw_id}")
    print(f"Request: {request[:100]}{'...' if len(request) > 100 else ''}")
    print()

    # Check Claude Code availability
    if not check_claude_available():
        print("[ERROR] Claude Code CLI not found!")
        print("Install with: npm install -g @anthropic-ai/claude-code")
        sys.exit(1)

    # Initialize state
    state = ADWState.load_or_create(adw_id)
    state.update(current_phase=ADWPhase.PLAN, spec_request=request)
    state.save()

    print("[INFO] Executing /quick-plan...")

    # Execute /quick-plan
    success, output = execute_slash_command(
        "/quick-plan", [request], adw_id, "planner"
    )

    if success:
        # Extract spec file path from output (look for specs/*.md)
        match = re.search(r"specs/[\w-]+\.md", output)
        if match:
            spec_file = match.group(0)
            state.update(spec_file=spec_file)
            print(f"[INFO] Spec file detected: {spec_file}")

        state.mark_phase_complete(ADWPhase.PLAN)
        state.save()
        print()
        print(f"[SUCCESS] Plan phase completed")
        print(f"State saved to: {state.get_state_path()}")
        if state.data.spec_file:
            print(f"Spec file: {state.data.spec_file}")
    else:
        state.add_error(f"Plan failed: {output}")
        state.save()
        print()
        print(f"[ERROR] Plan phase failed")
        print(f"Error: {output}")
        sys.exit(1)

    # Output state for chaining (JSON on last line)
    print()
    print(
        json.dumps(
            {
                "adw_id": adw_id,
                "spec_file": state.data.spec_file,
                "phase": "plan",
                "success": True,
            }
        )
    )


if __name__ == "__main__":
    main()
