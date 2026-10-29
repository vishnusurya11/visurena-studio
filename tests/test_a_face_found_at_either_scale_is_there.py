"""Jekyll ep06 (2026-10-29): YuNet read 0 faces on the 1024 px panels of shots 11 and 26 -- big, clear
faces at 30-40 % of the frame -- and 0.80 / 0.87 on the same pictures at 768 px.  Switching every
panel to 768 traded failures (it lost ep06 shot 09, ep05 shot 01, ep04 shot 04), so a frame over
DETECT_MAX is read at both sizes and a face found at either is there, one box per face."""
import numpy as np

from studio import face_end


def box(score, cx, cy, h):
    return {"h": h, "clipped": False, "edges": [], "score": score, "cx": cx, "cy": cy}


def test_two_reads_of_one_face_are_one_face_with_the_better_score():
    got = face_end.merged([box(0.59, 0.5, 0.4, 0.30)], [box(0.87, 0.51, 0.41, 0.31)])
    assert len(got) == 1 and got[0]["score"] == 0.87


def test_a_face_one_size_missed_is_kept():
    got = face_end.merged([box(0.9, 0.2, 0.5, 0.1)], [box(0.9, 0.2, 0.5, 0.1), box(0.85, 0.7, 0.5, 0.1)])
    assert sorted(f["cx"] for f in got) == [0.2, 0.7]


def test_a_big_frame_is_read_at_both_sizes(monkeypatch):
    seen = []
    monkeypatch.setattr(face_end, "detect", lambda rgb: seen.append(rgb.shape[1]) or [])
    face_end.faces(np.zeros((1024, 1024, 3), np.uint8))
    assert seen == [1024, face_end.DETECT_MAX]


def test_a_frame_at_or_under_the_size_is_read_once(monkeypatch):
    seen = []
    monkeypatch.setattr(face_end, "detect", lambda rgb: seen.append(rgb.shape[1]) or [])
    face_end.faces(np.zeros((768, 768, 3), np.uint8))
    assert seen == [768]
