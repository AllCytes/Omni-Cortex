#!/usr/bin/env python3
"""ADW Apply Learnings Phase - Implement improvements from retrospective."""

import asyncio
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.state import ADWState
from adw_modules.agent import run_skill, track_error


async def run_apply_learnings(state: ADWState) -> bool:
    """Execute the apply learnings phase.

    Reads the most recent retrospective and implements improvements.

    Args:
        state: ADW state from previous phases

    Returns:
        True if successful
    """
    print(f"\n[ADW Apply Learnings] Starting apply learnings phase")
    print(f"[ADW Apply Learnings] ID: {state.adw_id}")

    # Check if retrospective phase was completed
    if not state.is_phase_completed(ADWPhase.RETROSPECTIVE):
        print("[ADW Apply Learnings] Warning: Retrospective phase not completed.")

    state.start_phase(ADWPhase.APPLY_LEARNINGS)

    # Run /apply-learnings skill (defaults to most recent retrospective)
    apply_prompt = f"""Execute /apply-learnings to implement improvements from the most recent retrospective.

ADW: {state.adw_id}
Task: {state.task}

Apply actionable improvements:
1. Command updates - improve existing /commands
2. New templates - create reusable patterns
3. Documentation - add missing docs
4. Process improvements - update CLAUDE.md or workflows

Skip high-risk changes that need manual review.
"""

    success, output, output_file = await run_skill(
        skill_name="apply-learnings",
        args=apply_prompt,
        adw_id=state.adw_id,
        phase="apply-learnings",
    )

    if success:
        state.complete_phase(
            ADWPhase.APPLY_LEARNINGS,
            success=True,
            output_file=output_file,
        )
        print("[ADW Apply Learnings] Phase completed successfully")
    else:
        # Track the failure for visibility
        track_error(
            error_msg=output,
            adw_id=state.adw_id,
            phase="apply-learnings",
            agent_name="apply_learnings",
            is_unresolved_final=True,
        )
        state.complete_phase(
            ADWPhase.APPLY_LEARNINGS,
            success=False,
            error_message=output,
        )
        print(f"[ADW Apply Learnings] Phase failed: {output}")

    return success


def main():
    """CLI entry point - run apply learnings on an existing ADW session."""
    if len(sys.argv) < 2:
        print("ADW Apply Learnings: Implement improvements from retrospective")
        print()
        print("Usage:")
        print("  uv run adws/adw_apply_learnings.py <adw-id>")
        print("  python adws/adw_apply_learnings.py <adw-id>")
        print()
        print("Examples:")
        print('  uv run adws/adw_apply_learnings.py adw_1768194349_2ac26097')
        print()
        print("Note: This requires a retrospective to have been run first.")
        sys.exit(1)

    adw_id = sys.argv[1]

    # Load existing state
    state = ADWState(adw_id=adw_id)

    # Check if state file exists
    if not state.state_file.exists():
        print(f"Error: No ADW state found for {adw_id}")
        print(f"Expected state file: {state.state_file}")
        sys.exit(1)

    print(f"\n[ADW Apply Learnings] Starting for {adw_id}")
    print(f"[ADW Apply Learnings] Task: {state.task}")
    print(f"[ADW Apply Learnings] Completed phases: {len(state.data.completed_phases)}")

    success = asyncio.run(run_apply_learnings(state))

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
