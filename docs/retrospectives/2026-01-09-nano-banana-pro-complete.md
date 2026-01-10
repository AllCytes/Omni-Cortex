# Retrospective: Nano Banana Pro Image Generation (Complete)
Date: 2026-01-09

## Summary
Implemented Nano Banana Pro image generation integration for the Omni-Cortex dashboard and released as v1.2.0. Post-release, the user encountered multiple critical issues including UI layout problems, missing configuration UI, and runtime API errors. This document covers both the initial release and the subsequent debugging/fixes.

---

## Part 1: Initial Implementation & Release

### Tasks Completed
1. Backend image_service.py with 8 presets, batch generation, multi-turn refinement
2. API endpoints for image generation, refinement, status
3. Frontend ImageGenerationPanel.vue with memory selection, presets, gallery
4. ChatPanel.vue mode toggle integration
5. Frontend api.ts types and functions
6. Git commit and push to GitHub
7. PyPI publication (v1.2.0)
8. Local installation update

### Release Errors

| Error | Cause | Resolution | Prevention |
|-------|-------|------------|------------|
| `uv publish` credentials failure | uv doesn't read ~/.pypirc file | Used `python -m twine upload dist/*` instead | Update /omni command to use twine |
| Old dist files interfered | Previous build artifacts in dist/ | `rm -rf dist/` before build | Always clean dist/ before building |
| Version mismatch (pyproject.toml vs __init__.py) | pyproject.toml had 1.1.0, __init__.py had 1.0.11 | Updated both files, made extra commit | Always update BOTH version locations together |
| `pip install` failed in UV venv | UV-managed venvs don't have pip module | Used `uv pip install` instead | Document UV venv usage pattern |
| Force reinstall file lock | pydantic_core DLL locked by running process | Verified via `pip show` that PyPI version was correct | Kill dashboard before venv updates |

### Release Snags

1. **Double Version Locations**
   - `pyproject.toml` (line 7) and `src/omni_cortex/__init__.py` (line 3)
   - Required an extra commit to sync both
   - Solution: Update BOTH together when bumping version

2. **UV vs Twine for PyPI**
   - `uv publish` doesn't read ~/.pypirc credentials
   - Solution: Use `python -m twine upload` instead

---

## Part 2: Post-Release Fixes

### Issues Reported by User
1. Chat/Generate section too narrow (scrunched layout)
2. Dark mode not working on Memory Context and Image Generation sections
3. Need Settings section for API key configuration
4. Getting notice about GEMINI_API_KEY and google-genai installation
5. 404 error when trying to generate images
6. 500 error after image generation (bytes validation)
7. Same error when trying to refine/edit images
8. No error notification shown on refine failure

### Post-Release Errors

| Error | Cause | Resolution | Prevention |
|-------|-------|------------|------------|
| 404 NOT_FOUND for model | Model name `gemini-2.0-flash-preview-image-generation` doesn't exist | Changed to `gemini-3-pro-image-preview` | Check official docs/search before using model names |
| Pydantic ValidationError: bytes for string | `thought_signature` returned as bytes but model expected string | Convert bytes to base64: `base64.b64encode(sig).decode()` | Test with actual API before release |
| Same bytes error in refine endpoint | Same issue in refine_image() method | Applied same base64 conversion fix | When fixing a pattern, check ALL occurrences |
| TypeScript errors in SettingsModal.vue | Escaped quotes in Vue template | Created const variables for command strings | Avoid complex escaped strings in Vue templates |
| Frontend silently failing on refine | Error only logged to console | Added proper error handling with UI display | Always show errors to users |
| Deprecated package warning | `google.generativeai` is deprecated | Migrated to new `google.genai` package | Check deprecation warnings in test output |

### Post-Release Snags

1. **Model Name Discovery** (~5 min lost)
   - The 4500-line API docs mentioned `gemini-3-pro-image-preview` but implementation used wrong name
   - Feature completely blocked (404 on every request)
   - Solution: Web search confirmed correct model name

2. **thought_signature Binary Data** (Hit twice!)
   - Gemini API returns bytes, Pydantic expects string
   - First fix: generate_single_image()
   - Missed: refine_image() had same pattern
   - Solution: Check ALL occurrences when fixing a bug pattern

3. **Silent Frontend Failures**
   - Refine operation caught errors but only logged to console
   - User clicked refine, nothing happened, no feedback
   - Solution: Set error array and close modal to show user the error

4. **Package Migration Required**
   - `google.generativeai` deprecated during implementation
   - Full rewrite of chat_service.py needed
   - New pattern: `genai.Client(api_key=key).models.generate_content()`

---

## All Files Modified

### Initial Implementation (New Files)
| File | Description |
|------|-------------|
| `dashboard/backend/image_service.py` | Core image generation service (450 lines) |
| `dashboard/frontend/src/components/ImageGenerationPanel.vue` | Full-featured UI panel (550 lines) |

### Post-Release Fixes
| File | Changes |
|------|---------|
| `dashboard/frontend/src/App.vue` | Widened chat section (max-w-4xl → max-w-6xl) |
| `dashboard/frontend/src/components/ImageGenerationPanel.vue` | Dark mode fixes, error handling for refine |
| `dashboard/frontend/src/components/AppHeader.vue` | Added Settings button and modal integration |
| `dashboard/frontend/src/components/SettingsModal.vue` | **NEW**: API status, setup instructions |
| `dashboard/backend/image_service.py` | Fixed model name, bytes→base64 in generate and refine |
| `dashboard/backend/chat_service.py` | Migrated to new google.genai package |

---

## Combined Lessons Learned

### Development Phase
1. **Always sync both version files**: When bumping version, update BOTH `pyproject.toml` AND `src/omni_cortex/__init__.py`
2. **Clean dist/ before every build**: Old artifacts can cause conflicts with PyPI
3. **Use twine for PyPI uploads**: More reliable than `uv publish` for credential handling
4. **UV venvs need `uv pip`**: Regular pip doesn't work in UV-managed environments

### Testing Phase
5. **Test with real API before release**: Unit tests passing doesn't validate model names or response formats
6. **Watch deprecation warnings**: The `google.generativeai` deprecation was visible in test output

### Bug Fixing Phase
7. **Check ALL occurrences of a pattern**: When fixing bytes-to-string in generate(), should have immediately checked refine()
8. **Always show errors to users**: `console.error()` is for developers; users need UI feedback

### API Integration
9. **Verify model names via official sources**: API docs can be incomplete; web search confirms
10. **Handle binary data explicitly**: When API returns bytes, check if response model expects string

---

## Code Patterns Established

### 1. Binary to Base64 Conversion (Python)
```python
if hasattr(part, 'thought_signature') and part.thought_signature:
    sig = part.thought_signature
    if isinstance(sig, bytes):
        thought_signature = base64.b64encode(sig).decode()
    else:
        thought_signature = str(sig)
```

### 2. New google.genai Client Pattern (Python)
```python
from google import genai

_client = None

def get_client():
    global _client
    if _client is None and _api_key:
        _client = genai.Client(api_key=_api_key)
    return _client

# Usage
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=prompt,
)
```

### 3. Frontend Error Surfacing (Vue/TypeScript)
```typescript
try {
    const result = await refineImage({ ... })
    if (!result.success) {
        generationErrors.value = [result.error || 'Failed to refine image']
    }
} catch (e) {
    generationErrors.value = [e instanceof Error ? e.message : 'Failed to refine image']
}
```

---

## Command Improvements Needed

### `/omni` Command Updates:
1. **Add version sync step**: Update both version files together
2. **Clean dist/ before build**: `rm -rf dist/`
3. **Use twine instead of uv publish**: More reliable credentials
4. **Add local installation update**: `uv pip install --upgrade omni-cortex` after publish
5. **Add version verification step**: `pip show omni-cortex` to confirm

### `/test` Command Updates:
1. **Fail on deprecation warnings**: Option to treat DeprecationWarning as error
2. **API smoke test**: At least one real API call to verify model names

### `/build` Command Updates:
1. **API validation step**: Verify external APIs return expected format
2. **Check for duplicate bug patterns**: When fixing, grep for all occurrences

---

## Process Improvements

### Pre-Release Checklist
- [ ] Both version files updated
- [ ] dist/ directory cleaned
- [ ] Tests passing (no deprecation warnings)
- [ ] Frontend builds
- [ ] Real API tested (not just unit tests)
- [ ] Model names verified against official docs

### Post-Release Verification
- [ ] PyPI page accessible
- [ ] `pip install omni-cortex==X.Y.Z` works
- [ ] Local venv updated
- [ ] Feature tested in browser with real API
- [ ] Error paths tested (what happens on failure?)

### Error Handling Audit
- [ ] Every try/catch surfaces errors to users
- [ ] No silent failures (console.error only)
- [ ] Error messages are user-friendly
- [ ] Loading states cleared on error

---

## Metrics

| Metric | Release Phase | Fix Phase | Total |
|--------|--------------|-----------|-------|
| Duration | ~45 min | ~30 min | ~75 min |
| Errors Encountered | 5 | 6 | 11 |
| Files Created | 2 | 1 | 3 |
| Files Modified | 5 | 6 | 11 |
| Extra Commits Needed | 1 | 0 | 1 |
| User Interruptions | 0 | 4 | 4 |
| Time Lost to Avoidable Issues | 15 min | 15 min | 30 min |

---

## Action Items

### Completed
- [x] Implement Nano Banana Pro image generation
- [x] Release v1.2.0 to PyPI
- [x] Fix model name error
- [x] Fix thought_signature bytes conversion (both methods)
- [x] Add Settings modal with API setup instructions
- [x] Fix dark mode styling
- [x] Fix layout width
- [x] Add frontend error handling for refine
- [x] Migrate to new google.genai package
- [x] Create comprehensive retrospective

### Pending
- [ ] Update `/omni` command with improved workflow
- [ ] Add API smoke test to `/test` command
- [ ] Add pattern: Check related methods when fixing bugs
- [ ] Consider: Pre-commit hook for deprecation check
- [ ] Add google-genai to pyproject.toml dependencies

---

## Related Memories

- mem_1768007167466_d72f5ef4: Original implementation (had model name bug)
- mem_1768008640693_a8a95f59: v1.2.0 release notes
- mem_1768008126558_29de6fd0: Test results showing deprecation warning
- mem_1768012593922_86c94f36: Post-release fixes lessons learned
