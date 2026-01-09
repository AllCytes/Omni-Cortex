# Changelog

All notable changes to OmniCortex will be documented in this file.

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
