#!/usr/bin/env python3
"""ADW Orchestrator: Review -> Release.

This orchestrator runs two phases in sequence:
1. REVIEW: Reviews implementation against spec
2. RELEASE: Git commit, push, and optional PyPI publish

Usage:
    uv run adws/adw_review_release.py <adw-id> <spec-file>
    python adws/adw_review_release.py adw_1234567890_abc123 specs/done/feature.md
    python adws/adw_review_release.py adw_1234567890_abc123 specs/done/feature.md --skip-pypi
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.state import ADWState
from adw_modules.utils import format_duration
from adw_review import run_review
from adw_release import run_release


async def run_review_release(adw_id: str, spec_file: str, skip_pypi: bool = False) -> bool:
    """Execute the Review -> Release workflow.

    Args:
        adw_id: Existing ADW ID from previous phases
        spec_file: Path to spec file
        skip_pypi: If True, skip PyPI publish

    Returns:
        True if all phases successful
    """
    start_time = time.time()

    print("\n" + "=" * 70)
    print("ADW ORCHESTRATOR: Review -> Release")
    print("=" * 70)
    print(f"ADW ID: {adw_id}")
    print(f"Spec: {spec_file}")
    print(f"Skip PyPI: {skip_pypi}")
    print("=" * 70 + "\n")

    # Load existing state (ADWState automatically loads from file if it exists)
    state = ADWState(adw_id=adw_id, task_description=f"Review and release: {spec_file}")

    # Update spec file in state
    if spec_file:
        state.set_spec_file(spec_file)

    # Phase 1: REVIEW
    print("\n" + "-" * 50)
    print("PHASE 1/2: REVIEW")
    print("-" * 50)

    review_success = await run_review(state)

    if not review_success:
        print("\n[ORCHESTRATOR] Review phase failed.")
        print("[ORCHESTRATOR] Fix issues before releasing.")
        state.mark_failed("Review phase failed")
        return False

    print("\n[ORCHESTRATOR] Review complete.")

    # Phase 2: RELEASE
    print("\n" + "-" * 50)
    print("PHASE 2/2: RELEASE")
    print("-" * 50)

    release_success = await run_release(state, skip_pypi=skip_pypi)

    if not release_success:
        print("\n[ORCHESTRATOR] Release phase failed.")
        state.mark_failed("Release phase failed")
        return False

    # All phases complete
    state.mark_completed()
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("ADW WORKFLOW COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"ADW ID: {adw_id}")
    print(f"Duration: {format_duration(elapsed)}")
    print(f"Phases completed: {len(state.data.completed_phases)}")
    print(f"State file: agents/{adw_id}/adw_state.json")
    if state.spec:
        print(f"Spec file: {state.spec}")
    print("=" * 70 + "\n")

    return True


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ADW Orchestrator: Review -> Release",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run adws/adw_review_release.py adw_1234567890_abc123 specs/done/feature.md
  python adws/adw_review_release.py adw_1234567890_abc123 specs/done/feature.md --skip-pypi
        """,
    )
    parser.add_argument("adw_id", help="ADW ID from previous phases")
    parser.add_argument("spec_file", help="Path to spec file")
    parser.add_argument(
        "--skip-pypi",
        action="store_true",
        help="Skip PyPI publish, only do git operations",
    )

    args = parser.parse_args()

    success = asyncio.run(run_review_release(args.adw_id, args.spec_file, args.skip_pypi))

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
