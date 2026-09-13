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
from studio.episode_ref_official import arrival_clause, gerund

SEG = {"t": 0.0, "end": 4, "t_to": 4.0, "size": "close", "crowd": "",
       "frame": "Close on Holmes at the fire.",
       "motion": "Holmes turns his head toward the camera while the camera pushes in a hand's breadth.",
       "end_frame": "", "changed": ""}


def test_a_segment_with_a_written_end_says_where_it_arrives():
    seg = dict(SEG, end_frame="Close on the open eyes alone, the brow holding the TOP edge.")
    said = arrival_clause(seg)
    assert said.startswith("By 00:04")
    assert "the open eyes alone" in said


def test_a_segment_with_no_written_end_falls_back_to_the_action():
    assert "with the action of that shot completed" in arrival_clause(SEG)


def test_the_clause_never_cites_a_picture():
    """The whole point: no `<Picture N>` to cut to."""
    seg = dict(SEG, end_frame="Close on the open eyes alone.")
    assert "<Picture" not in arrival_clause(seg)


def test_the_clause_lands_on_the_segments_own_end_second():
    assert arrival_clause(dict(SEG, end=7)).startswith("By 00:07")


def test_the_clause_reads_as_one_sentence():
    """`By 00:04, Close on the open eyes` -- the mid-sentence capital again."""
    seg = dict(SEG, end_frame="The open eyes alone hold the frame.")
    assert "By 00:04, the open eyes alone" in arrival_clause(seg)


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
    assert "pushing in a hand's breadth" in said
    # the empty phrase may TRAIL a real statement; it may not be the whole of it
    assert not said.startswith("By 00:04, with the action")


def test_a_locked_off_shot_still_says_something_true():
    """No camera move named: the shot still has to have arrived somewhere."""
    seg = dict(SEG, end_frame="", motion="Holmes turns his head toward the camera.")
    said = arrival_clause(seg)
    assert said.startswith("By 00:04")
    assert "camera" in said.lower()


def test_a_written_end_still_wins_over_the_camera():
    seg = dict(SEG, end_frame="Close on the open eyes alone, the brow holding the TOP edge.")
    said = arrival_clause(seg)
    assert "the open eyes alone" in said
    assert "pushing" not in said
