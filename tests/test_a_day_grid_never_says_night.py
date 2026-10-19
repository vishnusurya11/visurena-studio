"""P2, experimental: an optional look.json `lead_day` leads a DAY setup's grid.

A day setup drawn on the night lead ("gaslight, deep shadow") came out dusk.  The key is never
the default: a book that does not declare it keeps every string byte for byte.
"""
import json
from pathlib import Path
from types import SimpleNamespace

from studio import book_look
from studio.panel_dq import NIGHT_WORDS

DAY = SimpleNamespace(outdoors=True, described="A square under a low grey sky, overcast", location="", light="")
NIGHT = SimpleNamespace(outdoors=True, described="A street at night, a gas lamp", location="", light="")


def declare(book: Path, **extra) -> Path:
    (book / "refs").mkdir(parents=True, exist_ok=True)
    (book / "refs" / "look.json").write_text(json.dumps(
        {"look": "photoreal", "lead": "Photo by gaslight at night. ", "by": "owner", **extra}), encoding="utf-8")
    return book


def test_a_day_grid_never_says_night(tmp_path):
    book = declare(tmp_path, lead_day="Photo in flat overcast daylight. ")
    assert not NIGHT_WORDS.search(book_look.grid_style(book, DAY))
    assert "overcast daylight" in book_look.grid_style(book, DAY)


def test_a_night_grid_keeps_the_lead(tmp_path):
    book = declare(tmp_path, lead_day="Photo in flat overcast daylight. ")
    assert "gaslight at night" in book_look.grid_style(book, NIGHT)


def test_without_the_key_nothing_changes(tmp_path):
    assert "gaslight at night" in book_look.grid_style(declare(tmp_path), DAY)


def test_no_setup_keeps_the_lead(tmp_path):
    book = declare(tmp_path, lead_day="Photo in flat overcast daylight. ")
    assert "gaslight at night" in book_look.grid_style(book)
