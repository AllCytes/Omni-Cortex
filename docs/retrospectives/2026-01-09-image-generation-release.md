# Retrospective: Nano Banana Pro Image Generation & v1.2.0 Release
Date: 2026-01-09

## Summary
Implemented Nano Banana Pro image generation integration for the Omni-Cortex dashboard and released as v1.2.0. The feature implementation went smoothly, but the release process encountered several snags related to version synchronization and PyPI publishing.

## Tasks Completed
1. Backend image_service.py with 8 presets, batch generation, multi-turn refinement
2. API endpoints for image generation, refinement, status
3. Frontend ImageGenerationPanel.vue with memory selection, presets, gallery
4. ChatPanel.vue mode toggle integration
5. Frontend api.ts types and functions
6. Git commit and push to GitHub
7. PyPI publication
8. Local installation update

## Errors Encountered

| Error | Cause | Resolution | Prevention |
|-------|-------|------------|------------|
| `uv publish` credentials failure | uv doesn't read ~/.pypirc file | Used `python -m twine upload dist/*` instead | Update /omni command to use twine |
| Old dist files interfered | Previous build artifacts in dist/ | `rm -rf dist/` before build | Always clean dist/ before building |
| Version mismatch (pyproject.toml vs __init__.py) | pyproject.toml had 1.1.0, __init__.py had 1.0.11 | Updated both files, made extra commit | Always update BOTH version locations together |
| `pip install` failed in UV venv | UV-managed venvs don't have pip module | Used `uv pip install` instead | Document UV venv usage pattern |
| Force reinstall file lock | pydantic_core DLL locked by running process | Verified via `pip show` that PyPI version was correct | Kill dashboard before venv updates |

## Snags & Blockers

1. **Double Version Locations** - The project has version defined in TWO places:
   - `pyproject.toml` (line 7): Used by build system
   - `src/omni_cortex/__init__.py` (line 3): Used by runtime
   - Impact: Required an extra commit to fix
   - Resolution: Updated both files and pushed additional commit

2. **UV vs Twine for PyPI** - UV's `uv publish` command:
   - Doesn't read ~/.pypirc credentials
   - Requires explicit `--token` flag
   - Impact: Wasted time debugging credentials
   - Resolution: Fell back to `python -m twine upload`

3. **Local Installation Verification** - Multiple Python environments:
   - System Python had older version
   - Project venv had editable install
   - Impact: Confusing version checks
   - Resolution: Use `pip show omni-cortex` for authoritative version

## Lessons Learned

1. **Always sync both version files**: When bumping version, update BOTH `pyproject.toml` AND `src/omni_cortex/__init__.py`

2. **Clean dist/ before every build**: Old artifacts can cause conflicts with PyPI

3. **Use twine for PyPI uploads**: More reliable than `uv publish` for credential handling

4. **UV venvs need `uv pip`**: Regular pip doesn't work in UV-managed environments

5. **Verify with `pip show`**: Most reliable way to check installed version

6. **Update local installation after release**: Add step to update local venv to match PyPI

## Command Improvements

### `/omni` Command Updates Needed:

1. **Add version sync step**: Update both version files together
2. **Clean dist/ before build**: `rm -rf dist/`
3. **Use twine instead of uv publish**: More reliable credentials
4. **Add local installation update**: `uv pip install --upgrade omni-cortex` after publish
5. **Add version verification step**: `pip show omni-cortex` to confirm

## Process Improvements

1. **Pre-release checklist**:
   - [ ] Both version files updated
   - [ ] dist/ directory cleaned
   - [ ] Tests passing
   - [ ] Frontend builds

2. **Post-release verification**:
   - [ ] PyPI page accessible
   - [ ] `pip install omni-cortex==X.Y.Z` works
   - [ ] Local venv updated
   - [ ] Version verified with `pip show`

## Metrics

- **Total Duration**: ~45 minutes
- **Feature Implementation**: ~30 minutes (smooth)
- **Release Process**: ~15 minutes (snags encountered)
- **Extra Commits Needed**: 1 (version sync fix)
- **Failed Commands**: 4 (uv publish x2, pip in UV venv, force reinstall)

## Files Created
- `dashboard/backend/image_service.py` (NEW)
- `dashboard/frontend/src/components/ImageGenerationPanel.vue` (NEW)
- `docs/retrospectives/2026-01-09-image-generation-release.md` (this file)

## Action Items

- [x] Create retrospective document
- [ ] Update `/omni` command with improved workflow
- [ ] Store lessons in memory for future sessions
