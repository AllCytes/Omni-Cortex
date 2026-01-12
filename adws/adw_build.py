#!/usr/bin/env python3
"""ADW Build Phase - Implements the plan using /build."""

import asyncio
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.state import ADWState
from adw_modules.agent import run_skill
from adw_modules.utils import get_project_root


async def run_build(state: ADWState) -> bool:
    """Execute the build phase.

    Args:
        state: ADW state with spec file from plan phase

    Returns:
        True if successful
    """
    print(f"\n[ADW Build] Starting build phase")
    print(f"[ADW Build] ID: {state.adw_id}")

    if not state.spec:
        error = "No spec file found. Run plan phase first."
        print(f"[ADW Build] Error: {error}")
        state.complete_phase(ADWPhase.BUILD, success=False, error_message=error)
        return False

    print(f"[ADW Build] Spec: {state.spec}")

    state.start_phase(ADWPhase.BUILD)

    # Read the spec file to pass to build
    spec_content = ""
    spec_path = Path(state.spec)
    if spec_path.exists():
        spec_content = spec_path.read_text(encoding='utf-8')

    # Run /build skill with spec reference
    build_prompt = f"""Build the implementation based on the following spec:

Spec file: {state.spec}

{spec_content[:2000]}  # Truncate if very long

Implement all items in the spec completely."""

    success, output, output_file = await run_skill(
        skill_name="build",
        args=build_prompt,
        adw_id=state.adw_id,
        phase="build",
    )

    if success:
        state.complete_phase(
            ADWPhase.BUILD,
            success=True,
            output_file=output_file,
        )
        print("[ADW Build] Phase completed successfully")
    else:
        state.complete_phase(
            ADWPhase.BUILD,
            success=False,
            error_message=output,
        )
        print(f"[ADW Build] Phase failed: {output}")

    return success


def main():
    """CLI entry point - requires existing state."""
    print("Build phase requires state from plan phase.")
    print("Use adw_plan_build_validate.py for full workflow.")
    sys.exit(1)


if __name__ == "__main__":
    main()
