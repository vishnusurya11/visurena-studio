"""ep26 (2026-10-09 12:00Z): the plan signed with ONE PER TAKE clean at the
series RATE (no voice yet); recorded, shots 13 and 14 measured shorter and the
take packer put them in one take -- step 06 refused the take's second block
(206 words against the 240 floor).  Nothing between the voice and the prompts
re-judged the pairs.  Step 05, which already cures measured holes after the
voice, now unpacks a measured pair with the hold cure BY THE VOICE, records it,
re-times and re-signs -- before any prompt or picture is built on it."""
from __future__ import annotations

import json
from types import SimpleNamespace

from scripts.episode import step_05_timeline as step
from studio import episode_home

PLAN = {"shots": [{"index": 13, "setup": "room", "beat_s": 0.0, "coda_s": 0.2},
                  {"index": 14, "setup": "room", "beat_s": 0.0, "coda_s": 0.2},
                  {"index": 15, "setup": "street", "beat_s": 0.0, "coda_s": 0.5}],
        "lines": []}
PACKED = {"shots": [{"index": 13, "seconds": 3.6}, {"index": 14, "seconds": 3.9}, {"index": 15, "seconds": 6.0}]}
APART = {"shots": [{"index": 13, "seconds": 4.4}, {"index": 14, "seconds": 4.2}, {"index": 15, "seconds": 6.0}]}


def _ctx(tmp_path, monkeypatch, placed_seq):
    book = tmp_path / "book"
    plan = episode_home.plan_path(book, 26)
    plan.parent.mkdir(parents=True)
    plan.write_text(json.dumps(PLAN), encoding="utf-8")
    monkeypatch.setattr(episode_home, "write_plan",
                        lambda path, doc: path.write_text(json.dumps(doc), encoding="utf-8"))
    seq = list(placed_seq)
    monkeypatch.setattr(step, "placed_of", lambda b, n: seq.pop(0) if len(seq) > 1 else seq[0])
    monkeypatch.setattr(step, "rendered", lambda ctx: False)
    calls = []
    monkeypatch.setattr(step, "retime", lambda ctx: calls.append("retime"))
    monkeypatch.setattr(step, "resign", lambda ctx, n, why="": calls.append("resign"))
    return SimpleNamespace(book_dir=book, number=26), calls


def test_the_measured_pairs_are_read_off_the_timeline(tmp_path, monkeypatch):
    ctx, _ = _ctx(tmp_path, monkeypatch, [PACKED])
    assert step.packed(ctx) == [[13, 14]]


def test_a_packed_pair_is_unpacked_recorded_retimed_and_resigned(tmp_path, monkeypatch):
    from studio import plan_cures
    ctx, calls = _ctx(tmp_path, monkeypatch, [PACKED, APART])

    def grow(doc, rate=3.0):
        doc["shots"][0]["coda_s"] = 1.0
        return doc
    monkeypatch.setattr(plan_cures, "holds", grow)
    ctx.capture_script = lambda script, *a: (calls.append(script.rsplit("/", 1)[-1] + " " + " ".join(a)), (0, ""))[1]
    step.unpack(ctx)
    # ep26 11:45Z: the hold cure split a shot and left two 'follow' moves running --
    # the free repair rounds run before the re-sign, then the timeline again
    assert calls == ["retime", "plan_repair.py --no-llm", "retime", "resign"]
    from studio import plan_provenance
    cures = (episode_home.plan_path(ctx.book_dir, 26).parent / plan_provenance.CURES_FILE).read_text(encoding="utf-8")
    assert '"holds"' in cures


def test_a_fresh_timeline_that_packs_a_pair_is_not_done(tmp_path, monkeypatch):
    """ep26's timeline was fresh, so step 05 was skipped and step 06 refused
    again: a packed pair on an unrendered episode keeps step 05 open."""
    ctx, _ = _ctx(tmp_path, monkeypatch, [PACKED])
    monkeypatch.setattr(step, "fresh", lambda book, n: True)
    monkeypatch.setattr(step.speech_gap, "refusal", lambda placed: None)
    assert step.done(ctx) is False
    ctx, _ = _ctx(tmp_path / "b", monkeypatch, [APART])
    monkeypatch.setattr(step, "fresh", lambda book, n: True)
    assert step.done(ctx) is True


def test_nothing_packed_does_nothing(tmp_path, monkeypatch):
    ctx, calls = _ctx(tmp_path, monkeypatch, [APART])
    step.unpack(ctx)
    assert calls == []
