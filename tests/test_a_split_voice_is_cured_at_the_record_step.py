"""ep21 (2026-10-08 15:16Z): the upload door refused 'unnamed_first_person_narrator
is not one voice (worst pair 0.423)' -- after every picture was made.  The
voice check had written that report at 00:30, and step 04 was 'done' because
the report EXISTED; nothing read its verdict before publish.  The brain then
misread the stop as step 09's and parked the episode.

Ten narrator pairs sat under their floors, eight of them calm pairs at
0.67-0.69 against 0.70; lines l03 and l16 were in most of them.  The cure is
the record step's: re-say the fewest lines that cover every failing pair,
once, before anything downstream is built on them."""
from __future__ import annotations

import json
from types import SimpleNamespace

from scripts.episode import step_04_record as step
from studio import autopilot

EP21 = [["l03", "l37"], ["l01", "l16"], ["l03", "l16"], ["l03", "l07"], ["l03", "l10"],
        ["l16", "l23"], ["l02", "l03"], ["l16", "l37"], ["l07", "l36"], ["l16", "l36"]]


def test_the_fewest_lines_that_cover_every_failing_pair():
    assert step.split_lines({"n": {"ok": False, "under": EP21}}) == [3, 7, 16]


def test_a_voice_that_holds_asks_for_nothing():
    assert step.split_lines({"n": {"ok": True, "under": []}, "c": {"ok": True}}) == []


def _ctx(tmp_path, report: dict, redone: list | None = None):
    home = tmp_path / f"ep21_{len(list(tmp_path.iterdir()))}"
    (home / "audio" / "lines").mkdir(parents=True)
    (home / "review").mkdir()
    (home / "plan.json").write_text(json.dumps({"lines": [{"index": 0}]}), encoding="utf-8")
    (home / "audio" / "lines" / "lines.json").write_text(json.dumps([{"index": 0}]), encoding="utf-8")
    (home / "review" / "speaker_check.json").write_text(json.dumps(report), encoding="utf-8")
    if redone is not None:
        (home / "review" / step.REVOICED).write_text(json.dumps(redone), encoding="utf-8")
    calls = []
    ctx = SimpleNamespace(home=home, extra=[], book_dir=tmp_path,
                          run_script=lambda script, *a, **k: calls.append((script, a)))
    return ctx, calls


def test_a_split_voice_is_not_done_until_its_lines_were_said_again(tmp_path):
    split = {"n": {"ok": False, "under": EP21}}
    ctx, _ = _ctx(tmp_path, split)
    assert step.done(ctx) is False
    ctx, _ = _ctx(tmp_path, split, redone=[3, 7, 16])
    assert step.done(ctx) is True                     # said again once: the door decides
    ctx, _ = _ctx(tmp_path, {"n": {"ok": True, "under": []}})
    assert step.done(ctx) is True


def test_a_split_report_from_before_the_pairs_were_kept_is_checked_again(tmp_path):
    """ep21's report (00:30Z) names only its worst pair: not done, so the run
    re-checks and then knows which lines to say again."""
    ctx, _ = _ctx(tmp_path, {"n": {"ok": False, "worst_pair": ["l24", "l36"]}})
    assert step.done(ctx) is False


def test_the_run_says_the_split_lines_again_and_checks_once_more(tmp_path, monkeypatch):
    ctx, calls = _ctx(tmp_path, {"n": {"ok": False, "under": EP21}})
    monkeypatch.setattr(step, "voiceless", lambda ctx: [])
    step.run(ctx)
    scripts = [(s.rsplit("/", 1)[-1], a) for s, a in calls]
    assert scripts[0][0] == "say_lines.py"
    assert ("say_lines.py", ("--redo=3,7,16",)) in scripts
    assert scripts[-1][0] == "speaker_check.py"
    assert json.loads((ctx.home / "review" / step.REVOICED).read_text(encoding="utf-8")) == [3, 7, 16]


def test_the_publish_refusal_routes_back_to_the_record_step():
    tail = ("REFUSED:\n  - speaker_check: unnamed_first_person_narrator is not one voice "
            "(worst pair 0.423)\nTraceback (most recent call last):\n")
    kind, reason, order = autopilot.classify(tail, set())
    assert (kind, reason, order) == ("cure", "split_voice", ("redo", "04"))


def test_the_brain_names_a_model_the_sdk_knows():
    from studio import brain
    assert brain.TRIAGE_MODEL == "claude-sonnet-5"
