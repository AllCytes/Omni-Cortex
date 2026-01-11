#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Security Phase - Security audit using /security command."""

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
        print("Usage: uv run adw_security.py <adw-id>")
        print("\nExample:")
        print("  uv run adw_security.py abc12345")
        sys.exit(1)

    adw_id = sys.argv[1]

    print(f"{'=' * 50}")
    print(f"ADW SECURITY PHASE")
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

    state.update(current_phase=ADWPhase.SECURITY)
    state.save()

    # Ensure output directory exists
    output_dir = state.get_output_dir("security")
    ensure_directory(output_dir)
    print(f"Output will be saved to: {output_dir}")
    print()

    print("[INFO] Executing /security...")

    # Execute /security
    success, output = execute_slash_command(
        "/security", [], adw_id, "security"
    )

    if success:
        state.update(security_passed=True)
        state.mark_phase_complete(ADWPhase.SECURITY)
        state.save()
        print()
        print(f"[SUCCESS] Security phase completed")
        print(f"No blocking security issues found")
    else:
        state.update(security_passed=False)
        state.add_error(f"Security audit failed: {output}")
        state.save()
        print()
        print(f"[ERROR] Security phase failed")
        print(f"Security issues found - release blocked")
        print(f"Error: {output}")
        sys.exit(1)

    # Output state for chaining
    print()
    print(
        json.dumps(
            {
                "adw_id": adw_id,
                "phase": "security",
                "security_passed": state.data.security_passed,
                "output_dir": output_dir,
                "success": True,
            }
        )
    )


if __name__ == "__main__":
    main()
