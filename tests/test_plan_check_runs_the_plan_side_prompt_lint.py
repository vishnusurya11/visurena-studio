"""The plan-side prompt lint (studio.prompt_lint.plan_faults: P3/P11/P12/P13/P17) runs in the
plan battery, not only in the take builder.

Jekyll ep02, 2026-10-26: six shots named a person who was not staged in their frame ("holding
the small man's stare" on an Utterson single).  plan_check never ran the plan-side lint, so the
plan was signed, voiced and timed before step 06's take builder refused it -- a relaunch, and a
hand fix, for a fault the battery could have handed the writer at step 02."""
import inspect
import json
import sys

sys.path.insert(0, "scripts/episode")


def test_main_runs_the_plan_side_prompt_lint():
    import plan_check

    assert "prompt_lint_gate(" in inspect.getsource(plan_check.main)


def test_the_gate_lints_the_checked_plan_file_and_counts_each_fault_hard(tmp_path, monkeypatch, capsys):
    import plan_check
    from studio import episode_home, prompt_lint

    (tmp_path / "scratch.json").write_text(json.dumps({"shots": [{"index": 18}]}), encoding="utf-8")
    seen = {}
    monkeypatch.setattr(episode_home, "home", lambda book, number: tmp_path)
    monkeypatch.setattr(prompt_lint, "characters", lambda book: [])
    monkeypatch.setattr(prompt_lint, "plan_faults",
                        lambda plan, rows: seen.setdefault("plan", plan) and
                        ["P13 unstaged person: shot 18 'the small man' (edward_hyde) is not staged"])
    token = plan_check.PLAN_FILE.set("scratch.json")
    try:
        hard = plan_check.prompt_lint_gate(tmp_path, 2)
    finally:
        plan_check.PLAN_FILE.reset(token)
    out = capsys.readouterr().out
    assert hard == 1
    assert seen["plan"] == {"shots": [{"index": 18}]}
    assert "G-PROMPTLINT : 1" in out and "the small man" in out


def test_a_clean_plan_prints_clean(tmp_path, monkeypatch, capsys):
    import plan_check
    from studio import episode_home, prompt_lint

    (tmp_path / "plan.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(episode_home, "home", lambda book, number: tmp_path)
    monkeypatch.setattr(prompt_lint, "characters", lambda book: [])
    monkeypatch.setattr(prompt_lint, "plan_faults", lambda plan, rows: [])
    assert plan_check.prompt_lint_gate(tmp_path, 2) == 0
    assert "G-PROMPTLINT : clean" in capsys.readouterr().out
