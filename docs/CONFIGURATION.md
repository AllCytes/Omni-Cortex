# Omni Cortex MCP - Configuration Guide

## Quick Start

After installation, run the setup command:

```bash
omni-cortex-setup
```

This automatically:
1. Adds the MCP server to `~/.claude.json`
2. Configures activity logging hooks in `~/.claude/settings.json`
3. Creates default configuration

## Configuration Files

### Project Configuration

Create `.omni-cortex/config.yaml` in your project directory:

```yaml
# Schema version (do not change)
schema_version: "1.0"

# Embedding/Semantic Search
embedding_enabled: false          # Enable semantic search (requires sentence-transformers)
embedding_model: "all-MiniLM-L6-v2"  # Embedding model name

# Importance Decay
decay_rate_per_day: 0.5          # How quickly importance decays
freshness_review_days: 30         # Days before memory needs review

# Output
max_output_truncation: 10000      # Max characters for tool output

# Session
auto_provide_context: true        # Automatically provide session context
context_depth: 3                  # Number of past sessions to summarize

# Search
default_search_mode: "hybrid"     # Default: keyword, semantic, or hybrid

# Global Features
global_sync_enabled: true         # Sync memories to global database
```

### Global Configuration

Create `~/.omni-cortex/config.yaml` for settings that apply to all projects:

```yaml
embedding_enabled: false
decay_rate_per_day: 0.5
freshness_review_days: 30
```

**Priority:** Project config > Global config > Defaults

## Database Locations

| Database | Path | Purpose |
|----------|------|---------|
| Project | `.omni-cortex/cortex.db` | Project-specific memories and activities |
| Global | `~/.omni-cortex/global.db` | Cross-project memory index |

## Semantic Search

### Enabling Semantic Search

1. Install dependencies:
   ```bash
   pip install omni-cortex[semantic]
   ```

2. Enable in config:
   ```yaml
   embedding_enabled: true
   ```

3. Restart Claude Code

### First Use Warning

On first use, the embedding model (~90MB) downloads automatically. This may cause a brief delay. If it hangs:

1. Disable embeddings: `embedding_enabled: false`
2. Use keyword search (works great for most cases)
3. Try again later when you have a stable connection

### Supported Models

| Model | Dimensions | Notes |
|-------|------------|-------|
| `all-MiniLM-L6-v2` | 384 | Default, fast, good quality |
| `sentence-transformers/all-mpnet-base-v2` | 768 | Higher quality, slower |

## Hook Configuration

Activity logging hooks are configured in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "\"C:\\Python313\\python.exe\" \"path\\to\\hooks\\pre_tool_use.py\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "\"C:\\Python313\\python.exe\" \"path\\to\\hooks\\post_tool_use.py\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "\"C:\\Python313\\python.exe\" \"path\\to\\hooks\\stop.py\""
          }
        ]
      }
    ]
  }
}
```

The `omni-cortex-setup` command configures these automatically.

## MCP Server Configuration

The MCP server is configured in `~/.claude.json`:

```json
{
  "mcpServers": {
    "omni-cortex": {
      "command": "C:\\Python313\\python.exe",
      "args": ["-m", "omni_cortex.server"]
    }
  }
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CLAUDE_PROJECT_DIR` | Current project directory (set by Claude Code) |
| `CLAUDE_SESSION_ID` | Current session ID (set by Claude Code) |

## Troubleshooting

### MCP Server Not Starting

1. Check `~/.claude.json` has correct Python path
2. Verify omni-cortex is installed: `pip show omni-cortex`
3. Test manually: `python -m omni_cortex.server`

### Hooks Not Logging

1. Check `~/.claude/settings.json` for hook configuration
2. Verify hook scripts exist at the configured paths
3. Test hook manually: `echo '{}' | python path/to/hooks/post_tool_use.py`

### Semantic Search Hanging

1. Set `embedding_enabled: false` in config
2. Use keyword search mode
3. The issue typically occurs during first model download on Windows

### Database Locked

1. Close other Claude Code sessions using the same project
2. Delete `.omni-cortex/cortex.db-wal` and `.omni-cortex/cortex.db-shm`

## Uninstalling

```bash
# Remove Claude Code configuration
omni-cortex-setup --uninstall

# Uninstall package
pip uninstall omni-cortex

# Optionally remove data
rm -rf .omni-cortex/           # Project data
rm -rf ~/.omni-cortex/         # Global data
```
