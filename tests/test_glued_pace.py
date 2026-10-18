"""A pace glued where no walk is (Jekyll Kawajiri ep01, 2026-10-18).

The L8 cure's own gait regex was not the judge's: it read `runs` and the
`walking` of "walking cane" as walks, and `figurative_gaits` runs `pace_words`
over the WHOLE plan.  The signed-to-be plan said "his black walking at a walking
pace cane" (x10), "the pavement runs at a walking pace", "sweat runs at a walking
pace down his face", and a girl who "run[s] at a walking pace".  L23 never saw any
of it: its PACE_MARK did not read the phrase the cure writes.  One ruler: the
cure paces only what the judge calls a gait, L23 reads the cure's phrase, and a
new row L24 finds a pace glued to a run or a walking cane, cured for $0."""
from __future__ import annotations

from studio import episode_ref_official as ro
from studio import plan_cures as pc


def doc_of(motion: str) -> dict:
    return {"shots": [{"index": 0, "frame": "", "motion": motion, "at_rest": "", "end": ""}],
            "setups": {}}


def motion(doc: dict) -> str:
    return doc["shots"][0]["motion"]


def test_a_walking_cane_is_not_a_walk_for_the_cure():
    doc = pc.pace_words(doc_of("he swings his black walking cane as he waits"))
    assert motion(doc) == "he swings his black walking cane as he waits"


def test_a_walking_cane_is_not_a_walk_for_the_judge():
    assert not ro.gaits("he swings his black walking cane as he waits")


def test_a_run_gets_no_walking_pace_from_the_cure():
    doc = pc.pace_words(doc_of("the girl runs in down the cross street; sweat runs down his face"))
    assert "walking pace" not in motion(doc)


def test_a_person_still_gets_a_pace():
    doc = pc.pace_words(doc_of("he walks under the lamps"))
    assert motion(doc) == "he walks at a walking pace under the lamps"


def test_l23_reads_the_phrase_the_cure_writes():
    text = "[Shot 1] From 00:00 to 00:04. The pavement runs at a walking pace from the corner."
    rows = ro.l23_pace_on_a_thing(text, {})
    assert rows and "L23 PACE ON A THING" in rows[0]


def test_drop_thing_pace_strips_the_cures_own_phrase_from_a_thing():
    doc = pc.drop_thing_pace(doc_of("the pavement runs at a walking pace from the corner"))
    assert motion(doc) == "the pavement runs from the corner"


def test_l24_finds_a_pace_glued_to_a_run_or_a_cane():
    text = ("[Shot 1] From 00:00 to 00:04. He swings his black walking at a walking pace cane; "
            "the girl's boots run at a walking pace in down the street.")
    rows = ro.l24_glued_pace(text, {})
    assert len(rows) == 2 and all("L24 GLUED PACE" in r for r in rows)
    assert ro.l24_glued_pace in ro.RULES


def test_l24_leaves_a_real_walk_alone():
    assert not ro.l24_glued_pace("[Shot 1] From 00:00 to 00:04. He walks at a walking pace under the lamps.", {})


def test_unglue_pace_restores_the_words():
    doc = pc.unglue_pace(doc_of("his black walking at a walking pace cane taps; the girl's boots "
                                "run at a walking pace in; sweat runs at a walking pace down"))
    assert motion(doc) == "his black walking cane taps; the girl's boots run in; sweat runs down"
    assert pc.unglue_pace(doc) == doc                                  # idempotent


def test_the_l24_row_routes_to_unglue_pace():
    row = ("G-TAKELINT shot 7: L24 GLUED PACE [shot 7]: 'walking at a walking pace' -- "
           "a pace glued to a run or a walking cane [plan]")
    assert pc.cure_for(row) == "unglue_pace"
