#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Release Phase - Publish using /omni."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from adw_modules.agent import execute_slash_command, check_claude_available
from adw_modules.data_types import ADWPhase


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_release.py <adw-id>")
        print("\nExample:")
        print("  uv run adw_release.py abc12345")
        sys.exit(1)

    adw_id = sys.argv[1]

    print(f"{'=' * 50}")
    print(f"ADW RELEASE PHASE")
    print(f"{'=' * 50}")
    print(f"ADW ID: {adw_id}")
    print()

    # Check Claude Code availability
    if not check_claude_available():
        print("[ERROR] Claude Code CLI not found!")
        print("Install with: npm install -g @anthropic-ai/claude-code")
        sys.exit(1)

    # Load state
    state = ADWState.load(adw_id)
    if not state:
        print(f"[ERROR] No state found for ADW ID: {adw_id}")
        print("Run earlier phases first")
        sys.exit(1)

    # Check prerequisites
    if not state.data.review_passed:
        print("[ERROR] Cannot release without passing review")
        print("Run review phase first and ensure it passes")
        sys.exit(1)

    print(f"Review passed: {state.data.review_passed}")
    print()

    state.update(current_phase=ADWPhase.RELEASE)
    state.save()

    print("[INFO] Executing /omni...")

    # Execute /omni
    success, output = execute_slash_command("/omni", [], adw_id, "releaser")

    if success:
        state.mark_phase_complete(ADWPhase.RELEASE)
        state.save()
        print()
        print(f"[SUCCESS] Release phase completed")
        print(f"ADW workflow fully completed!")
    else:
        state.add_error(f"Release failed: {output}")
        state.save()
        print()
        print(f"[ERROR] Release phase failed")
        print(f"Error: {output}")
        sys.exit(1)

    # Output state for chaining
    print()
    print(
        json.dumps(
            {
                "adw_id": adw_id,
                "phase": "release",
                "phases_completed": [p.value for p in state.data.phases_completed],
                "success": True,
            }
        )
    )


if __name__ == "__main__":
    main()
