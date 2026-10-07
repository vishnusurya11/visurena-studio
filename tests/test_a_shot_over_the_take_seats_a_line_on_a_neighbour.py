"""A31, met on ep19 rung 3 (2026-10-07 15:33Z): shot 1 projected 8.4 s against
the 8.0 s take -- two lines (4 + 14 words at 2.5 w/s = 7.2 s) plus handles and
the breath between them, beat 0, coda 0.  `holds` had nothing to shave and
the only cure was a paid re-ask for arithmetic.  The free cure: a shot over
the take with two or more lines seats its last line on the next shot when
that shot has room (lines cap and its own budget), else its first line on the
shot before; a line that fits nowhere stays, and the battery still says so."""
from __future__ import annotations

from studio import plan_cures as pc

RATE = 2.5
W4 = "one two three four"
W14 = " ".join(["w"] * 14)
W6 = " ".join(["x"] * 6)


def _doc(lines_by_shot: dict[int, list[str]], n: int = 3) -> dict:
    lines, k = [], 0
    for shot in range(n):
        for text in lines_by_shot.get(shot, []):
            lines.append({"index": k, "shot": shot, "speaker": "lead", "kind": "narration", "text": text})
            k += 1
    return {"shots": [{"index": i, "section": "hook" if i == 0 else "setup", "beat_s": 0.0, "coda_s": 0.0}
                      for i in range(n)], "lines": lines}


def _shots_of(doc: dict) -> list[int]:
    return [l["shot"] for l in doc["lines"]]


def test_the_last_line_moves_to_the_next_shot_when_it_has_room():
    doc = _doc({0: [W6], 1: [W4, W14], 2: []})
    assert pc._shot_secs(doc, RATE)[1] > pc.TAKE_BUDGET_S
    out = pc.seat_overflow(doc, RATE)
    assert _shots_of(out) == [0, 1, 2]
    assert max(pc._shot_secs(out, RATE).values()) <= pc.TAKE_BUDGET_S


def test_the_first_line_moves_back_when_the_next_shot_is_full():
    doc = _doc({0: [], 1: [W4, W14], 2: [W14, W4]})           # shot 2 is at the cap and over budget itself
    out = pc.seat_overflow(doc, RATE)
    assert _shots_of(out)[:2] == [0, 1]                      # W4 went back to shot 0, W14 stays on 1
    assert pc._shot_secs(out, RATE)[1] <= pc.TAKE_BUDGET_S
    assert max(pc._shot_secs(out, RATE).values()) <= pc.TAKE_BUDGET_S   # shot 2 split, nothing left over


def test_a_line_that_fits_nowhere_splits_the_shot_and_a_one_line_shot_is_left_alone():
    """ep19's shape: both neighbours at 7.9 s, nothing to shave anywhere."""
    doc = _doc({0: [W14], 1: [W4, W14], 2: [W14]})
    doc["shots"][0].update(beat_s=1.0, coda_s=0.8)           # 7.9 s: no room for 1.6 s + a breath
    doc["shots"][2].update(beat_s=1.0, coda_s=0.8)
    doc["beds"] = [{"from_shot": 2, "tone": "grave"}]
    doc["omit"] = [2]
    doc["shots"][1].update(section="turn", frame="f", setup="pit", take=2)
    out = pc.seat_overflow(doc, RATE)
    assert [s["index"] for s in out["shots"]] == [0, 1, 2, 3]
    assert _shots_of(out) == [0, 1, 2, 3]                    # W4 stays on 1, W14 on the new 2, the old 2 is 3
    assert out["shots"][2]["section"] == "reaction" and out["shots"][2]["setup"] == "pit"
    assert out["shots"][2].get("take") is None and out["shots"][1]["take"] == 2
    assert out["beds"] == [{"from_shot": 3, "tone": "grave"}] and out["omit"] == [3]
    assert max(pc._shot_secs(out, RATE).values()) <= pc.TAKE_BUDGET_S
    one = _doc({1: [" ".join(["y"] * 22)]})
    assert _shots_of(pc.seat_overflow(one, RATE)) == [1]


def test_a_button_split_keeps_the_button_on_the_last_line():
    doc = _doc({0: [W14], 1: [W4, W14]}, n=2)
    doc["shots"][1]["section"] = "button"
    doc["shots"][0].update(beat_s=1.0, coda_s=0.8)           # 7.9 s: full
    out = pc.seat_overflow(doc, RATE)
    assert [s["section"] for s in out["shots"]] == ["hook", "runout", "button"]
    assert out["lines"][-1]["shot"] == 2


def test_holds_runs_the_seating_so_the_take_length_line_is_cured_for_free():
    doc = _doc({0: [W6], 1: [W4, W14], 2: []})
    out = pc.holds(doc, RATE)
    assert max(pc._shot_secs(out, RATE).values()) <= pc.TAKE_BUDGET_S
    assert pc.cure_for("TAKE LENGTH  : [(1, 8.4)] (at 2.50 words/s, budget 8.0 s)") == "holds"
