# ADW Package Integration - Make ADWs Globally Available

## Problem Statement

Currently, ADWs (Agentic Development Workflows) are located in `adws/` at the project root and only work within the omni-cortex project. To embody the "system that builds the system" philosophy, ADWs should be:

1. Installable via `pip install omni-cortex`
2. Runnable from any project directory
3. Able to detect and use the current project's context

## Objectives

- Move ADW code into the omni-cortex package (`src/omni_cortex/adws/`)
- Add CLI entry points: `omni-cortex-adw plan|build|validate|run`
- Ensure ADWs work from any directory by detecting project root
- Load both project-level and user-level commands/skills
- Include ADWs in pip distribution

## Technical Approach

### 1. Package Structure

```
src/omni_cortex/
├── adws/
│   ├── __init__.py           # Package init + CLI entry point
│   ├── cli.py                # CLI argument parser and dispatcher
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── agent.py          # Claude SDK wrapper (existing)
│   │   ├── data_types.py     # ADW data structures (existing)
│   │   ├── state.py          # State management (existing)
│   │   └── utils.py          # Utilities (modified for portability)
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── plan.py           # Plan phase (from adw_plan.py)
│   │   ├── build.py          # Build phase (from adw_build.py)
│   │   ├── validate.py       # Validate phase (from adw_validate.py)
│   │   └── orchestrator.py   # Full workflow (from adw_plan_build_validate.py)
│   └── config.py             # ADW configuration and defaults
```

### 2. CLI Entry Points

Add to `pyproject.toml`:

```toml
[project.scripts]
omni-cortex = "omni_cortex.server:main"
omni-cortex-setup = "omni_cortex.setup:main"
omni-cortex-dashboard = "omni_cortex.dashboard:main"
omni-cortex-adw = "omni_cortex.adws.cli:main"  # NEW
```

### 3. CLI Interface Design

```bash
# Full workflow (plan -> build -> validate)
omni-cortex-adw run "Add dark mode toggle"

# Individual phases
omni-cortex-adw plan "Add user authentication"
omni-cortex-adw build                    # Uses latest spec from specs/todo/
omni-cortex-adw build specs/todo/my-plan.md  # Specific spec
omni-cortex-adw validate                 # Validates recent build

# Options
omni-cortex-adw run "task" --model opus  # Use specific model
omni-cortex-adw run "task" --max-turns 100  # Increase turn limit
omni-cortex-adw run "task" --verbose     # Verbose output
```

### 4. Project Root Detection

Create `src/omni_cortex/adws/config.py`:

```python
from pathlib import Path

def find_project_root(start_path: Path = None) -> Path:
    """Find project root by looking for markers."""
    markers = [
        ".git",
        "pyproject.toml",
        "package.json",
        ".claude",
        "specs",
    ]

    current = start_path or Path.cwd()

    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent

    # Fallback to cwd
    return Path.cwd()

def get_specs_dir(project_root: Path = None) -> Path:
    """Get specs directory, creating if needed."""
    root = project_root or find_project_root()
    specs_dir = root / "specs"
    specs_dir.mkdir(exist_ok=True)
    (specs_dir / "todo").mkdir(exist_ok=True)
    (specs_dir / "done").mkdir(exist_ok=True)
    return specs_dir

def get_agents_output_dir(project_root: Path = None) -> Path:
    """Get agents output directory for ADW artifacts."""
    root = project_root or find_project_root()
    agents_dir = root / "agents"
    agents_dir.mkdir(exist_ok=True)
    return agents_dir
```

### 5. Agent Module Updates

Update `agent.py` for portability:

```python
# Key changes:
# 1. Use find_project_root() instead of hardcoded paths
# 2. Ensure setting_sources includes ["project", "user"]
# 3. Pass cwd dynamically based on where command is run

async def run_claude_code(
    prompt: str,
    adw_id: str,
    phase: str,
    working_dir: str = None,  # Now optional, uses find_project_root()
    ...
):
    # Detect project root if not specified
    if working_dir is None:
        working_dir = str(find_project_root())

    options = ClaudeAgentOptions(
        model=resolved_model,
        cwd=working_dir,
        max_turns=max_turns,
        allowed_tools=allowed_tools,
        permission_mode="acceptEdits",
        env=env_vars,
        setting_sources=["project", "user"],  # Load both levels
    )
```

### 6. CLI Implementation

Create `src/omni_cortex/adws/cli.py`:

```python
#!/usr/bin/env python3
"""CLI entry point for ADW commands."""

import argparse
import asyncio
import sys

from .config import find_project_root
from .workflows.orchestrator import run_plan_build_validate
from .workflows.plan import run_plan
from .workflows.build import run_build
from .workflows.validate import run_validate


def main():
    parser = argparse.ArgumentParser(
        prog="omni-cortex-adw",
        description="Agentic Development Workflows - AI-powered development automation"
    )

    subparsers = parser.add_subparsers(dest="command", help="ADW commands")

    # Run command (full workflow)
    run_parser = subparsers.add_parser("run", help="Run full plan->build->validate workflow")
    run_parser.add_argument("task", help="Task description")
    run_parser.add_argument("--model", default="sonnet", choices=["sonnet", "opus", "haiku"])
    run_parser.add_argument("--max-turns", type=int, default=50)
    run_parser.add_argument("--verbose", action="store_true")

    # Plan command
    plan_parser = subparsers.add_parser("plan", help="Create implementation plan")
    plan_parser.add_argument("task", help="Task description")
    plan_parser.add_argument("--model", default="sonnet")

    # Build command
    build_parser = subparsers.add_parser("build", help="Build from spec")
    build_parser.add_argument("spec", nargs="?", help="Spec file path (optional)")
    build_parser.add_argument("--model", default="sonnet")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate build")
    validate_parser.add_argument("--model", default="sonnet")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Find project root
    project_root = find_project_root()
    print(f"[ADW] Project root: {project_root}")

    # Dispatch to appropriate workflow
    if args.command == "run":
        success = asyncio.run(run_plan_build_validate(args.task))
    elif args.command == "plan":
        success, _ = asyncio.run(run_plan(args.task))
    elif args.command == "build":
        success, _ = asyncio.run(run_build(args.spec))
    elif args.command == "validate":
        success, _ = asyncio.run(run_validate())

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
```

### 7. Packaging Configuration

Update `pyproject.toml`:

```toml
[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/hooks",
    "/scripts",
    "/dashboard/backend",
    "/dashboard/frontend/dist",
    "/README.md",
]
# Note: ADWs are now in /src, so automatically included

[tool.hatch.build.targets.wheel]
packages = ["src/omni_cortex"]
# ADWs included as subpackage
```

## Implementation Steps

### Phase 1: Restructure (30 min)
1. Create `src/omni_cortex/adws/` directory structure
2. Move `adws/adw_modules/` to `src/omni_cortex/adws/modules/`
3. Create `src/omni_cortex/adws/workflows/` from individual ADW files
4. Update all imports to use new package paths

### Phase 2: Portability (30 min)
1. Create `config.py` with project root detection
2. Update `agent.py` to use dynamic paths
3. Update `utils.py` to use `find_project_root()`
4. Test from different directories

### Phase 3: CLI (30 min)
1. Create `cli.py` with argument parser
2. Add entry point to `pyproject.toml`
3. Test CLI commands locally
4. Add `--help` documentation

### Phase 4: Testing & Packaging (30 min)
1. Test `pip install -e .` locally
2. Run ADW from a different project directory
3. Verify specs are created in correct location
4. Test all three phases (plan, build, validate)

### Phase 5: Cleanup (15 min)
1. Remove old `adws/` directory (after confirming new structure works)
2. Update any documentation references
3. Commit and publish new version

## Potential Challenges

| Challenge | Solution |
|-----------|----------|
| Import path changes | Use relative imports within adws package |
| Finding specs from any directory | `find_project_root()` + specs/todo/ convention |
| User commands not loading | `setting_sources=["project", "user"]` (already fixed) |
| State file location | Store in `{project}/agents/{adw_id}/` |

## Testing Strategy

1. **Unit Tests**: Test `find_project_root()` with various directory structures
2. **Integration Test**: Run full workflow from different directories
3. **CLI Test**: Verify all subcommands work correctly
4. **Package Test**: Fresh `pip install omni-cortex` in new venv, run ADW

## Success Criteria

- [ ] `pip install omni-cortex` includes ADW functionality
- [ ] `omni-cortex-adw run "task"` works from any project directory
- [ ] `omni-cortex-adw plan|build|validate` individual phases work
- [ ] Specs created in `{project}/specs/todo/`
- [ ] ADW artifacts stored in `{project}/agents/`
- [ ] Both project and user commands/skills load correctly
- [ ] Old `adws/` directory can be removed

## Files to Create/Modify

### New Files
- `src/omni_cortex/adws/__init__.py`
- `src/omni_cortex/adws/cli.py`
- `src/omni_cortex/adws/config.py`
- `src/omni_cortex/adws/modules/__init__.py`
- `src/omni_cortex/adws/modules/agent.py`
- `src/omni_cortex/adws/modules/data_types.py`
- `src/omni_cortex/adws/modules/state.py`
- `src/omni_cortex/adws/modules/utils.py`
- `src/omni_cortex/adws/workflows/__init__.py`
- `src/omni_cortex/adws/workflows/plan.py`
- `src/omni_cortex/adws/workflows/build.py`
- `src/omni_cortex/adws/workflows/validate.py`
- `src/omni_cortex/adws/workflows/orchestrator.py`

### Modified Files
- `pyproject.toml` - Add CLI entry point

### Deleted Files (after migration)
- `adws/` directory (entire folder)
