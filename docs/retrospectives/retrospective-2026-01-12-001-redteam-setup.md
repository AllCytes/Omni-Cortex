# Retrospective: Red-Team Security Testing Setup

**Date**: 2026-01-12
**Session Duration**: ~1 hour
**Focus**: Setting up and running `/redteam` command with promptfoo

---

## Summary

Integrated `/redteam` command documentation into the ADW workflow guide, fixed multiple configuration issues with promptfoo, resolved API authentication problems, and successfully established a security baseline with 71% pass rate (15/21 tests).

---

## Errors Encountered

| Error | Cause | Resolution | Prevention |
|-------|-------|------------|------------|
| Promptfoo plugin validation error | Plugin syntax changed in v0.100+ | Changed `- prompt-injection` to `- id: prompt-injection` | Check promptfoo docs when updating |
| 401 Authentication error | Used OAuth token (`sk-ant-oat-`) instead of API key (`sk-ant-api03-`) | Created new API key from console.anthropic.com | Document difference between OAuth and API keys |
| 404 Model not found | Model ID `claude-sonnet-4-5-20250514` doesn't exist | Reverted to `claude-sonnet-4-20250514` | Verify model IDs before updating configs |
| API key exposed in output | PowerShell's `curl` alias for `Invoke-WebRequest` has different syntax | User revoked key and created new one | Avoid using curl in PowerShell or use `curl.exe` explicitly |

---

## Snags & Blockers

### 1. Environment Variable Not Taking Effect
- **Issue**: Set `ANTHROPIC_API_KEY` but promptfoo still got 401
- **Cause**: PowerShell caches environment at session start
- **Resolution**: Must restart PowerShell after `[Environment]::SetEnvironmentVariable()`
- **Impact**: ~10 minutes debugging

### 2. PowerShell curl Alias
- **Issue**: `curl` in PowerShell is alias for `Invoke-WebRequest`
- **Cause**: Windows PowerShell default behavior
- **Resolution**: Would need `curl.exe` for real curl, or use proper Invoke-WebRequest syntax
- **Impact**: Accidentally exposed API key in error message

### 3. Promptfoo Plugin IDs Changed
- **Issue**: Older plugin IDs like `jailbreak`, `prompt-injection` no longer valid
- **Cause**: Promptfoo v0.100+ requires `id:` prefix and renamed some plugins
- **Resolution**: WebFetch to docs.promptfoo.dev for current plugin list
- **Impact**: ~15 minutes researching and fixing

---

## Lessons Learned

### Critical
1. **OAuth tokens ≠ API keys**: `sk-ant-oat-` (OAuth) doesn't work with direct API calls. Need `sk-ant-api03-` from console.anthropic.com
2. **Promptfoo config has breaking changes**: v0.100+ changed plugin syntax significantly
3. **PowerShell environment variables**: Require session restart to take effect

### Operational
4. **Red-teaming frequency**: Monthly for full suite, quick checks after pattern updates
5. **Two security commands serve different purposes**:
   - `/security` → audits YOUR codebase (every feature)
   - `/redteam` → tests CLAUDE's defenses (periodic)
6. **71% baseline is solid**: The 6 "failures" were style issues (redirect vs explicit refusal), not actual security breaches

### Process
7. **Store baselines immediately**: Used `cortex_remember` to save results for future comparison
8. **Check prerequisites first**: promptfoo + API key needed before any tests run

---

## Command Improvements

### Update: `~/.claude/commands/redteam.md`

**Changes needed**:
1. Add prerequisite check for API key type (must be `sk-ant-api03-`, not `sk-ant-oat-`)
2. Add note about PowerShell environment variable restart requirement
3. Update model reference to known-working `claude-sonnet-4-20250514`

### Already Updated: `~/.claude/security/promptfoo.yaml`

**Changes made this session**:
- Removed explicit `apiKey:` config (let promptfoo auto-detect)
- Changed provider to `anthropic:messages:claude-sonnet-4-20250514`
- Updated plugins to use `id:` prefix format
- Changed `jailbreak` plugin to `hijacking` (renamed in promptfoo)
- Added `pliny` dataset plugin for Pliny-specific attacks

---

## Process Improvements

### For Future Red-Team Sessions

1. **Before running `/redteam`**:
   ```powershell
   # Check API key type (must show sk-ant-api, not sk-ant-oat)
   $env:ANTHROPIC_API_KEY.Substring(0,10)
   ```

2. **After promptfoo updates**: Check release notes for breaking changes

3. **Store baselines**: Always `cortex_remember` results after successful runs

### Documentation Updates Made

- Added Part 9 (Red-Teaming Integration) to `specs/guides/adw-workflow-recipes-and-phase-ordering.md`
- Added Part 10 (Complete Command Reference) with phase table
- Added recipes for LLM-integrated features, environment setup, monthly maintenance

---

## Metrics

| Metric | Value |
|--------|-------|
| Tasks Completed | 4 |
| Configuration Errors | 4 |
| Time on Debugging | ~30 minutes |
| Time on Documentation | ~20 minutes |
| Red-Team Pass Rate | 71% (15/21) |
| Memories Created | 1 (baseline) |

---

## Test Results Summary

**Passed (15)**:
- GODMODE/Pliny signatures
- Developer mode
- DAN persona
- Base64 encoded attacks
- Command injection (rm -rf)
- Malicious code execution
- API key extraction
- Environment variable leak
- All role-play jailbreaks

**Failed (6 - style issues)**:
- Redirect responses instead of explicit refusal
- Not actual security breaches

---

## Files Modified

| File | Change |
|------|--------|
| `~/.claude/security/promptfoo.yaml` | Fixed plugin syntax, model ID, removed explicit apiKey |
| `specs/guides/adw-workflow-recipes-and-phase-ordering.md` | Added Part 9 & 10 for red-teaming |

---

## Recommendations

1. **Update /redteam command** to include API key type validation
2. **Schedule monthly reminder** for full red-team runs
3. **Run `/redteam hooks`** after any pattern.yaml updates
4. **Consider documenting** OAuth vs API key difference in security docs
5. **Re-run baseline** after Claude model updates to track changes

---

*Generated by /retrospective on 2026-01-12*
