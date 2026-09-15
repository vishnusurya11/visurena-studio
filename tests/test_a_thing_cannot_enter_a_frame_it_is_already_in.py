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


def test_episode_7_is_clean_now_that_shot_11_is_rewritten():
    from studio import episode_home
    book = episode_home.book_dir("20260822113400_a-study-in-scarlet")
    episode = episode_home.load_plan(book, 7)
    assert [f for f in episode.still_motions() if f[1] == "M10"] == []
