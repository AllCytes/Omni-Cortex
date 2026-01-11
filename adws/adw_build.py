#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Build Phase - Implements spec using /build."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from adw_modules.agent import execute_slash_command, check_claude_available
from adw_modules.data_types import ADWPhase


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_build.py <adw-id> [spec-file]")
        print("\nExamples:")
        print("  uv run adw_build.py abc12345")
        print("  uv run adw_build.py abc12345 specs/feature.md")
        sys.exit(1)

    adw_id = sys.argv[1]
    spec_file = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"{'=' * 50}")
    print(f"ADW BUILD PHASE")
    print(f"{'=' * 50}")
    print(f"ADW ID: {adw_id}")

    # Check Claude Code availability
    if not check_claude_available():
        print("[ERROR] Claude Code CLI not found!")
        print("Install with: npm install -g @anthropic-ai/claude-code")
        sys.exit(1)

    # Load state
    state = ADWState.load(adw_id)
    if not state:
        print(f"[ERROR] No state found for ADW ID: {adw_id}")
        print("Run adw_plan.py first or provide spec file")
        sys.exit(1)

    # Get spec file
    spec_file = spec_file or state.data.spec_file
    if not spec_file:
        print("[ERROR] No spec file provided or found in state")
        print("Provide spec file as argument or run plan phase first")
        sys.exit(1)

    print(f"Spec file: {spec_file}")
    print()

    state.update(current_phase=ADWPhase.BUILD)
    state.save()

    print("[INFO] Executing /build...")

    # Execute /build
    success, output = execute_slash_command("/build", [spec_file], adw_id, "builder")

    if success:
        state.mark_phase_complete(ADWPhase.BUILD)
        state.save()
        print()
        print(f"[SUCCESS] Build phase completed")
        print(f"State saved to: {state.get_state_path()}")
    else:
        state.add_error(f"Build failed: {output}")
        state.save()
        print()
        print(f"[ERROR] Build phase failed")
        print(f"Error: {output}")
        sys.exit(1)

    # Output state for chaining
    print()
    print(
        json.dumps(
            {
                "adw_id": adw_id,
                "spec_file": spec_file,
                "phase": "build",
                "success": True,
            }
        )
    )


if __name__ == "__main__":
    main()
