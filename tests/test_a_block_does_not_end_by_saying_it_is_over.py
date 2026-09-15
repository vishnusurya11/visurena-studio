r"""The last sentence a take's block says about motion decided that the motion stops.

`arrival_clause` closes every `[Shot k]` block, and on 18 of episode 5's 25
takes it closed it like this:

    By 00:07 the camera is where it began, with the action of that shot completed.

`frozen-share` is measured over exactly the tail this sentence describes, and it
is 67.2 of episode 5's 92.2 lost points. The model is told, in the block's final
clause, that by the last stamp the shot is done.

The sentence was not written to say that. `arrival_clause`'s own docstring
argues at length for saying the destination in WORDS rather than staging it as a
picture -- a real finding, about a `<Picture N>` the model cut to and finished
the take on -- and never once argues that the destination must be phrased as
*completed*. The word came in with the fallback and was never the point.

TWO CONSTRAINTS SHAPE THE REPLACEMENT, both already paid for:

  * no word from L2's stillness class -- `still`, `stays`, `holds`, `remains`,
    `pauses`, `waits`. That list is why the sentence says `stands at that
    distance` and not `holds there`. It also rules out the obvious fix, "is
    still pushing in".
  * no negation. MiniMax reads none, which is why it does not say "goes no
    further".

`continues ... through the last frame of the shot` satisfies both, and is the
vocabulary the builder already uses for its timed beats, so the block ends in
the same register it spent its middle in.

This composes with the camera-move rule rather than replacing it: with a move in
the head the sentence now says the move is still running at the last frame,
which is a thing H3 can render. See [[test_the_camera_is_what_moves]].
"""
from studio.episode_ref_official import STILL, arrival_clause

MOVING = {"end": 7.0, "motion": ("The camera pushes in a hand's breadth across the whole shot; "
                                 "his arm comes out; his shoulders come down.")}
STATIC = {"end": 7.0, "motion": "His arm comes out; his chin lifts; his shoulders come down."}


def test_a_block_never_says_the_shot_is_completed():
    assert "completed" not in arrival_clause(MOVING)
    assert "completed" not in arrival_clause(STATIC)


def test_the_arrival_says_the_action_reaches_the_last_frame():
    assert "last frame" in arrival_clause(MOVING)
    assert "last frame" in arrival_clause(STATIC)


def test_the_camera_move_is_named_as_still_running():
    assert "pushing in a hand's breadth" in arrival_clause(MOVING)


def test_the_arrival_carries_no_stillness_word():
    """L2's own class. It is why the sentence cannot say "is still pushing in"."""
    for seg in (MOVING, STATIC):
        assert not STILL.search(arrival_clause(seg)), arrival_clause(seg)


def test_the_arrival_carries_no_negation():
    """MiniMax reads no negation -- the reason it never said "goes no further"."""
    from studio.affirm import negations
    for seg in (MOVING, STATIC):
        assert not negations(arrival_clause(seg))


def test_it_still_lands_on_the_shots_own_stamp():
    assert arrival_clause(MOVING).startswith("By 00:07")


def test_a_written_end_frame_still_wins():
    """The `end_frame` branch was never the fault and is untouched."""
    got = arrival_clause({"end": 7.0, "motion": "x", "end_frame": "The door stands open"})
    assert "the door stands open" in got.lower()
