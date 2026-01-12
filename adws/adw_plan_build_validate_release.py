#!/usr/bin/env python3
"""ADW Orchestrator: Plan -> Build -> Validate -> Release (4-Phase).

This orchestrator runs four phases in sequence:
1. PLAN: Creates a spec using /quick-plan
2. BUILD: Implements the plan using /build
3. VALIDATE: Validates with visual testing and backend log checking using /validate
4. RELEASE: Git commit, push, and optional PyPI publish using /omni

This is the "quick deploy" workflow - skips review phase for faster iteration on bug fixes
and small features where validation alone provides sufficient confidence.

Use this for:
- Bug fixes
- Small UI improvements
- Feature tweaks
- Changes that are obviously correct after validation

Use 5-phase workflow for:
- Major features
- Breaking changes
- Security-sensitive changes
- When you need spec compliance review

Usage:
    uv run adws/adw_plan_build_validate_release.py "Your task description"
    python adws/adw_plan_build_validate_release.py "Fix dropdown bug"
    python adws/adw_plan_build_validate_release.py "Add tooltip" --skip-pypi
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.utils import generate_adw_id, format_duration
from adw_plan import run_plan
from adw_build import run_build
from adw_validate import run_validate
from adw_release import run_release


async def run_plan_build_validate_release(
    task_description: str, skip_pypi: bool = False
) -> bool:
    """Execute the complete 4-phase workflow.

    Args:
        task_description: What to implement
        skip_pypi: If True, skip PyPI publish in release phase

    Returns:
        True if all phases successful
    """
    start_time = time.time()
    adw_id = generate_adw_id()

    print("\n" + "=" * 70)
    print("ADW ORCHESTRATOR: Plan -> Build -> Validate -> Release (4-Phase)")
    print("=" * 70)
    print(f"ADW ID: {adw_id}")
    print(f"Task: {task_description}")
    print(f"Skip PyPI: {skip_pypi}")
    print("=" * 70 + "\n")

    # Phase 1: PLAN
    print("\n" + "-" * 50)
    print("PHASE 1/4: PLAN")
    print("-" * 50)

    plan_success, state = await run_plan(task_description, adw_id)

    if not plan_success:
        print("\n[ORCHESTRATOR] Plan phase failed. Stopping workflow.")
        state.mark_failed("Plan phase failed")
        return False

    print(f"\n[ORCHESTRATOR] Plan complete. Spec: {state.spec}")

    # Phase 2: BUILD
    print("\n" + "-" * 50)
    print("PHASE 2/4: BUILD")
    print("-" * 50)

    build_success = await run_build(state)

    if not build_success:
        print("\n[ORCHESTRATOR] Build phase failed. Stopping workflow.")
        state.mark_failed("Build phase failed")
        return False

    print("\n[ORCHESTRATOR] Build complete.")

    # Phase 3: VALIDATE
    print("\n" + "-" * 50)
    print("PHASE 3/4: VALIDATE")
    print("-" * 50)

    validate_success = await run_validate(state)

    if not validate_success:
        print("\n[ORCHESTRATOR] Validate phase failed. Stopping workflow.")
        print("[ORCHESTRATOR] Fix validation issues before proceeding.")
        state.mark_failed("Validate phase failed")
        return False

    print("\n[ORCHESTRATOR] Validate complete.")

    # Move spec file from todo/ to done/ after successful validation
    if state.spec:
        spec_path = Path(state.spec)
        if spec_path.exists() and "specs/todo/" in str(spec_path):
            done_dir = Path("specs/done")
            done_dir.mkdir(parents=True, exist_ok=True)
            new_spec_path = done_dir / spec_path.name
            spec_path.rename(new_spec_path)
            state.spec = str(new_spec_path)
            print(f"\n[ORCHESTRATOR] Moved spec: {spec_path.name} -> specs/done/")

    # Phase 4: RELEASE
    print("\n" + "-" * 50)
    print("PHASE 4/4: RELEASE")
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
    print("ADW WORKFLOW COMPLETED SUCCESSFULLY (4-Phase)")
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
        description="ADW Orchestrator: Plan -> Build -> Validate -> Release (4 phases)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This is the "quick deploy" workflow - ideal for bug fixes and small features.
Skips the review phase for faster iteration while still ensuring quality through validation.

Use this for:
- Bug fixes (like "Fix dropdown not closing")
- Small UI improvements (like "Add loading spinner")
- Feature tweaks (like "Change button color")
- Changes that are obviously correct after validation

Use 5-phase workflow (with review) for:
- Major features
- Breaking changes
- Security-sensitive changes
- When you need spec compliance review

Examples:
  uv run adws/adw_plan_build_validate_release.py "Fix memory selector bug"
  python adws/adw_plan_build_validate_release.py "Add dark mode toggle" --skip-pypi
        """,
    )
    parser.add_argument("task", help="Task description for the feature/fix")
    parser.add_argument(
        "--skip-pypi",
        action="store_true",
        help="Skip PyPI publish, only do git operations",
    )

    args = parser.parse_args()

    success = asyncio.run(
        run_plan_build_validate_release(args.task, args.skip_pypi)
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
