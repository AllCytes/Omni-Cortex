# Omni Cortex MCP

A universal memory system for Claude Code that combines activity logging with intelligent knowledge storage.

## Features

- **Zero Configuration**: Works out of the box - just install and run setup
- **Dual-Layer Storage**: Activity logging (audit trail) + Knowledge store (memories)
- **15 MCP Tools**: Full-featured API for memory management, activity tracking, and session continuity
- **Semantic Search**: AI-powered search using sentence-transformers (optional)
- **Hybrid Search**: Combines keyword (FTS5) + semantic search for best results
- **Full-Text Search**: SQLite FTS5-powered keyword search with smart ranking
- **Auto-Categorization**: Automatic memory type detection and tag suggestions
- **Session Continuity**: "Last time you were working on..." context
- **Importance Decay**: Frequently accessed memories naturally surface
- **Auto Activity Logging**: Automatically logs all tool calls via hooks

## Installation

### Quick Install (Recommended)

```bash
# Install the package
pip install omni-cortex

# Run automatic setup (configures MCP server + hooks)
omni-cortex-setup
```

That's it! Omni Cortex will now:
- Automatically log all Claude Code tool calls
- Provide memory tools (cortex_remember, cortex_recall, etc.)
- Create a per-project database at `.omni-cortex/cortex.db`

### With Semantic Search

For AI-powered semantic search capabilities:

```bash
pip install omni-cortex[semantic]
omni-cortex-setup
```

### From Source

```bash
git clone https://github.com/AllCytes/Omni-Cortex.git
cd omni-cortex
pip install -e ".[semantic]"
python -m omni_cortex.setup
```

### Manual Configuration

If you prefer manual setup, add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "omni-cortex": {
      "command": "python",
      "args": ["-m", "omni_cortex.server"]
    }
  }
}
```

And optionally configure hooks in `~/.claude/settings.json` for activity logging:

```json
{
  "hooks": {
    "PreToolUse": [{
      "type": "command",
      "command": "python -m omni_cortex.hooks.pre_tool_use"
    }],
    "PostToolUse": [{
      "type": "command",
      "command": "python -m omni_cortex.hooks.post_tool_use"
    }]
  }
}
```

### Uninstall

```bash
omni-cortex-setup --uninstall
pip uninstall omni-cortex
```

## Tools

### Memory Tools (6)

| Tool | Description |
|------|-------------|
| `cortex_remember` | Store information with auto-categorization |
| `cortex_recall` | Search memories (modes: keyword, semantic, hybrid) |
| `cortex_list_memories` | List memories with filters and pagination |
| `cortex_update_memory` | Update memory content, tags, or status |
| `cortex_forget` | Delete a memory |
| `cortex_link_memories` | Create relationships between memories |

### Activity Tools (3)

| Tool | Description |
|------|-------------|
| `cortex_log_activity` | Manually log an activity |
| `cortex_get_activities` | Query the activity log |
| `cortex_get_timeline` | Get a chronological timeline |

### Session Tools (3)

| Tool | Description |
|------|-------------|
| `cortex_start_session` | Start a new session with context |
| `cortex_end_session` | End session and generate summary |
| `cortex_get_session_context` | Get context from previous sessions |

### Utility Tools (3)

| Tool | Description |
|------|-------------|
| `cortex_list_tags` | List all tags with usage counts |
| `cortex_review_memories` | Review and update memory freshness |
| `cortex_export` | Export data to markdown or JSON |

## Memory Types

Memories are automatically categorized into:

- `general` - General notes and information
- `warning` - Cautions, things to avoid
- `tip` - Tips, tricks, best practices
- `config` - Configuration and settings
- `troubleshooting` - Debugging and problem-solving
- `code` - Code snippets and algorithms
- `error` - Error messages and failures
- `solution` - Solutions to problems
- `command` - CLI commands
- `concept` - Definitions and explanations
- `decision` - Architectural decisions

## Storage

- **Per-project**: `.omni-cortex/cortex.db` in your project directory
- **Global**: `~/.omni-cortex/global.db` for cross-project search

## Configuration

Create `.omni-cortex/config.yaml` in your project:

```yaml
schema_version: "1.0"
embedding_enabled: true
decay_rate_per_day: 0.5
freshness_review_days: 30
auto_provide_context: true
context_depth: 3
```

## Documentation

- [Tool Reference](docs/TOOLS.md) - Complete documentation for all 15 tools with examples
- [Configuration Guide](docs/CONFIGURATION.md) - Configuration options and troubleshooting

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
ruff check src tests
```

## Security

Omni Cortex v1.0.3 has been security reviewed:
- All SQL queries use parameterized statements
- Input validation via Pydantic models
- Model name validation prevents code injection
- YAML loading uses `safe_load()`

## License

MIT
