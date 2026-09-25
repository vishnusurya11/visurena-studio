"""The DINO embedder sends its picture to the `image_embed` workflow's own input.

ep12, 2026-09-25: take_leak.dino_embed sent it as 'image'; the workflow's one
inject point is 'image_1', so comfy.apply_inject raised KeyError and take_dq
died on the first take of the first episode through the take measures.
"""
import numpy as np

from studio import comfy, take_leak


def test_the_embedder_sends_image_1(monkeypatch):
    sent = {}
    monkeypatch.setattr(comfy, "stage_image", lambda path: "staged.png")

    def run_text(name, values, timeout=600.0):
        sent.update(values)
        return "[0.1, 0.2, 0.3]"

    monkeypatch.setattr(comfy, "run_text", run_text)
    vec = take_leak.dino_embed(np.zeros((8, 8, 3), dtype=np.uint8))
    assert "image_1" in sent and "image" not in sent
    assert vec.shape == (3,)
