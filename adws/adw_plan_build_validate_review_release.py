#!/usr/bin/env python3
"""ADW Orchestrator: Plan -> Build -> Validate -> Review -> Release.

This orchestrator runs five phases in sequence:
1. PLAN: Creates a spec using /quick-plan
2. BUILD: Implements the plan using /build
3. VALIDATE: Validates with visual testing using /validate
4. REVIEW: Reviews implementation against spec using /adw-review
5. RELEASE: Git commit, push, and optional PyPI publish using /omni

Usage:
    uv run adws/adw_plan_build_validate_review_release.py "Your task description"
    python adws/adw_plan_build_validate_review_release.py "Add dark mode toggle"
    python adws/adw_plan_build_validate_review_release.py "Fix bug" --skip-pypi
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
from adw_review import run_review
from adw_release import run_release


async def run_plan_build_validate_review_release(
    task_description: str, skip_pypi: bool = False
) -> bool:
    """Execute the complete 5-phase workflow.

    Args:
        task_description: What to implement
        skip_pypi: If True, skip PyPI publish in release phase

    Returns:
        True if all phases successful
    """
    start_time = time.time()
    adw_id = generate_adw_id()

    print("\n" + "=" * 70)
    print("ADW ORCHESTRATOR: Plan -> Build -> Validate -> Review -> Release")
    print("=" * 70)
    print(f"ADW ID: {adw_id}")
    print(f"Task: {task_description}")
    print(f"Skip PyPI: {skip_pypi}")
    print("=" * 70 + "\n")

    # Phase 1: PLAN
    print("\n" + "-" * 50)
    print("PHASE 1/5: PLAN")
    print("-" * 50)

    plan_success, state = await run_plan(task_description, adw_id)

    if not plan_success:
        print("\n[ORCHESTRATOR] Plan phase failed. Stopping workflow.")
        state.mark_failed("Plan phase failed")
        return False

    print(f"\n[ORCHESTRATOR] Plan complete. Spec: {state.spec}")

    # Phase 2: BUILD
    print("\n" + "-" * 50)
    print("PHASE 2/5: BUILD")
    print("-" * 50)

    build_success = await run_build(state)

    if not build_success:
        print("\n[ORCHESTRATOR] Build phase failed. Stopping workflow.")
        state.mark_failed("Build phase failed")
        return False

    print("\n[ORCHESTRATOR] Build complete.")

    # Phase 3: VALIDATE
    print("\n" + "-" * 50)
    print("PHASE 3/5: VALIDATE")
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

    # Phase 4: REVIEW
    print("\n" + "-" * 50)
    print("PHASE 4/5: REVIEW")
    print("-" * 50)

    review_success = await run_review(state)

    if not review_success:
        print("\n[ORCHESTRATOR] Review phase failed.")
        print("[ORCHESTRATOR] Implementation does not match spec requirements.")
        print("[ORCHESTRATOR] Fix review issues before releasing.")
        state.mark_failed("Review phase failed")
        return False

    print("\n[ORCHESTRATOR] Review complete.")

    # Phase 5: RELEASE
    print("\n" + "-" * 50)
    print("PHASE 5/5: RELEASE")
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
        description="ADW Orchestrator: Plan -> Build -> Validate -> Review -> Release (5 phases)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This workflow is ideal for:
- Complete feature implementation from planning to deployment
- Ensuring code quality with validation and review
- Production-ready releases with all checks

Examples:
  uv run adws/adw_plan_build_validate_review_release.py "Add dark mode toggle"
  python adws/adw_plan_build_validate_review_release.py "Fix authentication bug" --skip-pypi
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
        run_plan_build_validate_review_release(args.task, args.skip_pypi)
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
