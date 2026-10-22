"""The PreToolUse fence matched Write|Edit|NotebookEdit|Bash only, so a PowerShell
command that wrote under library/ never reached the hook (group R bench R-B8,
2026-10-22: 8 of 12 write attempts leaked on today's hook).  The matcher names
PowerShell, and its command text is read by the Bash patterns plus the cmdlets
and aliases that write a file (Set-Content/sc, Add-Content/ac, Out-File,
New-Item/ni, Copy-Item/cpi, Move-Item/mi, Remove-Item/ri, [IO.File]::Write*).
A defect fix, not a fence: dontAsk already denies an unlisted PowerShell tool."""
from __future__ import annotations

import anyio
import pytest

from studio import brain


def _denied(repo, command: str) -> bool:
    data = {"hook_event_name": "PreToolUse", "tool_name": "PowerShell",
            "tool_input": {"command": command}, "cwd": str(repo), "session_id": "s"}
    out = anyio.run(brain.deny_library_writes(repo), data, "tu-1", {})
    return out.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


def test_the_hook_matcher_names_powershell():
    assert "PowerShell" in brain.WRITERS.split("|")


@pytest.mark.parametrize("command", [
    r"Set-Content library\book\x.json '{}'",
    r"sc library/book/x.json '{}'",
    r"Add-Content -Path library\book\learnings.jsonl -Value '{}'",
    r"ac library\book\learnings.jsonl x",
    r"'{}' | Out-File library\book\plan.json",
    r"New-Item -ItemType File library\book\verdict.json -Force",
    r"ni library\book\verdict.json",
    r"Copy-Item C:\tmp\plan.json library\book\plan.json",
    r"cpi C:\tmp\plan.json library\book\plan.json",
    r"Move-Item C:\tmp\plan.json library\book\plan.json",
    r"Remove-Item library\book\episodes\ep01\plan.json",
    r"ri library\book\episodes\ep01\plan.json",
    r"[IO.File]::WriteAllText('library\book\x.json', '{}')",
    r"[System.IO.File]::AppendAllText('library/book/x.jsonl', 'x')",
    r"echo '{}' > library\book\x.json",
    r"uv run python scripts/episode/sign_plan.py book 20",
    r"git push origin master",
])
def test_a_powershell_write_into_library_is_denied(tmp_path, command):
    assert _denied(tmp_path, command)


@pytest.mark.parametrize("command", [
    r"Get-Content library\book\episodes\ep01\drive.jsonl -Tail 20",
    r"uv run --no-sync pytest -q tests/test_x.py",
    r"git log --oneline -5",
    r"Set-Content studio\notes.txt 'x'",
])
def test_a_powershell_read_or_a_write_elsewhere_is_allowed(tmp_path, command):
    assert not _denied(tmp_path, command)
