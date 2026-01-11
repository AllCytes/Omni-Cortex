# Omni-Cortex ADW (Agentic Development Workflow) System

## Problem Statement

Currently, the omni-cortex development workflow is manual and involves multiple terminal sessions with ad-hoc command execution. The goal is to create a structured, repeatable ADW system inspired by IndyDevDan's patterns that:

1. Automates the development lifecycle (plan → build → validate → review → release)
2. Provides state management between workflow phases
3. Captures screenshots and validation evidence
4. Integrates with OmniCortex memory for context persistence
5. Supports both individual phases and orchestrated workflows

## Objectives

- Create first working ADWs for omni-cortex project
- Establish `adws/` directory structure matching IndyDevDan's pattern
- Implement state management with JSON persistence
- Create individual phase scripts and orchestrator scripts
- Integrate with existing slash commands (/quick-plan, /build, /validate, /review, /omni)
- Store screenshots in organized directory structure
- Document terminal session workflow

## Architecture Decisions

### Key Differences from IndyDevDan's Implementation

| Aspect | IndyDevDan (tac-7) | Omni-Cortex |
|--------|-------------------|-------------|
| Task Source | GitHub Issues | Local spec files |
| Isolation | Git worktrees | Single repo (no worktrees initially) |
| State Location | `agents/{adw_id}/` | `agents/{adw_id}/` (same) |
| Commands | Custom slash commands | Existing slash commands |
| Screenshots | R2 upload | Local storage in agents/ |
| Triggers | Webhook/Cron | Manual invocation |

### Directory Structure

```
omni-cortex/
├── adws/                           # ADW scripts directory
│   ├── __init__.py
│   ├── adw_modules/                # Shared modules
│   │   ├── __init__.py
│   │   ├── data_types.py           # Pydantic models
│   │   ├── state.py                # ADWState class
│   │   ├── agent.py                # Claude Code execution
│   │   └── utils.py                # Utilities
│   ├── adw_plan.py                 # Planning phase
│   ├── adw_build.py                # Build phase
│   ├── adw_validate.py             # Validation phase
│   ├── adw_review.py               # Review phase
│   ├── adw_retrospective.py        # Retrospective phase
│   ├── adw_release.py              # Release phase
│   ├── adw_plan_build.py           # Orchestrator: Plan + Build
│   ├── adw_plan_build_validate.py  # Orchestrator: Plan + Build + Validate
│   ├── adw_plan_build_validate_review.py  # Full validation workflow
│   └── adw_sdlc.py                 # Full SDLC workflow
├── agents/                         # ADW output directory
│   └── {adw_id}/
│       ├── adw_state.json          # Persistent state
│       ├── plan_spec.md            # Generated spec
│       ├── planner/
│       │   └── raw_output.jsonl    # Claude Code output
│       ├── builder/
│       │   └── raw_output.jsonl
│       ├── validator/
│       │   ├── raw_output.jsonl
│       │   └── screenshots/        # Validation screenshots
│       ├── reviewer/
│       │   ├── raw_output.jsonl
│       │   └── review_img/         # Review screenshots
│       └── retrospective/
│           └── raw_output.jsonl
└── .claude/commands/
    ├── review.md                   # NEW: Review command
    └── validate.md                 # UPDATE: Screenshot paths
```

## Implementation Plan

### Phase 1: Core Infrastructure (adw_modules/)

#### 1.1 Create data_types.py

```python
"""Data types for Omni-Cortex ADW system."""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from enum import Enum

class RetryCode(str, Enum):
    NONE = "none"
    CLAUDE_CODE_ERROR = "claude_code_error"
    TIMEOUT_ERROR = "timeout_error"
    EXECUTION_ERROR = "execution_error"

class ADWPhase(str, Enum):
    PLAN = "plan"
    BUILD = "build"
    VALIDATE = "validate"
    REVIEW = "review"
    RETROSPECTIVE = "retrospective"
    RELEASE = "release"

class ReviewIssueSeverity(str, Enum):
    BLOCKER = "blocker"
    TECH_DEBT = "tech_debt"
    SKIPPABLE = "skippable"

class ADWStateData(BaseModel):
    """Persistent state for ADW workflow."""
    adw_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    spec_file: Optional[str] = None
    spec_request: Optional[str] = None
    branch_name: Optional[str] = None
    current_phase: Optional[ADWPhase] = None
    phases_completed: List[ADWPhase] = Field(default_factory=list)
    validation_passed: Optional[bool] = None
    review_passed: Optional[bool] = None
    screenshots: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

class ReviewIssue(BaseModel):
    """Individual review issue."""
    issue_number: int
    description: str
    resolution: str
    severity: ReviewIssueSeverity
    screenshot_path: Optional[str] = None

class ReviewResult(BaseModel):
    """Result from review phase."""
    success: bool
    summary: str
    issues: List[ReviewIssue] = Field(default_factory=list)
    screenshots: List[str] = Field(default_factory=list)

class ValidationResult(BaseModel):
    """Result from validation phase."""
    overall_status: Literal["passed", "failed", "partial"]
    tests: List[dict] = Field(default_factory=list)
    screenshots: List[str] = Field(default_factory=list)
    issues: List[dict] = Field(default_factory=list)
```

#### 1.2 Create state.py

```python
"""State management for ADW workflows."""
import json
import os
from typing import Optional
from .data_types import ADWStateData, ADWPhase

class ADWState:
    """Container for ADW workflow state with file persistence."""

    STATE_FILENAME = "adw_state.json"

    def __init__(self, adw_id: str):
        self.adw_id = adw_id
        self.data = ADWStateData(adw_id=adw_id)

    def get_agents_dir(self) -> str:
        """Get path to agents directory for this ADW."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, "agents", self.adw_id)

    def get_state_path(self) -> str:
        """Get path to state file."""
        return os.path.join(self.get_agents_dir(), self.STATE_FILENAME)

    def get_screenshot_dir(self, phase: str) -> str:
        """Get screenshot directory for a phase."""
        if phase == "validate":
            return os.path.join(self.get_agents_dir(), "validator", "screenshots")
        elif phase == "review":
            return os.path.join(self.get_agents_dir(), "reviewer", "review_img")
        return os.path.join(self.get_agents_dir(), phase, "screenshots")

    def update(self, **kwargs):
        """Update state with new values."""
        for key, value in kwargs.items():
            if hasattr(self.data, key):
                setattr(self.data, key, value)

    def mark_phase_complete(self, phase: ADWPhase):
        """Mark a phase as completed."""
        if phase not in self.data.phases_completed:
            self.data.phases_completed.append(phase)
        self.data.current_phase = None

    def save(self) -> None:
        """Save state to file."""
        state_path = self.get_state_path()
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, "w") as f:
            json.dump(self.data.model_dump(mode="json"), f, indent=2, default=str)

    @classmethod
    def load(cls, adw_id: str) -> Optional["ADWState"]:
        """Load state from file if exists."""
        state = cls(adw_id)
        state_path = state.get_state_path()
        if os.path.exists(state_path):
            with open(state_path, "r") as f:
                data = json.load(f)
            state.data = ADWStateData(**data)
            return state
        return None

    @classmethod
    def load_or_create(cls, adw_id: str) -> "ADWState":
        """Load existing state or create new."""
        existing = cls.load(adw_id)
        if existing:
            return existing
        return cls(adw_id)
```

#### 1.3 Create agent.py

```python
"""Claude Code agent execution for ADW."""
import subprocess
import os
import json
from typing import Optional
from .data_types import RetryCode

# Get Claude Code CLI path
CLAUDE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")

def execute_slash_command(
    slash_command: str,
    args: list[str],
    adw_id: str,
    agent_name: str,
    working_dir: Optional[str] = None
) -> tuple[bool, str]:
    """Execute a slash command via Claude Code CLI.

    Returns: (success, output)
    """
    # Build prompt
    prompt = f"{slash_command} {' '.join(args)}"

    # Create output directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "agents", adw_id, agent_name)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "raw_output.jsonl")

    # Build command
    cmd = [
        CLAUDE_PATH,
        "-p", prompt,
        "--output-format", "stream-json",
        "--dangerously-skip-permissions",
        "--verbose"
    ]

    # Execute
    cwd = working_dir or project_root
    try:
        with open(output_file, "w") as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd
            )

        # Parse result from JSONL
        with open(output_file, "r") as f:
            lines = f.readlines()

        for line in reversed(lines):
            try:
                data = json.loads(line.strip())
                if data.get("type") == "result":
                    return not data.get("is_error", False), data.get("result", "")
            except json.JSONDecodeError:
                continue

        return result.returncode == 0, "Command completed"

    except Exception as e:
        return False, str(e)
```

#### 1.4 Create utils.py

```python
"""Utilities for ADW system."""
import secrets
import os
from datetime import datetime

def generate_adw_id() -> str:
    """Generate unique 8-character ADW ID."""
    return secrets.token_hex(4)

def get_project_root() -> str:
    """Get project root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def format_timestamp() -> str:
    """Get formatted timestamp for filenames."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def ensure_directory(path: str) -> str:
    """Ensure directory exists, return path."""
    os.makedirs(path, exist_ok=True)
    return path
```

### Phase 2: Individual Phase Scripts

#### 2.1 adw_plan.py

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Plan Phase - Creates implementation spec using /quick-plan."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.utils import generate_adw_id
from adw_modules.state import ADWState
from adw_modules.agent import execute_slash_command
from adw_modules.data_types import ADWPhase

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_plan.py <request-or-spec-file> [adw-id]")
        sys.exit(1)

    request = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else generate_adw_id()

    print(f"=== ADW PLAN PHASE ===")
    print(f"ADW ID: {adw_id}")

    # Initialize state
    state = ADWState.load_or_create(adw_id)
    state.update(current_phase=ADWPhase.PLAN, spec_request=request)
    state.save()

    # Execute /quick-plan
    success, output = execute_slash_command(
        "/quick-plan",
        [request],
        adw_id,
        "planner"
    )

    if success:
        # Extract spec file path from output (look for specs/*.md)
        import re
        match = re.search(r'specs/[\w-]+\.md', output)
        if match:
            spec_file = match.group(0)
            state.update(spec_file=spec_file)

        state.mark_phase_complete(ADWPhase.PLAN)
        state.save()
        print(f"[SUCCESS] Plan phase completed")
        print(f"Spec file: {state.data.spec_file}")
    else:
        state.data.errors.append(f"Plan failed: {output}")
        state.save()
        print(f"[ERROR] Plan phase failed: {output}")
        sys.exit(1)

    # Output state for chaining
    print(json.dumps({"adw_id": adw_id, "spec_file": state.data.spec_file}))

if __name__ == "__main__":
    main()
```

#### 2.2 adw_build.py

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Build Phase - Implements spec using /build."""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from adw_modules.agent import execute_slash_command
from adw_modules.data_types import ADWPhase

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_build.py <adw-id> [spec-file]")
        sys.exit(1)

    adw_id = sys.argv[1]
    spec_file = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"=== ADW BUILD PHASE ===")
    print(f"ADW ID: {adw_id}")

    # Load state
    state = ADWState.load(adw_id)
    if not state:
        print(f"[ERROR] No state found for ADW ID: {adw_id}")
        sys.exit(1)

    # Get spec file
    spec_file = spec_file or state.data.spec_file
    if not spec_file:
        print("[ERROR] No spec file provided or found in state")
        sys.exit(1)

    state.update(current_phase=ADWPhase.BUILD)
    state.save()

    # Execute /build
    success, output = execute_slash_command(
        "/build",
        [spec_file],
        adw_id,
        "builder"
    )

    if success:
        state.mark_phase_complete(ADWPhase.BUILD)
        state.save()
        print(f"[SUCCESS] Build phase completed")
    else:
        state.data.errors.append(f"Build failed: {output}")
        state.save()
        print(f"[ERROR] Build phase failed: {output}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### 2.3 adw_validate.py

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Validate Phase - Visual validation using /validate with Chrome MCP."""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from adw_modules.agent import execute_slash_command
from adw_modules.data_types import ADWPhase

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_validate.py <adw-id>")
        sys.exit(1)

    adw_id = sys.argv[1]

    print(f"=== ADW VALIDATE PHASE ===")
    print(f"ADW ID: {adw_id}")

    # Load state
    state = ADWState.load(adw_id)
    if not state:
        print(f"[ERROR] No state found for ADW ID: {adw_id}")
        sys.exit(1)

    state.update(current_phase=ADWPhase.VALIDATE)
    state.save()

    # Ensure screenshot directory exists
    screenshot_dir = state.get_screenshot_dir("validate")
    os.makedirs(screenshot_dir, exist_ok=True)

    # Execute /validate with ADW context
    # Note: /validate command should be updated to accept adw_id for screenshot storage
    success, output = execute_slash_command(
        "/validate",
        [f"--adw-id={adw_id}"],
        adw_id,
        "validator"
    )

    if success:
        state.update(validation_passed=True)
        state.mark_phase_complete(ADWPhase.VALIDATE)
        state.save()
        print(f"[SUCCESS] Validate phase completed")
        print(f"Screenshots: {screenshot_dir}")
    else:
        state.update(validation_passed=False)
        state.data.errors.append(f"Validation failed: {output}")
        state.save()
        print(f"[ERROR] Validate phase failed: {output}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### 2.4 adw_review.py

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Review Phase - Compare implementation against spec using /review."""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from adw_modules.agent import execute_slash_command
from adw_modules.data_types import ADWPhase

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_review.py <adw-id> [spec-file]")
        sys.exit(1)

    adw_id = sys.argv[1]
    spec_file = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"=== ADW REVIEW PHASE ===")
    print(f"ADW ID: {adw_id}")

    # Load state
    state = ADWState.load(adw_id)
    if not state:
        print(f"[ERROR] No state found for ADW ID: {adw_id}")
        sys.exit(1)

    spec_file = spec_file or state.data.spec_file
    if not spec_file:
        print("[ERROR] No spec file provided or found in state")
        sys.exit(1)

    state.update(current_phase=ADWPhase.REVIEW)
    state.save()

    # Ensure screenshot directory exists
    screenshot_dir = state.get_screenshot_dir("review")
    os.makedirs(screenshot_dir, exist_ok=True)

    # Execute /review
    success, output = execute_slash_command(
        "/review",
        [adw_id, spec_file],
        adw_id,
        "reviewer"
    )

    if success:
        state.update(review_passed=True)
        state.mark_phase_complete(ADWPhase.REVIEW)
        state.save()
        print(f"[SUCCESS] Review phase completed")
    else:
        state.update(review_passed=False)
        state.data.errors.append(f"Review failed: {output}")
        state.save()
        print(f"[ERROR] Review phase failed: {output}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### 2.5 adw_retrospective.py

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Retrospective Phase - Document lessons learned using /retrospective."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from adw_modules.agent import execute_slash_command
from adw_modules.data_types import ADWPhase

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_retrospective.py <adw-id> [session-name]")
        sys.exit(1)

    adw_id = sys.argv[1]
    session_name = sys.argv[2] if len(sys.argv) > 2 else adw_id

    print(f"=== ADW RETROSPECTIVE PHASE ===")
    print(f"ADW ID: {adw_id}")

    # Load state
    state = ADWState.load(adw_id)
    if not state:
        print(f"[ERROR] No state found for ADW ID: {adw_id}")
        sys.exit(1)

    state.update(current_phase=ADWPhase.RETROSPECTIVE)
    state.save()

    # Execute /retrospective
    success, output = execute_slash_command(
        "/retrospective",
        [session_name],
        adw_id,
        "retrospective"
    )

    if success:
        state.mark_phase_complete(ADWPhase.RETROSPECTIVE)
        state.save()
        print(f"[SUCCESS] Retrospective phase completed")
    else:
        state.data.errors.append(f"Retrospective failed: {output}")
        state.save()
        print(f"[WARNING] Retrospective phase failed: {output}")
        # Don't exit with error - retrospective is optional

if __name__ == "__main__":
    main()
```

#### 2.6 adw_release.py

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Release Phase - Publish using /omni."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.state import ADWState
from adw_modules.agent import execute_slash_command
from adw_modules.data_types import ADWPhase

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_release.py <adw-id>")
        sys.exit(1)

    adw_id = sys.argv[1]

    print(f"=== ADW RELEASE PHASE ===")
    print(f"ADW ID: {adw_id}")

    # Load state
    state = ADWState.load(adw_id)
    if not state:
        print(f"[ERROR] No state found for ADW ID: {adw_id}")
        sys.exit(1)

    # Check prerequisites
    if not state.data.review_passed:
        print("[ERROR] Cannot release without passing review")
        sys.exit(1)

    state.update(current_phase=ADWPhase.RELEASE)
    state.save()

    # Execute /omni
    success, output = execute_slash_command(
        "/omni",
        [],
        adw_id,
        "releaser"
    )

    if success:
        state.mark_phase_complete(ADWPhase.RELEASE)
        state.save()
        print(f"[SUCCESS] Release phase completed")
    else:
        state.data.errors.append(f"Release failed: {output}")
        state.save()
        print(f"[ERROR] Release phase failed: {output}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Phase 3: Orchestrator Workflows

#### 3.1 adw_plan_build.py

```python
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
        print("\nThis runs: Plan → Build")
        sys.exit(1)

    request = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else generate_adw_id()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"Using ADW ID: {adw_id}")

    # Plan phase
    print(f"\n=== PLAN PHASE ===")
    plan_cmd = ["uv", "run", os.path.join(script_dir, "adw_plan.py"), request, adw_id]
    plan = subprocess.run(plan_cmd)
    if plan.returncode != 0:
        print("Plan phase failed")
        sys.exit(1)

    # Build phase
    print(f"\n=== BUILD PHASE ===")
    build_cmd = ["uv", "run", os.path.join(script_dir, "adw_build.py"), adw_id]
    build = subprocess.run(build_cmd)
    if build.returncode != 0:
        print("Build phase failed")
        sys.exit(1)

    print(f"\n=== WORKFLOW COMPLETED ===")
    print(f"ADW ID: {adw_id}")

if __name__ == "__main__":
    main()
```

#### 3.2 adw_plan_build_validate.py

```python
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
        print("\nThis runs: Plan → Build → Validate")
        sys.exit(1)

    request = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else generate_adw_id()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"Using ADW ID: {adw_id}")

    # Plan phase
    print(f"\n=== PLAN PHASE ===")
    subprocess.run(["uv", "run", os.path.join(script_dir, "adw_plan.py"), request, adw_id], check=True)

    # Build phase
    print(f"\n=== BUILD PHASE ===")
    subprocess.run(["uv", "run", os.path.join(script_dir, "adw_build.py"), adw_id], check=True)

    # Validate phase
    print(f"\n=== VALIDATE PHASE ===")
    subprocess.run(["uv", "run", os.path.join(script_dir, "adw_validate.py"), adw_id], check=True)

    print(f"\n=== WORKFLOW COMPLETED ===")
    print(f"ADW ID: {adw_id}")

if __name__ == "__main__":
    main()
```

#### 3.3 adw_plan_build_validate_review.py

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Plan + Build + Validate + Review Orchestrator."""

import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adw_modules.utils import generate_adw_id

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run adw_plan_build_validate_review.py <request> [adw-id]")
        print("\nThis runs: Plan → Build → Validate → Review")
        sys.exit(1)

    request = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else generate_adw_id()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"Using ADW ID: {adw_id}")

    phases = [
        ("PLAN", ["uv", "run", os.path.join(script_dir, "adw_plan.py"), request, adw_id]),
        ("BUILD", ["uv", "run", os.path.join(script_dir, "adw_build.py"), adw_id]),
        ("VALIDATE", ["uv", "run", os.path.join(script_dir, "adw_validate.py"), adw_id]),
        ("REVIEW", ["uv", "run", os.path.join(script_dir, "adw_review.py"), adw_id]),
    ]

    for phase_name, cmd in phases:
        print(f"\n=== {phase_name} PHASE ===")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"{phase_name} phase failed")
            sys.exit(1)

    print(f"\n=== WORKFLOW COMPLETED ===")
    print(f"ADW ID: {adw_id}")

if __name__ == "__main__":
    main()
```

#### 3.4 adw_sdlc.py

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///
"""ADW Full SDLC Orchestrator: Plan → Build → Validate → Review → Retrospective → Release."""

import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adw_modules.utils import generate_adw_id

def main():
    skip_release = "--skip-release" in sys.argv
    if skip_release:
        sys.argv.remove("--skip-release")

    if len(sys.argv) < 2:
        print("Usage: uv run adw_sdlc.py <request> [adw-id] [--skip-release]")
        print("\nThis runs: Plan → Build → Validate → Review → Retrospective → Release")
        sys.exit(1)

    request = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else generate_adw_id()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"Using ADW ID: {adw_id}")

    phases = [
        ("PLAN", ["uv", "run", os.path.join(script_dir, "adw_plan.py"), request, adw_id]),
        ("BUILD", ["uv", "run", os.path.join(script_dir, "adw_build.py"), adw_id]),
        ("VALIDATE", ["uv", "run", os.path.join(script_dir, "adw_validate.py"), adw_id]),
        ("REVIEW", ["uv", "run", os.path.join(script_dir, "adw_review.py"), adw_id]),
        ("RETROSPECTIVE", ["uv", "run", os.path.join(script_dir, "adw_retrospective.py"), adw_id]),
    ]

    if not skip_release:
        phases.append(("RELEASE", ["uv", "run", os.path.join(script_dir, "adw_release.py"), adw_id]))

    for phase_name, cmd in phases:
        print(f"\n=== {phase_name} PHASE ===")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            if phase_name == "RETROSPECTIVE":
                print(f"[WARNING] {phase_name} phase failed, continuing...")
            else:
                print(f"[ERROR] {phase_name} phase failed")
                sys.exit(1)

    print(f"\n=== FULL SDLC COMPLETED ===")
    print(f"ADW ID: {adw_id}")
    print(f"State: agents/{adw_id}/adw_state.json")

if __name__ == "__main__":
    main()
```

### Phase 4: Slash Commands

#### 4.1 Create /review Command

Create `.claude/commands/review.md`:

```markdown
---
description: Review implementation against spec with visual validation
argument-hint: <adw-id> <spec-file>
allowed-tools: Read, Bash, Glob, Grep, mcp__omni-cortex__cortex_recall, mcp__omni-cortex__cortex_remember, mcp__claude-in-chrome__*
---

# Review Implementation Against Specification

Review work done against a specification file to ensure implemented features match requirements.

## Variables

ADW_ID: $1
SPEC_FILE: $2
SCREENSHOT_DIR: agents/{ADW_ID}/reviewer/review_img/

## Instructions

1. **Read the spec file** to understand requirements
2. **Check git diff** to see what was implemented
3. **Visual validation** (if UI changes):
   - Use Chrome MCP to navigate to dashboard
   - Take screenshots of key functionality (1-5 max)
   - Save to SCREENSHOT_DIR with numbered names: 01_description.png
4. **Compare implementation vs spec**
5. **Report issues** with severity:
   - `blocker` - Must fix before release
   - `tech_debt` - Should fix later
   - `skippable` - Minor, can ignore

## Report

Return JSON:
```json
{
  "success": true/false,
  "review_summary": "2-3 sentences about implementation",
  "review_issues": [
    {
      "issue_number": 1,
      "description": "Issue description",
      "resolution": "How to fix",
      "severity": "blocker|tech_debt|skippable",
      "screenshot_path": "optional path"
    }
  ],
  "screenshots": ["path1.png", "path2.png"]
}
```

## Post-Review Memory Storage

Store review results: `cortex_remember`
- Content: Review summary and issues
- Tags: ["review", "adw", ADW_ID]
- Type: "progress" if success, "troubleshooting" if failed
```

#### 4.2 Update /validate Command

Update `.claude/commands/validate.md` to support ADW screenshot storage:

Add to the Variables section:
```markdown
ADW_ID: Parse from --adw-id argument if provided
SCREENSHOT_DIR: If ADW_ID provided, use `agents/{ADW_ID}/validator/screenshots/`
               Otherwise use `validation-screenshots/{TIMESTAMP}/`
```

### Phase 5: Terminal Session Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     RECOMMENDED WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  OPTION A: Manual Terminal Sessions                              │
│  ════════════════════════════════                                │
│                                                                  │
│  Terminal 1 (Planning):                                          │
│  ┌──────────────────────────────────────┐                       │
│  │ /quick-plan "add feature X"          │                       │
│  │ → Creates specs/feature-x.md         │                       │
│  └──────────────────────────────────────┘                       │
│                    ↓                                             │
│  Terminal 2 (Building + Validation):                             │
│  ┌──────────────────────────────────────┐                       │
│  │ /build specs/feature-x.md            │                       │
│  │ /validate                            │                       │
│  │ /retrospective feature-x             │                       │
│  └──────────────────────────────────────┘                       │
│                    ↓                                             │
│  Terminal 3 (Review + Release):                                  │
│  ┌──────────────────────────────────────┐                       │
│  │ /review <adw-id> specs/feature-x.md  │                       │
│  │ /omni                                │                       │
│  └──────────────────────────────────────┘                       │
│                                                                  │
│  ════════════════════════════════════════════════════════════   │
│                                                                  │
│  OPTION B: ADW Automation (Single Command)                       │
│  ═════════════════════════════════════════                       │
│                                                                  │
│  Quick workflows:                                                │
│  ┌──────────────────────────────────────┐                       │
│  │ uv run adws/adw_plan_build.py "request"                      │
│  │ uv run adws/adw_plan_build_validate.py "request"             │
│  │ uv run adws/adw_plan_build_validate_review.py "request"      │
│  └──────────────────────────────────────┘                       │
│                                                                  │
│  Full SDLC:                                                      │
│  ┌──────────────────────────────────────┐                       │
│  │ uv run adws/adw_sdlc.py "request"    │                       │
│  │ → Plan → Build → Validate → Review   │                       │
│  │   → Retrospective → Release          │                       │
│  └──────────────────────────────────────┘                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Testing Strategy

### Unit Tests
1. Test `generate_adw_id()` produces valid 8-char hex
2. Test `ADWState` save/load cycle
3. Test state update and phase completion

### Integration Tests
1. Run `adw_plan.py` with simple request
2. Verify state file created in `agents/{adw_id}/`
3. Verify spec file created in `specs/`

### End-to-End Tests
1. Run full `adw_plan_build.py` workflow
2. Verify all phases complete
3. Check screenshot storage paths

## Success Criteria

1. ✅ `adws/` directory created with all scripts
2. ✅ `adw_modules/` contains data_types, state, agent, utils
3. ✅ State persists between phases in `agents/{adw_id}/adw_state.json`
4. ✅ Screenshots stored in `agents/{adw_id}/{phase}/screenshots/`
5. ✅ `/review` command created and functional
6. ✅ `/validate` updated for ADW screenshot paths
7. ✅ Orchestrator workflows chain phases correctly
8. ✅ Full SDLC workflow completes end-to-end

## Potential Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Claude Code CLI not installed | Check on startup, provide install instructions |
| Slash command parsing | Use regex to extract paths from output |
| Screenshot capture timing | Add wait commands in Chrome MCP steps |
| State corruption | Use atomic file writes with temp files |
| Phase failures | Save state before exiting, allow resume |

## Future Enhancements

1. **Git Worktree Support** - Isolated parallel execution like IndyDevDan
2. **File Watcher Trigger** - Auto-run when new spec files appear
3. **Dashboard Integration** - Show ADW status in OmniCortex dashboard
4. **WebSocket Events** - Real-time ADW progress broadcasting
5. **Retry Logic** - Automatic retry with exponential backoff
