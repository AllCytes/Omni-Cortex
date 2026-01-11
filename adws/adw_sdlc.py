#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Full SDLC Orchestrator: Plan -> Build -> Validate -> Security -> Review -> Retrospective -> Release."""

import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adw_modules.utils import generate_adw_id


def main():
    # Parse flags
    skip_release = "--skip-release" in sys.argv
    skip_security = "--skip-security" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg not in ("--skip-release", "--skip-security")]

    if len(args) < 1:
        print("Usage: uv run adw_sdlc.py <request> [adw-id] [--skip-release] [--skip-security]")
        print("\nThis runs: Plan -> Build -> Validate -> Security -> Review -> Retrospective -> Release")
        print("\nOptions:")
        print("  --skip-release   Skip the release phase")
        print("  --skip-security  Skip the security audit phase")
        print("\nExamples:")
        print('  uv run adw_sdlc.py "Add dark mode toggle"')
        print('  uv run adw_sdlc.py "Fix login bug" custom_id')
        print('  uv run adw_sdlc.py "Add feature" --skip-release')
        print('  uv run adw_sdlc.py "Quick fix" --skip-security --skip-release')
        sys.exit(1)

    request = args[0]
    adw_id = args[1] if len(args) > 1 else generate_adw_id()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"{'#' * 60}")
    print(f"# ADW FULL SDLC ORCHESTRATOR")
    print(f"{'#' * 60}")
    print(f"ADW ID: {adw_id}")
    print(f"Request: {request[:80]}{'...' if len(request) > 80 else ''}")
    print(f"Skip security: {skip_security}")
    print(f"Skip release: {skip_release}")
    print()

    # Build phases list dynamically
    phases = [
        ("PLAN", ["uv", "run", os.path.join(script_dir, "adw_plan.py"), request, adw_id], True),
        ("BUILD", ["uv", "run", os.path.join(script_dir, "adw_build.py"), adw_id], True),
        ("VALIDATE", ["uv", "run", os.path.join(script_dir, "adw_validate.py"), adw_id], True),
    ]

    # Add Security phase (blocking - failures prevent release)
    if not skip_security:
        phases.append(("SECURITY", ["uv", "run", os.path.join(script_dir, "adw_security.py"), adw_id], True))

    phases.append(("REVIEW", ["uv", "run", os.path.join(script_dir, "adw_review.py"), adw_id], True))
    phases.append(("RETROSPECTIVE", ["uv", "run", os.path.join(script_dir, "adw_retrospective.py"), adw_id], False))  # Non-blocking

    if not skip_release:
        phases.append(("RELEASE", ["uv", "run", os.path.join(script_dir, "adw_release.py"), adw_id], True))

    total_phases = len(phases)
    completed = 0

    for i, (phase_name, cmd, is_blocking) in enumerate(phases, 1):
        print(f"\n{'=' * 60}")
        print(f"PHASE {i}/{total_phases}: {phase_name}")
        print(f"{'=' * 60}")
        result = subprocess.run(cmd)

        if result.returncode != 0:
            if is_blocking:
                print(f"\n[ORCHESTRATOR] {phase_name} phase failed, stopping workflow")
                print(f"Completed {completed}/{total_phases} phases")
                sys.exit(1)
            else:
                print(f"\n[ORCHESTRATOR] {phase_name} phase failed (non-blocking), continuing...")
        else:
            completed += 1

    print(f"\n{'#' * 60}")
    print(f"# FULL SDLC WORKFLOW COMPLETED")
    print(f"{'#' * 60}")
    print(f"ADW ID: {adw_id}")
    print(f"Phases completed: {completed}/{total_phases}")
    print(f"State: agents/{adw_id}/adw_state.json")
    print()

    if skip_security:
        print("Security audit was skipped. To run manually:")
        print(f"  uv run adws/adw_security.py {adw_id}")

    if skip_release:
        print("Release was skipped. To release:")
        print(f"  uv run adws/adw_release.py {adw_id}")


if __name__ == "__main__":
    main()
