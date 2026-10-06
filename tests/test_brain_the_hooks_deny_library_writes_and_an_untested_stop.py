"""The leash is mechanical, not a prompt.  A PreToolUse hook denies any write that
resolves under library/ (data is written by the runner and its judges, never by
hand), any shell route into it (sed -i, tee, a redirect), every sign script,
`git push|reset|amend` and `uv add|remove`.  The fixer's Stop hook refuses to end a
session that edited code without running pytest -- once: `stop_hook_active` is the
loop guard the docs require.  Both rungs run `dontAsk`: an unlisted tool is denied,
never a prompt, so the allow and deny sets are asserted here as the contract."""
from __future__ import annotations

from pathlib import Path

import anyio

from studio import brain

REPO = Path(__file__).resolve().parents[1]


def _pre(tool: str, **tool_input) -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input,
            "cwd": str(REPO), "session_id": "s"}


def _denied(repo: Path, tool: str, **tool_input) -> bool:
    out = anyio.run(brain.deny_library_writes(repo), _pre(tool, **tool_input), "tu-1", {})
    return out.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


def test_an_edit_under_library_is_denied_by_resolved_path(tmp_path):
    assert _denied(tmp_path, "Edit", file_path=str(tmp_path / "library" / "book" / "plan.json"))
    assert _denied(tmp_path, "Write", file_path=str(tmp_path / "studio" / ".." / "library" / "x.json"))
    assert _denied(tmp_path, "NotebookEdit", notebook_path=str(tmp_path / "library" / "n.ipynb"))


def test_a_relative_library_path_resolves_against_the_sessions_cwd(tmp_path):
    hook = brain.deny_library_writes(tmp_path)
    data = {**_pre("Edit", file_path="library/book/episodes/ep20/plan.json"), "cwd": str(tmp_path)}
    out = anyio.run(hook, data, "tu-1", {})
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_an_edit_under_studio_is_allowed(tmp_path):
    assert not _denied(tmp_path, "Edit", file_path=str(tmp_path / "studio" / "brain.py"))
    assert not _denied(tmp_path, "Write", file_path=str(tmp_path / "tests" / "test_x.py"))


def test_shell_routes_into_library_are_denied(tmp_path):
    assert _denied(tmp_path, "Bash", command="sed -i 's/a/b/' library/book/episodes/ep20/plan.json")
    assert _denied(tmp_path, "Bash", command="echo '{}' > library/book/x.json")
    assert _denied(tmp_path, "Bash", command="cat plan.json | tee library/book/plan.json")
    assert _denied(tmp_path, "Bash", command="printf x >> ./library/book/learnings.jsonl")


def test_sign_scripts_and_history_rewrites_are_denied(tmp_path):
    assert _denied(tmp_path, "Bash", command="uv run python scripts/episode/sign_plan.py book 20")
    assert _denied(tmp_path, "Bash", command="git push origin master")
    assert _denied(tmp_path, "Bash", command="git reset --hard HEAD~1")
    assert _denied(tmp_path, "Bash", command="git commit --amend --no-edit")
    assert _denied(tmp_path, "Bash", command="uv add requests")
    assert _denied(tmp_path, "Bash", command="uv remove requests")


def test_read_only_shell_and_the_suite_are_allowed(tmp_path):
    assert not _denied(tmp_path, "Bash", command="uv run --no-sync pytest -q tests/test_brain_x.py")
    assert not _denied(tmp_path, "Bash", command="git log --oneline -5")
    assert not _denied(tmp_path, "Bash", command="git diff HEAD~1 -- studio/brain.py")
    assert not _denied(tmp_path, "Bash", command="cat library/book/episodes/ep20/drive.jsonl")
    assert not _denied(tmp_path, "Bash", command="git commit -m 'a fix with its test'")


def test_the_denial_names_the_rule(tmp_path):
    out = anyio.run(brain.deny_library_writes(tmp_path), _pre("Bash", command="git push"), "t", {})
    assert "library" in out["hookSpecificOutput"]["permissionDecisionReason"]
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"


# --- the Stop guard ---------------------------------------------------------------

def _stop(state, active: bool = False) -> dict:
    hook = brain.refuse_stop_without_tests(state)
    return anyio.run(hook, {"hook_event_name": "Stop", "stop_hook_active": active}, "t", {})


def _post(state, tool: str, **tool_input) -> None:
    hook = brain.audit_tool_call(state)
    anyio.run(hook, {"hook_event_name": "PostToolUse", "tool_name": tool,
                     "tool_input": tool_input, "tool_response": {}}, "t", {})


def test_a_stop_after_an_edit_without_pytest_is_blocked():
    state = brain.FixerState()
    _post(state, "Edit", file_path="studio/x.py")
    assert _stop(state) == {"decision": "block", "reason": brain.STOP_REASON}


def test_a_stop_after_the_suite_ran_is_allowed():
    state = brain.FixerState()
    _post(state, "Edit", file_path="studio/x.py")
    _post(state, "Bash", command="uv run --no-sync pytest -q tests/test_x.py")
    assert _stop(state) == {}


def test_an_edit_after_the_suite_needs_the_suite_again():
    state = brain.FixerState()
    _post(state, "Bash", command="uv run --no-sync pytest -q")
    _post(state, "Write", file_path="tests/test_y.py")
    assert _stop(state)["decision"] == "block"


def test_a_stop_with_no_edit_is_allowed():
    assert _stop(brain.FixerState()) == {}


def test_the_loop_guard_lets_a_second_stop_through():
    state = brain.FixerState()
    _post(state, "Edit", file_path="studio/x.py")
    assert _stop(state, active=True) == {}


# --- the options are the contract ------------------------------------------------

def test_triage_reads_runs_the_suite_and_never_writes():
    opts = brain.triage_options(REPO)
    assert opts.permission_mode == "dontAsk" and opts.setting_sources == ["project"]
    assert opts.model == "claude-sonnet-5-5" and opts.effort == "medium"
    assert opts.max_turns == 15 and opts.max_budget_usd == 1.0
    assert "Bash(uv run --no-sync pytest *)" in opts.allowed_tools
    assert "Bash(uv run --no-sync python scripts/episode/plan_check.py *)" in opts.allowed_tools
    assert {"Edit", "Write", "NotebookEdit", "WebSearch", "WebFetch", "AskUserQuestion",
            "mcp__*"} <= set(opts.disallowed_tools)
    assert not any(t.startswith(("Edit", "Write")) for t in opts.allowed_tools)


def test_the_fixer_edits_code_but_never_library_and_commits_without_pushing():
    opts = brain.fixer_options(REPO)
    assert opts.model == "claude-opus-5-5" and opts.fallback_model == "claude-sonnet-5-5"
    assert opts.effort == "high" and opts.max_turns == 60 and opts.max_budget_usd == 3.0
    assert {"Edit", "Write", "Bash(git add *)", "Bash(git commit *)",
            "Workflow(fix-parked)"} <= set(opts.allowed_tools)
    assert "Edit(/library/**)" in opts.disallowed_tools
    assert not any("push" in t for t in opts.allowed_tools)
    assert set(opts.hooks) == {"PreToolUse", "PostToolUse", "Stop"}


def test_both_rungs_answer_the_verdict_schema_in_utf8_with_one_level_of_subagents():
    for opts in (brain.triage_options(REPO), brain.fixer_options(REPO)):
        assert opts.output_format["type"] == "json_schema"
        assert "response" in opts.output_format["schema"]["properties"]
        assert opts.env["PYTHONUTF8"] == "1"
        assert opts.env["CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH"] == "1"
        assert Path(opts.cwd) == REPO
        assert "PreToolUse" in opts.hooks
