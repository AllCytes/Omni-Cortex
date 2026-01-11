"""Omni-Cortex ADW (Agentic Development Workflow) System.

This package provides automation for the development lifecycle:
- Plan: Create implementation specs from requirements
- Build: Implement specs using existing slash commands
- Validate: Visual validation with Chrome MCP screenshots
- Review: Compare implementation against spec
- Retrospective: Document lessons learned
- Release: Publish using /omni

Usage:
    # Individual phases
    uv run adws/adw_plan.py "feature request"
    uv run adws/adw_build.py <adw-id>

    # Orchestrated workflows
    uv run adws/adw_plan_build.py "feature request"
    uv run adws/adw_sdlc.py "feature request" [--skip-release]
"""
