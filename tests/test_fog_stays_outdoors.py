"""A book's atmosphere fills the air outdoors only: the fireside is never fogged.

Jekyll anime chain test (2026-10-13, docs/audit/2026-10-13_jekyll_anime_chain/README.md,
"pipeline changes" #2): `ATMOSPHERE_GRID` says the fog is there "in every frame", so the
ch3 fireside study would be drawn in fog, and the H3 style line reserved "fog, damp haze"
for every take.  A setup under the sky (`Setup.outdoors`), or one whose description
names no room, keeps the atmosphere; an interior gets the line without it.  A caller
that names no setup keeps today's line byte for byte.
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
spec = importlib.util.spec_from_file_location("grids_fog", ROOT / "scripts" / "episode" / "grids.py")
grids = importlib.util.module_from_spec(spec)
sys.modules["grids_fog"] = grids
spec.loader.exec_module(grids)

STUDY = SimpleNamespace(outdoors=False, described="A warm Victorian study at night: a fireplace, two armchairs",
                        location="", light="")
STREET = SimpleNamespace(outdoors=False, described="A street corner at three in the morning, a gas lamp",
                         location="", light="")
YARD = SimpleNamespace(outdoors=True, described="The yard behind the hall, open to the sky", location="", light="")


def declare(book: Path) -> Path:
    (book / "refs").mkdir(parents=True, exist_ok=True)
    (book / "refs" / "look.json").write_text(json.dumps(
        {"look": "anime_gothic", "lead": "Anime gothic.", "atmosphere": "fog, damp haze"}), encoding="utf-8")
    return book


@pytest.fixture(autouse=True)
def clean_house():
    yield
    house_style.adopt("", "")
    house_style.adopt_atmosphere("")


def test_under_the_sky():
    assert book_look.under_sky(None) and book_look.under_sky(STREET) and book_look.under_sky(YARD)
    assert not book_look.under_sky(STUDY)


def test_the_grid_fogs_the_street_not_the_study(tmp_path):
    book = declare(tmp_path)
    assert "fog, damp haze" in book_look.grid_style(book, STREET)
    assert "fog" not in book_look.grid_style(book, STUDY)
    assert book_look.grid_style(book) == book_look.grid_style(book, STREET)


def test_the_grid_kwargs_follow_the_setup(tmp_path):
    book = declare(tmp_path)
    assert "fog" not in grids.look_for(book, STUDY)["style"]
    assert "fog" in grids.look_for(book, YARD)["style"]


def test_the_take_line_keeps_the_fog_outdoors_only():
    house_style.adopt("London, 1886", "firelight from the left, deep black")
    house_style.adopt_atmosphere("fog, damp haze")
    assert "fog" in house_style.live(STREET)
    assert "fog" not in house_style.live(STUDY)
    assert "fog" in house_style.live()
