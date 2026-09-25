"""Clones are pairwise: two readable faces in one frame whose embeddings sit at
or above DRIFT are one man drawn twice.  Cast-vs-cast measured at most 0.20."""
from pathlib import Path

import numpy as np

from studio import identity_gate
from studio.measure import faces

FIX = Path(__file__).parent / "fixtures" / "measures"


def test_two_faces_that_read_as_one_man_are_a_clone_pair():
    vecs = np.load(FIX / "faces_pairs.npy")
    seen = [{"h": 0.3, "vec": v} for v in vecs]
    pairs = faces.clone_pairs(seen)
    assert [(p["i"], p["j"], p["by"]) for p in pairs] == [(0, 1, "facenet")]
    assert pairs[0]["cosine"] >= identity_gate.DRIFT


def test_two_different_men_are_no_pair():
    vecs = np.load(FIX / "faces_pairs.npy")
    assert faces.clone_pairs([{"h": 0.3, "vec": vecs[0]}, {"h": 0.3, "vec": vecs[2]}]) == []
