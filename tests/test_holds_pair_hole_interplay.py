"""ONE PER TAKE and G-HOLE close on the SAME doc: holds()'s pair growth is
hole-aware.  Growing a pair's holds past the take budget splits a take but can
open a hole over the wall, so every add is capped by that silence's headroom
(recomputed from the shared projection after each write), and a pair whose
every growable slot has no headroom comes back in `unsplit` for the micro-line
path -- speech splits a take without opening silence."""
from __future__ import annotations

from studio import episode_takes as tk
from studio import plan_cures as pc
from studio import speech_gap as sg

RATE = 2.5
WALL = sg.MAX_GAP_S - sg.HOLE_MARGIN_S


def projection_rows(doc: dict) -> list[dict]:
    secs = pc._shot_secs(doc, RATE)
    return [{"index": s["index"], "seconds": secs[s["index"]], "setup": s.get("setup")}
            for s in doc["shots"]]


def pair_with_headroom() -> dict:
    """Two short voiced shots sharing a setup: growth can split them without
    opening a hole (the next line is close)."""
    return {"shots": [{"index": 0, "setup": "a", "beat_s": 0.0, "coda_s": 0.2},
                      {"index": 1, "setup": "a", "beat_s": 0.0, "coda_s": 0.2},
                      {"index": 2, "setup": "b", "beat_s": 0.0, "coda_s": 0.2}],
            "lines": [{"shot": 0, "text": "five short words sit here"},
                      {"shot": 1, "text": "five more words sit here"},
                      {"shot": 2, "text": "the button line lands here"}]}


def pair_without_headroom() -> dict:
    """The pair's silence already sits in a hole AT the wall: any growth would
    cross it, so the pair stays packed and comes back in `unsplit`."""
    return {"shots": [{"index": 0, "setup": "a", "beat_s": 0.0, "coda_s": 1.0},
                      {"index": 1, "setup": "a", "beat_s": 0.5, "coda_s": 3.0},
                      {"index": 2, "setup": "b", "beat_s": 0.0, "coda_s": 0.2}],
            "lines": [{"shot": 0, "text": "five short words sit here"},
                      {"shot": 2, "text": "the button line lands here"}]}


def test_a_pair_with_headroom_is_grown_apart_and_opens_no_hole():
    doc, unsplit = pc.holds_and_unsplit(pair_with_headroom(), rate=RATE)
    assert unsplit == []
    runs = tk.groups(projection_rows(doc))
    assert all(len(run) == 1 for run in runs)                    # every shot its own take
    assert sg.over_wall(pc._projection(doc, RATE), WALL) == []   # and no hole opened


def test_a_pair_without_headroom_is_left_packed_and_reported():
    before = pair_without_headroom()
    hole = max(b - a for a, b, _ in
               sg.over_wall(pc._projection(before, RATE), WALL - 0.1))
    assert abs(hole - WALL) < 0.06                               # at the wall already
    doc, unsplit = pc.holds_and_unsplit(pair_without_headroom(), rate=RATE)
    assert (0, 1) in unsplit
    assert sg.over_wall(pc._projection(doc, RATE), WALL) == []   # growth never crossed it


def test_headroom_reads_the_hole_the_shots_silence_sits_in():
    doc = pair_without_headroom()
    assert pc._headroom(doc, RATE, 0) <= 0.0                     # inside the at-wall hole
    roomy = pair_with_headroom()
    assert pc._headroom(roomy, RATE, 0) > 2.0


def test_holds_still_returns_the_doc_alone():
    doc = pc.holds(pair_with_headroom(), rate=RATE)
    assert isinstance(doc, dict) and "shots" in doc
