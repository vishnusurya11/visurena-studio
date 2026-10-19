"""The face refine's tracker, round 2 of the face-blur fix (2026-10-19; PLAN_FINAL section 1a,
ideas ported from ComfyUI-H3-FaceRefine (Carasibana, MIT) and VideoFaceDetailer / BSAI FaceRefine
(ideas only, licences not ours)):

- a track never jumps to another person: a detection joins a live track only at the track's own
  size, and a track that LOST its face re-acquires only a face that reads as the same head;
- a track keeps a `lost` count (sampled frames inside its life with no detection of its own);
- a weak detection (under the worker's 0.6) never starts a face, it only continues one;
- the refine runs where the face is soft, with hysteresis: on under 120 px, off over 150 px;
- the crop's side is frozen per run, so H3 sees one scale;
- the crop stays inside its shot and on H3's 17k+5 grid, never a wasted frame past a fade.
Pure numpy: no detector, no video."""
from __future__ import annotations

import numpy as np
import pytest

from studio import face_track as ft


def box(cx, cy, h=30.0):
    return (cx - h / 2, cy - h / 2, cx + h / 2, cy + h / 2)


# ---- never another person ---------------------------------------------------------------------

def test_a_face_twice_the_size_never_continues_a_track():
    """Enfield's 60 px face passes beside Utterson's lost 30 px one, inside its reach."""
    dets = {0: [box(100, 100, 30)], 3: [box(100, 100, 30)], 6: [box(130, 100, 60)]}
    tracks = ft.link(dets)
    assert len(tracks) == 2 and [len(t) for t in tracks] == [2, 1]


def test_a_lost_track_reacquires_only_the_same_head():
    """After a miss, a face in reach and at size joins only when `same` says it is that head."""
    dets = {0: [box(100, 100)], 3: [box(100, 100)], 9: [box(110, 100)]}
    assert len(ft.link(dets, same=lambda track, b, t, others: False)) == 2
    assert len(ft.link(dets, same=lambda track, b, t, others: True)) == 1


def test_the_check_sees_the_other_people_of_the_moment():
    seen = []
    dets = {0: [box(100, 100), box(400, 100)], 3: [box(100, 100), box(400, 100)], 9: [box(110, 100), box(400, 100)]}
    ft.link(dets, same=lambda track, b, t, others: seen.append(len(others)) or True)
    assert seen == [1, 1]          # both faces came back after the missed sample, each asked with the other


def test_a_face_seen_every_sample_is_never_asked_who_it_is():
    asked = []
    dets = {t: [box(100 + t, 100)] for t in range(0, 30, 3)}
    ft.link(dets, same=lambda track, b, t, others: asked.append(t) or False)
    assert asked == []


def test_a_stitch_never_joins_a_head_that_is_not_the_same():
    a = [(t, box(100, 100)) for t in range(0, 30, 3)]
    b = [(t, box(120, 100)) for t in range(45, 90, 3)]
    assert len(ft.stitch([a, b], same=lambda track, bx, t, others: False)) == 2
    assert len(ft.stitch([a, b], same=lambda track, bx, t, others: True)) == 1


def test_a_stitch_never_joins_a_face_of_another_size():
    a = [(t, box(100, 100, 30)) for t in range(0, 30, 3)]
    b = [(t, box(120, 100, 70)) for t in range(45, 90, 3)]
    assert len(ft.stitch([a, b])) == 2


def test_the_lost_count_is_the_samples_without_the_face():
    track = [(t, box(100, 100)) for t in (0, 3, 6, 15, 18)]
    assert ft.lost(track) == 2


# ---- weak detections ---------------------------------------------------------------------------

def test_a_weak_detection_continues_a_face_it_never_starts_one():
    strong = {0: [box(100, 100)], 3: [box(100, 100)], 6: [box(100, 100)], 9: [box(100, 100)]}
    weak = {12: [box(102, 100)], 15: [box(104, 100)], 30: [box(400, 400)]}
    tracks = ft.rescue(ft.link(strong), weak)
    assert len(tracks) == 1 and ft.life(tracks[0]) == (0, 15)


def test_a_weak_detection_never_takes_another_tracks_face_at_its_own_frame():
    """ep01 T07: a body face extended the child's first piece into the frames her second piece held."""
    a = [(t, box(100, 100)) for t in range(0, 15, 3)]
    b = [(t, box(130, 100)) for t in range(18, 40, 3)]
    got = ft.rescue([a, b], {18: [box(131, 100)], 21: [box(129, 100)]})
    assert ft.life(got[0]) == (0, 12)


def test_a_weak_face_more_than_a_face_away_is_not_the_tracks():
    """ep01 T01: Enfield's body face, 70 px below Utterson's last one (46 px), joined Utterson's track."""
    strong = {t: [box(286, 290, 46)] for t in range(72, 85, 3)}
    got = ft.rescue(ft.link(strong), {87: [box(250, 354, 40)]})
    assert ft.life(got[0]) == (72, 84)


def test_a_weak_face_after_a_lost_sample_must_be_the_same_head():
    strong = {t: [box(100, 100)] for t in range(0, 13, 3)}
    weak = {18: [box(104, 100)]}
    assert ft.life(ft.rescue(ft.link(strong), weak, same=lambda tr, b, t, others: False)[0]) == (0, 12)
    assert ft.life(ft.rescue(ft.link(strong), weak, same=lambda tr, b, t, others: True)[0]) == (0, 18)


def test_a_weak_detection_of_another_size_is_not_the_face():
    strong = {0: [box(100, 100, 30)], 3: [box(100, 100, 30)]}
    tracks = ft.rescue(ft.link(strong), {6: [box(100, 100, 70)]})
    assert ft.life(tracks[0]) == (0, 3)


def test_detections_split_by_the_strong_line():
    found = {0: [{"box": [0, 0, 9, 9], "score": 0.9}, {"box": [20, 0, 29, 9], "score": 0.4}]}
    strong, weak = ft.by_strength(found, 0.6)
    assert strong == {0: [(0, 0, 9, 9)]} and weak == {0: [(20, 0, 29, 9)]}


# ---- where the refine runs ---------------------------------------------------------------------

def test_a_push_in_is_refined_until_its_face_reads():
    """On under 120 px, off once over 150 px (the hysteresis), never back on for a dip to 140."""
    heights = [60 + t for t in range(0, 174, 3)]
    track = [(t, box(384, 384, h)) for t, h in zip(range(0, 174, 3), heights)]
    a, b = ft.soft_span(track, 174)
    assert a == 0 and 85 <= b <= 95


def test_a_face_that_hovers_round_the_wall_stays_refined():
    track = [(t, box(384, 384, 115 + 15 * (t // 30 % 2))) for t in range(0, 180, 3)]
    assert ft.soft_span(track, 180) == (0, 177)


def test_a_face_that_never_reads_soft_has_no_span():
    track = [(t, box(384, 384, 200)) for t in range(0, 90, 3)]
    assert ft.soft_span(track, 90) is None


def test_the_crop_side_is_frozen_for_the_run():
    track = [(t, box(384, 384, 60 + t / 3)) for t in range(0, 120, 3)]
    boxes = ft.fill(track, 120)
    side = ft.frozen_side(boxes, (0, 119), 768, 768)
    wins = ft.windows(boxes, 768, 768, side=side)
    assert {s for _, _, s in wins} == {side} and side >= int(max(boxes[:, 3] - boxes[:, 1]) * ft.MARGIN)


def test_a_small_face_keeps_the_floor_side():
    track = [(t, box(100, 100, 20)) for t in range(0, 60, 3)]
    assert ft.frozen_side(ft.fill(track, 60), (0, 59), 768, 768) == ft.MIN_SIDE


# ---- the crop's frames -------------------------------------------------------------------------

def test_a_crop_never_reaches_across_a_hard_cut():
    """A 40-frame life ending 3 frames before a cut: the 56-frame crop starts earlier instead."""
    start, n = ft.crop_span((60, 99), 200, cuts=[103])
    assert n % 17 == 5 and start + n <= 103 and start <= 60


def test_a_life_a_few_frames_over_the_grid_is_trimmed_not_rendered_long():
    """41 frames: the grid offers 39 (2 trimmed at the fades) or 56 (15 rendered for nothing)."""
    assert ft.grid_frames(41) == 39 and ft.grid_frames(50) == 56 and ft.grid_frames(39) == 39


def test_a_short_life_is_never_trimmed_by_more_than_a_quarter():
    """ep01 T07's child lived 10 frames: the grid's 5 would drop half of her."""
    assert ft.grid_frames(10) == 22 and ft.grid_frames(24) == 22


def test_a_shot_shorter_than_the_grid_crops_what_it_holds():
    start, n = ft.crop_span((10, 29), 200, cuts=[8, 30])
    assert n == 22 and start == 8
