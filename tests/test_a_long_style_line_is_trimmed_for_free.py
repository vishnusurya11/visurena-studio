"""ep21 rung 1 (2026-10-08 05:11Z): the only refusal was the contract's
"`where` + `light` render a 19-word style line; the wall is 16", and no cure
routed for that wording, so the writer was re-asked for arithmetic.  The last
clause of `light`, then of `where`, goes until house_style is satisfied."""
from __future__ import annotations

from studio import house_style, plan_cures as pc


def test_the_fault_routes_to_trim_style():
    assert pc.cure_for("CONTRACT : `where` + `light` render a 19-word style line; the wall is 16 (ep05-08 had 13)") == "trim_style"


def test_light_loses_a_loose_clause_and_keeps_its_direction_and_its_black():
    """The writer's black ('deep shadow') and the direction clause stay; the
    decorative clause between them goes."""
    doc = {"where": "Mortlake", "light": "grey daylight through the kitchen doorway, dust in the air, deep shadow"}
    assert house_style.style_faults(doc["where"], doc["light"])
    out = pc.trim_style(doc)
    assert not house_style.style_faults(out["where"], out["light"])
    assert out["where"] == "Mortlake"
    assert out["light"] == "grey daylight through the kitchen doorway, deep shadow"
    assert house_style.BLACKS.search(out["light"])


def test_where_gives_words_before_the_direction_clause_does():
    doc = {"where": "the ruined villa at Mortlake", "light": "grey daylight through the doorway, deep shadow"}   # 18 words
    out = pc.trim_style(doc)
    assert not house_style.style_faults(out["where"], out["light"])
    assert out["light"] == "grey daylight through the doorway, deep shadow"
    assert out["where"] == "the ruined villa"


def test_a_line_already_under_the_wall_is_untouched():
    doc = {"where": "Woking", "light": "low sun, hard shadows"}
    assert pc.trim_style(dict(doc)) == doc


def test_a_field_is_never_cut_below_two_words():
    doc = {"where": "a long place name of many many words indeed here", "light": "noon sun"}
    out = pc.trim_style(doc)
    assert len(out["light"].split()) >= 2 and len(out["where"].split()) >= 2
