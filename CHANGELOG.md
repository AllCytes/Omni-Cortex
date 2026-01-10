# Changelog

All notable changes to OmniCortex will be documented in this file.

## [1.4.0] - 2026-01-10

### Security Remediation
Comprehensive security audit and remediation addressing 19 vulnerabilities:

- **XSS Protection**: Added DOMPurify sanitization to ChatPanel and MemoryCard
- **Path Traversal Protection**: PathValidator class validates all file path parameters
- **Security Headers**: Added X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, CSP
- **Prompt Injection Protection**: XML-based sanitization for LLM prompts
- **CORS Hardening**: Restricted methods and headers from wildcards
- **Input Validation**: Enhanced validation for all API endpoints
- **Log Sanitization**: Sensitive fields redacted from activity logs
- **Dependency Updates**: Upgraded axios to patch CVE-2025-58754 and CVE-2025-27152

### Added
- `dashboard/backend/security.py` - PathValidator for file path validation
- `dashboard/backend/prompt_security.py` - Prompt injection protection utilities
- `dashboard/backend/.env.example` - Environment variable template
- `dashboard/frontend/src/utils/sanitize.ts` - Client-side XSS protection
- `dashboard/frontend/src/utils/logger.ts` - Development-only console logging
- 31 new security tests in `tests/test_prompt_security.py`

## [1.3.0] - 2026-01-09

### Added
- **Slash Command/Skill Analytics Dashboard**
  - `CommandUsageChart.vue`: Bar chart for slash command usage with scope filtering (universal/project)
  - `SkillUsageChart.vue`: Bar chart for skill adoption and success rates
  - `MCPUsageChart.vue`: Doughnut chart for MCP server integration metrics
  - Enhanced `ActivityTimeline.vue`: Expandable rows with full JSON input/output, copy-to-clipboard
  - MCP server badges and command/skill badges in activity display

- **Database Migration v1.1**
  - New columns: `command_name`, `command_scope`, `mcp_server`, `skill_name`
  - Indexed for efficient querying
  - Backward compatible with older databases

- **Auto-Detection System**
  - Extracts skill names from Skill tool calls
  - Determines scope (universal/project) by checking file locations
  - Identifies MCP servers from tool naming patterns (`mcp__servername__toolname`)

- **New API Endpoints**
  - `GET /api/stats/command-usage` - Slash command usage statistics
  - `GET /api/stats/skill-usage` - Skill usage statistics
  - `GET /api/stats/mcp-usage` - MCP server usage statistics
  - `GET /api/activities/{id}` - Full activity details with input/output

## [1.2.0] - 2026-01-09

### Added
- **Nano Banana Pro Image Generation**
  - Integrated Gemini 3 Pro image generation into Ask AI panel
  - Mode toggle in ChatPanel header (Chat / Generate)
  - 8 preset templates: Infographic, Key Insights, Tips & Tricks, Quote Card, Workflow, Comparison, Summary Card, Custom
  - Memory selection side panel with search and select all/none
  - Batch generation (1, 2, or 4 images per request)
  - Per-image preset, aspect ratio, and size controls
  - Click-to-edit refinement with multi-turn conversation
  - 10 aspect ratios: 1:1, 16:9, 9:16, 4:3, 3:4, 4:5, 5:4, 2:3, 3:2, 21:9
  - 3 resolutions: 1K, 2K, 4K
  - Google Search grounding toggle for real-time data

### New Components
- `dashboard/backend/image_service.py` - Image generation service (450 lines)
- `dashboard/frontend/src/components/ImageGenerationPanel.vue` - Full-featured panel (550 lines)
- API endpoints: `/api/image/generate-batch`, `/api/image/refine`, `/api/image/status`, `/api/image/presets`

## [1.0.8] - 2026-01-08

### Added
- **Dashboard UX Enhancements**
  - **Live Update Timer**: Real-time elapsed time display ("Just now", "5s ago", etc.) with Page Visibility API optimization
  - **Onboarding Flow**: 7-step guided tour for first-time users with spotlight overlay
  - **Help Guide System**: Modal with keyboard shortcuts, feature overview, and tour replay option
  - Pulsing green dot indicator when connected to show live status

### New Components
- `useElapsedTime.ts`: Composable for reactive elapsed time formatting
- `onboardingStore.ts`: Pinia store for tour state management
- `OnboardingOverlay.vue`: Spotlight tour component with keyboard navigation (Arrow keys, Enter, Esc)
- `HelpModal.vue`: Tabbed help dialog (Shortcuts, Features, About)

## [1.0.7] - 2026-01-08

### Added
- Storage Architecture PDF explaining SQLite design decision
- Ask AI upgraded to Gemini 3 Flash model

## [1.0.6] - 2026-01-08

### Added
- **IndyDevDan-style structured logging** for dashboard backend
  - `[SUCCESS]` logs with key metrics for all endpoints
  - `[ERROR]` logs with full tracebacks and context
  - Agent-readable format: `[YYYY-MM-DD HH:MM:SS] [LEVEL] message`
  - Enables autonomous debugging and monitoring
- New logging module: `dashboard/backend/logging_config.py`
- Structured logging functions: `log_success()` and `log_error()`

### Changed
- Dashboard endpoints now emit structured logs for better observability
- Key endpoints (`/api/memories`, `/api/chat`, update/delete) include comprehensive logging
- Logs include relevant metrics (count, timing, operation details)

### Documentation
- Added Troubleshooting FAQ PDF with common issues and solutions
- PATH configuration guidance for Windows users
- Dashboard command troubleshooting

## [1.0.5] - 2026-01-04

### Added
- Comprehensive documentation suite (5 PDFs)
- Dashboard web interface with 6 feature tabs
- Visual relationship graph with D3.js
- Activity heatmap visualization

### Fixed
- Recall timeout issue when embeddings disabled

## [1.0.4] - 2026-01-03

### Added
- `omni-cortex-dashboard` CLI command
- Web dashboard with Vue 3 frontend

## [1.0.2-1.0.3] - 2025-12

### Added
- Core MCP server functionality
- 18 specialized tools for memory management
- Dual-layer storage (activity log + knowledge store)
- Session management
- Global cross-project search

## [1.0.0] - 2025-12

### Added
- Initial release
- Basic memory storage and recall
- SQLite FTS5 search
- MCP protocol integration
