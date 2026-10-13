"""A book declares its ATMOSPHERE once, and it reaches the grid and the take.

Jekyll ep01 (2026-10-13, docs/audit/2026-10-13_jekyll_ep01_review/LOOK.md cause 2):
the owner-approved style A is "fog, gaslight, deep shadow" and none of the 27
shots had fog.  The H3 style line's 16-word wall cut it ("Photoreal live-action,
The Sunday walks of London, 1886, gas, black shadows, 35 mm film grain"), and the
photoreal negative banned "blurry", which Qwen reads against haze and depth.

So `refs/look.json` carries `atmosphere`; the grid's photoreal style line says
it, the take's style line reserves its words before the light gets any, and a
fog book's negative asks for a sharp subject instead of banning blur.  A book
with no declaration -- WotW -- keeps every string byte for byte.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from studio import book_look, house_style

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("grids_atmos", ROOT / "scripts" / "episode" / "grids.py")
grids = importlib.util.module_from_spec(spec)
sys.modules["grids_atmos"] = grids
spec.loader.exec_module(grids)

LEAD = "Cinematic live-action photograph, photoreal. "


def declare(book: Path, **extra) -> Path:
    (book / "refs").mkdir(parents=True, exist_ok=True)
    (book / "refs" / "look.json").write_text(json.dumps(
        {"look": "photoreal", "lead": LEAD, "tail": " No text.", "by": "owner", **extra}), encoding="utf-8")
    return book


@pytest.fixture(autouse=True)
def clean_house():
    yield
    house_style.adopt("", "")
    house_style.adopt_look("")
    house_style.adopt_atmosphere("")
    house_style.adopt_places({})


def test_no_declaration_declares_no_atmosphere(tmp_path):
    assert book_look.atmosphere(tmp_path) == ""
    assert book_look.atmosphere(declare(tmp_path)) == ""


def test_the_book_files_its_atmosphere(tmp_path):
    assert book_look.atmosphere(declare(tmp_path, atmosphere="fog, damp haze.")) == "fog, damp haze"


def test_the_photoreal_grid_line_carries_the_atmosphere(tmp_path):
    said = book_look.grid_style(declare(tmp_path, atmosphere="fog, damp haze")).format(n=2)
    assert "fog, damp haze" in said and "<image2>" in said


def test_a_photoreal_grid_line_with_no_atmosphere_is_unchanged(tmp_path):
    assert book_look.grid_style(declare(tmp_path)) == book_look.PHOTO_GRID.format(lead=LEAD.strip())


def test_a_fog_book_stops_banning_blur(tmp_path):
    said = grids.negative_for(declare(tmp_path, atmosphere="fog, damp haze"))
    assert "blurry" not in said.split(", ")
    assert "out of focus subject" in said and "motion smear" in said


def test_a_clear_photoreal_book_keeps_its_negative(tmp_path):
    assert grids.negative_for(declare(tmp_path)) == grids.PHOTO_NEGATIVE


def test_the_house_negative_is_untouched(tmp_path):
    assert grids.negative_for(tmp_path) == grids.NEGATIVE


def test_the_take_line_reserves_the_atmosphere():
    house_style.adopt("London, 1886", "cold side light from the left, coal-black shadows")
    house_style.adopt_atmosphere("fog, damp haze")
    said = house_style.live()
    assert "fog, damp haze" in said
    assert len(said.split()) <= house_style.MAX_STYLE_WORDS, said


def test_a_long_place_gives_way_before_the_atmosphere():
    """T13's place: 'The Sunday walks of London, 1886' took the wall and fog fell off."""
    house_style.adopt("London, 1886", "cold side light from the left, coal-black shadows")
    house_style.adopt_places({"walks": "The Sunday walks of London"})
    house_style.adopt_atmosphere("fog, damp haze")
    setup = SimpleNamespace(location="walks", described="Grey daylight from the left, deep shadow.")
    said = house_style.live(setup)
    assert "fog, damp haze" in said
    assert len(said.split()) <= house_style.MAX_STYLE_WORDS, said


def test_no_atmosphere_leaves_the_take_line_byte_for_byte():
    house_style.adopt("Surrey, 1894", "low sun from the left, black shadow")
    before = house_style.LIVE.format(where="Surrey, 1894", light="low sun from the left, black shadow")
    assert house_style.live() == before


def test_the_take_run_adopts_the_book_atmosphere(tmp_path, monkeypatch):
    found = importlib.util.spec_from_file_location("takes_atmos", ROOT / "scripts" / "episode" / "takes_r2v.py")
    takes = importlib.util.module_from_spec(found)
    sys.modules["takes_atmos"] = takes
    found.loader.exec_module(takes)
    monkeypatch.setattr(takes, "place_names", lambda book: {})
    plan = SimpleNamespace(aspect="1:1", where="London, 1886", light="gaslight from the left, deep shadow", look="")
    takes.adopt_canon(declare(tmp_path, atmosphere="fog, damp haze"), plan)
    assert "fog, damp haze" in house_style.live()
    takes.adopt_canon(tmp_path / "none", plan)
    assert "fog" not in house_style.live()


# ---- any declared look, not photoreal alone (coordinator 2026-10-13: Jekyll may go anime gothic) ----

ANIME_LEAD = "Anime gothic: inked line work, cel shading, muted palette. "


def declare_drawn(book: Path, **extra) -> Path:
    (book / "refs").mkdir(parents=True, exist_ok=True)
    (book / "refs" / "look.json").write_text(json.dumps(
        {"look": "anime_gothic", "lead": ANIME_LEAD, "by": "owner", **extra}), encoding="utf-8")
    return book


def test_a_drawn_look_gets_its_own_grid_line_and_atmosphere(tmp_path):
    said = book_look.grid_style(declare_drawn(tmp_path, atmosphere="fog, damp haze")).format(n=2)
    assert ANIME_LEAD.strip() in said and "<image2>" in said and "fog, damp haze" in said
    assert "PHOTOGRAPHIC" not in said and "photoreal" not in said.lower().replace(ANIME_LEAD.lower(), "")


def test_a_drawn_look_is_an_illustration_and_bans_the_photograph(tmp_path):
    book = declare_drawn(tmp_path, atmosphere="fog")
    assert grids.look_for(book)["medium"] == "illustration"
    said = grids.negative_for(book)
    assert "photographic" in said and "narrator" not in said and "blurry" not in said.split(", ")


def test_a_drawn_look_names_the_take_line(tmp_path):
    assert book_look.plan_look(declare_drawn(tmp_path), "Angular stylised 3D animation") == "Anime gothic"
    assert book_look.plan_look(declare_drawn(tmp_path, take="Gothic anime film"), "x") == "Gothic anime film"
