#!/usr/bin/env python3
"""ADW Orchestrator: Build -> Validate -> Release (3-Phase).

This orchestrator runs three phases in sequence, using an EXISTING spec file:
1. BUILD: Implements the plan using /build
2. VALIDATE: Validates with visual testing and backend log checking using /validate
3. RELEASE: Git commit, push, and optional PyPI publish using /omni

Use this when you already have a spec written in specs/todo/ and want to skip planning.

Usage:
    uv run adws/adw_build_validate_release.py specs/todo/my-feature.md
    python adws/adw_build_validate_release.py specs/todo/response-composer-feature.md
    python adws/adw_build_validate_release.py specs/todo/my-feature.md --skip-pypi
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
from adw_modules.utils import generate_adw_id, format_duration
from adw_build import run_build
from adw_validate import run_validate
from adw_release import run_release


async def run_build_validate_release(
    spec_path: str, skip_pypi: bool = False
) -> bool:
    """Execute the 3-phase workflow with an existing spec.

    Args:
        spec_path: Path to existing spec file (e.g., specs/todo/my-feature.md)
        skip_pypi: If True, skip PyPI publish in release phase

    Returns:
        True if all phases successful
    """
    start_time = time.time()
    adw_id = generate_adw_id()

    # Validate spec exists
    spec_file = Path(spec_path)
    if not spec_file.exists():
        print(f"\n[ERROR] Spec file not found: {spec_path}")
        return False

    print("\n" + "=" * 70)
    print("ADW ORCHESTRATOR: Build -> Validate -> Release (3-Phase)")
    print("=" * 70)
    print(f"ADW ID: {adw_id}")
    print(f"Spec: {spec_path}")
    print(f"Skip PyPI: {skip_pypi}")
    print("=" * 70 + "\n")

    # Create state with existing spec (skip plan phase)
    state = ADWState(adw_id)
    state.set_spec_file(str(spec_file.absolute()))

    # Mark plan as already completed (we're using existing spec)
    state.data.completed_phases.append(ADWPhase.PLAN.value)

    # Phase 1: BUILD
    print("\n" + "-" * 50)
    print("PHASE 1/3: BUILD")
    print("-" * 50)

    build_success = await run_build(state)

    if not build_success:
        print("\n[ORCHESTRATOR] Build phase failed. Stopping workflow.")
        state.mark_failed("Build phase failed")
        return False

    print("\n[ORCHESTRATOR] Build complete.")

    # Phase 2: VALIDATE
    print("\n" + "-" * 50)
    print("PHASE 2/3: VALIDATE")
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
        spec_path_obj = Path(state.spec)
        if spec_path_obj.exists() and "specs/todo/" in str(spec_path_obj):
            done_dir = Path("specs/done")
            done_dir.mkdir(parents=True, exist_ok=True)
            new_spec_path = done_dir / spec_path_obj.name
            spec_path_obj.rename(new_spec_path)
            state.spec = str(new_spec_path)
            print(f"\n[ORCHESTRATOR] Moved spec: {spec_path_obj.name} -> specs/done/")

    # Phase 3: RELEASE
    print("\n" + "-" * 50)
    print("PHASE 3/3: RELEASE")
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
    print("ADW WORKFLOW COMPLETED SUCCESSFULLY (3-Phase)")
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
        description="ADW Orchestrator: Build -> Validate -> Release (3 phases, uses existing spec)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Use this when you already have a spec file and want to skip the planning phase.

Examples:
  uv run adws/adw_build_validate_release.py specs/todo/response-composer-feature.md
  python adws/adw_build_validate_release.py specs/todo/my-feature.md --skip-pypi
        """,
    )
    parser.add_argument("spec", help="Path to existing spec file (e.g., specs/todo/my-feature.md)")
    parser.add_argument(
        "--skip-pypi",
        action="store_true",
        help="Skip PyPI publish, only do git operations",
    )

    args = parser.parse_args()

    success = asyncio.run(
        run_build_validate_release(args.spec, args.skip_pypi)
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
