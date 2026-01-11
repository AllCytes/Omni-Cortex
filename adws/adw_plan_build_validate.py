#!/usr/bin/env python3
"""ADW Orchestrator: Plan -> Build -> Validate.

This orchestrator runs three phases in sequence:
1. PLAN: Creates a spec using /quick-plan
2. BUILD: Implements the plan using /build
3. VALIDATE: Validates the implementation using /validate

Usage:
    uv run adws/adw_plan_build_validate.py "Your task description"
    python adws/adw_plan_build_validate.py "Add dark mode toggle"
"""

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


async def run_plan_build_validate(task_description: str) -> bool:
    """Execute the complete Plan -> Build -> Validate workflow.

    Args:
        task_description: What to implement

    Returns:
        True if all phases successful
    """
    start_time = time.time()
    adw_id = generate_adw_id()

    print("\n" + "=" * 70)
    print("ADW ORCHESTRATOR: Plan -> Build -> Validate")
    print("=" * 70)
    print(f"ADW ID: {adw_id}")
    print(f"Task: {task_description}")
    print("=" * 70 + "\n")

    # Phase 1: PLAN
    print("\n" + "-" * 50)
    print("PHASE 1/3: PLAN")
    print("-" * 50)

    plan_success, state = await run_plan(task_description, adw_id)

    if not plan_success:
        print("\n[ORCHESTRATOR] Plan phase failed. Stopping workflow.")
        state.mark_failed("Plan phase failed")
        return False

    print(f"\n[ORCHESTRATOR] Plan complete. Spec: {state.spec}")

    # Phase 2: BUILD
    print("\n" + "-" * 50)
    print("PHASE 2/3: BUILD")
    print("-" * 50)

    build_success = await run_build(state)

    if not build_success:
        print("\n[ORCHESTRATOR] Build phase failed. Stopping workflow.")
        state.mark_failed("Build phase failed")
        return False

    print("\n[ORCHESTRATOR] Build complete.")

    # Phase 3: VALIDATE
    print("\n" + "-" * 50)
    print("PHASE 3/3: VALIDATE")
    print("-" * 50)

    validate_success = await run_validate(state)

    if not validate_success:
        print("\n[ORCHESTRATOR] Validate phase failed.")
        state.mark_failed("Validate phase failed")
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
    if len(sys.argv) < 2:
        print("ADW Orchestrator: Plan -> Build -> Validate")
        print()
        print("Usage:")
        print("  uv run adws/adw_plan_build_validate.py <task_description>")
        print("  python adws/adw_plan_build_validate.py <task_description>")
        print()
        print("Examples:")
        print('  uv run adws/adw_plan_build_validate.py "Add dark mode toggle"')
        print('  uv run adws/adw_plan_build_validate.py "Fix dashboard stats not showing"')
        print()
        print("This will:")
        print("  1. Create a spec using /quick-plan")
        print("  2. Build the implementation using /build")
        print("  3. Validate with visual testing using /validate")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    success = asyncio.run(run_plan_build_validate(task))

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
