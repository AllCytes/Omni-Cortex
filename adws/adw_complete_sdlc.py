#!/usr/bin/env python3
"""ADW Complete SDLC Orchestrator: 9-Phase Workflow.

This orchestrator runs the complete 9-phase SDLC workflow:

1. PLAN           → Creates spec using /quick-plan
2. BUILD          → Implements the plan using /build
3. VALIDATE       → Validates with visual testing using /validate
4. SECURITY       → Audits for vulnerabilities using /security
5. SECURITY-FIX   → Fixes security issues using /security-fix
6. REVIEW         → Compares implementation to spec using /adw-review
7. RETROSPECTIVE  → Documents lessons learned using /retrospective
8. APPLY-LEARNINGS → Implements improvements using /apply-learnings
9. RELEASE        → Git commit, push, PyPI publish using /omni

Usage:
    uv run adws/adw_complete_sdlc.py "Your task description"
    uv run adws/adw_complete_sdlc.py "Add dark mode toggle" --skip-release
    uv run adws/adw_complete_sdlc.py "Fix auth bug" --skip-security --skip-release

Options:
    --skip-security     Skip security audit phases (4-5)
    --skip-release      Skip release phase (9)
    --skip-learnings    Skip retrospective and apply-learnings (7-8)
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
from adw_modules.agent import store_in_cortex

# Import individual phase runners
from adw_plan import run_plan
from adw_build import run_build
from adw_validate import run_validate
from adw_security import run_security
from adw_security_fix import run_security_fix
from adw_review import run_review
from adw_retrospective import run_retrospective
from adw_apply_learnings import run_apply_learnings
from adw_release import run_release


async def run_complete_sdlc(
    task_description: str,
    skip_security: bool = False,
    skip_release: bool = False,
    skip_learnings: bool = False,
    skip_pypi: bool = False,
) -> bool:
    """Execute the complete 9-phase SDLC workflow.

    Args:
        task_description: What to implement
        skip_security: Skip security audit phases (4-5)
        skip_release: Skip release phase (9)
        skip_learnings: Skip retrospective and apply-learnings (7-8)
        skip_pypi: Only do git operations, skip PyPI publish

    Returns:
        True if all phases successful
    """
    start_time = time.time()
    adw_id = generate_adw_id()

    print("\n" + "=" * 70)
    print("ADW COMPLETE SDLC ORCHESTRATOR (9 Phases)")
    print("=" * 70)
    print(f"ADW ID: {adw_id}")
    print(f"Task: {task_description}")
    print(f"Skip Security: {skip_security}")
    print(f"Skip Learnings: {skip_learnings}")
    print(f"Skip Release: {skip_release}")
    print("=" * 70 + "\n")

    # Track phase count for display
    total_phases = 9
    if skip_security:
        total_phases -= 2
    if skip_learnings:
        total_phases -= 2
    if skip_release:
        total_phases -= 1

    current_phase = 0

    def phase_header(name: str, description: str):
        nonlocal current_phase
        current_phase += 1
        print(f"\n{'-' * 50}")
        print(f"PHASE {current_phase}/{total_phases}: {name}")
        print(f"{description}")
        print(f"{'-' * 50}")

    # ===== PHASE 1: PLAN =====
    phase_header("PLAN", "Creating implementation spec")
    plan_success, state = await run_plan(task_description, adw_id)

    if not plan_success:
        print("\n[ORCHESTRATOR] Plan phase failed. Stopping workflow.")
        state.mark_failed("Plan phase failed")
        store_in_cortex(
            content=f"ADW {adw_id} FAILED at Plan phase: {task_description}",
            tags=["adw-failed", "plan", f"adw_{adw_id}"],
            importance=85,
        )
        return False

    print(f"\n[ORCHESTRATOR] Plan complete. Spec: {state.spec}")

    # ===== PHASE 2: BUILD =====
    phase_header("BUILD", "Implementing the spec")
    build_success = await run_build(state)

    if not build_success:
        print("\n[ORCHESTRATOR] Build phase failed. Stopping workflow.")
        state.mark_failed("Build phase failed")
        return False

    print("\n[ORCHESTRATOR] Build complete.")

    # ===== PHASE 3: VALIDATE =====
    phase_header("VALIDATE", "Visual validation and testing")
    validate_success = await run_validate(state)

    if not validate_success:
        print("\n[ORCHESTRATOR] Validate phase failed. Continuing with caution.")
        # Don't stop - validation failures aren't always fatal

    print("\n[ORCHESTRATOR] Validate complete.")

    # ===== PHASE 4-5: SECURITY (optional) =====
    if not skip_security:
        # Phase 4: Security Audit
        phase_header("SECURITY", "Security vulnerability audit")
        security_success = await run_security(state)

        if not security_success:
            print("\n[ORCHESTRATOR] Security audit failed. Continuing.")

        # Phase 5: Security Fix
        phase_header("SECURITY-FIX", "Fixing security issues")
        security_fix_success = await run_security_fix(state)

        if not security_fix_success:
            print("\n[ORCHESTRATOR] Security fix phase failed. Continuing.")

    # ===== PHASE 6: REVIEW =====
    phase_header("REVIEW", "Spec compliance review")
    review_success = await run_review(state)

    if not review_success:
        print("\n[ORCHESTRATOR] Review phase failed. Continuing.")

    # ===== PHASE 7-8: LEARNINGS (optional) =====
    if not skip_learnings:
        # Phase 7: Retrospective
        phase_header("RETROSPECTIVE", "Documenting lessons learned")
        retro_success = await run_retrospective(state)

        if not retro_success:
            print("\n[ORCHESTRATOR] Retrospective failed. Continuing.")

        # Phase 8: Apply Learnings
        phase_header("APPLY-LEARNINGS", "Implementing improvements")
        apply_success = await run_apply_learnings(state)

        if not apply_success:
            print("\n[ORCHESTRATOR] Apply learnings failed. Continuing.")

    # ===== PHASE 9: RELEASE (optional) =====
    if not skip_release:
        phase_header("RELEASE", "Git commit, push, and publish")
        release_success = await run_release(state, skip_pypi=skip_pypi)

        if not release_success:
            print("\n[ORCHESTRATOR] Release phase failed.")
            state.mark_failed("Release phase failed")
            return False

    # All phases complete
    state.mark_completed()
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("ADW COMPLETE SDLC WORKFLOW COMPLETED")
    print("=" * 70)
    print(f"ADW ID: {adw_id}")
    print(f"Duration: {format_duration(elapsed)}")
    print(f"Phases completed: {len(state.data.completed_phases)}/{total_phases}")
    print(f"State file: agents/{adw_id}/adw_state.json")
    if state.spec:
        print(f"Spec file: {state.spec}")
    print("=" * 70)

    # Store success in Cortex
    store_in_cortex(
        content=f"""ADW {adw_id} COMPLETED successfully.

Task: {task_description}
Duration: {format_duration(elapsed)}
Phases: {len(state.data.completed_phases)}
Spec: {state.spec}

Completed phases: {", ".join(p.value for p in state.data.completed_phases)}""",
        tags=["adw-completed", "success", f"adw_{adw_id}"],
        importance=80,
    )

    print("\n")
    return True


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ADW Complete SDLC Orchestrator - 9 Phase Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run adws/adw_complete_sdlc.py "Add dark mode toggle"
  uv run adws/adw_complete_sdlc.py "Fix auth bug" --skip-security
  uv run adws/adw_complete_sdlc.py "Add feature X" --skip-release
  uv run adws/adw_complete_sdlc.py "Refactor module" --git-only

Phases:
  1. PLAN           - Creates spec using /quick-plan
  2. BUILD          - Implements the plan using /build
  3. VALIDATE       - Visual validation using /validate
  4. SECURITY       - Security audit using /security
  5. SECURITY-FIX   - Fix security issues using /security-fix
  6. REVIEW         - Spec compliance using /adw-review
  7. RETROSPECTIVE  - Document lessons using /retrospective
  8. APPLY-LEARNINGS - Implement improvements using /apply-learnings
  9. RELEASE        - Git commit, push, PyPI using /omni
        """,
    )

    parser.add_argument(
        "task",
        nargs="*",
        help="Task description (what to implement)",
    )
    parser.add_argument(
        "--skip-security",
        action="store_true",
        help="Skip security audit phases (4-5)",
    )
    parser.add_argument(
        "--skip-release",
        action="store_true",
        help="Skip release phase (9)",
    )
    parser.add_argument(
        "--skip-learnings",
        action="store_true",
        help="Skip retrospective and apply-learnings phases (7-8)",
    )
    parser.add_argument(
        "--git-only",
        action="store_true",
        help="Only do git operations, skip PyPI publish",
    )

    args = parser.parse_args()

    if not args.task:
        parser.print_help()
        print("\nError: Task description is required.")
        sys.exit(1)

    task = " ".join(args.task)

    success = asyncio.run(
        run_complete_sdlc(
            task_description=task,
            skip_security=args.skip_security,
            skip_release=args.skip_release,
            skip_learnings=args.skip_learnings,
            skip_pypi=args.git_only,
        )
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
