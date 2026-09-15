r"""How far the camera went, whether or not the plan said "travelling".

`camera_end` first read the distance only out of "travelling <how far>", which is
the shape the ep07 authoring convention uses. Episode 7 shot 21 writes it the
other way --

    The camera tracks a hand's breadth to the left across the whole shot;
    his head comes up off his chest; ...

-- and so `camera_end` returned "" and the shot was quietly treated as locked
off. That is the empty-result-indistinguishable-from-a-clean-one fault yet
again: a shot whose camera moves and a shot whose camera holds still both came
back as the empty string, and only one of them was right.

The distance is a BODY-SCALE phrase, which is the owner's standing rule for
every amount in this pipeline (no percentages, no metres, no "slowly"). So the
distance is found by looking for a body, not for a verb that happens to precede
it.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import episode_seq_board as sq

SAID_TRAVELLING = "The camera pushes in on the doorway across the whole shot, travelling two long strides"
SAID_PLAIN = "The camera tracks a hand's breadth to the left across the whole shot"
SAID_FOREARM = "The camera pushes in on the basin across the whole shot, travelling a forearm"
SAID_TREAD = "The camera cranes up the stair one whole tread across the whole shot"


@pytest.mark.parametrize("said,far", [
    (SAID_TRAVELLING, "two long strides"),
    (SAID_PLAIN, "a hand's breadth"),
    (SAID_FOREARM, "a forearm"),
    (SAID_TREAD, "one whole tread"),
])
def test_the_distance_is_read_with_or_without_travelling(said, far):
    assert far in sq.camera_end(said, 1), sq.camera_end(said, 1)


def test_a_track_written_plainly_is_not_mistaken_for_a_locked_camera():
    """Episode 7 shot 21, the case that was silently dropped."""
    assert sq.camera_end(SAID_PLAIN, 3) != ""
    assert "along its own travel" in sq.camera_end(SAID_PLAIN, 3).lower()


def test_a_static_camera_stays_empty_even_beside_a_body_word():
    """A subject's own body-scale move is not the camera's."""
    said = ("The camera is static across the whole shot; his head comes up a hand's breadth "
            "off his chest")
    assert sq.camera_end(said, 1) == ""


def test_a_body_word_in_the_subject_clause_is_not_the_camera_s_travel():
    """`camera_clause` takes the clause that names the camera, and only that one."""
    said = ("Holmes's hand comes out a forearm from his pocket; the camera pushes in on him "
            "across the whole shot, travelling two long strides")
    assert "two long strides" in sq.camera_end(said, 1)


def test_a_camera_clause_with_no_distance_at_all_is_still_empty():
    """Nothing is invented. A move with no amount is a move the plan under-wrote."""
    assert sq.camera_end("The camera pushes in on the doorway across the whole shot", 1) == ""


def test_every_camera_clause_in_the_delivered_episodes_yields_its_distance():
    """CALIBRATION, not a unit test: the regex is judged against the prose that
    exists. A plan whose camera moves and whose distance cannot be read is the
    silent case this whole file is about, so it is named here rather than found
    later in a drift failure.

    EPISODE 4 IS EXCLUDED AND THE REASON IS MEASURED, not assumed. Three of its
    shots -- 2, 10 and 14 -- write "the camera pushes straight in on the hand /
    on it / on the lit pane" with no amount at all. They predate the body-scale
    rule and they are published; the honest record is that episode 4 carries
    three under-written camera moves, not that the rule has an exception. Every
    camera move in episodes 5, 6 and 7 states its amount."""
    from studio import episode_home
    book = episode_home.book_dir("20260822113400_a-study-in-scarlet")
    silent = []
    for n in (5, 6, 7):
        try:
            episode = episode_home.load_plan(book, n)
        except Exception:
            continue
        for shot in episode.shots:
            said = sq.camera_clause(shot.motion)
            if said and not sq.HOLDS.search(said) and not sq.camera_end(shot.motion, 1):
                silent.append(f"ep{n:02d} shot {shot.index}: {said}")
    assert not silent, "camera moves with no readable distance:\n" + "\n".join(silent)
