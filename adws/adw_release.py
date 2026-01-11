#!/usr/bin/env python3
"""ADW Release Phase - Git commit, push, and optional PyPI publish using /omni."""

import asyncio
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.state import ADWState
from adw_modules.agent import run_skill


async def run_release(state: ADWState, skip_pypi: bool = False) -> bool:
    """Execute the release phase.

    Args:
        state: ADW state from previous phases
        skip_pypi: If True, only do git operations, skip PyPI publish

    Returns:
        True if successful
    """
    print(f"\n[ADW Release] Starting release phase")
    print(f"[ADW Release] ID: {state.adw_id}")
    print(f"[ADW Release] Skip PyPI: {skip_pypi}")

    state.start_phase(ADWPhase.RELEASE)

    # Run /omni skill for release
    release_prompt = f"""Execute /omni to release the changes from this ADW session.

ADW: {state.adw_id}
Task: {state.task}

{"Skip PyPI publish, only do git operations." if skip_pypi else "Do the full release including PyPI publish if version was bumped."}

Steps:
1. Stage all changes (git add)
2. Create commit with descriptive message referencing the task
3. Push to remote
4. {"Skip PyPI" if skip_pypi else "Publish to PyPI if appropriate"}
"""

    success, output, output_file = await run_skill(
        skill_name="omni",
        args="--git-only" if skip_pypi else "",
        adw_id=state.adw_id,
        phase="release",
    )

    if success:
        state.complete_phase(
            ADWPhase.RELEASE,
            success=True,
            output_file=output_file,
        )
        print("[ADW Release] Phase completed successfully")
    else:
        state.complete_phase(
            ADWPhase.RELEASE,
            success=False,
            error_message=output,
        )
        print(f"[ADW Release] Phase failed: {output}")

    return success


def main():
    """CLI entry point - requires existing state."""
    print("Release phase requires state from previous phases.")
    print("Use adw_complete_sdlc.py for full workflow.")
    sys.exit(1)


if __name__ == "__main__":
    main()
