#!/usr/bin/env python3
"""ADW Security Fix Phase - Fix security issues using /security-fix."""

import asyncio
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.state import ADWState
from adw_modules.agent import run_skill, track_error, MAX_RETRIES


async def run_security_fix(state: ADWState) -> bool:
    """Execute the security fix phase.

    Reads the most recent security audit and implements fixes.

    Args:
        state: ADW state from previous phases

    Returns:
        True if successful
    """
    print(f"\n[ADW Security Fix] Starting security fix phase")
    print(f"[ADW Security Fix] ID: {state.adw_id}")

    # Check if security phase was completed
    if not state.is_phase_completed(ADWPhase.SECURITY):
        print("[ADW Security Fix] Warning: Security audit phase not completed.")

    state.start_phase(ADWPhase.SECURITY_FIX)

    # Run /security-fix skill (defaults to most recent audit)
    fix_prompt = f"""Execute /security-fix to fix the security issues found in the most recent audit.

ADW: {state.adw_id}
Task: {state.task}

Fix all HIGH and CRITICAL severity issues.
For MEDIUM issues, fix if straightforward.
Document any issues that cannot be fixed automatically.
"""

    success, output, output_file = await run_skill(
        skill_name="security-fix",
        args=fix_prompt,
        adw_id=state.adw_id,
        phase="security-fix",
    )

    if success:
        state.complete_phase(
            ADWPhase.SECURITY_FIX,
            success=True,
            output_file=output_file,
        )
        print("[ADW Security Fix] Phase completed successfully")
    else:
        # Track the failure for retrospective visibility
        track_error(
            error_msg=output,
            adw_id=state.adw_id,
            phase="security-fix",
            agent_name="security_fix",
            is_unresolved_final=True,
        )
        state.complete_phase(
            ADWPhase.SECURITY_FIX,
            success=False,
            error_message=output,
        )
        print(f"[ADW Security Fix] Phase failed: {output}")

    return success


def main():
    """CLI entry point - requires existing state."""
    print("Security Fix phase requires state from previous phases.")
    print("Use adw_complete_sdlc.py for full workflow.")
    sys.exit(1)


if __name__ == "__main__":
    main()
