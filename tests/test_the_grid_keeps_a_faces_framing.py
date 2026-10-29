"""The grid's framing tail is cut only under a FOCUS that names no person, and walk-ons are told apart by count of
walk-ons, not by count of the cast (wave-2 review of craft ruling A21).

`FACE_WORDS` knew no jaw, chin, brow or gaze and no person, so ep01 s23 ("the man in <image1>'s heavy jaw ...")
lost "head and shoulders fill the centre" and night_door panel 2 ("the two men") lost "the head sits in the upper
third" -- the census's FOCUS 5 -> 0 read the same classifier.  Under re.I the FOCUS end `[A-Z]{3,}` matched any
word, so "in the doorway" ended the capture.  `varied_group(named=len(faces))` dropped the "different individuals"
clause for two constables in a two-face shot (the ep06 shot 10 duplicate class); the plan's own walk-on count
(`Shot.extras`) decides now, and TWIN refuses only the generic "the two men" on a staged pair.  The NEG warning
fired on all 22 ep01 grids from the builder's own fixed sentences; they are exempt like UNWRITTEN."""
from __future__ import annotations

from types import SimpleNamespace

from scripts.episode import grids
from studio import grid_lint
from studio import storyboard_grid as sg


def focus(text: str) -> str:
    return f"THE FOCUS OF THE PICTURE IS {text}."


def test_a_face_part_is_a_face_focus():
    assert sg.face_focus(focus("the man in <image1>'s heavy jaw at the CENTRE, his head a third of the frame"))
    assert sg.face_focus(focus("the man in <image2>'s lowered brow and steady gaze at the CENTRE"))


def test_a_person_is_a_face_focus():
    assert sg.face_focus(focus("the two men at the CENTRE"))
    assert sg.framing("medium", True, focus("the two men at the CENTRE")) == sg.PEOPLED_CUT["medium"]


def test_a_hand_or_a_fist_is_no_face_focus():
    assert not sg.face_focus(focus("the man in <image1>'s black-gloved fist on the man in <image2>'s coat collar"))
    assert not sg.face_focus(focus("the knuckly pale hand at the CENTRE, palm up"))


def test_the_focus_ends_only_at_an_upper_case_place():
    hit = sg.FOCUS.search(focus("the brass knocker in the doorway at the CENTRE"))
    assert hit.group(1) == "the brass knocker in the doorway"


def test_walk_ons_keep_their_clause_beside_a_named_pair():
    assert sg.varied_group("two constables stand by the door", named=2, extras=2).startswith("The two constables")
    assert sg.varied_group("the two men face each other", named=2, extras=0) == ""


def test_the_grid_body_reads_the_plans_walk_on_count():
    shot = SimpleNamespace(frame="Two constables stand by the door", at_rest="", size="medium",
                           faces=["utterson", "enfield"], extras=2)
    assert "two different individuals" in grids.body_of(shot)


def test_twin_refuses_the_named_pair_not_two_walk_ons():
    pair = "<image1> and <image2> stand. The two men are two different individuals: each one has his own face."
    assert [f.split()[0] for f in grid_lint.panel_faults(pair)] == ["TWIN"]
    walk = "<image1> and <image2> stand. The two constables are two different individuals: each one has his own."
    assert grid_lint.panel_faults(walk) == []


def test_neg_skips_the_builders_fixed_sentences():
    text = ("A storyboard of 4 panels in 2 columns and 2 rows, all the same size, thin white gutters between them, "
            "no lettering anywhere. The people in <image1> and <image2> are never dressed alike. "
            f"{sg.UNWRITTEN}")
    assert grid_lint.negations(text) == []
    assert grid_lint.negations(text + " He does not look up.") == ["not look up"]


def test_a_person_standing_at_a_door_is_a_face_focus():
    """Jekyll ep06 shot 0 (2026-10-28): 'the man in <image1> standing in the narrow gap of the black
    panelled door' read as a FOCUS on a door and refused step 06.  A part counts only as the focus's
    own subject ('<image1>'s fist'); a place he stands in is no part of him."""
    assert sg.face_focus("THE FOCUS OF THE PICTURE IS the man in <image1> standing in the narrow gap of the "
                         "black panelled door at the CENTRE, his head a third of the frame's height.")
    assert not sg.face_focus("THE FOCUS OF THE PICTURE IS the man in <image1>'s clenched fist on the door at the CENTRE.")
    assert not sg.face_focus("THE FOCUS OF THE PICTURE IS the hand of the man in <image1> on the door at the CENTRE.")
