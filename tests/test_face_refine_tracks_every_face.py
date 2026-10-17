"""Every face in a take becomes its own crop track (studio/face_track.py): detections
linked frame to frame by nearness, gaps interpolated, the window held at one size,
the H3 crop span on the model's frame grid.  F2 tracked one face per take and drifted
from Utterson to Enfield on T22 as they walked out; one track per person, cut at its
own life, is the cure.  Pure numpy: no detector, no video."""
from __future__ import annotations

import numpy as np
import pytest

from studio import face_track as ft


def box(cx, cy, h=30.0):
    return (cx - h / 2, cy - h / 2, cx + h / 2, cy + h / 2)


def test_two_faces_walking_side_by_side_make_two_tracks():
    dets = {t: [box(100 + t, 300), box(400 - t, 310)] for t in range(0, 40, 4)}
    tracks = ft.link(dets)
    assert len(tracks) == 2
    assert all(len(tr) == 10 for tr in tracks)
    assert {round(tr[0][1][0]) for tr in tracks} == {85, 385}


def test_a_far_jump_starts_a_new_track_instead_of_stealing_the_old_one():
    dets = {0: [box(100, 300)], 4: [box(104, 300)], 8: [box(600, 300)]}
    assert sorted(len(t) for t in ft.link(dets)) == [1, 2]


def test_a_track_unseen_too_long_ends():
    dets = {0: [box(100, 300)], 4: [box(100, 300)], 40: [box(102, 300)]}
    assert sorted(len(t) for t in ft.link(dets, gap=12)) == [1, 2]


def test_a_flicker_of_a_detection_is_no_track():
    tracks = [[(0, box(1, 1))], [(t, box(5, 5)) for t in range(0, 40, 4)]]
    assert ft.keep(tracks) == [tracks[1]]


def test_boxes_fill_every_frame_of_the_life_and_hold_at_its_ends():
    track = [(4, box(100, 300)), (12, box(120, 300))]
    full = ft.fill(track, 20, smooth=1)
    assert full.shape == (20, 4)
    assert full[8][0] == pytest.approx(box(110, 300)[0])
    assert full[0][0] == pytest.approx(full[4][0]) and full[19][0] == pytest.approx(full[12][0])


def test_the_life_is_first_to_last_detection():
    assert ft.life([(4, box(1, 1)), (40, box(1, 1))]) == (4, 40)


def test_the_window_is_one_size_square_round_the_face_inside_the_frame():
    boxes = np.array([box(100, 300, 30)] * 3 + [box(760, 300, 30)])
    wins = ft.windows(boxes, 768, 768)
    sides = {s for _, _, s in wins}
    assert sides == {ft.MIN_SIDE}                  # 30 x 2.4 = 72 < the floor
    assert all(0 <= x <= 768 - s and 0 <= y <= 768 - s for x, y, s in wins)


def test_a_big_face_gets_a_window_of_its_margin():
    wins = ft.windows(np.array([box(300, 300, 60)] * 5), 768, 768)
    assert wins[0][2] == int(60 * ft.MARGIN)


def test_the_crop_span_is_on_h3s_grid_and_inside_the_take():
    a, n = ft.crop_span((10, 80), 192)
    assert n % 17 == 5 and n >= 71 and a <= 10 and a + n <= 192


def test_a_span_at_the_tail_slides_back_inside_the_take():
    a, n = ft.crop_span((150, 191), 192)
    assert a + n == 192 and a <= 150


def test_a_span_longer_than_an_off_grid_take_shrinks_onto_the_grid():
    a, n = ft.crop_span((0, 99), 100)
    assert (a, n) == (0, 90)


def test_colour_histograms_tell_a_black_hat_from_a_brown_one():
    black = np.zeros((40, 40, 3), np.uint8)
    brown = np.full((40, 40, 3), (150, 100, 50), np.uint8)
    assert ft.hist_similarity(black, black) > ft.hist_similarity(black, brown)


def test_the_head_box_takes_the_hat_above_the_face():
    x1, y1, x2, y2 = ft.head_box((100, 100, 130, 130), 768, 768)
    assert y1 < 100 - 15 and x1 < 100 and x2 > 130 and y2 > 130


def test_two_pieces_of_one_face_split_by_a_missed_stretch_are_stitched():
    a = [(t, box(300, 300)) for t in range(0, 24, 4)]
    b = [(t, box(312, 302)) for t in range(48, 72, 4)]
    got = ft.stitch([a, b])
    assert len(got) == 1 and ft.life(got[0]) == (0, 68)


def test_two_faces_seen_at_once_are_never_stitched():
    a = [(t, box(300, 300)) for t in range(0, 40, 4)]
    b = [(t, box(320, 300)) for t in range(20, 60, 4)]
    assert len(ft.stitch([a, b])) == 2


def test_pieces_far_apart_stay_apart():
    a = [(t, box(100, 300)) for t in range(0, 24, 4)]
    b = [(t, box(600, 300)) for t in range(40, 64, 4)]
    assert len(ft.stitch([a, b])) == 2


def test_a_face_big_enough_to_read_is_left_alone():
    small = [(t, box(100, 300, 30)) for t in range(0, 24, 4)]
    big = [(t, box(400, 300, 150)) for t in range(0, 24, 4)]
    assert ft.small([small, big], 60.0) == [small]
