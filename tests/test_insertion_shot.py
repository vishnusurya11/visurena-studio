"""The micro-line chooser: the shot whose insertion splits the hole most
evenly (minimizing the larger sub-hole), wordless preferred, never on or past
the button shot, never on a full shot, and never where 14 more words would
push the shot past the take budget.  No candidate -> None: the row stays
creative."""
from __future__ import annotations

from studio import plan_cures as pc
from studio import speech_gap as sg

RATE = 2.5
WALL = sg.MAX_GAP_S - sg.HOLE_MARGIN_S


def doc_of(beat2=0.0, coda2=1.6) -> dict:
    return {"shots": [{"index": 0, "setup": "a", "beat_s": 0.0, "coda_s": 1.0},
                      {"index": 1, "setup": "a", "beat_s": 0.0, "coda_s": 1.6},
                      {"index": 2, "setup": "a", "beat_s": beat2, "coda_s": coda2},
                      {"index": 3, "setup": "b", "beat_s": 0.0, "coda_s": 0.2}],
            "lines": [{"shot": 0, "text": "just four words here"},
                      {"shot": 3, "text": "the button line lands here"}]}


def hole_of(doc: dict) -> tuple:
    holes = sg.over_wall(pc._projection(doc, RATE), WALL)
    assert len(holes) == 1
    return holes[0]


def test_the_chooser_splits_the_hole_most_evenly():
    doc = doc_of()
    assert pc.insertion_shot(doc, hole_of(doc), RATE) == 2


def test_a_shot_the_take_budget_refuses_falls_to_the_next_candidate():
    doc = doc_of(beat2=1.5, coda2=4.0)       # 14 words would project shot 2 past 8.0 s
    assert pc.insertion_shot(doc, hole_of(doc), RATE) == 1


def test_no_candidate_means_none():
    doc = {"shots": [{"index": 0, "beat_s": 0.0, "coda_s": 4.0},
                     {"index": 1, "beat_s": 1.0, "coda_s": 4.0}],
           "lines": [{"shot": 0, "text": "one"}, {"shot": 0, "text": "two"},
                     {"shot": 1, "text": "the button"}]}
    holes = sg.over_wall(pc._projection(doc, RATE), 3.0)
    assert holes
    assert pc.insertion_shot(doc, holes[0], RATE) is None        # full shot, then the button


def test_an_unsplit_pair_names_its_line_light_shot_and_hole():
    doc = {"shots": [{"index": 0, "setup": "a", "beat_s": 0.0, "coda_s": 1.0},
                     {"index": 1, "setup": "a", "beat_s": 0.5, "coda_s": 3.0},
                     {"index": 2, "setup": "b", "beat_s": 0.0, "coda_s": 0.2}],
           "lines": [{"shot": 0, "text": "five short words sit here"},
                     {"shot": 2, "text": "the button line lands here"}]}
    got = pc.pair_insertion_shot(doc, (0, 1), RATE)
    assert got is not None
    shot_index, (start, end, ids) = got
    assert shot_index == 1                                       # the wordless one
    assert end - start > 4.0 and 1 in ids
    no_room = {"shots": doc["shots"],
               "lines": [{"shot": 0, "text": "the button line lands here"}]}
    assert pc.pair_insertion_shot(no_room, (0, 1), RATE) is None  # nothing before the button
