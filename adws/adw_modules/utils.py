"""Utility functions for ADWs."""

import os
import secrets
import subprocess
from datetime import datetime
from pathlib import Path


def generate_adw_id() -> str:
    """Generate a unique ADW ID.

    Format: adw_{timestamp}_{random_hex}
    Example: adw_1704825600_a1b2c3d4
    """
    timestamp = int(datetime.now().timestamp())
    random_hex = secrets.token_hex(4)
    return f"adw_{timestamp}_{random_hex}"


def get_project_root() -> Path:
    """Get the project root directory.

    Walks up from current directory looking for markers like:
    - .git directory
    - pyproject.toml
    - package.json
    """
    current = Path.cwd()

    for path in [current] + list(current.parents):
        if (path / ".git").exists():
            return path
        if (path / "pyproject.toml").exists():
            return path
        if (path / "package.json").exists():
            return path

    return current


def get_agents_dir(adw_id: str) -> Path:
    """Get the agents directory for an ADW.

    Creates: agents/{adw_id}/
    """
    project_root = get_project_root()
    agents_dir = project_root / "agents" / adw_id
    agents_dir.mkdir(parents=True, exist_ok=True)
    return agents_dir


def get_phase_dir(adw_id: str, phase: str) -> Path:
    """Get the directory for a specific phase.

    Creates: agents/{adw_id}/{phase}/
    """
    phase_dir = get_agents_dir(adw_id) / phase
    phase_dir.mkdir(parents=True, exist_ok=True)
    return phase_dir


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def cleanup_dashboard_ports(port: int = 8765, verbose: bool = False) -> bool:
    """Clean up orphaned processes on dashboard port.

    This prevents 'address already in use' errors when starting the dashboard
    after a previous run didn't shut down cleanly.

    Args:
        port: Port number to clean up (default: 8765)
        verbose: Print status messages if True

    Returns:
        True if cleanup was successful or not needed
    """
    import platform

    if platform.system() == "Windows":
        try:
            # Find processes using the port
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                if verbose:
                    print(f"[Cleanup] Could not check port {port}")
                return False

            # Parse output to find PIDs
            pids = []
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        if pid.isdigit():
                            pids.append(pid)

            if not pids:
                if verbose:
                    print(f"[Cleanup] Port {port} is free")
                return True

            # Kill each process
            for pid in pids:
                try:
                    subprocess.run(
                        ["powershell", "-Command", f"Stop-Process -Id {pid} -Force"],
                        capture_output=True,
                        timeout=5,
                    )
                    if verbose:
                        print(f"[Cleanup] Killed process {pid} on port {port}")
                except Exception as e:
                    if verbose:
                        print(f"[Cleanup] Failed to kill process {pid}: {e}")

            return True

        except Exception as e:
            if verbose:
                print(f"[Cleanup] Error during cleanup: {e}")
            return False

    else:
        # Unix/Linux/Mac
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0 or not result.stdout.strip():
                if verbose:
                    print(f"[Cleanup] Port {port} is free")
                return True

            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid.isdigit():
                    try:
                        subprocess.run(["kill", "-9", pid], timeout=5)
                        if verbose:
                            print(f"[Cleanup] Killed process {pid} on port {port}")
                    except Exception as e:
                        if verbose:
                            print(f"[Cleanup] Failed to kill process {pid}: {e}")

            return True

        except FileNotFoundError:
            if verbose:
                print("[Cleanup] lsof command not found (Unix/Linux/Mac only)")
            return False
        except Exception as e:
            if verbose:
                print(f"[Cleanup] Error during cleanup: {e}")
            return False
