"""The panel and take content checks compare the staged look's MARKERS, not the
concatenated row (retro 2026-10-10: a row saying "dark" AND "grey" let the
hair check pass every colour).  A row without markers keeps the prose rule."""
from __future__ import annotations

from studio import panel_content as pc, take_content as tc
from studio.panel_content import Seen

GREY = {"headwear": "felt_hat", "hair_colour": "grey", "facial_hair": "beard", "top": "shirt", "dirt": "muddy"}
SUIT = {"headwear": "boater", "hair_colour": "dark", "facial_hair": "none", "top": "suit_jacket", "dirt": ""}


def seen(*subjects: str) -> Seen:
    return Seen(people=1, subjects=list(subjects))


def test_dark_hair_on_a_grey_look_drifts():
    assert tc.drifted(seen("man", "dark hair"), ["grey, dark"], [GREY]) == ["dark hair"]


def test_brown_hair_is_the_same_family_as_dark():
    assert tc.drifted(seen("brown hair"), ["x"], [SUIT]) == []


def test_a_face_whose_hair_is_unstated_is_not_judged_by_markers():
    assert tc.drifted(seen("grey hair"), ["thick chestnut hair"], [{"hair_colour": ""}]) == ["grey hair"]


def test_without_markers_the_prose_rule_stands():
    assert tc.drifted(seen("grey hair"), ["thick chestnut hair"]) == ["grey hair"]


def test_a_beard_on_a_clean_shaven_look_contradicts():
    assert pc.contradictions(seen("beard"), ["a man"], [SUIT]) == ["beard on a clean-shaven look"]


def test_a_beard_on_a_bearded_look_is_fine():
    assert pc.contradictions(seen("beard"), ["a clean-shaven man"], [GREY]) == []


def test_the_panel_look_advisory_names_the_sheets_boater():
    notes = pc.look_advisories(seen("man in suit", "straw hat", "tie"), [GREY])
    assert any("headwear" in n and "felt_hat" in n for n in notes)
    assert any("top" in n for n in notes)


def test_the_look_advisory_is_silent_on_a_right_panel_and_on_two_faces():
    assert pc.look_advisories(seen("man with grey hair", "beard", "felt hat", "shirt"), [GREY]) == []
    assert pc.look_advisories(seen("straw hat"), [GREY, SUIT]) == []


def test_a_hair_colour_that_changes_across_frames_is_logged():
    reads = [seen("dark hair"), seen("grey hair"), seen("grey hair")]
    assert tc.look_log(reads, [GREY]) and tc.look_log(reads[1:], [GREY]) == []
