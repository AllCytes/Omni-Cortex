#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Retrospective Phase - Document lessons learned using /retrospective."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from adw_modules.agent import execute_slash_command, check_claude_available
from adw_modules.data_types import ADWPhase


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_retrospective.py <adw-id> [session-name]")
        print("\nExamples:")
        print("  uv run adw_retrospective.py abc12345")
        print("  uv run adw_retrospective.py abc12345 feature-x-implementation")
        sys.exit(1)

    adw_id = sys.argv[1]
    session_name = sys.argv[2] if len(sys.argv) > 2 else adw_id

    print(f"{'=' * 50}")
    print(f"ADW RETROSPECTIVE PHASE")
    print(f"{'=' * 50}")
    print(f"ADW ID: {adw_id}")
    print(f"Session name: {session_name}")
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

    state.update(current_phase=ADWPhase.RETROSPECTIVE)
    state.save()

    print("[INFO] Executing /retrospective...")

    # Execute /retrospective
    success, output = execute_slash_command(
        "/retrospective", [session_name], adw_id, "retrospective"
    )

    if success:
        state.mark_phase_complete(ADWPhase.RETROSPECTIVE)
        state.save()
        print()
        print(f"[SUCCESS] Retrospective phase completed")
    else:
        state.add_error(f"Retrospective failed: {output}")
        state.save()
        print()
        print(f"[WARNING] Retrospective phase failed (non-blocking)")
        print(f"Error: {output}")
        # Don't exit with error - retrospective is optional

    # Output state for chaining
    print()
    print(
        json.dumps(
            {
                "adw_id": adw_id,
                "session_name": session_name,
                "phase": "retrospective",
                "success": success,
            }
        )
    )


if __name__ == "__main__":
    main()
