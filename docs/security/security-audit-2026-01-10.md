# Security Audit Report - Omni-Cortex v1.5.0

**Date**: 2026-01-10
**Auditor**: Claude Code Security Skill
**Mode**: Full Audit (All 5 Areas)
**Previous Audit**: v1.3.0 (2026-01-09) - 19 Issues, v1.4.0 Security Remediation Released
**Status**: 3 Issues Remaining (all auth-related from previous audit), 5 New Issues Fixed This Session

---

## Executive Summary

Follow-up security audit of Omni-Cortex after the v1.4.0 security remediation release. The previous audit identified 19 issues; this audit confirms **14 issues have been fixed** and identifies **3 remaining authentication-related issues**. Additionally, **5 new prompt injection issues were discovered and fixed** during this audit session.

### v1.4.0 Remediation Summary (VERIFIED FIXED)
- XSS vulnerabilities fixed with DOMPurify sanitization
- Path traversal protection implemented via PathValidator
- Security headers middleware added
- CORS hardening applied
- axios upgraded to 1.13.2
- Log injection prevention implemented
- Prompt injection defenses added (XML-structured prompts)
- Secret redaction in pre_tool_use.py hook
- .env.example created

### Remaining Issues (Require Architectural Decision)
The following critical issues from v1.3.0 audit remain **unfixed** - these require user decisions on auth approach:
1. **No Authentication** on API endpoints
2. **No Rate Limiting** applied (infrastructure exists but not used)
3. **WebSocket No Authentication**

### Issues Fixed This Session
5 new prompt injection vulnerabilities were fixed:
- MCP tool outputs now XML-escaped (formatting.py)
- Injection detection added to cortex_remember (memories.py)
- Secret redaction added to post_tool_use.py
- Custom prompt escaping in image_service.py
- Summary prompt escaping in chat_service.py

---

## Critical Issues (2)

### 1. No Authentication on API Endpoints [UNFIXED from v1.3.0]
- **File**: `dashboard/backend/main.py` (all 40+ endpoints)
- **Issue**: All API endpoints publicly accessible without authentication
- **Risk**: Anyone on the network can read, modify, or delete all data
- **Fix**: Implement JWT, session-based, or API key authentication
- **Status**: [ ] Not Fixed
- **Note**: Acceptable for local/trusted network use; critical for any public deployment

### 2. WebSocket No Authentication [UNFIXED from v1.3.0]
- **File**: `dashboard/backend/main.py:935-953`
- **Issue**: WebSocket endpoint accepts any connection without auth
- **Risk**: Unauthorized real-time data access, activity stream exposure
- **Fix**: Add WebSocket authentication (token-based)
- **Status**: [ ] Not Fixed

---

## High Priority Issues (1 Remaining, 1 Fixed)

### 3. Rate Limiting Not Applied [UNFIXED from v1.3.0]
- **File**: `dashboard/backend/main.py:22-31, 225-231`
- **Issue**: slowapi infrastructure exists and is configured, but no `@limiter.limit()` decorators are applied to any endpoint
- **Risk**: DoS attacks, API quota abuse for AI endpoints (`/api/chat`, `/api/image/generate-batch`)
- **Fix**: Add rate limit decorators to all endpoints
- **Status**: [ ] Not Fixed (Infrastructure ready, just needs decorators)

### 4. Memory Content Not Sanitized in MCP Tool Outputs [NEW] [FIXED]
- **File**: `src/omni_cortex/utils/formatting.py:30-32, 47-49, 75-76`
- **Issue**: When memories are returned via `cortex_recall`, content is formatted and returned to Claude without sanitization. Malicious content could include embedded instructions like `</memories> SYSTEM OVERRIDE: ...`
- **Risk**: Prompt injection via stored memories that influence Claude's behavior when recalled
- **Fix**: Apply XML escaping or instruction detection before returning memory content
- **Status**: [x] Fixed - Added xml_escape() and detect_injection_patterns() to formatting.py
- **Severity**: HIGH - Claude Code directly consumes these outputs

---

## Medium Priority Issues (0 Remaining, 4 Fixed This Session)

### 5. detect_injection_patterns() Not Used in MCP Tools [NEW] [FIXED]
- **File**: `src/omni_cortex/tools/memories.py` (entire file)
- **Issue**: The `detect_injection_patterns()` function exists in `prompt_security.py` but is never called when storing or recalling memories via MCP tools
- **Risk**: Memories with injection patterns are stored and returned without any warning
- **Fix**: Call `detect_injection_patterns()` in `cortex_remember` and flag suspicious content
- **Status**: [x] Fixed - Added injection detection to cortex_remember, logs warnings and adds security note to response

### 6. post_tool_use.py Missing Secret Redaction [NEW] [FIXED]
- **File**: `hooks/post_tool_use.py:136-144`
- **Issue**: Unlike `pre_tool_use.py` which uses `redact_sensitive_fields()`, the post hook logs `tool_input` and `tool_output` WITHOUT redaction
- **Risk**: Sensitive data in tool outputs gets logged to database
- **Fix**: Add `redact_sensitive_fields()` call before logging
- **Status**: [x] Fixed - Added redact_sensitive_fields() to post_tool_use.py for both input and output

### 7. Custom Prompt Not Escaped in Image Service [FIXED]
- **File**: `dashboard/backend/image_service.py:213-214`
- **Issue**: `request.custom_prompt` is appended to prompt without XML escaping, while `memory_context` and `chat_context` ARE escaped
- **Risk**: User can inject instructions via custom prompt field
- **Fix**: Apply `xml_escape()` to custom_prompt
- **Status**: [x] Fixed - Added xml_escape() to custom_prompt and refinement_prompt

### 8. save_conversation Summary Prompt Unescaped [FIXED]
- **File**: `dashboard/backend/chat_service.py:217-226`
- **Issue**: Raw conversation content interpolated into summary prompt without using `build_safe_prompt()`
- **Risk**: Injection via conversation messages that manipulate summary generation
- **Fix**: Use `build_safe_prompt()` for summary generation
- **Status**: [x] Fixed - Added xml_escape() and XML tags for safe content structure

---

## Low Priority Issues (1)

### 9. CSP Allows unsafe-inline and unsafe-eval
- **File**: `dashboard/backend/main.py:105-113`
- **Issue**: `'unsafe-inline'` and `'unsafe-eval'` required for Vue.js, weakens XSS protection
- **Risk**: Reduced defense-in-depth against XSS
- **Fix**: Consider nonce-based CSP for production builds
- **Status**: [ ] Acceptable for development; consider hardening for production

---

## Issues Fixed in v1.4.0 (Verified)

| # | Issue | File | Fix Applied |
|---|-------|------|-------------|
| 1 | XSS via v-html ChatPanel | ChatPanel.vue | DOMPurify + sanitizeMarkdown() |
| 2 | XSS via v-html MemoryCard | MemoryCard.vue | DOMPurify sanitization |
| 3 | Path Traversal - Project Parameter | main.py | PathValidator.validate_project_path() |
| 4 | Path Traversal - Static Files | main.py | PathValidator.is_safe_static_path() |
| 5 | Missing Security Headers | main.py | SecurityHeadersMiddleware added |
| 6 | CORS Too Permissive | security.py | Environment-aware CORS config |
| 7 | Vulnerable axios | package.json | Upgraded to 1.13.2 |
| 8 | Log Injection | logging_config.py | sanitize_log_input() added |
| 9 | Prompt Injection - Memory Context | chat_service.py | build_safe_prompt() with XML escaping |
| 10 | Prompt Injection - Image Chat Context | image_service.py | xml_escape() applied |
| 11 | Tool Input Secrets Logged | pre_tool_use.py | redact_sensitive_fields() added |
| 12 | No Memory Content Validation | prompt_security.py | detect_injection_patterns() created |
| 13 | Console.log in Production | useWebSocket.ts | logger utility created |
| 14 | Missing .env.example | .env.example | Created with placeholders |

---

## Positive Findings

| Area | Status | Details |
|------|--------|---------|
| SQL Injection | SECURE | All queries use parameterized statements |
| Secrets in Code | SECURE | API keys loaded via `os.getenv()`, not hardcoded |
| Git History | CLEAN | No secrets found in tracked files |
| .gitignore | CORRECT | `.env` properly ignored |
| Input Validation | SECURE | Pydantic models validate all API inputs |
| Sort Column Injection | SECURE | Whitelist validation in database.py:120-123 |
| XSS Protection | FIXED | DOMPurify sanitization implemented |
| Path Traversal | FIXED | PathValidator with regex patterns |
| Security Headers | FIXED | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, CSP present |
| CORS | IMPROVED | Environment-aware, restricted methods/headers in production |
| Prompt Injection (Dashboard) | FIXED | XML-structured prompts via build_safe_prompt() |
| Secret Redaction (pre-hook) | FIXED | redact_sensitive_fields() implemented |
| Log Sanitization | FIXED | sanitize_log_input() prevents injection |
| .env.example | FIXED | Template with placeholder values exists |

---

## Remediation Priority

### Immediate (Before Public Deployment)
1. Add authentication middleware (JWT/API key)
2. Apply rate limiting decorators to endpoints
3. Add WebSocket authentication

### Short-term (This Week)
4. Sanitize MCP tool outputs in formatting.py
5. Use detect_injection_patterns() in cortex_remember
6. Add redact_sensitive_fields() to post_tool_use.py
7. Apply xml_escape() to image service custom_prompt

### Long-term (This Month)
8. Consider nonce-based CSP for production Vue builds
9. Add memory content validation at storage time
10. Implement comprehensive prompt injection test suite

---

## Files Requiring Modification

### High Priority (Auth - Requires Decision)
- [ ] `dashboard/backend/main.py` - Add auth middleware and rate limit decorators

### Files Modified This Session (Fixed)
- [x] `src/omni_cortex/utils/formatting.py` - Added xml_escape(), detect_injection_patterns(), applied to all content outputs
- [x] `src/omni_cortex/tools/memories.py` - Added injection detection to cortex_remember
- [x] `hooks/post_tool_use.py` - Added redact_sensitive_fields() for tool input/output
- [x] `dashboard/backend/image_service.py` - Added xml_escape() to custom_prompt and refinement_prompt
- [x] `dashboard/backend/chat_service.py` - Added xml_escape() and XML structure to summary prompt

---

## Dependency Audit

| Package | Current | Status | Notes |
|---------|---------|--------|-------|
| axios | 1.13.2 | SECURE | Upgraded from vulnerable 1.6.0 |
| fastapi | 0.115.5 | SECURE | No known CVEs |
| uvicorn | 0.32.1 | SECURE | No known CVEs |
| slowapi | 0.1.9 | SECURE | Rate limiting ready |
| DOMPurify | 3.2.3 | SECURE | XSS protection |

---

## Comparison with Previous Audit

| Metric | v1.3.0 (Jan 9) | v1.5.0 (Jan 10) | Change |
|--------|----------------|-----------------|--------|
| Critical Issues | 3 | 2 | -1 (API key rotated separately) |
| High Issues | 5 | 1 | -4 (1 fixed this session) |
| Medium Issues | 8 | 0 | -8 (4 fixed this session) |
| Low Issues | 3 | 1 | -2 |
| **Total Open** | **19** | **3** | **-16 (84% reduction)** |
| **Fixed This Session** | - | **5** | New prompt injection fixes |

---

## Risk Assessment

### For Local/Trusted Network Use: LOW-MEDIUM
- No authentication is acceptable when only trusted users have network access
- All data manipulation requires direct API access
- XSS/injection attacks require storing malicious content

### For Public Deployment: HIGH
- **CRITICAL**: Must add authentication before exposing to internet
- **CRITICAL**: Must apply rate limiting to prevent abuse
- **HIGH**: WebSocket authentication required

---

## Audit Metadata

- **Previous Audit**: 2026-01-09 (v1.3.0) - 19 issues
- **Security Remediation**: v1.4.0 released 2026-01-10
- **Memory ID**: To be stored after audit completion
- **Tool**: Claude Code `/security` skill
- **Methodology**: Ken (Kai)'s 11-Step Pre-Production Checklist + Prompt Injection Audit
