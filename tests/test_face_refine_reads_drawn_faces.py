"""The face refine's gate on DRAWN faces (Jekyll Kawajiri POC W, 2026-10-18).

The gate refused a refine that by eye was better with "faces 6 != 3": it summed
facenet's detections over six sampled crops, and the sharper refined face was
simply detected in all six frames where the soft source face was found in three.
Identity was unread on both sides: facenet finds no face on the drawn sheet.

Now the count is per frame -- faces whose centre is inside the crop window,
overlapping boxes merged -- and a clone is a frame with more faces than the
source ever showed (at least the one the track was cut round).  Identity is read
on every crop at the face box the window was cut round when no detector fires,
against the sheet's face found in its head band when facenet misses it there.
"""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from scripts.episode import face_refine as cli
from studio import face_gate as fg
from studio import face_refine as fr


def box(x1, y1, x2, y2, score=0.99):
    return {"box": [x1, y1, x2, y2], "score": score}


def test_a_face_whose_centre_is_outside_the_window_core_is_a_neighbour():
    assert fg.inside([300, 300, 460, 470], 768)
    assert not fg.inside([0, 300, 60, 400], 768)


def test_iou_is_overlap_over_union():
    from studio.face_track import iou
    assert iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1.0
    assert iou((0, 0, 10, 10), (5, 0, 15, 10)) == pytest.approx(50 / 150)
    assert iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0


def test_overlapping_boxes_are_one_face():
    found = [box(300, 300, 460, 470, 0.9), box(305, 296, 466, 474, 0.99), box(520, 300, 600, 400, 0.8)]
    kept = fg.dedupe(found)
    assert len(kept) == 2 and kept[0]["score"] == 0.99


def test_faces_are_counted_inside_the_window_and_deduped():
    found = [box(300, 300, 460, 470), box(305, 296, 466, 474), box(0, 300, 60, 400)]
    assert fg.count(found, 768) == 1


def test_the_window_face_box_is_the_one_the_crop_was_cut_round():
    x1, y1, x2, y2 = fg.window_face(768)
    assert x2 - x1 == pytest.approx(768 / 2.4) and (x1 + x2) / 2 == pytest.approx(384)
    assert (y1 + y2) / 2 > 384


def test_a_sharper_face_found_in_more_frames_is_no_clone():
    """POC W: one face per frame, found in 3 of 6 source crops and 6 of 6 refined."""
    m = fr.Measures(id_src=0.6, id_ref=0.6, seam=9.8, flick_src=16.6, flick_ref=14.4, faces_src=1, faces_ref=1,
                    outside=0.0)
    assert fr.decide(m) == (True, "kept")


def test_a_second_face_in_a_frame_is_a_clone():
    m = fr.Measures(id_src=0.6, id_ref=0.6, seam=4.0, flick_src=3.0, flick_ref=3.0, faces_src=1, faces_ref=2)
    kept, why = fr.decide(m)
    assert not kept and "faces" in why


def test_a_source_nobody_detected_still_owns_its_one_face():
    m = fr.Measures(id_src=0.6, id_ref=0.6, seam=4.0, flick_src=3.0, flick_ref=3.0, faces_src=0, faces_ref=1,
                    outside=0.0)
    assert fr.decide(m)[0]


def test_a_face_the_refine_lost_falls_back():
    m = fr.Measures(id_src=0.6, id_ref=0.6, seam=4.0, flick_src=3.0, flick_ref=3.0, faces_src=1, faces_ref=0)
    assert not fr.decide(m)[0]


def test_the_count_is_the_most_faces_any_one_crop_shows():
    crops = [np.full((768, 768, 3), k, np.uint8) for k in range(3)]
    per = {0: [], 1: [box(300, 300, 460, 470)], 2: [box(300, 300, 460, 470), box(305, 296, 466, 474)]}
    n, _ = fg.read_faces(crops, None, lambda rgb: per[int(rgb[0, 0, 0])], lambda rgb, b: None)
    assert n == 1


def test_identity_is_read_at_the_window_face_when_no_detector_fires():
    seen = []
    embed = lambda rgb, b: seen.append(tuple(b)) or np.array([1.0, 0.0])
    _, ident = fg.read_faces([np.zeros((768, 768, 3), np.uint8)], np.array([1.0, 0.0]), lambda rgb: [], embed)
    assert ident == pytest.approx(1.0) and seen == [tuple(fg.window_face(768))]


def test_a_drawn_sheet_facenet_misses_is_read_in_its_head_band(tmp_path):
    a = np.full((300, 200, 3), 240, np.uint8)
    a[40:260, 70:130] = 30                     # a dark figure on a plain backdrop
    (tmp_path / "s.png").parent.mkdir(exist_ok=True)
    Image.fromarray(a).save(tmp_path / "s.png")
    seen = []
    embed = lambda rgb, b: seen.append([float(v) for v in b]) or np.array([0.0, 1.0])
    vec, head = cli.sheet_face(tmp_path, "s.png", lambda rgb: [], embed, lambda rgb: [])
    assert vec is not None and head is not None
    x1, y1, x2, y2 = seen[0]
    assert 70 <= (x1 + x2) / 2 <= 130 and 40 <= y1 < y2 <= 130
