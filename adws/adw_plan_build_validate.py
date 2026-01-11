#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Plan + Build + Validate Orchestrator."""

import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adw_modules.utils import generate_adw_id


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_plan_build_validate.py <request> [adw-id]")
        print("\nThis runs: Plan -> Build -> Validate")
        print("\nExamples:")
        print('  uv run adw_plan_build_validate.py "Add dark mode toggle"')
        print('  uv run adw_plan_build_validate.py "Fix login bug" custom_id')
        sys.exit(1)

    request = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else generate_adw_id()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"{'#' * 60}")
    print(f"# ADW ORCHESTRATOR: Plan + Build + Validate")
    print(f"{'#' * 60}")
    print(f"ADW ID: {adw_id}")
    print(f"Request: {request[:80]}{'...' if len(request) > 80 else ''}")
    print()

    phases = [
        ("PLAN", ["uv", "run", os.path.join(script_dir, "adw_plan.py"), request, adw_id]),
        ("BUILD", ["uv", "run", os.path.join(script_dir, "adw_build.py"), adw_id]),
        ("VALIDATE", ["uv", "run", os.path.join(script_dir, "adw_validate.py"), adw_id]),
    ]

    for i, (phase_name, cmd) in enumerate(phases, 1):
        print(f"\n{'=' * 60}")
        print(f"PHASE {i}: {phase_name}")
        print(f"{'=' * 60}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"\n[ORCHESTRATOR] {phase_name} phase failed, stopping workflow")
            sys.exit(1)

    print(f"\n{'#' * 60}")
    print(f"# WORKFLOW COMPLETED: Plan + Build + Validate")
    print(f"{'#' * 60}")
    print(f"ADW ID: {adw_id}")
    print(f"State: agents/{adw_id}/adw_state.json")
    print()
    print("Next steps:")
    print(f"  - Review: uv run adws/adw_review.py {adw_id}")
    print(f"  - Release: uv run adws/adw_release.py {adw_id}")


if __name__ == "__main__":
    main()
