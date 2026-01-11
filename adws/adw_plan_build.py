#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Plan + Build Orchestrator."""

import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adw_modules.utils import generate_adw_id


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_plan_build.py <request> [adw-id]")
        print("\nThis runs: Plan -> Build")
        print("\nExamples:")
        print('  uv run adw_plan_build.py "Add dark mode toggle"')
        print('  uv run adw_plan_build.py "Fix login bug" custom_id')
        sys.exit(1)

    request = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else generate_adw_id()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"{'#' * 60}")
    print(f"# ADW ORCHESTRATOR: Plan + Build")
    print(f"{'#' * 60}")
    print(f"ADW ID: {adw_id}")
    print(f"Request: {request[:80]}{'...' if len(request) > 80 else ''}")
    print()

    # Plan phase
    print(f"\n{'=' * 60}")
    print(f"PHASE 1: PLAN")
    print(f"{'=' * 60}")
    plan_cmd = ["uv", "run", os.path.join(script_dir, "adw_plan.py"), request, adw_id]
    plan = subprocess.run(plan_cmd)
    if plan.returncode != 0:
        print("\n[ORCHESTRATOR] Plan phase failed, stopping workflow")
        sys.exit(1)

    # Build phase
    print(f"\n{'=' * 60}")
    print(f"PHASE 2: BUILD")
    print(f"{'=' * 60}")
    build_cmd = ["uv", "run", os.path.join(script_dir, "adw_build.py"), adw_id]
    build = subprocess.run(build_cmd)
    if build.returncode != 0:
        print("\n[ORCHESTRATOR] Build phase failed, stopping workflow")
        sys.exit(1)

    print(f"\n{'#' * 60}")
    print(f"# WORKFLOW COMPLETED: Plan + Build")
    print(f"{'#' * 60}")
    print(f"ADW ID: {adw_id}")
    print(f"State: agents/{adw_id}/adw_state.json")
    print()
    print("Next steps:")
    print(f"  - Validate: uv run adws/adw_validate.py {adw_id}")
    print(f"  - Review:   uv run adws/adw_review.py {adw_id}")


if __name__ == "__main__":
    main()
