"""An END panel is the shot's LAST frame, so it is taken from where the camera ended.

MEASURED, episode 7 take 22.  The plan says

    motion: The camera pushes in on the doorway across the whole shot,
            travelling two long strides; the boy's hand comes down off his
            forelock to his side; his head turns back to the stair.

The take obeys it: a clean, continuous push from a full of the room to a much
tighter framing on the boy, no cut, no drift off the staging.  The drawn END
cell `Q22_0E.png` is the SAME camera position and the SAME scale as the start --
the only difference in the whole picture is the boy's hand, now at his side.
`drift_gate` then measured the take's last frame against that unmoved picture,
got 0.397, and HARD-failed a good take for doing exactly what it was told.

The cause is in this module and it is two sentences long:

    end_text: "Panel {k} - PANEL {j} ONE ACTION LATER, from the same camera."
    keeps_camera: strips every REFRAMING phrase out of the END picture.

Both are RIGHT for a locked-off shot, and both were written when locked-off was
the normal case: episodes 2 to 5 hold the camera still in most shots.  Episode 6
cured the stillness by moving the camera across the WHOLE shot in every shot,
and at that moment "from the same camera" became a false statement about every
END panel in the episode -- the same fault class as the camera-move regex that
was wrong from episode 2, and as FOREIGN_MIN: a constant calibrated on a world
that has since changed.

So the END panel now inherits the camera's TRAVEL, and only a shot whose camera
really does hold still is told the camera holds still.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import episode_seq_board as sq

PUSH = ("The camera pushes in on the doorway across the whole shot, travelling two long "
        "strides; the boy's hand comes down off his forelock to his side.")
PULL = ("The camera pulls back off the muzzle across the whole shot, travelling a hand's "
        "breadth; the wiry coat goes still along the ribs.")
TILT = ("The camera tilts up the ladder across the whole shot, travelling a long stride; "
        "the curtain inside the window lifts once in the draught.")
TRACK = ("The camera tracks down the lane to the left across the whole shot, travelling two "
         "long strides; a boy with a milk can walks the cobbles.")
STILL = ("The camera is static across the whole shot; Holmes raises the glass to the light "
         "and turns it once.")


def end(motion, changed="the boy's hand is down at his side"):
    """The panel text as the PIPELINE builds it, through `end_panel`.

    This used to hand `end_text` a dict written here, carrying a `motion` key.
    `end_panel` sets `motion=""` on every END seg it makes -- deliberately, so
    the END panel does not print the shot's motion prose -- so the real END seg
    never had one, `camera_end` read "" for every shot on disk, and the whole
    fix was a no-op that eight green tests reported as working. It was caught by
    a redrawn Q10_0E coming back byte-identical to the cell it replaced.

    A test that builds its own input tests the code it was written beside. This
    one goes through `cell` and `end_panel`, which is the only path a real panel
    takes.

    Lower-cased: the panel SHOUTS the direction on purpose, so the model cannot
    read past it, and the test asserts the word, not the shouting."""
    start = {"shot": 3, "sub": 0, "frame": "A ragged boy round the door jamb.",
             "motion": motion, "path": 0.5, "faces": [], "size": "full",
             "camera": "at the hearth rug, a 35mm lens", "at_rest": "",
             "end_frame": "", "changed": changed, "crowd": ""}
    return sq.end_text(4, sq.end_panel(start, 3), "").lower()


def test_a_push_ends_nearer_than_it_began():
    said = end(PUSH)
    assert "same camera" not in said, said
    assert "two long strides" in said, said
    assert "nearer" in said, said


def test_a_pull_ends_further_back():
    said = end(PULL)
    assert "hand's breadth" in said and "further back" in said, said


def test_a_tilt_ends_higher():
    said = end(TILT)
    assert "risen a long stride above panel 3" in said, said


def test_a_track_ends_along_its_own_travel():
    said = end(TRACK)
    assert "two long strides" in said and "same camera" not in said, said


def test_a_camera_that_holds_still_is_still_told_to_hold_still():
    """The old sentence was not wrong; it was wrong for MOVING shots only."""
    said = end(STILL)
    assert "same camera" in said, said


def test_a_shot_with_no_motion_at_all_keeps_the_old_sentence():
    assert "same camera" in end("")


def test_a_moving_end_may_say_how_it_is_framed():
    """`keeps_camera` exists to stop an END panel RE-SPECIFYING a camera it was
    told to keep.  When the camera did not keep, the reframing IS the panel."""
    frame = "A ragged boy round the door jamb, from two long strides nearer."
    start = {"shot": 3, "sub": 0, "frame": frame, "motion": PUSH, "path": 0.5, "faces": [],
             "size": "full", "camera": "", "at_rest": "", "end_frame": "",
             "changed": "his hand is down", "crowd": ""}
    assert "nearer" in sq.end_text(4, sq.end_panel(start, 3), "")


def test_a_still_end_still_may_not():
    frame = "A ragged boy round the door jamb, from a tighter framing."
    start = {"shot": 3, "sub": 0, "frame": frame, "motion": STILL, "path": 0.5, "faces": [],
             "size": "full", "camera": "", "at_rest": "", "end_frame": "",
             "changed": "his hand is down", "crowd": ""}
    assert "tighter framing" not in sq.end_text(4, sq.end_panel(start, 3), "")
