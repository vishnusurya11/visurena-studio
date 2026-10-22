"""A figure under haze is drawn solid (Jekyll ep01 shot 2, 2026-10-18).

The grid's atmosphere sentence let the drawer fog the BODY into the street; the hand cure was a
plan edit ("coat solid to the BOTTOM edge, haze far behind").  The single ATMOSPHERE_GRID
constant now says the haze hangs behind the figures; a shot that dissolves, fades or
transforms is exempt; an interior and a book with no atmosphere are unchanged.
"""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from studio import book_look

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("grids_solid", ROOT / "scripts" / "episode" / "grids.py")
grids = importlib.util.module_from_spec(spec)
sys.modules["grids_solid"] = grids
spec.loader.exec_module(grids)

OLD_SENTENCE = " The air holds fog, damp haze in every frame, softening the far distance."   # A21's wording
SOLID = (" The haze hangs behind the figures; every figure stays solid, sharp-edged and opaque"
         " to the frame edge.")
STREET = SimpleNamespace(outdoors=True, described="A street at night, a gas lamp", location="", light="")
STUDY = SimpleNamespace(outdoors=False, described="A warm study, a fireplace", location="", light="")


def declare(book: Path, **extra) -> Path:
    (book / "refs").mkdir(parents=True, exist_ok=True)
    (book / "refs" / "look.json").write_text(json.dumps(
        {"look": "photoreal", "lead": "Photo. ", "by": "owner", **extra}), encoding="utf-8")
    return book


def test_the_old_sentence_differs_by_exactly_the_solid_clause(tmp_path):
    book = declare(tmp_path, atmosphere="fog, damp haze")
    old = book_look.PHOTO_GRID.format(lead="Photo.") + OLD_SENTENCE
    assert book_look.grid_style(book, STREET) == old + SOLID


def test_an_interior_is_unchanged(tmp_path):
    book = declare(tmp_path, atmosphere="fog, damp haze")
    assert book_look.grid_style(book, STUDY) == book_look.PHOTO_GRID.format(lead="Photo.")


def test_a_book_with_no_atmosphere_is_unchanged(tmp_path):
    assert book_look.grid_style(declare(tmp_path), STREET) == book_look.PHOTO_GRID.format(lead="Photo.")


def test_a_dissolving_shot_is_exempt(tmp_path):
    book = declare(tmp_path, atmosphere="fog, damp haze")
    said = book_look.grid_style(book, STREET, "Hyde's body dissolves into the fog")
    assert said.endswith(OLD_SENTENCE) and "solid" not in said


def test_the_exemption_words():
    assert all(book_look.dissolving(p) for p in ("fades to white", "He transforms", "it dissolved"))
    assert not book_look.dissolving("Lanyon stands in the fog, coat solid")


def test_the_grid_look_carries_the_prose(tmp_path):
    book = declare(tmp_path, atmosphere="fog, damp haze")
    assert "solid" in grids.look_for(book, STREET)["style"]
    assert "solid" not in grids.look_for(book, STREET, "the shape fades away")["style"]
