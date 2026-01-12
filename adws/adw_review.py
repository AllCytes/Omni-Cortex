#!/usr/bin/env python3
"""ADW Review Phase - Spec compliance review using /review or /adw-review."""

import asyncio
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.state import ADWState
from adw_modules.agent import run_skill
from adw_modules.utils import cleanup_dashboard_ports


async def run_review(state: ADWState) -> bool:
    """Execute the spec compliance review phase.

    Args:
        state: ADW state from previous phases

    Returns:
        True if successful
    """
    print(f"\n[ADW Review] Starting review phase")
    print(f"[ADW Review] ID: {state.adw_id}")

    state.start_phase(ADWPhase.REVIEW)

    # Determine spec file for review
    spec_ref = state.spec or "the implementation"

    # Run /adw-review skill (more comprehensive than /review)
    review_prompt = f"""Execute /adw-review to compare the implementation against the spec.

ADW: {state.adw_id}
Task: {state.task}
Spec file: {spec_ref}

Review the implementation for:
1. Spec compliance - all requirements met
2. Code quality - follows best practices
3. Completeness - nothing missing
4. Visual validation - UI matches expectations (if applicable)
"""

    success, output, output_file = await run_skill(
        skill_name="adw-review",
        args=spec_ref,
        adw_id=state.adw_id,
        phase="review",
    )

    if success:
        state.complete_phase(
            ADWPhase.REVIEW,
            success=True,
            output_file=output_file,
        )
        print("[ADW Review] Phase completed successfully")
    else:
        state.complete_phase(
            ADWPhase.REVIEW,
            success=False,
            error_message=output,
        )
        print(f"[ADW Review] Phase failed: {output}")

    # Cleanup: Kill any orphaned dashboard processes
    print("[ADW Review] Cleaning up dashboard processes...")
    cleanup_dashboard_ports(port=8765, verbose=True)

    return success


def main():
    """CLI entry point - requires existing state."""
    print("Review phase requires state from previous phases.")
    print("Use adw_complete_sdlc.py for full workflow.")
    sys.exit(1)


if __name__ == "__main__":
    main()
