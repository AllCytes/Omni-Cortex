# Security Audit Report - Omni-Cortex v1.3.0

**Date**: 2026-01-09
**Auditor**: Claude Code Security Skill
**Mode**: Full Audit (All 5 Areas)
**Status**: 19 Issues Found (Updated with Prompt Injection Audit)

---

## Executive Summary

Comprehensive security audit of the Omni-Cortex MCP project identified 19 security issues across 4 severity levels. The application has good SQL injection protection via parameterized queries, but lacks authentication, rate limiting, and has XSS vulnerabilities in the Vue frontend.

**Update (Prompt Injection Audit)**: Additional Area 5 audit identified 4 medium-severity prompt injection vulnerabilities related to memory content being injected into LLM prompts without sanitization.

---

## Critical Issues (3)

### 1. Real API Key Exposed in .env File
- **File**: `dashboard/backend/.env:3`
- **Issue**: Production Gemini API key stored in local .env file
- **Risk**: Key exposure if file is accidentally shared, synced, or accessed by unauthorized users
- **Fix**: Rotate immediately at https://aistudio.google.com/apikey
- **Status**: [ ] Fixed

### 2. No Authentication on API Endpoints
- **File**: `dashboard/backend/main.py` (all 40+ endpoints)
- **Issue**: All API endpoints publicly accessible without authentication
- **Risk**: Anyone on the network can read, modify, or delete all data
- **Fix**: Implement JWT, session-based, or API key authentication
- **Status**: [ ] Fixed

### 3. No Rate Limiting
- **File**: Project-wide
- **Issue**: No rate limiting on any endpoint including AI-intensive ones
- **Risk**: DoS attacks, resource exhaustion, API quota abuse
- **Fix**: Add `slowapi` middleware (suggest 100 req/15min general, 10 req/min for AI endpoints)
- **Status**: [ ] Fixed

---

## High Priority Issues (5)

### 4. XSS via v-html in ChatPanel.vue
- **File**: `dashboard/frontend/src/components/ChatPanel.vue:899`
- **Code**: `v-html="renderMarkdown(message.content, message.sources)"`
- **Risk**: Malicious content in memories can execute JavaScript when viewed
- **Fix**: Install DOMPurify and sanitize markdown output
- **Status**: [ ] Fixed

### 5. XSS via v-html in MemoryCard.vue
- **File**: `dashboard/frontend/src/components/MemoryCard.vue:84`
- **Code**: `v-html="contentPreview"`
- **Risk**: Same as above - script injection via memory content
- **Fix**: Sanitize with DOMPurify before rendering
- **Status**: [ ] Fixed

### 6. Path Traversal - Project Parameter
- **File**: `dashboard/backend/main.py:257`
- **Code**: `project: str = Query(...)` - accepts any file path
- **Risk**: Attacker can access any SQLite database on the filesystem
- **Fix**: Validate paths to `.omni-cortex/cortex.db` within allowed directories only
- **Status**: [ ] Fixed

### 7. Path Traversal - Static File Serving
- **File**: `dashboard/backend/main.py:980-985`
- **Code**: `file_path = DIST_DIR / path` without sanitization
- **Risk**: Requests like `/../../../etc/passwd` could escape DIST_DIR
- **Fix**: Use `Path.resolve()` and verify result is within DIST_DIR
- **Status**: [ ] Fixed

### 8. Missing Security Headers
- **File**: `dashboard/backend/main.py`
- **Missing Headers**:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Content-Security-Policy`
  - `Strict-Transport-Security`
- **Risk**: Clickjacking, MIME sniffing, XSS attacks
- **Fix**: Add security headers middleware
- **Status**: [ ] Fixed

---

## Medium Priority Issues (8)

### 9. WebSocket No Authentication
- **File**: `dashboard/backend/main.py:815-833`
- **Issue**: WebSocket endpoint accepts any connection without auth
- **Risk**: Unauthorized real-time data access
- **Fix**: Add WebSocket authentication (token-based)
- **Status**: [ ] Fixed

### 10. CORS Too Permissive
- **File**: `dashboard/backend/main.py:140-147`
- **Code**: `allow_methods=["*"], allow_headers=["*"]`
- **Risk**: Cross-origin attacks in production
- **Fix**: Restrict to specific methods (GET, POST, PUT, DELETE) and headers needed
- **Status**: [ ] Fixed

### 11. Vulnerable axios Dependency
- **File**: `dashboard/frontend/package.json`
- **Version**: axios 1.6.0
- **CVEs**: CVE-2025-58754 (DoS), CVE-2025-27152 (SSRF)
- **Fix**: `npm install axios@latest` (1.12.0+)
- **Status**: [ ] Fixed

### 12. Log Injection Vulnerability
- **File**: `dashboard/backend/logging_config.py:69-70`
- **Code**: User input interpolated directly into log messages
- **Risk**: Attackers can inject fake log entries
- **Fix**: Sanitize/escape log input or use structured logging
- **Status**: [ ] Fixed

### 13. Prompt Injection via Memory Content (NEW - Area 5)
- **File**: `dashboard/backend/chat_service.py:42-61`
- **Code**: `{context_str}` directly interpolated into Gemini prompt
- **Risk**: Malicious memory content can manipulate LLM behavior, bypass safety guidelines, or cause information leakage
- **Fix**: Use XML-based prompt structure to separate user data from instructions:
  ```python
  <memories>{xml_escape(context_str)}</memories>
  <user_question>{xml_escape(question)}</user_question>
  ```
- **Status**: [ ] Fixed

### 14. Prompt Injection via Chat Context in Image Generation (NEW - Area 5)
- **File**: `dashboard/backend/image_service.py:170-181`
- **Code**: Chat messages directly inserted into image generation prompt without sanitization
- **Risk**: User chat messages can manipulate image generation or bypass content policies
- **Fix**: Apply XML-based sanitization approach for chat context
- **Status**: [ ] Fixed

### 15. Tool Input Logging Exposes Secrets (NEW - Area 5)
- **File**: `hooks/pre_tool_use.py:141,153`
- **Code**: `truncate(json.dumps(tool_input, default=str))` logged to database
- **Risk**: API keys, passwords, or tokens passed as tool parameters are logged in plain text
- **Fix**: Add sanitization for sensitive fields before logging:
  ```python
  def sanitize_sensitive_data(tool_input: dict) -> dict:
      sensitive_fields = {'api_key', 'password', 'token', 'secret', 'credential'}
      return {k: '[REDACTED]' if k.lower() in sensitive_fields else v
              for k, v in tool_input.items()}
  ```
- **Status**: [ ] Fixed

### 16. No Validation of Memory Content for Injection Patterns (NEW - Area 5)
- **File**: `src/omni_cortex/tools/memories.py` (cortex_remember tool)
- **Issue**: Memory content stored without validation for instruction-like patterns
- **Risk**: Users can create memories containing adversarial instructions that affect future prompts
- **Fix**: Add content validation when storing memories:
  ```python
  suspicious_patterns = [
      r'(?i)(ignore|disregard|forget).*instructions',
      r'(?i)(new system|system prompt|override)',
  ]
  ```
- **Status**: [ ] Fixed

---

## Low Priority Issues (3)

> **Note**: Issue numbers 13-16 are new from Area 5 (Prompt Injection Audit). Original issues 13-15 renumbered to 17-19.

### 17. No HTTPS Enforcement
- **File**: `dashboard/backend/main.py:992-1000`
- **Issue**: Server runs on HTTP without SSL
- **Risk**: Data transmitted in plaintext
- **Fix**: Configure SSL certificates or use reverse proxy (nginx/Caddy)
- **Status**: [ ] Fixed

### 18. Console.log in Production
- **Files**: Multiple Vue components, `useWebSocket.ts`
- **Issue**: Debug statements visible in browser console
- **Risk**: Information leakage to attackers
- **Fix**: Use logging library with production disable or remove statements
- **Status**: [ ] Fixed

### 19. Missing .env.example
- **File**: `dashboard/backend/` (missing)
- **Issue**: No template for required environment variables
- **Risk**: Developers may hardcode secrets or share .env files
- **Fix**: Create `.env.example` with placeholder values
- **Status**: [ ] Fixed

---

## Positive Findings

| Area | Status | Details |
|------|--------|---------|
| SQL Injection | SECURE | All queries use parameterized statements |
| Secrets in Code | SECURE | API keys loaded via `os.getenv()` |
| Git History | CLEAN | No secrets found in commit history |
| .gitignore | CORRECT | `.env` properly ignored (line 99) |
| Input Validation | GOOD | Pydantic models validate all API inputs |
| Sort Column Injection | SECURE | Whitelist validation in memory.py |
| WebFetch Usage | SECURE | No external URL fetching implemented |
| Code Execution from LLM | SECURE | No eval/exec on LLM outputs |
| MCP Tool Inputs | SECURE | Pydantic validation on all tool parameters |
| Jailbreak Patterns | CLEAN | No known attack signatures found |
| CLAUDE.md | CLEAN | No secrets or backdoor instructions |

---

## Remediation Priority

### Immediate (Do Now)
1. Rotate Gemini API key
2. Install DOMPurify and fix XSS
3. Add path validation
4. **Sanitize memory content in LLM prompts (NEW)** - Use XML-based prompt structure

### Short-term (This Week)
5. Add authentication middleware
6. Add rate limiting
7. Add security headers
8. Fix static file path traversal
9. Upgrade axios
10. **Redact secrets from tool input logging (NEW)**
11. **Add memory content validation for injection patterns (NEW)**

### Long-term (This Month)
12. WebSocket authentication
13. CORS hardening for production
14. Log injection fix
15. HTTPS configuration
16. Remove console.log statements
17. Create .env.example
18. **Implement prompt injection testing suite (NEW)**

---

## Files Modified by This Audit

- [ ] `dashboard/backend/.env` - Rotate API key
- [ ] `dashboard/backend/main.py` - Auth, rate limiting, headers, path validation
- [ ] `dashboard/backend/logging_config.py` - Log sanitization
- [ ] `dashboard/frontend/src/components/ChatPanel.vue` - DOMPurify
- [ ] `dashboard/frontend/src/components/MemoryCard.vue` - DOMPurify
- [ ] `dashboard/frontend/src/composables/useWebSocket.ts` - Remove console.log
- [ ] `dashboard/frontend/package.json` - Upgrade axios
- [ ] `dashboard/backend/.env.example` - Create new file

**New from Prompt Injection Audit (Area 5):**
- [ ] `dashboard/backend/chat_service.py` - XML-based prompt sanitization
- [ ] `dashboard/backend/image_service.py` - Sanitize chat context in prompts
- [ ] `hooks/pre_tool_use.py` - Redact sensitive fields from tool input logging
- [ ] `src/omni_cortex/tools/memories.py` - Add content validation for injection patterns

---

## Audit Metadata

- **Previous Audit**: v1.0.2 (2 days ago) - 1 medium issue (model_name validation)
- **Memory ID**: mem_1768024332176_9fa12fe7
- **Tool**: Claude Code `/security` skill
- **Methodology**: Ken (Kai)'s 11-Step Pre-Production Checklist + IndyDevDan patterns + Prompt Injection Audit (Area 5)
- **Updated**: 2026-01-10 - Added Area 5 Prompt Injection findings
