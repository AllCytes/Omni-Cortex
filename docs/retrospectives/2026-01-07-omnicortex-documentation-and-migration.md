# Retrospective: OmniCortex Documentation & Ken MCP Migration
Date: 2026-01-07

## Summary

This session focused on finalizing the OmniCortex MCP project by creating comprehensive teaching materials (4 PDFs) and migrating all slash commands from the deprecated Ken MCP to OmniCortex. The session also established a universal `/retrospective` command for future sessions.

## Tasks Completed

| Task | Status | Files |
|------|--------|-------|
| Create OmniCortex Quick Start PDF | Complete | `docs/OmniCortex_QuickStart.pdf` |
| Create Feature Comparison PDF | Complete | `docs/OmniCortex_FeatureComparison.pdf` |
| Create Philosophy & Inspiration PDF | Complete | `docs/OmniCortex_Philosophy.pdf` |
| Create Command Reference PDF | Complete | `docs/OmniCortex_CommandReference.pdf` |
| Fix PDF title overlap issues | Complete | `docs/create_pdfs.py` |
| Update global CLAUDE.md | Complete | `C:\Users\Tony\.claude\CLAUDE.md` |
| Update 32 slash command files | Complete | Multiple projects |
| Create universal /retrospective | Complete | `C:\Users\Tony\.claude\commands\retrospective.md` |

## Errors Encountered

| Error | Cause | Resolution | Prevention |
|-------|-------|------------|------------|
| `ModuleNotFoundError: reportlab` | Multiple Python environments, venv without pip | Used full path to working Python: `C:/Users/Tony/AppData/Local/Microsoft/WindowsApps/python.exe` | Always verify Python environment before running scripts |
| `KeyError: Style 'Bullet' already defined` | reportlab has built-in styles that conflict with custom names | Renamed all custom styles with 'OC' prefix (OCBody, OCCode, etc.) | Always use unique prefixes for custom PDF styles |
| PDF title/subtitle overlap | Insufficient spacing between title and subtitle elements | Increased `spaceBefore` on subtitle, added explicit `leading` values | Use `leading` >= fontSize + 6 for headers |

## Snags & Blockers

1. **Python Environment Confusion**
   - Impact: 5+ minutes debugging
   - Resolution: Found working Python via `where python` and used full path
   - Learning: Windows Store Python has issues with some venvs

2. **reportlab Style Conflicts**
   - Impact: Multiple edit cycles needed
   - Resolution: Created naming convention with 'OC' prefix
   - Learning: Always check built-in style names before creating custom ones

## Lessons Learned

1. **PDF Generation with reportlab:**
   - Use unique prefixes for all custom ParagraphStyles
   - `leading` controls line height and prevents overlap
   - `spaceBefore` on subtitles is more reliable than `spaceAfter` on titles

2. **Batch File Updates:**
   - Python scripts are more reliable than shell scripts for cross-platform updates
   - Use explicit patterns for find/replace to avoid unintended changes
   - Always exclude `node_modules` and backup directories from searches

3. **Ken MCP to OmniCortex Migration:**
   - Tool mapping: `mcp__ken-you-remember__*` → `mcp__omni-cortex__cortex_*`
   - remember → cortex_remember
   - recall → cortex_recall
   - list_memories → cortex_list_memories

4. **OmniCortex Advantages over Ken MCP:**
   - 18 tools vs 3 (remember, recall, list_memories)
   - Activity logging with automatic hooks
   - Session management with context
   - Cross-project global search
   - Multiple search modes (keyword, semantic, hybrid)

## Command Improvements

- **Created `/retrospective`**: Universal command in global `.claude/commands/` that uses OmniCortex tools for session analysis
- **Updated all global commands**: 14 commands in `C:\Users\Tony\.claude\commands\` now use OmniCortex

## Process Improvements

1. **PDF Creation Workflow:**
   - Create styles with unique prefixes first
   - Test with a single page before building full document
   - Use explicit spacing values (never rely on defaults)

2. **Bulk File Migration:**
   - Create a Python script for complex replacements
   - Test on a single file first
   - Keep a list of files to update in the script for auditability

## Metrics

- **Tasks Completed:** 8
- **Files Updated:** 37 (4 PDFs + 32 command files + CLAUDE.md)
- **Errors Resolved:** 3
- **Time Spent on Issues:** ~15% (mostly Python environment and style conflicts)
- **Time Spent Productively:** ~85%

## Files Created

- `docs/OmniCortex_QuickStart.pdf` (3 pages)
- `docs/OmniCortex_FeatureComparison.pdf` (1 page)
- `docs/OmniCortex_Philosophy.pdf` (2 pages)
- `docs/OmniCortex_CommandReference.pdf` (2 pages)
- `docs/create_pdfs.py` (PDF generation script)
- `C:\Users\Tony\.claude\commands\retrospective.md` (universal command)
- `docs/retrospectives/2026-01-07-omnicortex-documentation-and-migration.md` (this file)

## Recommendations

1. **Consider adding PDF generation to OmniCortex:**
   - The `create_pdfs.py` script could be a template for future documentation
   - Could integrate with FileFactory skill for consistent styling

2. **Verify Ken MCP removal:**
   - Remove Ken MCP from Claude Desktop config if not already done
   - Search for any remaining references in other projects

3. **Document the migration:**
   - Add a note to OmniCortex README about migrating from Ken MCP
   - Include tool name mapping for users transitioning

4. **Test the universal /retrospective:**
   - Run it in a few different projects to verify it works globally
   - Consider adding more OmniCortex tools (get_activities, get_timeline) to enhance analysis
