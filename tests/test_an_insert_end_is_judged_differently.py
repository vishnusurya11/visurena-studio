"""On an insert the subject IS the frame, so whole-frame cosine measures the
subject and not the camera.

`reaches` decides whether a take may be aimed at its own END cell, by scoring
the pair with `frame_match` and demanding `END_FLOOR <= s <= END_CEILING`.  The
floor exists for a real fault: episode 2's drawer answered "the shot ends here"
by moving to a DIFFERENT CAMERA SETUP, 9 of 13 cells below the floor, and aiming
a take at one of those caused every one of that episode's seven drift failures.

That reasoning holds for a frame with a room in it.  It inverts on an insert.
Episode 4's shot 10 is a half-sovereign held between finger and thumb, edge-on,
which "turns over once" to show its face -- the same lens, the same hand, the
same distance, the subject rotated 90 degrees.  Q10_0 vs Q10_0E scores 0.166 and
the gate called it re-staged, so the take was given no END cell.

MEASURED, 2026-09-13: H3 then invented the reveal, and the coin it minted reads
"SOLVUNT EF . CENOWLEBH" around a figure who is not Victoria -- invented
lettering, on the one shot whose whole content is a reveal, while the correct
coin face sat drawn and unused in `Q10_0E.png`.

The CEILING still applies: an insert that ends where it began is the stillness
the owner banned, whatever its size.  Only the floor is dropped, and only for a
size whose subject fills the frame.
"""
from studio.episode_seq_board import END_CEILING, END_FLOOR, end_pair_verdict


def test_the_floor_still_refuses_a_re_staged_room():
    assert end_pair_verdict(0.166) == "restaged"


def test_a_turned_subject_reaches_on_an_insert():
    """The same 0.166 that refuses a room accepts a coin turning over."""
    assert end_pair_verdict(0.166, size="insert") == "ok"


def test_an_insert_that_ends_where_it_began_is_still_a_copy():
    """The ceiling is about stillness, which no framing excuses."""
    assert end_pair_verdict(0.99, size="insert") == "copy"
    assert end_pair_verdict(END_CEILING + 0.01, size="insert") == "copy"


def test_the_band_is_unchanged_for_every_other_size():
    for size in ("wide", "full", "medium", "medium_close", "close"):
        assert end_pair_verdict(0.166, size=size) == "restaged"
        assert end_pair_verdict(0.99, size=size) == "copy"
        assert end_pair_verdict(0.60, size=size) == "ok"


def test_a_middling_score_is_still_ok_on_an_insert():
    assert end_pair_verdict((END_FLOOR + END_CEILING) / 2, size="insert") == "ok"


def test_no_size_given_is_the_strict_band():
    """Callers that do not know the size get the rule that refuses more."""
    assert end_pair_verdict(0.166) == "restaged"


def test_reaches_passes_the_size_through(tmp_path):
    """The rule has to arrive where the decision is made."""
    import inspect

    from studio import episode_seq_board as sq
    assert "size" in inspect.signature(sq.reaches).parameters
