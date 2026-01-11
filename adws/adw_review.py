#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Review Phase - Compare implementation against spec using /review."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from adw_modules.agent import execute_slash_command, check_claude_available
from adw_modules.data_types import ADWPhase
from adw_modules.utils import ensure_directory


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_review.py <adw-id> [spec-file]")
        print("\nExamples:")
        print("  uv run adw_review.py abc12345")
        print("  uv run adw_review.py abc12345 specs/feature.md")
        sys.exit(1)

    adw_id = sys.argv[1]
    spec_file = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"{'=' * 50}")
    print(f"ADW REVIEW PHASE")
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
        print("Run earlier phases first")
        sys.exit(1)

    spec_file = spec_file or state.data.spec_file
    if not spec_file:
        print("[ERROR] No spec file provided or found in state")
        print("Provide spec file as argument or run plan phase first")
        sys.exit(1)

    print(f"Spec file: {spec_file}")
    print()

    state.update(current_phase=ADWPhase.REVIEW)
    state.save()

    # Ensure screenshot directory exists
    screenshot_dir = state.get_screenshot_dir("review")
    ensure_directory(screenshot_dir)
    print(f"Screenshots will be saved to: {screenshot_dir}")
    print()

    print("[INFO] Executing /review...")

    # Execute /review
    success, output = execute_slash_command(
        "/review", [adw_id, spec_file], adw_id, "reviewer"
    )

    if success:
        state.update(review_passed=True)
        state.mark_phase_complete(ADWPhase.REVIEW)
        state.save()
        print()
        print(f"[SUCCESS] Review phase completed")
    else:
        state.update(review_passed=False)
        state.add_error(f"Review failed: {output}")
        state.save()
        print()
        print(f"[ERROR] Review phase failed")
        print(f"Error: {output}")
        sys.exit(1)

    # Output state for chaining
    print()
    print(
        json.dumps(
            {
                "adw_id": adw_id,
                "spec_file": spec_file,
                "phase": "review",
                "review_passed": state.data.review_passed,
                "success": True,
            }
        )
    )


if __name__ == "__main__":
    main()
