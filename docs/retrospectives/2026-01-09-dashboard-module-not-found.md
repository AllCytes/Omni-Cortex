# Retrospective: Dashboard Module Not Found Error

Date: 2026-01-09

## Summary

Brief debugging session to resolve a `ModuleNotFoundError` when running `omni-cortex-dashboard` command. The issue was caused by having the package installed from PyPI in non-editable mode while developing locally.

## Errors Encountered

| Error | Cause | Resolution | Prevention |
|-------|-------|------------|------------|
| `ModuleNotFoundError: No module named 'omni_cortex'` | Package installed from PyPI (v1.2.0) in standard mode, not linked to local source | Reinstalled with `pip install -e .` (editable mode) | Always use editable installs during development |

## Snags & Blockers

- **PyPI vs Local Source Conflict**: When a package is installed from PyPI, the entry points (like `omni-cortex-dashboard.exe`) point to the installed package in site-packages, not the local source code. This means local changes to the dashboard module aren't reflected until reinstalled.

## Lessons Learned

1. **Always use editable installs during development**: Running `pip install -e .` ensures entry points use local source code
2. **Check installation mode when debugging import errors**: Use `pip show <package>` to see where it's installed; if it's in site-packages (not a `.egg-link`), it's not editable
3. **After publishing to PyPI, re-run editable install**: Publishing and installing from PyPI can overwrite the editable install

## Command Improvements (IMPLEMENTED)

- **`/dashboard` command**: Added troubleshooting section for ModuleNotFoundError
- **`/omni` command**: Added "Post-Release Local Development" section with `pip install -e .` reminder
- **`/omni` command**: Added new issue to Common Issues section

## Process Improvements (IMPLEMENTED)

1. **Development mode check in dashboard.py**: Added `check_editable_install()` and `warn_non_editable_install()` functions that detect non-editable installs and warn the user
2. **CONTRIBUTING.md created**: New contributor guide emphasizing editable installs throughout the development workflow

## Diagnostic Steps That Worked

1. `pip show omni-cortex` - Confirmed package was installed (v1.2.0)
2. `python -c "from omni_cortex.dashboard import main"` - Confirmed module exists in source
3. The disconnect between these two findings pointed to installation mode issue

## Metrics

- Tasks completed: 1 (fix dashboard command)
- Time spent on issue: ~2 minutes
- Resolution: Single command (`pip install -e .`)

## Quick Reference

**Symptom**: `ModuleNotFoundError` when running CLI commands, but module imports fine in Python

**Likely Cause**: Package installed from PyPI, not in editable mode

**Fix**:
```powershell
pip install -e .
```

**Verify Fix**:
```powershell
omni-cortex-dashboard --help
```
