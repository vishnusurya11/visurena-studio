"""The face refine's tracker never hands a track to another person (face-blur round 2, fix round,
2026-10-19; the skeptic's two cases).

- Crossing: two faces of near size (36 / 32 px, inside SIZE_JUMP) passing each other swapped tracks,
  because each detection went greedily to the NEAREST track.  Detections now go to the live tracks
  by least total cost (the Hungarian assignment, scipy): the distance from where the track's motion
  carries it (SORT's constant-velocity idea, at most one sample ahead), its size step, and -- when
  the head check offers `like` -- how unlike the track's latest head it reads.
- A newcomer with no rival: covered in tests/test_face_refine_runs_round_two.py (the head check
  lives beside the frames, in scripts/episode/face_refine.Same).
Pure numpy: no detector, no video."""
from __future__ import annotations

import pytest

from studio import face_track as ft


def box(cx, cy, h=30.0):
    return (cx - h / 2, cy - h / 2, cx + h / 2, cy + h / 2)


def heights(track):
    return {round(ft.height(b)) for _, b in track}


def test_two_faces_of_near_size_crossing_keep_their_own_tracks():
    """36 px walking right, 32 px walking left, 12 px a sample: they pass between samples 4 and 5."""
    dets = {3 * k: [box(100 + 12 * k, 200, 36), box(208 - 12 * k, 200, 32)] for k in range(10)}
    tracks = ft.link(dets)
    assert len(tracks) == 2 and sorted(map(min, map(heights, tracks))) == [32, 36]
    assert all(len(heights(tr)) == 1 for tr in tracks)


def test_two_faces_of_one_size_crossing_keep_their_ways():
    dets = {3 * k: [box(100 + 12 * k, 200, 30), box(208 - 12 * k, 204, 30)] for k in range(10)}
    tracks = ft.link(dets)
    xs = [[ft.centre(b)[0] for _, b in tr] for tr in tracks]
    assert len(tracks) == 2 and all(x == sorted(x) or x == sorted(x, reverse=True) for x in xs)


class Labelled:
    """A head check that knows who each box is (a test's stand-in for the Lab colour of the head)."""

    def __init__(self, who: dict):
        self.who = who

    def __call__(self, track, b, t, others=()):
        return self.who[b] == self.who[track[-1][1]]

    def like(self, track, b, t) -> float:
        return 1.0 if self.who[b] == self.who[track[-1][1]] else 0.2


class Unlike:
    def like(self, track, b, t) -> float:
        return 0.2


def test_a_head_that_reads_like_the_track_wins_over_a_nearer_one():
    """Utterson and Enfield step past each other between two samples: nearness alone swaps them."""
    a0, b0, a1, b1 = box(100, 200), box(130, 200), box(127, 200), box(104, 200)
    who = {a0: "utterson", a1: "utterson", b0: "enfield", b1: "enfield"}
    tracks = ft.link({0: [a0, b0], 3: [a1, b1]}, same=Labelled(who))
    assert sorted({who[b] for _, b in tr} == {who[tr[0][1]]} for tr in tracks) == [True, True]
    assert ft.link({0: [a0, b0], 3: [a1, b1]})[0][1][1] == b1        # nearness alone: the swap


def test_the_motion_carries_a_track_at_most_one_sample_ahead():
    track = [(0, box(100, 200)), (3, box(112, 200))]
    assert ft.centre(ft.predicted(track, 6)) == pytest.approx((124.0, 200.0))
    assert ft.centre(ft.predicted(track, 15)) == pytest.approx((124.0, 200.0))
    assert ft.predicted(track[:1], 6) == track[0][1]


def test_the_cost_counts_distance_size_and_likeness():
    track = [(0, box(100, 200, 30)), (3, box(100, 200, 30))]
    here, far, big = box(100, 200, 30), box(130, 200, 30), box(100, 200, 40)
    assert ft.cost(track, here, 6) == pytest.approx(0.0)
    assert ft.cost(track, far, 6) > 0 and ft.cost(track, big, 6) > 0
    assert ft.cost(track, here, 6, Unlike()) == pytest.approx(0.8)


class Steady:
    """A head check whose per-sample word is no."""

    def __call__(self, track, b, t, others=()):
        return True

    def continues(self, track, b, t) -> bool:
        return False


def test_a_face_in_the_next_sample_still_answers_the_per_sample_check():
    dets = {0: [box(100, 200)], 3: [box(104, 200)]}
    assert len(ft.link(dets, same=Steady())) == 2
    weak = ft.rescue([[(t, box(100, 200)) for t in range(0, 12, 3)]], {12: [box(102, 200)]}, same=Steady())
    assert ft.life(weak[0]) == (0, 9)


def test_a_stitch_never_counts_the_piece_itself_as_its_rival():
    """The stitch asked `same` with the lost piece's own original among the others, so 'at least as
    like as any rival' read own >= own and only the 0.4 floor stood (found in the fix round)."""
    a = [(t, box(100, 100)) for t in range(0, 12, 3)]
    b = [(t, box(110, 100)) for t in range(15, 27, 3)]
    c = [(t, box(400, 100)) for t in range(15, 27, 3)]
    seen = []
    ft.stitch([a, b, c], same=lambda tr, bx, t, others: seen.append(others) or True)
    assert seen == [[c]]


def test_a_detection_no_track_fits_starts_its_own():
    tracks = ft.link({0: [box(100, 200)], 3: [box(400, 200)]})
    assert len(tracks) == 2
