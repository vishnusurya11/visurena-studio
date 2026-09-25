"""The style outlier needs an embedding node the installed ComfyUI does not have.
Until it does, a style read that cannot run is a missing measure for that
sheet -- the judge completes, signs on the calibrated rows, and raises no
style fault -- never a crash of the LOOK gate (first real run)."""
from __future__ import annotations

from studio.judges import look


def test_a_rejected_embedding_workflow_is_a_missing_measure(tmp_path):
    def rejected(picture):
        raise RuntimeError("ComfyUI rejected the workflow: missing_node_type")

    assert look.style_of(tmp_path / "x.png", lambda name: rejected) is None


def test_a_dead_ask_is_a_missing_measure(tmp_path):
    def dead(picture):
        raise TimeoutError("still running after 900 s")

    assert look.style_of(tmp_path / "x.png", lambda name: dead) is None


def test_a_vector_is_kept(tmp_path):
    got = look.style_of(tmp_path / "x.png", lambda name: (lambda p: [0.1, 0.2]))
    assert list(got) == [0.1, 0.2]
