"""Under READABLE an embedding is noise (faces at 8-10 % of frame height scored
0.46-0.72 against their own sheet).  A small pair is compared as pictures: the
64x64 zero-mean cosine of the two crops, and identical renders score >= 0.9."""
import numpy as np
from PIL import Image, ImageDraw

from studio import identity_gate
from studio.measure import faces


def _crop(seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    im = Image.fromarray(rng.integers(60, 200, (24, 24, 3), dtype=np.uint8)).resize((40, 40))
    ImageDraw.Draw(im).ellipse((8, 6, 32, 34), outline=(240, 230, 210), width=3)
    return im


def _small(seed: int) -> dict:
    return {"h": identity_gate.READABLE - 0.05, "sig": faces.structure(_crop(seed))}


def test_a_small_face_uses_the_structural_prefilter():
    pairs = faces.clone_pairs([_small(1), _small(1)])
    assert [(p["i"], p["j"], p["by"]) for p in pairs] == [(0, 1, "structure")]
    assert pairs[0]["cosine"] >= faces.STRUCTURAL


def test_two_different_small_faces_are_no_pair():
    assert faces.clone_pairs([_small(1), _small(2)]) == []


def test_a_readable_pair_is_never_judged_by_structure():
    rng = np.random.default_rng(3)
    v = rng.standard_normal(512)
    v /= np.linalg.norm(v)
    big = {"h": 0.3, "vec": v, "sig": faces.structure(_crop(1))}
    same_look = {"h": 0.3, "vec": -v, "sig": faces.structure(_crop(1))}
    assert faces.clone_pairs([big, same_look]) == []
