#!/usr/bin/env python3
"""ADW Validate Phase - Visual validation using /validate."""

import asyncio
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.state import ADWState
from adw_modules.agent import run_skill
from adw_modules.utils import get_phase_dir, cleanup_dashboard_ports


async def run_validate(state: ADWState) -> bool:
    """Execute the validate phase.

    Args:
        state: ADW state from previous phases

    Returns:
        True if successful
    """
    print(f"\n[ADW Validate] Starting validate phase")
    print(f"[ADW Validate] ID: {state.adw_id}")

    if not state.is_phase_completed(ADWPhase.BUILD):
        print("[ADW Validate] Warning: Build phase not completed.")

    state.start_phase(ADWPhase.VALIDATE)

    # Prepare screenshots directory
    screenshots_dir = get_phase_dir(state.adw_id, "validate") / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    # Run /validate skill
    validate_prompt = f"""Validate the implementation for ADW: {state.adw_id}

Task: {state.task}
Spec: {state.spec or 'No spec file'}

Run visual validation tests and take screenshots to verify:
1. The implementation works as expected
2. The UI looks correct (if applicable)
3. Key functionality is operational

Save screenshots to: {screenshots_dir}

Report any issues found."""

    success, output, output_file = await run_skill(
        skill_name="validate",
        args=validate_prompt,
        adw_id=state.adw_id,
        phase="validate",
    )

    # Collect any screenshots as artifacts
    artifacts = [str(p) for p in screenshots_dir.glob("*.png")]

    if success:
        state.complete_phase(
            ADWPhase.VALIDATE,
            success=True,
            output_file=output_file,
            artifacts=artifacts,
        )
        print(f"[ADW Validate] Phase completed with {len(artifacts)} screenshots")
    else:
        state.complete_phase(
            ADWPhase.VALIDATE,
            success=False,
            error_message=output,
            artifacts=artifacts,
        )
        print(f"[ADW Validate] Phase failed: {output}")

    # Cleanup: Kill any orphaned dashboard processes
    print("[ADW Validate] Cleaning up dashboard processes...")
    cleanup_dashboard_ports(port=8765, verbose=True)

    return success


def main():
    """CLI entry point - requires existing state."""
    print("Validate phase requires state from previous phases.")
    print("Use adw_plan_build_validate.py for full workflow.")
    sys.exit(1)


if __name__ == "__main__":
    main()
