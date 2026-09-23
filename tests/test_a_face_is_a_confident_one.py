"""A face counts only when the detector is sure of it.

MEASURED 2026-09-22 on every cast-sized detection in the ep06-09 panels (60):
51 scored 0.9 or more, and every real frontal face scored 0.86 or more. The
misfires were smoke (0.51), steam round a gas lamp (0.53 and 0.78), and back-of-
head or silhouette shapes (0.56-0.68), which are not faces. With no floor,
the smoke behind ep09's hussar counted as a second person and failed his
close-up for people and clones.
"""
from studio.panel_dq import FACE_SCORE, confident_faces


def face(h, score):
    return {"h": h, "score": score}


def test_the_floor_sits_between_the_misfires_and_the_real_faces():
    assert 0.78 < FACE_SCORE <= 0.86


def test_smoke_and_steam_do_not_count():
    assert confident_faces([face(0.2, 0.92), face(0.15, 0.51), face(0.1, 0.78)]) == [0.2]


def test_every_real_face_counts():
    assert confident_faces([face(0.3, 0.86), face(0.2, 0.99)]) == [0.2, 0.3]


def test_nothing_found_is_nothing():
    assert confident_faces([]) == []
    assert confident_faces(None) == []
