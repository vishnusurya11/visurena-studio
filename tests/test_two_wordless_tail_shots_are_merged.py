"""ep26 (2026-10-09 09:35Z): the plan deferred twice on a pair of faults no hold
can cure together -- G-STORY's wordless tail 6.09 s against 6.0, and ONE PER
TAKE (24, 25): the button shot and the first wordless shot after it packed into
one take.  Growing the pair lengthens the tail; shaving the tail packs the pair.
Two wordless shots of one setup after the button are one shot: merging the first
into the next keeps both holds, drops one pair of handles (0.5 s off the tail)
and leaves the button shot facing a longer neighbour."""
from __future__ import annotations

from studio import plan_cures as pc


def _doc():
    shots = [{"index": 0, "setup": "room", "beat_s": 0.0, "coda_s": 0.5},
             {"index": 1, "setup": "room", "beat_s": 0.19, "coda_s": 1.26},
             {"index": 2, "setup": "room", "beat_s": 0.94, "coda_s": 0.8},
             {"index": 3, "setup": "room", "beat_s": 0.0, "coda_s": 1.0}]
    lines = [{"shot": 0, "text": "one two three four five six seven eight", "kind": "narration"},
             {"shot": 1, "text": "Down she went and lay quite still upon the floor.", "kind": "narration"}]
    beds = [{"from_shot": 0}, {"from_shot": 2}]
    return {"shots": shots, "lines": lines, "beds": beds, "answer": "shot 0"}


def test_the_first_wordless_tail_shot_merges_into_the_next():
    doc = pc.merge_silent_tail(_doc())
    assert len(doc["shots"]) == 3
    last = doc["shots"][-1]
    assert last["index"] == 2
    assert abs(float(last["beat_s"]) + float(last["coda_s"]) - (0.94 + 0.8 + 1.0)) < 1e-6
    assert [b["from_shot"] for b in doc["beds"]] == [0, 2]      # the removed shot's bed follows it


def test_the_tail_loses_one_pair_of_handles():
    before, after = _doc(), pc.merge_silent_tail(_doc())
    tail = lambda d: sum(pc._shot_secs(d, 2.5)[s["index"]] for s in d["shots"] if s["index"] >= 1)
    assert abs(tail(before) - tail(after) - 2 * pc.HANDLE_S) < 1e-6


def test_one_wordless_tail_shot_is_left_alone():
    doc = _doc()
    doc["shots"] = doc["shots"][:3]
    assert pc.merge_silent_tail(doc) == doc


def test_wordless_tail_shots_of_two_setups_are_left_alone():
    doc = _doc()
    doc["shots"][3]["setup"] = "street"
    assert len(pc.merge_silent_tail(doc)["shots"]) == 4


def test_the_route_sends_the_wordless_tail_to_the_merge():
    assert pc.cure_for("G-STORY shots 24-26: wordless tail after the last line in projected seconds, "
                       "measured 6.09 against 6.0") == "merge_silent_tail"
