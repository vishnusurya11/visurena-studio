"""How many commits HEAD is ahead of a sha.  Lives outside studio/command_center: the web
process spawns nothing (test_the_web_process_imports_nothing_from_scripts), so the board
receives this function as a callable."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def commits_after(sha: str) -> int:
    """Commits on HEAD after `sha` (git rev-list --count); 0 when git cannot say."""
    try:
        out = subprocess.run(["git", "rev-list", "--count", f"{sha}..HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=5, check=True).stdout
        return int(out.strip() or 0)
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0
