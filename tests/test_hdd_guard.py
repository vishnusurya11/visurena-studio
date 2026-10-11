"""The Bash guard refuses a recursive scan that climbs above the repo or sweeps
library/ on the D: hard disk (2026-10-11: an orphaned `grep -rn ... . ..` and a
cache scan held D: at 700-1000% disk time)."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "hdd_guard.py"
spec = importlib.util.spec_from_file_location("hdd_guard", GUARD)
hdd_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hdd_guard)


def test_a_recursive_grep_that_climbs_above_the_repo_is_refused():
    assert hdd_guard.refusal("grep -rn foo --include=*.json -l . ..")


def test_a_recursive_grep_over_library_is_refused():
    assert hdd_guard.refusal("grep -R episode library/")


def test_a_find_over_the_drive_root_is_refused():
    assert hdd_guard.refusal("find /d/ -name '*.mp4'")


def test_a_scoped_grep_over_code_passes():
    assert hdd_guard.refusal("grep -rn load_placed studio scripts tests") is None


def test_a_plain_command_passes():
    assert hdd_guard.refusal("git status --short") is None


def test_a_library_read_that_is_not_a_scan_passes():
    assert hdd_guard.refusal("cat library/x/episodes/ep27/plan.json") is None


def test_the_hook_denies_on_stdin_json():
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "grep -r x .."}})
    out = subprocess.run([sys.executable, str(GUARD)], input=payload, capture_output=True, text=True)
    assert json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_the_hook_is_silent_on_a_passing_command():
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}})
    out = subprocess.run([sys.executable, str(GUARD)], input=payload, capture_output=True, text=True)
    assert out.returncode == 0 and out.stdout == ""
