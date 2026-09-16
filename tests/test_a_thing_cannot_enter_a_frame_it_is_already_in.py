r"""M10: the motion may not bring in something `at_rest` has already put in frame.

MEASURED, episode 7 shot 11, the worst take in the episode at 40/100:

    at_rest: "A wooden ladder runs up the CENTRE of frame from the BOTTOM to the
              TOP against wet soot-brick, AN OPEN SASH WINDOW STANDS AT THE TOP
              CENTRE at the height of two hands with a curtain inside it ..."
    motion : "The camera tilts up the ladder across the whole shot, travelling a
              long stride; THE OPEN WINDOW COMES DOWN INTO FRAME as the camera
              rises; the curtain inside it lifts once in the draught."

`at_rest` is the FIRST frame. The window is in it. So the window cannot come
into frame, and the only way a renderer can obey both sentences is to start the
camera somewhere the window is not -- which is to say, to throw away the
staging it was given. Take 11 did exactly that: it pulled off the ladder at
3.3 s, re-established the whole mews lane, and ended on a wide alley with a man
walking away. It measured 0.976 against `plate_mews_lane.png`; its own start
cell had fallen to 0.176.

The `foreign` gate caught the wreck. Nothing caught the sentence, and the
sentence was free to catch -- it is a contradiction between two fields of the
plan, visible before the $0.20 sheet and before the GPU.

The rule is conservative on purpose: it fires only when the HEAD NOUN of the
entering thing is named in `at_rest`. "A hand comes into frame" beside an
`at_rest` that mentions no hand is a perfectly good instruction and stays legal.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import episode_spec as es

LADDER_REST = ("A wooden ladder runs up the CENTRE of frame from the BOTTOM to the TOP against "
               "wet soot-brick, an open sash window stands at the TOP CENTRE at the height of "
               "two hands with a curtain inside it, and the brick wall fills both edges")
LADDER_MOTION = ("The camera tilts up the ladder across the whole shot, travelling a long "
                 "stride; the open window comes down into frame as the camera rises; the "
                 "curtain inside it lifts once in the draught.")


def test_the_shot_that_wrecked_take_11():
    faults = es.already_in_frame(LADDER_REST, LADDER_MOTION)
    assert faults, "the window is at TOP CENTRE at rest and cannot come into frame"
    assert "window" in " ".join(faults).lower()


def test_a_thing_at_rest_does_not_mention_may_enter():
    rest = "A wooden ladder runs up the CENTRE of frame against wet soot-brick"
    motion = "The camera holds; a gloved hand comes into frame at the BOTTOM and takes a rung."
    assert es.already_in_frame(rest, motion) == []


def test_entering_the_frame_is_recognised_however_it_is_said():
    rest = "A brass lamp stands at the LEFT of frame at the height of a hand"
    for said in ("the brass lamp comes into frame at the LEFT",
                 "the brass lamp enters the frame at the LEFT",
                 "the brass lamp comes into view at the LEFT",
                 "the brass lamp swings up into frame"):
        motion = f"The camera pushes in a hand's breadth; {said}; the wick gutters once."
        assert es.already_in_frame(rest, motion), said


def test_leaving_the_frame_is_not_entering_it():
    """A thing that IS in frame is exactly the thing that can leave it."""
    rest = "A brass lamp stands at the LEFT of frame at the height of a hand"
    motion = "The camera tracks a hand's breadth to the right; the brass lamp goes out of frame."
    assert es.already_in_frame(rest, motion) == []


def test_a_plural_at_rest_still_catches_its_singular():
    rest = "Both hands rest open on the deal table at the CENTRE of frame"
    motion = "The camera holds; his hand comes into frame and takes the knife."
    assert es.already_in_frame(rest, motion)


def test_a_shot_with_no_at_rest_cannot_contradict_one():
    assert es.already_in_frame("", LADDER_MOTION) == []


def test_the_fault_reaches_still_motions_as_a_hard_one():
    """`seq_boards` and `takes_r2v` both refuse on HARD_MOTION, which is where
    this has to land: an advisory would have printed above take 11 and been
    rendered anyway."""
    assert "M10" in es.HARD_MOTION


def test_episode_7_shot_11_is_clean_now_that_it_is_rewritten():
    """SHOT 11, not the episode. This asserted the whole of ep07 when M10 could
    match almost nothing; with the matcher widened, ep07 shot 24 turns out to
    carry the fault too ("his open palm comes up into the bottom of frame"
    against an at_rest that already holds the palm at the BOTTOM of frame). That
    is a real fault in a published episode, recorded below, not hidden by
    keeping this assertion broad enough to be false."""
    from studio import episode_home
    book = episode_home.book_dir("20260822113400_a-study-in-scarlet")
    episode = episode_home.load_plan(book, 7)
    assert [f for f in episode.still_motions() if f[1] == "M10" and f[0] == 11] == []


# ---- the matcher, measured against the prose that exists ---------------------
#
# M10 shipped this morning and catches NOTHING. Run over all 174 shots of the
# seven delivered plans it fires 0 times, which read as "the fault is extinct"
# and is not: its `ENTERS` pattern engages on 1 of 220 segments, because it
# demands `into (the) frame` with nothing in between, and these plans write
#
#     "a bare hand comes into the BOTTOM OF frame"          ep06 shot 0
#     "his open palm comes up into the BOTTOM OF frame"     ep07 shot 24
#     "the hansom enters AT THE LEFT EDGE OF frame"         ep01 shot 3
#
# all three of which are the fault, all three uncaught. A gate that passes its
# own unit test and matches nothing real is worse than no gate: it reports zero
# and the zero is believed.
#
# The widening has a trap, and it is why this is not a one-line change. These
# plans use body parts as a SIZE LADDER -- "at the height of a standing woman's
# shoulder" -- so a looser matcher reads ep06 shot 15's "a woman's shoulder
# comes into the LEFT of frame" as a contradiction with a measuring stick. A
# noun that appears in `at_rest` only as a unit of measure is not a thing
# standing in the frame.

NEAR = [
    ("ep06 shot 0", "a bare hand rests at the BOTTOM edge of frame",
     "a bare hand comes into the bottom of frame and draws the nearest paper"),
    ("ep07 shot 24", "an open palm holds a pair of steel handcuffs at the BOTTOM of frame",
     "his open palm comes up into the bottom of frame with the handcuffs on it"),
    ("ep01 shot 3", "The hansom stands halted at the LEFT of frame with its whole length inside",
     "the hansom enters at the left edge of frame"),
]


@pytest.mark.parametrize("where,rest,motion", NEAR)
def test_the_three_real_instances_are_caught(where, rest, motion):
    assert es.already_in_frame(rest, motion), where


def test_a_measuring_stick_is_not_a_thing_in_the_frame():
    """ep06 shot 15's shape. "shoulder" is in `at_rest` only as a unit of size."""
    rest = ("The white marble mantelpiece stands at the LEFT at the height of a standing "
            "woman's shoulder, and the red Turkey carpet holds the BOTTOM")
    motion = "The camera holds; a woman's shoulder comes into the LEFT of frame."
    assert es.already_in_frame(rest, motion) == []


def test_a_real_object_beside_a_measuring_stick_is_still_caught():
    """The guard must not swallow the gate: the lamp IS in frame."""
    rest = ("A brass lamp stands at the LEFT at the height of a standing woman's shoulder, "
            "and the carpet holds the BOTTOM")
    motion = "The camera holds; the brass lamp comes into the LEFT of frame."
    assert es.already_in_frame(rest, motion)


def test_leaving_by_an_edge_is_still_not_entering():
    rest = "A plastered finger stands at the TOP of frame at the height of a thumb"
    motion = "The camera holds; the plastered finger lifts out of the top of frame."
    assert es.already_in_frame(rest, motion) == []


def test_the_wider_matcher_catches_exactly_the_known_three():
    """The census, pinned. Widening a HARD gate is only safe if what it now
    refuses is known, so the three real instances in the delivered plans are
    named here and any fourth fails this test.

        ep01 shot 3   "the hansom enters at the left edge of frame"
                      at_rest: "The hansom stands halted at the LEFT of frame"
        ep06 shot 0   "a bare hand comes into the bottom of frame"
                      at_rest: "a bare hand rests at the BOTTOM edge of frame"
        ep07 shot 24  "his open palm comes up into the bottom of frame"
                      at_rest: "an open palm holds ... at the BOTTOM of frame"

    All three are published. They are recorded, not re-cut."""
    from studio import episode_home
    book = episode_home.book_dir("20260822113400_a-study-in-scarlet")
    found = set()
    for n in range(1, 8):
        try:
            episode = episode_home.load_plan(book, n)
        except Exception:
            continue
        found |= {(n, i) for i, code, _ in episode.still_motions() if code == "M10"}
    assert found == {(1, 3), (6, 0), (7, 24)}, f"M10's census has moved: {sorted(found)}"
