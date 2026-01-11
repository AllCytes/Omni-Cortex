# Contributing to Omni-Cortex

Thank you for your interest in contributing to Omni-Cortex!

## Development Setup

### Quick Setup (with Claude Code)

If you're using Claude Code, just run:

```bash
/dev-setup
```

This command will guide you through the entire setup process.

### Prerequisites

- Python 3.10+
- Node.js 18+ (for dashboard frontend)
- Git

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/AllCytes/Omni-Cortex.git
cd Omni-Cortex

# Install in editable mode (CRITICAL!)
pip install -e .
```

### Editable Install (Important!)

Always use `pip install -e .` (editable mode) during development. This ensures:

- CLI commands (`omni-cortex`, `omni-cortex-dashboard`) use your local source code
- Changes you make are immediately reflected without reinstalling
- Entry points work correctly with local modules

**Common Issue**: If you see `ModuleNotFoundError: No module named 'omni_cortex'` when running CLI commands, you likely have a non-editable install. Fix with:

```bash
pip install -e .
```

### Dashboard Development

```bash
# Install dashboard backend dependencies
cd dashboard/backend
pip install -r requirements.txt

# Install dashboard frontend dependencies
cd ../frontend
npm install

# Build frontend (required for production mode)
npm run build

# Or run in development mode with hot reload
npm run dev
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src/omni_cortex
```

## Making Changes

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Run tests to ensure nothing is broken
4. Commit with a descriptive message
5. Push and create a pull request

## After Pulling Updates

If you pull updates that modify `pyproject.toml` or package structure, re-run:

```bash
pip install -e .
```

This ensures your local entry points are up to date.

## Post-Release Local Development

After a new version is published to PyPI, if you installed from PyPI, your local CLI commands will use the PyPI version, not your local source. To switch back to development mode:

```bash
# Re-install in editable mode
pip install -e .

# Verify you're using local source
pip show omni-cortex
# Location should point to your repo, not site-packages
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings to public functions and classes
- Keep functions focused and reasonably sized

## Questions?

Open an issue on GitHub if you have questions or run into problems.
