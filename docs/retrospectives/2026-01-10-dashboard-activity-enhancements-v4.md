# Retrospective: Dashboard Activity Enhancements v4

**Date:** 2026-01-10
**Duration:** ~30 minutes
**Outcome:** Successfully released v1.5.0

## Summary

Implemented comprehensive dashboard activity enhancements including natural language summaries, command analytics fields, automatic database migrations, and backfill utilities. Released as v1.5.0 to PyPI.

## Errors Encountered

| Error | Cause | Resolution | Prevention |
|-------|-------|------------|------------|
| `pydantic-core` import failure | Corrupted venv metadata after UV operations | Ran `uv pip install pydantic pydantic-core --force-reinstall` | Use `/omni` command's venv health check; add to pre-release checklist |
| TypeScript build failure | `ActivityDetail` interface in `api.ts` was duplicate and missing summary fields | Updated both the `types/index.ts` and `services/api.ts` interfaces | Grep for duplicate type definitions before modifying; prefer single source of truth |
| Tests failing on `command_name` column | Base schema.py didn't include v1.1 columns; only migration existed | Added columns to base schema AND kept migration for existing DBs | Always update base schema when adding migrations - new DBs need columns too |
| `rm -rf dist/` blocked by hook | damage-control hook prevents delete operations on certain paths | Used `uv build` directly (creates new files, overwrites existing) | Hook is working as intended; just skip explicit delete |

## Snags & Blockers

### 1. Duplicate TypeScript Types
- **Impact:** 10 minutes debugging why ActivityDetail didn't have summary_detail
- **Description:** `ActivityDetail` was defined in both `types/index.ts` (extends Activity) AND `services/api.ts` (standalone). The component imported from `api.ts`.
- **Resolution:** Updated BOTH files with new fields
- **Lesson:** Prefer extending base types over duplicating; grep for type names before modifying

### 2. Windows Path Syntax in Bash
- **Impact:** 2 minutes - first cd command failed
- **Description:** `cd d:\Projects\omni-cortex` fails; need `cd /d/Projects/omni-cortex`
- **Resolution:** Used Unix-style paths with drive letter prefix
- **Lesson:** This is expected behavior - not actually an issue

### 3. Schema vs Migration Confusion
- **Impact:** 5 minutes - tests failing after "correct" migration
- **Description:** Migration v1.1 existed but base schema.py lacked the columns. Fresh test DBs use base schema directly.
- **Resolution:** Added columns to schema.py (for new DBs) and kept migration (for existing DBs)
- **Lesson:** Migrations are for EXISTING databases; new databases need base schema updated too

## Lessons Learned

1. **Duplicate Type Definitions Cause Hidden Bugs**
   - Always grep for type/interface names before modifying
   - Prefer `extends` over duplication
   - Consider consolidating to single type definition file

2. **Schema Updates Require TWO Changes**
   - Update base `schema.py` for new databases
   - Add migration in `migrations.py` for existing databases
   - Both are required for complete coverage

3. **UV Venv Metadata Can Corrupt**
   - After heavy UV operations, run health check: `python -c "import pydantic"`
   - Solution: `uv pip install --force-reinstall <package>`
   - Consider adding venv health check to build workflow

4. **Release Workflow Works Well**
   - `/omni` command streamlined the release process
   - Automatic version check against PyPI prevented conflicts
   - Commit-push-publish flow is reliable

## Command Improvements

### `/build` Command
**No changes needed** - worked well with plan file input

### `/omni` Command
**Consider adding:**
- Pre-release venv health check: `python -c "import pydantic; import mcp"`
- Automatic syntax check of modified Python files before commit

## Process Improvements

### 1. Type Definition Hygiene
Before modifying TypeScript interfaces:
```bash
grep -r "interface ActivityDetail" dashboard/frontend/src/
```
Ensure only ONE definition exists, or update ALL definitions.

### 2. Schema Change Checklist
When adding database columns:
- [ ] Add to base `schema.py` (for new databases)
- [ ] Add migration to `migrations.py` (for existing databases)
- [ ] Run tests with fresh database
- [ ] Run tests with migrated database

### 3. Pre-Build Validation
Add to build workflow:
```bash
# Check venv health
python -c "import pydantic; import mcp; print('venv OK')"

# Check for type duplicates (if TS changes)
grep -rh "^export interface" dashboard/frontend/src/ | sort | uniq -d
```

## Metrics

- **Tasks Completed:** 8 (all phases of v4 spec)
- **Tests Passed:** 97/97 Python + TypeScript build
- **Files Changed:** 21 files, +1581/-167 lines
- **Time on Issues:** ~15 minutes (venv, types, schema)
- **Productive Time:** ~15 minutes (actual implementation)
- **Ratio:** 50/50 - could improve with pre-checks

## What Worked Well

1. **TodoWrite for tracking** - 8-item checklist kept progress visible
2. **Spec-driven development** - v4.md spec was comprehensive
3. **Parallel tool calls** - Read + cortex_recall saved time
4. **Memory system** - Recalled previous build issues to avoid repeating
5. **Incremental testing** - Caught TypeScript issue before full build

## Action Items

- [ ] Consider adding venv health check to `/build` command
- [ ] Document "schema + migration" pattern in project README
- [ ] Add TypeScript duplicate detection to pre-commit hook
- [ ] Review all `services/api.ts` types for consolidation opportunities
