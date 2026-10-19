"""The body fallback for a face the face model misses (face-blur round 2, 2026-10-19; BSAI FaceRefine
v5's idea, ported).  The person model's boxes (person_yolov8m-seg.pt, already on disk) give a face
box by ep01's own geometry: on the 9 round-1 takes, 509 people holding one detected face put it
at 0.100 of the person's height (p10-p90 0.086-0.164), its centre 0.125 down from the top, centred.

- A body face extends a face track it fits, either way in time (ep01 T06: the person model sees
  Hyde from frame 0, the face model from frame 17).
- A track from bodies alone is kept only for a FAR figure (face estimate under 24 px, where the face
  model's recall is unknown), seen for a second or more, that no face track ever comes near: a big
  faceless person is turned away or cropped (ep01 T15 frames 129-144, T18's figures cut by the
  frame's foot), never refined.
- A person cut by the frame's top or bottom gives no face (its height, and so its face, is wrong).
Pure numpy."""
from __future__ import annotations

import pytest

from studio import face_track as ft


def box(cx, cy, h=30.0):
    return (cx - h / 2, cy - h / 2, cx + h / 2, cy + h / 2)


def person(cx, top, h):
    return (cx - 0.3 * h, top, cx + 0.3 * h, top + h)


def test_a_persons_face_follows_ep01s_geometry():
    x1, y1, x2, y2 = ft.body_face(person(100, 200, 300))
    assert y2 - y1 == pytest.approx(30.0) and (y1 + y2) / 2 == pytest.approx(237.5) and (x1 + x2) / 2 == pytest.approx(100.0)


def test_a_person_cut_by_the_frame_gives_no_face():
    found = {0: [person(100, 500, 268), person(300, 0, 200), person(500, 200, 300)]}
    assert ft.body_faces(found, 768, 768) == {0: [ft.body_face(person(500, 200, 300))]}


def test_a_body_face_extends_its_track_back_to_where_the_face_model_found_it():
    faces = [(t, box(450, 340, 13)) for t in range(18, 60, 3)]
    bodies = {t: [ft.body_face(person(450, 326, 120))] for t in range(0, 60, 3)}
    got = ft.rescue([faces], bodies)
    assert ft.life(got[0]) == (0, 57)


def far_bodies(cx, h=150, frames=range(0, 60, 3)):
    return {t: [ft.body_face(person(cx, 200, h))] for t in frames}


def test_a_far_figure_no_face_track_reaches_becomes_its_own_track():
    faces = [[(t, box(600, 300, 40)) for t in range(0, 60, 3)]]
    got = ft.body_only(far_bodies(100), faces)
    assert len(got) == 1 and ft.life(got[0]) == (0, 57)


def test_a_big_faceless_person_is_never_a_face():
    assert ft.body_only(far_bodies(100, h=400), []) == []


def test_a_body_beside_a_face_track_is_that_face_not_another():
    bodies = far_bodies(100)
    faces = [[(t, bodies[t][0]) for t in range(0, 30, 3)]]
    assert ft.body_only(bodies, faces) == []


def test_a_glimpse_of_a_body_is_no_track():
    assert ft.body_only(far_bodies(100, frames=range(0, 9, 3)), []) == []


def test_a_body_seen_under_a_second_is_no_track():
    """ep01 T07 and T08 frames 0-12: a 13-frame body track was the child from behind, then a passer-by."""
    assert ft.body_only(far_bodies(100, frames=range(0, 13, 3)), []) == []
    assert len(ft.body_only(far_bodies(100, frames=range(0, 25, 3)), [])) == 1
