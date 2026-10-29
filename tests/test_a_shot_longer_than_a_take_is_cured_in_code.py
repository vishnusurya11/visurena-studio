"""Jekyll ep06 (2026-10-28): the plan deferred after three writer rounds (26 min) on one row,
'TAKE BUILDER : shot 7 projects 8.17 s; ... longer than a take (8.0 s)'.  `holds` -- seat a line on
a neighbour, else split the shot -- cures it in code (26 shots -> 27, none over), but the router
knew only the 'TAKE LENGTH' row, so the builder's row went to the writer as creative."""
from studio import plan_cures

BUILDER = ("battery at plan: TAKE BUILDER : shot 7 projects 8.17 s; shot 13 projects 8.56 s -- "
           "longer than a take (8.0 s). Split each into two shots with two lines;")


def test_the_take_builders_row_is_cured_by_holds():
    assert plan_cures.cure_for(BUILDER) == "holds"


def test_the_take_length_row_still_is():
    assert plan_cures.cure_for("battery at plan: TAKE LENGTH  : [(7, 8.17)]") == "holds"


def test_the_button_breath_lands_before_the_button_lines_shot():
    """ep06: `holds` split shot 23 (the shot before the button, beat 1.0); its copy, now the shot
    before the button, starts at beat 0 and the contract dropped the whole cure.  The breath belongs
    to the shot before the BUTTON LINE's shot (Episode.button), not to shots[-2]."""
    doc = {"shots": [{"index": i, "beat_s": 0.0} for i in range(5)],
           "lines": [{"shot": 1}, {"shot": 3}]}                  # a runout shot 4 follows the button
    out = plan_cures.button_beat(doc)
    assert out["shots"][2]["beat_s"] >= 1.0 and out["shots"][3]["beat_s"] == 0.0


def two_sentence_shot():
    """ep06 shot 23: one 18-word line of two sentences, a shot past the take at 2.55 words/s."""
    text = ("Poole's news never changed. The doctor now kept to the cabinet above the laboratory, "
            "and sometimes slept there.")
    return {"answer": "line 2",
            "shots": [{"index": i, "beat_s": 1.0 if i == 1 else 0.0, "coda_s": 0.3, "setup": "a", "section": s}
                      for i, s in enumerate(("hook", "friction", "button"))],
            "lines": [{"index": 0, "kind": "narration", "speaker": "narrator", "text": "A short one.", "shot": 0},
                      {"index": 1, "kind": "narration", "speaker": "narrator", "text": text, "shot": 1},
                      {"index": 2, "kind": "narration", "speaker": "narrator", "text": "He is silent.", "shot": 2}]}


def test_a_two_sentence_line_splits_at_its_sentence_break():
    doc = plan_cures.split_line(two_sentence_shot(), 1)
    assert [l["text"] for l in doc["lines"]][1:3] == [
        "Poole's news never changed.",
        "The doctor now kept to the cabinet above the laboratory, and sometimes slept there."]
    assert [l["index"] for l in doc["lines"]] == [0, 1, 2, 3] and doc["answer"] == "line 3"
    assert doc["lines"][2]["shot"] == 1


def test_a_one_sentence_line_is_never_split():
    doc = two_sentence_shot()
    assert plan_cures.split_line(doc, 0)["lines"] == two_sentence_shot()["lines"]


def test_a_one_line_shot_past_the_take_splits_its_line_then_its_shot():
    doc = plan_cures.seat_overflow(two_sentence_shot(), 2.55)
    secs = plan_cures._shot_secs(doc, 2.55)
    assert max(secs.values()) <= plan_cures.TAKE_BUDGET_S and len(doc["lines"]) == 4
