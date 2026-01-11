#!/usr/bin/env python3
"""ADW Plan Phase - Creates a spec using /quick-plan."""

import asyncio
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.state import ADWState
from adw_modules.agent import run_skill
from adw_modules.utils import generate_adw_id, get_project_root


async def run_plan(task_description: str, adw_id: str = None) -> tuple[bool, ADWState]:
    """Execute the plan phase.

    Args:
        task_description: What to plan
        adw_id: Existing ADW ID or None to generate new

    Returns:
        Tuple of (success, state)
    """
    # Initialize state
    if adw_id is None:
        adw_id = generate_adw_id()

    state = ADWState(
        adw_id=adw_id,
        task_description=task_description,
        project_path=str(get_project_root()),
    )

    print(f"\n[ADW Plan] Starting plan phase")
    print(f"[ADW Plan] ID: {adw_id}")
    print(f"[ADW Plan] Task: {task_description}")

    state.start_phase(ADWPhase.PLAN)

    # Run /quick-plan skill (now async)
    success, output, output_file = await run_skill(
        skill_name="quick-plan",
        args=task_description,
        adw_id=adw_id,
        phase="plan",
    )

    if success:
        # Try to find the generated spec file in specs/todo/
        specs_todo_dir = get_project_root() / "specs" / "todo"
        if specs_todo_dir.exists():
            # Find most recent spec file in todo folder
            spec_files = sorted(specs_todo_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            if spec_files:
                state.set_spec_file(str(spec_files[0]))
                print(f"[ADW Plan] Spec file: {spec_files[0]}")

        state.complete_phase(
            ADWPhase.PLAN,
            success=True,
            output_file=output_file,
        )
        print("[ADW Plan] Phase completed successfully")
    else:
        state.complete_phase(
            ADWPhase.PLAN,
            success=False,
            error_message=output,
        )
        print(f"[ADW Plan] Phase failed: {output}")

    return success, state


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python adw_plan.py <task_description>")
        print("Example: python adw_plan.py 'Add dark mode toggle'")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    success, state = asyncio.run(run_plan(task))

    if success:
        print(f"\nPlan phase completed. ADW ID: {state.adw_id}")
        if state.spec:
            print(f"Spec file: {state.spec}")
    else:
        print("\nPlan phase failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
