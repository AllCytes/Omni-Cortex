#!/usr/bin/env python3
"""ADW Security Phase - Security audit using /security."""

import asyncio
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.data_types import ADWPhase
from adw_modules.state import ADWState
from adw_modules.agent import run_skill
from adw_modules.utils import get_phase_dir


async def run_security(state: ADWState) -> bool:
    """Execute the security audit phase.

    Args:
        state: ADW state from previous phases

    Returns:
        True if successful
    """
    print(f"\n[ADW Security] Starting security audit phase")
    print(f"[ADW Security] ID: {state.adw_id}")

    state.start_phase(ADWPhase.SECURITY)

    # Run /security skill
    security_prompt = f"""Run a comprehensive security audit for ADW: {state.adw_id}

Task being implemented: {state.task}
Spec: {state.spec or 'No spec file'}

Execute the /security skill to:
1. Audit for hardcoded secrets
2. Check for SQL injection vulnerabilities
3. Check for XSS vulnerabilities
4. Audit authentication and authorization
5. Check API security

Save the audit report to docs/security/ with sequential numbering.
"""

    success, output, output_file = await run_skill(
        skill_name="security",
        args=security_prompt,
        adw_id=state.adw_id,
        phase="security",
    )

    # Find the generated security audit file
    audit_files = list(Path("docs/security").glob("security-audit-*.md"))
    artifacts = [str(f) for f in audit_files] if audit_files else []

    if success:
        state.complete_phase(
            ADWPhase.SECURITY,
            success=True,
            output_file=output_file,
            artifacts=artifacts,
        )
        print(f"[ADW Security] Phase completed. Audit files: {len(artifacts)}")
    else:
        state.complete_phase(
            ADWPhase.SECURITY,
            success=False,
            error_message=output,
        )
        print(f"[ADW Security] Phase failed: {output}")

    return success


def main():
    """CLI entry point - run security audit on an existing ADW session."""
    if len(sys.argv) < 2:
        print("ADW Security: Run security audit on an ADW session")
        print()
        print("Usage:")
        print("  uv run adws/adw_security.py <adw-id>")
        print("  python adws/adw_security.py <adw-id>")
        print()
        print("Examples:")
        print('  uv run adws/adw_security.py adw_1768194349_2ac26097')
        print()
        print("This will audit for:")
        print("  - Hardcoded secrets")
        print("  - SQL injection vulnerabilities")
        print("  - XSS vulnerabilities")
        print("  - Authentication/authorization issues")
        print("  - API security problems")
        sys.exit(1)

    adw_id = sys.argv[1]

    # Load existing state
    state = ADWState(adw_id=adw_id)

    # Check if state file exists
    if not state.state_file.exists():
        print(f"Error: No ADW state found for {adw_id}")
        print(f"Expected state file: {state.state_file}")
        sys.exit(1)

    print(f"\n[ADW Security] Starting security audit for {adw_id}")
    print(f"[ADW Security] Task: {state.task}")
    print(f"[ADW Security] Completed phases: {len(state.data.completed_phases)}")

    success = asyncio.run(run_security(state))

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
