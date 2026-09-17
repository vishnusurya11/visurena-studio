"""With no END PICTURE, the shot's destination is stated in WORDS instead.

THE EXPERIMENT (owner, 2026-09-13): episode 3 rendered every take WITH an END
cell. Re-render every take WITHOUT one, describing the arrival as a camera
movement in the prompt, and compare. So this must test "picture versus words",
not "picture versus nothing" -- dropping the picture and saying nothing would
leave no statement anywhere of where the shot gets to, and the comparison would
be unfair to the owner's proposal.

`last_frame_text` was the only sentence that said it, and it lived in
`subject_definitions` bolted to a `<Picture N>`. Without a picture it has no
home there, so it moves into the shot block as a closing clause: one emitter,
zero reference slots, zero dollars.

MEASURED, the fault this is testing against: in 5 of 7 END takes the prompt
declared the END picture AND the next shot's first picture at the SAME SECOND,
both fully_preserved, and the END cell was never anchored in the graph -- an
unpinned whole-frame composition the model is free to cut to. Episode 2's T15
and T19 did exactly that and finished their takes there.
"""
import re

from studio.episode_ref_official import arrival_clause, gerund

SEG = {"t": 0.0, "end": 4, "t_to": 4.0, "size": "close", "crowd": "",
       "frame": "Close on Holmes at the fire.",
       "motion": "Holmes turns his head toward the camera while the camera pushes in a hand's breadth.",
       "end_frame": "", "changed": ""}


def test_a_segment_with_a_written_end_says_where_it_arrives():
    """A written `end` is a LAYOUT for the drawer ("the brow holding the TOP
    edge"), so the arrival is still the camera's, carrying one noun from the
    layout as what is now in frame."""
    seg = dict(SEG, end_frame="Close on the open eyes alone, the brow holding the TOP edge.")
    said = arrival_clause(seg)
    assert said.startswith("By 00:04 the camera is pushing in")
    assert "with the open eyes alone now in frame" in said
    assert "TOP edge" not in said


def test_a_segment_with_no_written_end_falls_back_to_the_action():
    """It used to fall back to `with the action of that shot completed`, which
    is the LAST thing the block says about motion on 18 of episode 5's 25 takes
    -- over exactly the tail `frozen-share` measures.  See
    tests/test_a_block_does_not_end_by_saying_it_is_over.py."""
    assert "the action continues with it" in arrival_clause(SEG)


def test_the_clause_never_cites_a_picture():
    """The whole point: no `<Picture N>` to cut to."""
    seg = dict(SEG, end_frame="Close on the open eyes alone.")
    assert "<Picture" not in arrival_clause(seg)


def test_the_clause_lands_on_the_segments_own_end_second():
    assert arrival_clause(dict(SEG, end=7)).startswith("By 00:07")


def test_the_clause_reads_as_one_sentence():
    """`By 00:04, Close on the open eyes` -- the mid-sentence capital again; and
    episode 9's "By 00:07, ferrier's head" -- the name lowercased.  A proper name
    keeps its capital and nothing else has one."""
    seg = dict(SEG, end_frame="The open eyes alone stand in the frame.")
    said = arrival_clause(seg)
    assert said.startswith("By 00:04 the camera is pushing in") and ", the open eyes alone" not in said
    named = dict(SEG, end_frame="Holmes has turned to the window.")
    assert ", and Holmes has turned to the window." in arrival_clause(named, ("Holmes",))
    assert not re.search(r"[a-z], [A-Z]", arrival_clause(named, ("Holmes",)))


# ---- when the plan wrote no END frame, the CAMERA says where it arrived -----

def test_the_camera_verb_becomes_a_gerund():
    """"pushes in a hand's breadth" -> "pushing in a hand's breadth"."""
    assert gerund("pushes in a hand's breadth") == "pushing in a hand's breadth"
    assert gerund("pulls back a foot") == "pulling back a foot"
    assert gerund("tilts down one hand's breadth") == "tilting down one hand's breadth"
    assert gerund("pans a hand's breadth along the rails") == "panning a hand's breadth along the rails"
    assert gerund("tracks along the counter") == "tracking along the counter"
    assert gerund("dollies in") == "dollying in"
    assert gerund("") == ""


def test_with_no_written_end_the_arrival_is_the_camera_move_completed():
    """EVERY episode 3 segment is this case -- 0 of 37 carry a written `end` --
    so the fallback IS the experiment. "with the action of that shot completed"
    says nothing a model can aim at; the camera's own move does."""
    seg = dict(SEG, end_frame="")
    said = arrival_clause(seg)
    assert "By 00:04" in said
    # the verb and its particle, and no more of the head: episode 10 carried the
    # whole camera clause twice a block (dq10/J.md §5)
    assert "the camera is pushing in through the last frame" in said
    assert "hand's breadth" not in said
    # the empty phrase may TRAIL a real statement; it may not be the whole of it
    assert not said.startswith("By 00:04, with the action")


def test_a_locked_off_shot_still_says_something_true():
    """No camera move named: the shot still has to have arrived somewhere."""
    seg = dict(SEG, end_frame="", motion="Holmes turns his head toward the camera.")
    said = arrival_clause(seg)
    assert said.startswith("By 00:04")
    assert "continues through the last frame" in said


def test_a_written_end_never_replaces_the_camera():
    """It used to: the drawer's `end` layout became the block's closing motion
    sentence -- "By 00:05, the log house stands twice its size..." -- a still
    composition as the destination, on 29 of episode 9's 30 blocks, where ep06
    and ep07 ended "the camera is pushing in ... through the last frame".  The
    camera arrives; the layout lends at most one noun."""
    seg = dict(SEG, end_frame="Close on the open eyes alone, the brow holding the TOP edge.")
    said = arrival_clause(seg)
    assert "the open eyes alone" in said
    assert "the camera is pushing in through the last frame" in said
