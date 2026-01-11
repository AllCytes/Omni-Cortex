#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Validate Phase - Visual validation using /validate with Chrome MCP."""

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
        print("Usage: uv run adw_validate.py <adw-id>")
        print("\nExample:")
        print("  uv run adw_validate.py abc12345")
        sys.exit(1)

    adw_id = sys.argv[1]

    print(f"{'=' * 50}")
    print(f"ADW VALIDATE PHASE")
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
        print("Run plan and build phases first")
        sys.exit(1)

    state.update(current_phase=ADWPhase.VALIDATE)
    state.save()

    # Ensure screenshot directory exists
    screenshot_dir = state.get_screenshot_dir("validate")
    ensure_directory(screenshot_dir)
    print(f"Screenshots will be saved to: {screenshot_dir}")
    print()

    print("[INFO] Executing /validate...")

    # Execute /validate with ADW context
    success, output = execute_slash_command(
        "/validate", [f"--adw-id={adw_id}"], adw_id, "validator"
    )

    if success:
        state.update(validation_passed=True)
        state.mark_phase_complete(ADWPhase.VALIDATE)
        state.save()
        print()
        print(f"[SUCCESS] Validate phase completed")
        print(f"Screenshots: {screenshot_dir}")
    else:
        state.update(validation_passed=False)
        state.add_error(f"Validation failed: {output}")
        state.save()
        print()
        print(f"[ERROR] Validate phase failed")
        print(f"Error: {output}")
        sys.exit(1)

    # Output state for chaining
    print()
    print(
        json.dumps(
            {
                "adw_id": adw_id,
                "phase": "validate",
                "validation_passed": state.data.validation_passed,
                "screenshot_dir": screenshot_dir,
                "success": True,
            }
        )
    )


if __name__ == "__main__":
    main()
