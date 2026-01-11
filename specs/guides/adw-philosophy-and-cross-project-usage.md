# ADW Philosophy and Cross-Project Usage Guide

## Your Questions Answered

You asked several excellent questions about how ADWs work across projects. Let me address each one.

---

## 1. Why We Went This Route

### The Original Problem

ADWs currently live in `omni-cortex/adws/` and ONLY work from within the omni-cortex project. This defeats the purpose of the "system that builds the system" philosophy because:

- You can't use ADWs when starting a new project
- You can't use them in your existing projects (React apps, Python backends, etc.)
- The automation is locked to one repo

### The Solution: Package Integration

By moving ADWs into `src/omni_cortex/adws/` and adding a CLI entry point, you get:

```bash
# After pip install omni-cortex (or pip install -e . in dev)
# From ANY project directory:
omni-cortex-adw run "Add dark mode toggle"
```

This works because:
1. The CLI detects your current project root (via `.git`, `pyproject.toml`, `.claude`, `specs` markers)
2. It loads commands from BOTH your project AND your user-level defaults
3. It creates specs/artifacts in YOUR project's folders

---

## 2. How ADWs Work Across Different Projects

### The Key Insight: Separation of Orchestration and Intelligence

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADW ORCHESTRATOR (GENERIC)                   │
│   plan.py → build.py → validate.py                              │
│   (Deterministic sequencing - same for all projects)            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                      Invokes Skills/Commands
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                PROJECT-SPECIFIC COMMANDS                         │
│   .claude/commands/quick-plan.md    ← React-specific planning   │
│   .claude/commands/build.md         ← Uses npm/vite/etc.        │
│   .claude/commands/validate.md      ← Tests React components    │
└─────────────────────────────────────────────────────────────────┘
                              +
┌─────────────────────────────────────────────────────────────────┐
│                USER-LEVEL COMMANDS (FALLBACK)                    │
│   ~/.claude/commands/quick-plan.md  ← Your generic defaults     │
│   ~/.claude/commands/build.md       ← Framework-agnostic        │
└─────────────────────────────────────────────────────────────────┘
```

### What This Means

- **ADW orchestrators are GENERIC** - They just sequence phases
- **Commands/Skills are PROJECT-SPECIFIC** - They know about your stack
- **`setting_sources=["project", "user"]`** - Loads both levels (line 98 of agent.py)

---

## 3. Do ADWs Need to Be Specialized Per Project?

### Short Answer: Yes and No

**NO - The orchestrators themselves are generic:**
- `adw_plan.py` - Always runs a planning phase
- `adw_build.py` - Always runs an implementation phase
- `adw_validate.py` - Always runs a validation phase
- `adw_plan_build_validate.py` - Always sequences plan → build → validate

**YES - The COMMANDS are specialized per project:**

| Project Type | `/quick-plan` knows about | `/build` runs | `/validate` checks |
|-------------|---------------------------|---------------|-------------------|
| Vue + Vite | Vue components, Pinia | `npm run build`, `npm test` | Vue component rendering |
| FastAPI | FastAPI routes, SQLAlchemy | `pytest`, `uvicorn` | API endpoints, OpenAPI |
| React + Next.js | React components, Next routing | `npm run build`, `npm run lint` | Page rendering, SSR |
| Omni-Cortex | MCP tools, dashboard, hooks | `pip install -e .`, `npm run build` | Dashboard visual tests |

---

## 4. IndyDevDan's Philosophy: "Build the System That Builds the System"

### What It Means

From the tac-8 course materials and orchestrator analysis:

> "Deterministic orchestration + non-deterministic intelligence"

- **Deterministic**: The workflow steps are predictable (plan → build → validate)
- **Non-deterministic**: Claude's implementation within each step is creative/intelligent

### The Agent Layer Primitives (from tac-8 App 1)

Two approaches to agentic development:

```
MINIMAL APPROACH:                    SCALED APPROACH:
├── specs/                          ├── specs/
├── .claude/commands/               ├── .claude/commands/
└── adws/                           ├── adws/
                                    ├── database (PostgreSQL)
                                    ├── WebSockets
                                    ├── Dashboard UI
                                    └── GitHub integration
```

We're implementing the MINIMAL approach first - just specs, commands, and ADWs.

### Why Each Project Is Different

IndyDevDan says each project has different:
- Tech stacks (React vs Vue vs Python)
- Testing requirements
- Deployment targets
- Team workflows

But the ORCHESTRATION PATTERN is the same:
1. **Plan** - Create a spec from requirements
2. **Build** - Implement the spec
3. **Validate** - Verify it works
4. **Review** - Check against spec (optional)
5. **Release** - Publish (optional)

---

## 5. How You Actually Use This

### Scenario 1: New React Project

```bash
# Create new React project
npm create vite@latest my-react-app -- --template react-ts
cd my-react-app

# Create project-specific commands
mkdir -p .claude/commands
cat > .claude/commands/build.md << 'EOF'
---
description: Build React app with TypeScript checks
---
Run these steps:
1. npm run lint
2. npm run build
3. npm test
EOF

# Now run ADW!
omni-cortex-adw run "Add a todo list component with local storage"
```

What happens:
1. ADW detects project root (sees `package.json`)
2. Runs `/quick-plan` (from your user-level commands OR creates one)
3. Runs `/build` (uses YOUR project's `.claude/commands/build.md`)
4. Runs `/validate` (if you have one, or uses user-level default)

### Scenario 2: Existing Python Project

```bash
cd ~/projects/my-fastapi-app

# You already have .claude/commands/build.md that knows about FastAPI
# Just run ADW
omni-cortex-adw run "Add rate limiting middleware"
```

### Scenario 3: Brand New Project (No Commands Yet)

```bash
mkdir new-project && cd new-project
git init

# ADW still works - uses your ~/.claude/commands/ defaults!
omni-cortex-adw run "Set up a basic Python package with pytest"
```

---

## 6. The Command Loading Order

When ADW runs `/build`, Claude looks for commands in this order:

1. **Project level**: `./.claude/commands/build.md`
2. **User level**: `~/.claude/commands/build.md`

If your project has a `/build` command, it uses that.
If not, it falls back to your user-level default.

This is controlled by `setting_sources=["project", "user"]` in `agent.py`:

```python
options = ClaudeAgentOptions(
    model=resolved_model,
    cwd=working_dir,
    max_turns=max_turns,
    allowed_tools=allowed_tools,
    permission_mode="acceptEdits",
    env=env_vars,
    setting_sources=["project", "user"],  # ← KEY LINE
)
```

---

## 7. Template Strategy for New Projects

### Option A: Starter Templates

Create reusable command templates for different project types:

```
~/.claude/templates/
├── react/
│   └── commands/
│       ├── quick-plan.md
│       ├── build.md
│       └── validate.md
├── fastapi/
│   └── commands/
│       ├── quick-plan.md
│       ├── build.md
│       └── validate.md
└── generic/
    └── commands/
        ├── quick-plan.md
        └── build.md
```

Then when starting a new project:
```bash
cp -r ~/.claude/templates/react/commands .claude/commands
```

### Option B: Let ADW Create Commands

The first time you run `omni-cortex-adw plan "task"` in a new project, the `/quick-plan` command (from your user-level) can DETECT the project type and suggest creating project-specific commands.

### Option C: Bootstrap Command

Create a `/init-adw` command that:
1. Detects project type (package.json → Node, pyproject.toml → Python, etc.)
2. Creates appropriate `.claude/commands/` from templates
3. Creates `specs/` folder structure

---

## 8. What Gets Created Where

When you run ADW from any project:

```
your-project/
├── specs/
│   ├── todo/           ← New specs go here
│   │   └── add-dark-mode-toggle.md
│   └── done/           ← Completed specs moved here
├── agents/             ← ADW artifacts
│   └── adw_1234567890_abc123/
│       ├── adw_state.json
│       ├── plan/
│       │   └── quick_plan_output.jsonl
│       ├── build/
│       │   └── build_output.jsonl
│       └── validate/
│           └── validate_output.jsonl
└── .claude/
    └── commands/       ← Project-specific commands (optional)
        ├── build.md
        └── validate.md
```

---

## 9. Summary: The Mental Model

```
┌──────────────────────────────────────────────────────────────┐
│                  omni-cortex (pip package)                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  ADW Orchestrators (GENERIC - works everywhere)         │ │
│  │  - omni-cortex-adw plan "task"                          │ │
│  │  - omni-cortex-adw build                                │ │
│  │  - omni-cortex-adw validate                             │ │
│  │  - omni-cortex-adw run "task" (full workflow)           │ │
│  └─────────────────────────────────────────────────────────┘ │
│               ↓ invokes skills ↓                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Claude Agent SDK (claude-agent-sdk package)            │ │
│  │  - setting_sources=["project", "user"]                  │ │
│  │  - Loads commands from both levels                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│                   YOUR PROJECT                                │
│  .claude/commands/           ~/.claude/commands/              │
│  ├── quick-plan.md  ←──OR──→ ├── quick-plan.md (fallback)    │
│  ├── build.md       ←──OR──→ ├── build.md (fallback)         │
│  └── validate.md    ←──OR──→ └── validate.md (fallback)      │
│                                                               │
│  specs/todo/  ← Plans created here                           │
│  agents/      ← ADW artifacts stored here                    │
└──────────────────────────────────────────────────────────────┘
```

---

## 10. Next Steps

1. **Implement the package integration** (specs/todo/adw-package-integration.md)
2. **Create user-level default commands** in `~/.claude/commands/`
3. **Test from different project directories**
4. **Optionally create project type templates**

---

## Key Takeaways

1. **ADWs are GENERIC orchestrators** - They work in any project
2. **Commands are PROJECT-SPECIFIC** - They know your stack
3. **Two levels**: Project (`.claude/commands/`) > User (`~/.claude/commands/`)
4. **IndyDevDan's pattern**: Deterministic orchestration + non-deterministic intelligence
5. **You don't need to templatize ADWs** - You templatize COMMANDS instead
6. **`setting_sources=["project", "user"]`** makes cross-project work possible
