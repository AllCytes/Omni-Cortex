#!/usr/bin/env python3
"""ADW Retrospective Phase - Document lessons learned using /retrospective."""

import asyncio
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.state import ADWState
from adw_modules.agent import run_skill


async def run_retrospective(state: ADWState) -> bool:
    """Execute the retrospective documentation phase.

    Args:
        state: ADW state from previous phases

    Returns:
        True if successful
    """
    print(f"\n[ADW Retrospective] Starting retrospective phase")
    print(f"[ADW Retrospective] ID: {state.adw_id}")

    state.start_phase(ADWPhase.RETROSPECTIVE)

    # Get completed phases for context
    completed = [p.value for p in state.data.completed_phases]

    # Run /retrospective skill
    retro_prompt = f"""Execute /retrospective to document lessons learned from this ADW session.

ADW: {state.adw_id}
Task: {state.task}
Completed phases: {", ".join(completed)}

Use Omni-Cortex to recall:
1. Any errors encountered during build (cortex_recall: "error adw_{state.adw_id}")
2. Any unresolved issues (cortex_recall: "unresolved needs-human")
3. Decisions made during implementation

Document:
1. What worked well
2. What didn't work (including errors from cortex)
3. Lessons learned
4. Actionable improvements
5. HUMAN ATTENTION REQUIRED section (for unresolved issues)
"""

    success, output, output_file = await run_skill(
        skill_name="retrospective",
        args=state.adw_id,
        adw_id=state.adw_id,
        phase="retrospective",
    )

    # Find generated retrospective files
    retro_files = list(Path("docs/retrospectives").glob("retrospective-*.md"))
    artifacts = [str(f) for f in retro_files] if retro_files else []

    if success:
        state.complete_phase(
            ADWPhase.RETROSPECTIVE,
            success=True,
            output_file=output_file,
            artifacts=artifacts,
        )
        print(f"[ADW Retrospective] Phase completed. Retro files: {len(artifacts)}")
    else:
        state.complete_phase(
            ADWPhase.RETROSPECTIVE,
            success=False,
            error_message=output,
        )
        print(f"[ADW Retrospective] Phase failed: {output}")

    return success


def main():
    """CLI entry point - requires existing state."""
    print("Retrospective phase requires state from previous phases.")
    print("Use adw_complete_sdlc.py for full workflow.")
    sys.exit(1)


if __name__ == "__main__":
    main()
