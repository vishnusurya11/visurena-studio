"""Three ways the cut gate reported something that did not happen.

All three were measured on episode 3's own records, 2026-09-13.

  C1 A SUPERSEDED DRAFT IS NOT ANOTHER SHOT.  `foreign_names` globs `Q??_?*.png`,
     which sweeps up `Q11_0.before.png` -- the take's OWN cell as it was before a
     $0.08 redraw.  Ten of ep03's eighteen foreign-flagged samples (56 %) were a
     `.before` sibling, and T12 hard-failed on three of them at a margin of 0.08
     against a threshold of 0.05.  A picture the take used to be is not an
     intrusion from elsewhere.

  C2 A FRAME THAT MATCHES NOTHING HAS NOT "GONE BACK".  `landing` calls a frame
     landed only when `own_s >= LAND`, but calls it a PING-PONG on the bare
     argmax with no floor at all.  T07's camera walks off its cell (end_sim
     0.087); for 44 straight frames every own-score is 0.022-0.352, argmax falls
     on whichever cell is the better nearest-neighbour of noise, and the gate
     reports "the take cut back to shot 0".  It did not.  Four identical
     re-rolls could never fix it, because the camera moves the same way each
     time.

  C3 A FLOOR IS NOT A MEASUREMENT.  `PRE = 24` bounds the backward search, so a
     cut that landed 40 frames early reports exactly -24.  Both of ep03's
     catastrophic takes report exactly -24, which is the search limit wearing a
     number's clothes.
"""
import numpy as np

from studio import cut_landing as cl


def sig(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = rng.random(cl.SIG_H * cl.SIG_W if hasattr(cl, "SIG_H") else 48 * 84).astype(np.float32)
    return out / np.linalg.norm(out)


# ---- C1  a `.before` sibling is the take's own picture ----------------------

def test_a_before_sibling_is_not_a_foreign_cell(tmp_path):
    for name in ("Q11_0.png", "Q11_0.before.png", "Q11_1.png", "Q23_0.png", "plate_hall.png"):
        (tmp_path / name).write_bytes(b"")
    got = cl.foreign_names(tmp_path, {"Q11_0.png"})
    assert "Q11_0.before.png" not in got


def test_another_shots_before_sibling_is_not_foreign_either(tmp_path):
    """A draft of ANY cell is a draft, not a shot. It was never rendered, so no
    take can legitimately be drifting onto it."""
    for name in ("Q11_0.png", "Q23_0.png", "Q23_0.before.png"):
        (tmp_path / name).write_bytes(b"")
    assert not [n for n in cl.foreign_names(tmp_path, {"Q11_0.png"}) if ".before." in n]


def test_a_real_other_cell_and_a_plate_are_still_foreign(tmp_path):
    for name in ("Q11_0.png", "Q23_0.png", "plate_hall.png"):
        (tmp_path / name).write_bytes(b"")
    got = cl.foreign_names(tmp_path, {"Q11_0.png"})
    assert set(got) == {"Q23_0.png", "plate_hall.png"}


# ---- C2  a ping-pong has to actually BE the earlier cell --------------------

def test_a_frame_matching_nothing_is_not_a_ping_pong():
    """T07's shape: segment 1 is pinned and lands, then the camera leaves its
    cell and every own-score collapses. Nothing here is shot 0."""
    a, b = sig(1), sig(2)
    per_frame = ([{"own": "Q07_0.png", "own_s": 0.99, "other": "", "other_s": 0.0, "foreign": False}] * 10
                 + [{"own": "Q07_1.png", "own_s": 0.95, "other": "", "other_s": 0.0, "foreign": False}] * 5
                 + [{"own": "Q07_0.png", "own_s": 0.21, "other": "", "other_s": 0.0, "foreign": False}] * 20)
    rows = cl.landing(per_frame, [("Q07_0.png", 0), ("Q07_1.png", 10)])
    assert rows[0]["pingpong"] == 0


def test_a_frame_that_really_is_the_earlier_cell_still_counts():
    per_frame = ([{"own": "Q07_0.png", "own_s": 0.99, "other": "", "other_s": 0.0, "foreign": False}] * 10
                 + [{"own": "Q07_1.png", "own_s": 0.95, "other": "", "other_s": 0.0, "foreign": False}] * 5
                 + [{"own": "Q07_0.png", "own_s": 0.93, "other": "", "other_s": 0.0, "foreign": False}] * 20)
    rows = cl.landing(per_frame, [("Q07_0.png", 0), ("Q07_1.png", 10)])
    assert rows[0]["pingpong"] == 20 and rows[0]["pingpong_to"] == "Q07_0.png"


# ---- C3  the search window is wide enough to be a number -------------------

def test_the_backward_search_reaches_two_seconds():
    """At PRE = 24 a cut that landed 40 frames early reported exactly -24 and
    every such take reported the same figure. Two seconds makes it a value."""
    assert cl.PRE >= cl.FPS * 2
