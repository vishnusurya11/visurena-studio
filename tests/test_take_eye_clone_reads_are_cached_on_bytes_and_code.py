"""Jekyll ep07 retro S9: the take eye re-read facenet clones over every kept take on each re-sign
(about 41 s a rerun on ep07, where relaunches re-signed unchanged takes).  The clone pairs depend
only on the take's bytes and the clone-reading code, so they are cached beside the take on both;
a moved judge re-reads (brick 4: a verdict signed by old code is not current)."""
from __future__ import annotations

from studio.judges import take_eye

PAIRS = [{"i": 0, "j": 1, "cosine": 0.81, "by": "facenet", "frame": 3, "t": 2.1}]


def counting():
    calls = []

    def clones(take):
        calls.append(take.name)
        return PAIRS
    return clones, calls


def test_the_same_bytes_under_the_same_code_are_read_once(tmp_path):
    take = tmp_path / "T10.mp4"
    take.write_bytes(b"take bytes")
    clones, calls = counting()
    read = take_eye.cached_clones(clones, code="c1")
    assert read(take) == PAIRS and read(take) == PAIRS
    assert calls == ["T10.mp4"]


def test_new_bytes_are_read_again(tmp_path):
    take = tmp_path / "T10.mp4"
    take.write_bytes(b"take bytes")
    clones, calls = counting()
    take_eye.cached_clones(clones, code="c1")(take)
    take.write_bytes(b"a retaken T10")
    take_eye.cached_clones(clones, code="c1")(take)
    assert len(calls) == 2


def test_moved_clone_code_is_read_again(tmp_path):
    take = tmp_path / "T10.mp4"
    take.write_bytes(b"take bytes")
    clones, calls = counting()
    take_eye.cached_clones(clones, code="c1")(take)
    take_eye.cached_clones(clones, code="c2")(take)
    assert len(calls) == 2


def test_cannot_tell_is_never_cached(tmp_path):
    take = tmp_path / "T10.mp4"
    take.write_bytes(b"take bytes")
    calls = []
    read = take_eye.cached_clones(lambda t: calls.append(1), code="c1")
    assert read(take) is None and read(take) is None and len(calls) == 2


def test_the_clone_code_hash_names_its_files():
    assert len(take_eye.clone_code()) == 8
