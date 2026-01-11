# Retrospective: ADW Fixes and v1.7.1 Release
Date: 2026-01-10

## Summary

This session focused on releasing v1.7.1 with documentation improvements, consolidating .env configuration, fixing a critical security gap (read hook for .env files), and debugging the ADW (Agentic Development Workflow) system.

**Key Accomplishments:**
- Released v1.7.1 to PyPI and GitHub
- Added beginner-friendly "Getting Started (5 Minutes)" guide to README
- Consolidated .env configuration to project root
- Created read-tool-damage-control.py hook to protect secrets
- Discovered ADW architecture issue - subprocess approach doesn't invoke skills
- Discovered IndyDevDan uses `claude-agent-sdk` for proper agent orchestration

## Errors Encountered

| Error | Cause | Resolution | Prevention |
|-------|-------|------------|------------|
| `[WinError 2] system cannot find file` | ADW agent.py hardcoded "claude" command | Added `find_claude_cli()` function | Use .env with CLAUDE_CODE_PATH |
| `stream-json requires --verbose` | Missing --verbose flag with --print | Added `--verbose` to command args | Document CLI requirements |
| `charmap codec can't decode byte 0x8f` | Windows default encoding vs UTF-8 | Added `encoding="utf-8", errors="replace"` | Always specify encoding on Windows |
| ADW skills not invoking | Claude treats -p prompts as conversation | **UNSOLVED** - needs claude-agent-sdk | Redesign ADWs to use SDK |
| API key visible in conversation | No read hook for .env files | Created read-tool-damage-control.py | Hook now blocks .env reads |

## Snags & Blockers

1. **API Key Exposure (Security)**
   - Impact: Gemini API key visible in conversation, had to rotate twice
   - Resolution: Created read hook for .env files in damage-control hooks
   - Root cause: Edit hook existed but Read hook didn't

2. **ADW Skill Invocation Failure**
   - Impact: ADWs "complete" but don't actually do anything
   - Resolution: UNRESOLVED - needs architectural change
   - Root cause: `claude -p "prompt"` treats input as conversation, not command

3. **Windows Subprocess Issues**
   - Impact: Multiple errors with .cmd files and encoding
   - Resolution: shell=True for .cmd, UTF-8 encoding, list2cmdline()
   - Root cause: Windows-specific subprocess handling

## Lessons Learned

### Technical Lessons
1. **claude-agent-sdk is the proper way** - IndyDevDan uses `claude-agent-sdk` Python package for programmatic agent control, not subprocess calls to `claude -p`
2. **Read hooks are as important as Edit hooks** - Secrets need protection from both reading AND writing
3. **Windows subprocess requires special handling** - .cmd files need shell=True, encoding must be explicit
4. **Claude CLI flags interact** - `--print` with `--output-format=stream-json` requires `--verbose`

### Architecture Lessons
1. **ADWs need redesign** - Current subprocess approach is fundamentally limited
2. **claude-agent-sdk provides**: ClaudeSDKClient, async message streaming, session resume, proper hooks
3. **Skills can't be invoked via -p prompts** - Claude interprets them as conversation

### Process Lessons
1. **Check both read and write access** when protecting sensitive files
2. **Rotate keys immediately** when exposed, don't wait
3. **Test Windows compatibility** during development, not just on Mac

## Command Improvements

| Command | Change Needed |
|---------|--------------|
| `/omni` | Add step to clean dist/ with elevated permissions |
| ADW system | Migrate from subprocess to claude-agent-sdk |
| `/validate` | No changes needed |

## Process Improvements

### For Future Sessions
1. **Before protecting sensitive files**: Ensure BOTH read and write hooks exist
2. **When fixing Windows issues**: Test encoding, shell mode, and path handling together
3. **For ADW development**: Use claude-agent-sdk instead of subprocess

### Recommended Next Steps

1. **ADW Migration** (High Priority)
   - Install `claude-agent-sdk` in omni-cortex
   - Rewrite agent.py to use ClaudeSDKClient instead of subprocess
   - Reference: `D:\Projects\TAC\multi-agent-orchestration\apps\orchestrator_3_stream\backend\modules\agent_manager.py`

2. **Update Other ADWs**
   - adw_build.py needs same fixes as agent.py
   - adw_validate.py needs same fixes
   - All should use unified agent module

3. **Security Improvements**
   - Audit patterns.yaml for any missing sensitive file patterns
   - Consider adding .npmrc, .pypirc to zeroAccessPaths if not present

## Metrics

| Metric | Value |
|--------|-------|
| Tasks Completed | 5 major |
| Errors Encountered | 5 |
| Errors Resolved | 4 (80%) |
| API Keys Rotated | 2 |
| Files Modified | 15+ |
| Version Released | 1.7.1 |
| Security Hooks Added | 1 (read-tool-damage-control.py) |

## Files Created/Modified This Session

### Created
- `D:\Projects\omni-cortex\.env.example` - Root env config template
- `C:\Users\Tony\.claude\hooks\damage-control\read-tool-damage-control.py` - Secret protection
- `D:\Projects\omni-cortex\docs\retrospectives\2026-01-10-v1.7.0-release-retrospective.md`

### Modified
- `README.md` - Added Getting Started guide
- `pyproject.toml` - Added python-dotenv, bumped to 1.7.1
- `src/omni_cortex/__init__.py` - Version bump
- `dashboard/backend/chat_service.py` - Load from root .env
- `dashboard/backend/image_service.py` - Load from root .env
- `dashboard/backend/.env.example` - Points to root
- `adws/adw_modules/agent.py` - Multiple Windows fixes
- `~/.claude/settings.json` - Added read hook

## Recommendations

### Immediate (This Week)
1. **Install claude-agent-sdk** and prototype ADW migration
2. **Commit ADW fixes** even if skills don't work - subprocess fixes are valuable
3. **Document .env setup** in ADW README

### Short-term (This Month)
1. **Complete ADW migration** to claude-agent-sdk
2. **Create ADW test suite** to validate all phases work
3. **Add ADW troubleshooting** to docs

### Long-term
1. **Consider publishing ADWs** as separate package (omni-cortex-adw)
2. **Create ADW templates** for common workflows
3. **Add ADW dashboard** to visualize workflow progress

---
*Generated by /retrospective skill*
*Key discovery: claude-agent-sdk is the proper tool for multi-agent orchestration*
