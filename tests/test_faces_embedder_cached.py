"""The facenet/MTCNN weights load once per process and device."""
from __future__ import annotations

from studio.measure import faces


def test_two_embedder_calls_build_mtcnn_once(monkeypatch):
    built = []
    monkeypatch.setattr(faces, "build_embedder", lambda device: built.append(device) or object())
    monkeypatch.setattr(faces, "EMBEDDERS", {})
    a, b = faces.embedder("cpu"), faces.embedder("cpu")
    assert a is b and built == ["cpu"]
    faces.embedder("cuda")
    assert built == ["cpu", "cuda"]
