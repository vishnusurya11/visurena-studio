"""The identity gate the refs and clips steps climb their ladders against.

`studio.identity` knows how to score a pair; this is the part that fetches
the two shippable models once, reads a file into a vector, and turns a cast
of vectors into the list of pairs a recogniser cannot tell apart.  Sessions
are injected: no test loads a model or touches the network.
"""
from __future__ import annotations

import numpy as np
import pytest

from studio import identity_gate as gate
from studio.identity import SFACE


class TestEnsureModels:
    def test_fetches_each_missing_model_once(self, tmp_path):
        calls = []

        def fetch(url, dest):
            calls.append(url)
            dest.write_bytes(b"onnx")
        first = gate.ensure_models(tmp_path, fetch=fetch)
        gate.ensure_models(tmp_path, fetch=fetch)
        assert set(first) == {"yunet.onnx", "sface.onnx"}
        assert len(calls) == 2


class FakeDetector:
    def __init__(self, faces):
        self.faces = faces

    def setInputSize(self, size):  # the cv2 name; no snake-case alias in 4.13
        pass

    def detect(self, image):
        return 1, self.faces


class FakeInput:
    name = "data"


class FakeRecogniser:
    def get_inputs(self):
        return [FakeInput()]

    def run(self, _, feeds):
        return [np.array([[3.0, 4.0]])]


def face(width, x=10.0):
    box = [x, 10.0, width, width]
    points = [30, 40, 60, 40, 45, 55, 35, 70, 55, 70, 0.9]
    return np.array(box + points, dtype=np.float32)


class TestEmbedImage:
    def test_no_face_is_none_with_zero_pixels(self):
        sessions = gate.Sessions(FakeDetector(None), FakeRecogniser())
        vector, px = gate.embed_image(sessions, np.zeros((120, 120, 3), np.uint8))
        assert vector is None and px == 0

    def test_largest_face_is_embedded_and_unit_length(self):
        sessions = gate.Sessions(FakeDetector([face(20), face(80, x=30)]), FakeRecogniser())
        vector, px = gate.embed_image(sessions, np.zeros((200, 200, 3), np.uint8))
        assert px == 80
        assert np.isclose(np.linalg.norm(vector), 1.0)


class TestCollisions:
    def test_a_pair_above_the_same_person_line_collides(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.95, np.sqrt(1 - 0.95 ** 2)])
        c = np.array([0.0, 1.0])
        found = gate.collisions({"a": a, "b": b, "c": c}, {"a": 90, "b": 90, "c": 90})
        assert [(f["a"], f["b"]) for f in found] == [("a", "b")]
        assert found[0]["similarity"] > SFACE.same_person_at

    def test_a_face_too_small_to_read_is_never_a_collision(self):
        a = np.array([1.0, 0.0])
        found = gate.collisions({"a": a, "b": a.copy()}, {"a": 90, "b": 30})
        assert found == []

    def test_worst_against_names_the_closest_bound_face(self):
        bound = {"a": np.array([1.0, 0.0]), "b": np.array([0.0, 1.0])}
        who, score = gate.worst_against(np.array([0.6, 0.8]), bound)
        assert who == "b" and score == pytest.approx(0.8)

    def test_worst_against_an_empty_cast_is_zero(self):
        assert gate.worst_against(np.array([1.0, 0.0]), {}) == (None, 0.0)


class TestFrameTimes:
    def test_samples_avoid_the_reference_leak_at_the_head(self):
        times = gate.frame_times(7.0, count=3, head=1.0)
        assert times[0] >= 1.0 and times[-1] < 7.0 and len(times) == 3


class TestClipIdentity:
    def test_best_frame_scores_the_clip(self, tmp_path, monkeypatch):
        from PIL import Image
        vectors = iter([np.array([0.0, 1.0]), np.array([0.6, 0.8]), np.array([1.0, 0.0])])
        monkeypatch.setattr(gate, "embed_file", lambda s, p: (next(vectors), 90))

        def grab(video, when, dest):
            Image.new("RGB", (4, 4)).save(dest)
            return dest
        score, px = gate.clip_identity(None, tmp_path / "x.mp4", 7.0, np.array([1.0, 0.0]),
                                       tmp_path / "work", grab=grab)
        assert score == pytest.approx(1.0) and px == 90
