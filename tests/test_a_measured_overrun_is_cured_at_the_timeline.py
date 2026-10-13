"""Jekyll ep01 (2026-10-13): the plan projected 148 s at the series rate; the
new book's narrator measured slower and the timeline came to 174.8 s against
the 174 s picture budget -- 0.8 s over with 10.6 s of holds (a 5 s wordless
hole at 156.7 s).  timeline.py refused, and nothing cured it: the measured-hole
trim only answers a hole over the wall, and the plan's `holds` cure only lifts
the floor.  Worse, timeline.py writes placed.json BEFORE its band check, so the
resume found a fresh timeline and SKIPPED step 05 into the grids.

Step 05 now (a) is not done while the measured runtime is outside the band,
and (b) on an overrun shaves holds -- largest first, floors kept, any shot --
to the budget less a margin, records it, re-times and re-signs, once."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from scripts.episode import step_05_timeline as step
from studio import episode_home, plan_cures as pc
from studio.episode_spec import MAX_SECONDS


def doc_of() -> dict:
    return {"shots": [{"index": 0, "beat_s": 0.0, "coda_s": 0.0},
                      {"index": 1, "beat_s": 1.0, "coda_s": 3.0},    # wordless runout
                      {"index": 2, "beat_s": 1.5, "coda_s": 0.0},    # pre-button: floor 1.0
                      {"index": 3, "beat_s": 0.0, "coda_s": 3.0}],   # button: floor 0.6
            "lines": [{"index": 0, "shot": 0, "text": "one two three"},
                      {"index": 1, "shot": 2, "text": "four five six"},
                      {"index": 2, "shot": 3, "text": "the button"}]}


def holds_of(doc: dict) -> float:
    return sum(float(s.get("beat_s") or 0) + float(s.get("coda_s") or 0) for s in doc["shots"])


def test_an_overrun_is_shaved_to_the_budget_less_the_margin():
    doc = doc_of()
    before = holds_of(doc)
    n = pc.trim_measured_runtime(doc, {"duration_s": MAX_SECONDS + 0.8})
    assert n > 0
    assert abs((before - holds_of(doc)) - (0.8 + pc.RUNTIME_MARGIN_S)) < 0.02
    assert len(doc["lines"]) == 3                                 # trims only


def test_the_runtime_trim_keeps_every_floor():
    doc = doc_of()
    pc.trim_measured_runtime(doc, {"duration_s": MAX_SECONDS + 9.0})
    by = {s["index"]: s for s in doc["shots"]}
    assert by[1]["coda_s"] >= 0.5                                 # wordless
    assert by[2]["beat_s"] >= 1.0                                 # before the button
    assert by[3]["coda_s"] >= 0.6                                 # the button's rest


def test_a_runtime_inside_the_budget_changes_nothing():
    doc = doc_of()
    before = json.dumps(doc, sort_keys=True)
    assert pc.trim_measured_runtime(doc, {"duration_s": MAX_SECONDS - 1.0}) == 0
    assert json.dumps(doc, sort_keys=True) == before


def _ctx(tmp_path, monkeypatch, placed_seq, timeline_refuses: list[bool]):
    book = tmp_path / "book"
    plan = episode_home.plan_path(book, 1)
    plan.parent.mkdir(parents=True)
    plan.write_text(json.dumps(doc_of()), encoding="utf-8")
    monkeypatch.setattr(episode_home, "write_plan",
                        lambda path, doc: path.write_text(json.dumps(doc), encoding="utf-8"))
    seq = list(placed_seq)
    monkeypatch.setattr(step, "placed_of", lambda b, n: seq.pop(0) if len(seq) > 1 else seq[0])
    monkeypatch.setattr(step, "rendered", lambda ctx: False)
    monkeypatch.setattr(step, "unpack", lambda ctx: None)
    calls = []

    def retime(ctx):
        calls.append("retime")
        if timeline_refuses.pop(0):
            raise SystemExit("REFUSED: scripts/episode/timeline.py exit 1")
    monkeypatch.setattr(step, "retime", retime)
    monkeypatch.setattr(step, "resign", lambda ctx, n, why="": calls.append(f"resign {why}"))
    return SimpleNamespace(book_dir=book, number=1), calls


def test_step_05_cures_a_measured_overrun_records_retimes_and_resigns(tmp_path, monkeypatch):
    over, inside = {"duration_s": MAX_SECONDS + 0.8, "lines": []}, {"duration_s": MAX_SECONDS - 0.4, "lines": []}
    ctx, calls = _ctx(tmp_path, monkeypatch, [over, inside], [True, False])
    step.run(ctx)
    assert calls == ["retime", "retime", "resign measured-runtime trim"]
    from studio import plan_provenance
    cures = (episode_home.plan_path(ctx.book_dir, 1).parent / plan_provenance.CURES_FILE).read_text(encoding="utf-8")
    assert "trim_measured_runtime" in cures


def test_a_timeline_refusal_that_is_not_an_overrun_stands(tmp_path, monkeypatch):
    ctx, calls = _ctx(tmp_path, monkeypatch, [{}], [True])        # e.g. lines not rendered
    with pytest.raises(SystemExit, match="timeline.py exit 1"):
        step.run(ctx)
    assert calls == ["retime"]


def test_a_fresh_timeline_over_the_budget_is_not_done(tmp_path, monkeypatch):
    """The skip: timeline.py wrote placed.json and then refused its band."""
    ctx, _ = _ctx(tmp_path, monkeypatch, [{"duration_s": MAX_SECONDS + 0.8, "lines": [], "shots": []}], [])
    monkeypatch.setattr(step, "fresh", lambda book, n: True)
    assert step.done(ctx) is False
    ctx, _ = _ctx(tmp_path / "b", monkeypatch, [{"duration_s": MAX_SECONDS - 0.8, "lines": [], "shots": []}], [])
    monkeypatch.setattr(step, "fresh", lambda book, n: True)
    assert step.done(ctx) is True
