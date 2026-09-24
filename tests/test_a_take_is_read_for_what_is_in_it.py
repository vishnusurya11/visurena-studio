"""CONTENT DQ FOR THE VIDEO, not only the panel.

`panel_content` reads the storyboard panel and catches what the drawer put in
it. Nothing reads the TAKE, and the take is what ships. ep07's T26 rendered a
grey-haired woman in an apron where the panel and the cast sheet both show a
woman of twenty-nine, and the only reason anyone knows is that I opened the
file by hand.

OWNER 2026-09-22: "i love how you do dq so far ... keep improving that
further".

A take is judged on the SAME closed vocabulary as a panel, from a contact
sheet of frames sampled past H3's one-second reference leak, with two
differences that the video makes necessary:

  a figure may leave or enter, so the count is the MOST seen in any frame and
  a take is judged on what it holds at its fullest, not on an average;

  a copy is the thing that matters most, because identity drift across a cut
  is the fault the owner has caught by eye every single time.
"""
from __future__ import annotations

import pytest

from studio.panel_content import Seen
from studio.take_content import busiest, drifted, take_faults


def seen(**kw) -> Seen:
    base = dict(landform="flat", people=0, lookalikes=0, text=False,
                hour="night", subjects=[])
    base.update(kw)
    return Seen(**base)


# ---- a take is judged at its fullest ---------------------------------------
def test_the_count_is_the_most_seen_in_any_frame():
    """A man walks into the second half of a shot cast for nobody. Averaging
    him away is how he ships."""
    got = busiest([seen(people=0), seen(people=2), seen(people=1)])
    assert got.people == 2


def test_copies_carry_across_frames_too():
    got = busiest([seen(people=2, lookalikes=0), seen(people=2, lookalikes=2)])
    assert got.lookalikes == 2


def test_lettering_anywhere_in_the_take_counts():
    assert busiest([seen(text=False), seen(text=True)]).text is True


def test_the_subjects_of_every_frame_are_kept():
    got = busiest([seen(subjects=["heather"]), seen(subjects=["a doll", "heather"])])
    assert set(got.subjects) == {"heather", "a doll"}


def test_reading_no_frames_is_refused():
    """An unread take must never look like a clean one."""
    with pytest.raises(ValueError):
        busiest([])


# ---- identity drift, the fault that has always needed an eye ---------------
def test_a_face_the_cast_row_forbids_is_drift():
    assert drifted(seen(subjects=["man", "grey hair", "apron"]),
                   "a slim woman of twenty-nine with chestnut-auburn hair")


def test_the_face_the_row_asks_for_is_not_drift():
    assert not drifted(seen(subjects=["woman", "chestnut hair", "apron"]),
                       "a slim woman of twenty-nine with chestnut-auburn hair")


def test_drift_needs_a_row_to_compare_against():
    assert not drifted(seen(subjects=["grey hair"]), "")


# ---- the whole verdict -----------------------------------------------------
def test_a_clean_take_has_no_faults():
    assert take_faults([seen(people=1)], planned=1, crowd=False, flat=True,
                       night=True, physical="", frame="a man on the road") == []


def test_a_take_that_invents_a_person_is_named():
    got = take_faults([seen(people=1), seen(people=3, lookalikes=2)],
                      planned=1, crowd=False, flat=True, night=True,
                      physical="", frame="a man on the road")
    assert got and any("copies" in f or "figure" in f for f in got)


def test_a_take_keeps_the_posture_most_of_its_frames_show():
    """ep11 T06, T09, T16: busiest() rebuilt the take's Seen without posture, so
    every take read 'unread' and failed a shot that asks for sitting. ep10 T18
    stood for two frames and lay for one: the take reads standing."""
    from studio.panel_content import Seen as S
    from studio.take_content import busiest
    reads = [S(people=1, posture="standing"), S(people=1, posture="standing"), S(people=1, posture="lying")]
    assert busiest(reads).posture == "standing"
    assert busiest([S(people=1, posture=""), S(people=1, posture="sitting")]).posture == "sitting"
