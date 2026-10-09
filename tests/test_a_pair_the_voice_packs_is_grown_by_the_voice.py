"""ep21, 2026-10-08 08:50Z: the battery judged ONE PER TAKE on the recorded
voice (shots 0+1 = 7.88 s, packed) while the holds cure measured the same
pair by the series rate (8.29 s, clear) and grew nothing; four rounds of the
ladder, a brain park and a retry turned on a 0.4 s disagreement between two
rulers.  A voice is a recording of a text: wherever that text sits, every
projection -- the checker's, the cures' -- reads its measured seconds when the
line is recorded, and the rate only for a line nobody has voiced yet."""
from __future__ import annotations

import json

import pytest

from studio import episode_takes as tk
from studio import plan_cures as pc
from studio import plan_gates

A = "On the sixth day, I heard the curate drinking in the dark."      # 12 words
B = "My hand found the bottle."                                       # 5 words
RATE = 2.49
VOICE = {A: 3.87, B: 2.5}
DOC = {"shots": [{"index": 0, "setup": "pantry", "beat_s": 0.0, "coda_s": 0.48},
                 {"index": 1, "setup": "pantry", "beat_s": 0.0, "coda_s": 0.0}],
       "lines": [{"shot": 0, "text": A, "kind": "narration", "speaker": "n"},
                 {"shot": 1, "text": B, "kind": "narration", "speaker": "n"}]}


@pytest.fixture
def voice():
    """Set the voice for one test and put the empty default back after it."""
    token = plan_gates.VOICE.set(VOICE)
    try:
        yield VOICE
    finally:
        plan_gates.VOICE.reset(token)


def pairs(doc: dict) -> list[list[int]]:
    secs = pc._shot_secs(doc, RATE)
    rows = [{"index": s["index"], "seconds": secs[s["index"]], "setup": s["setup"]} for s in doc["shots"]]
    return [g for g in tk.groups(rows) if len(g) > 1]


def test_the_projection_alone_is_blind_to_a_pair_the_voice_packs(voice):
    token = plan_gates.VOICE.set({})
    try:
        assert pairs(DOC) == []                      # 5.79 + 2.50 = 8.29 s at the rate
    finally:
        plan_gates.VOICE.reset(token)
    assert pairs(DOC) == [[0, 1]]                    # 4.87 + 3.00 = 7.87 s as recorded


def test_the_holds_cure_grows_the_pair_past_the_take_by_the_voice(voice):
    cured = pc.holds(json.loads(json.dumps(DOC)), rate=RATE)
    assert pairs(cured) == []
    secs = pc._shot_secs(cured, RATE)
    assert secs[0] + secs[1] > 8.0


def test_the_checkers_projection_reads_the_voice_too(voice):
    from types import SimpleNamespace
    ep = SimpleNamespace(
        shots=[SimpleNamespace(index=0, beat_s=0.0, coda_s=0.48, cuts=[]),
               SimpleNamespace(index=1, beat_s=0.0, coda_s=0.0, cuts=[])],
        lines=[SimpleNamespace(index=0, shot=0, text=A, kind="narration", speaker="n", words=lambda: 12),
               SimpleNamespace(index=1, shot=1, text=B, kind="narration", speaker="n", words=lambda: 5)])
    ep.cut_shots = lambda: ep.shots
    ep.lines_of = lambda i: [l for l in ep.lines if l.shot == i]
    placed = plan_gates.projected_place(ep, RATE)
    by = {s["index"]: s["seconds"] for s in placed["shots"]}
    assert abs(by[0] - (0.5 + 3.87 + 0.48)) < 0.05 and abs(by[1] - (0.5 + 2.5)) < 0.05


def test_take_length_is_judged_at_the_rate_like_the_renderer(voice):
    """ep26 (2026-10-09): the voice made shots 4 and 17 0.2-0.4 s longer than the
    8.0 s budget; the renderer (takes_r2v.refuse_long_shots, Episode.long_shots)
    judges at the rate and renders them, and no hold can shorten speech.  The
    plan's TAKE LENGTH stays with the renderer's ruler; pairs stay with the voice."""
    import sys
    sys.path.insert(0, "scripts/episode")
    import plan_check
    from types import SimpleNamespace
    ep = SimpleNamespace(shots=[SimpleNamespace(index=0, beat_s=0.0, coda_s=2.0)],
                         lines=[SimpleNamespace(shot=0, text=A)])          # 12 words: 4.8 s at 2.49 -> 7.3 s
    token = plan_gates.VOICE.set({A: 9.0})                                 # recorded far longer
    try:
        assert plan_check.long_shots(ep, RATE) == []
    finally:
        plan_gates.VOICE.reset(token)


def test_voice_of_reads_the_recorded_lines_by_text(tmp_path):
    rows = [{"index": 0, "shot": 0, "text": A, "seconds": 3.87, "passed": True},
            {"index": 1, "shot": 1, "text": B, "seconds": 9.9, "passed": False},
            {"index": 2, "shot": 2, "text": "Unheard yet.", "seconds": None}]
    f = tmp_path / "episodes" / "ep21" / "audio" / "lines" / "lines.json"
    f.parent.mkdir(parents=True)
    f.write_text(json.dumps(rows), encoding="utf-8")
    assert plan_gates.voice_of(tmp_path, 21) == {A: 3.87}
    assert plan_gates.voice_of(tmp_path, 22) == {}


def test_a_line_nobody_voiced_still_projects_at_the_rate():
    assert abs(plan_gates.line_seconds("one two three", 3.0) - 1.0) < 1e-9
