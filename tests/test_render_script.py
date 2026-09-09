"""Rendering the page: one take per beat, vertical, longer than it plays."""
from __future__ import annotations

from pathlib import Path

from scripts.trailer import render_script as render
from studio.h3 import FPS
from studio.trailer_assemble import HANDLE, HEAD_TRIM

SHOT = {"beat_id": "B03", "seconds": 3.5, "character": "char-sherlock_holmes",
        "second": None, "place": "loc-221b_baker_street", "prompt": "a document"}


def test_a_take_renders_longer_than_the_beat_plays():
    """HEAD_TRIM of reference leak at the front and a seek handle at the back
    are rendered and never cut in, so the page's seconds come out of the middle
    of a clean take."""
    frames = render.frames_for(3.5)
    assert frames / FPS >= 3.5 + HEAD_TRIM + HANDLE
    assert frames % 17 == 5                      # H3's own frame grid


def test_the_frame_is_vertical():
    """9:16 is the format: H3's native 1344x768, turned."""
    values = render.values_for(SHOT)
    assert (values["width"], values["height"]) == (768, 1344)
    assert values["height"] > values["width"]


def test_the_person_takes_the_first_slot_and_the_place_the_second():
    """<Subject 1> binds positionally to the first staged image, so the face
    must be first or every label in the prompt points at the wrong picture."""
    assert render.bound_slots(SHOT) == ["char-sherlock_holmes", "loc-221b_baker_street"]
    two = dict(SHOT, second="char-john_watson")
    assert render.bound_slots(two) == ["char-sherlock_holmes", "char-john_watson"]
    empty = dict(SHOT, character=None, second=None)
    assert render.bound_slots(empty) == ["loc-221b_baker_street"]


def test_a_beat_keeps_its_seed_across_runs():
    """A re-run reuses its renders rather than rolling new ones."""
    assert render.seed_for("B03") == render.seed_for("B03")
    assert render.seed_for("B03") != render.seed_for("B04")


def test_render_one_names_the_file_after_the_beat(tmp_path, monkeypatch):
    seen = {}

    def fake(values, bound, refs, book, dest, **kw):
        seen.update(values=values, bound=bound, dest=dest)
        return dest

    monkeypatch.setattr(render, "render_take", fake)
    out = render.render_one(SHOT, {}, Path("book"), tmp_path / "clips")
    assert out.name == "B03.mp4"
    assert seen["values"]["prompt"] == "a document"
    assert seen["bound"] == ["char-sherlock_holmes", "loc-221b_baker_street"]
