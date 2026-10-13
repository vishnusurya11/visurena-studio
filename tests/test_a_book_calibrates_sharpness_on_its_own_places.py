"""Jekyll ep01 (2026-10-13): panel_check opened WotW's horsell_common wides
as its sharpness control in a book that has none, and crashed. A book with no
house control calibrates on its own place pictures, median per hour."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("panel_check_ctl", ROOT / "scripts" / "episode" / "panel_check.py")
pc = importlib.util.module_from_spec(spec)
sys.modules["panel_check_ctl"] = pc
spec.loader.exec_module(pc)


def picture(path: Path, value: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    a = np.zeros((32, 32, 3), np.uint8)
    a[:, 16:] = value
    Image.fromarray(a).save(path)


def test_a_book_without_the_house_control_uses_its_own_places(tmp_path):
    loc = tmp_path / "refs" / "locations"
    picture(loc / "door" / "wide_establishing.png", 200)
    picture(loc / "street" / "night_street.png", 100)
    got = pc.controls(tmp_path)
    assert set(got) == {"day", "night"} and got["day"] > got["night"] > 0


def test_a_book_with_no_night_picture_uses_its_day_for_night(tmp_path):
    picture(tmp_path / "refs" / "locations" / "door" / "wide_establishing.png", 200)
    got = pc.controls(tmp_path)
    assert got["night"] == got["day"]


def test_the_house_control_still_wins_where_it_exists(tmp_path):
    folder = tmp_path / "refs" / "locations" / pc.CONTROL_PLACE
    for name in pc.CONTROLS.values():
        picture(folder / name, 255)
    picture(tmp_path / "refs" / "locations" / "other" / "wide_establishing.png", 10)
    got = pc.controls(tmp_path)
    assert got["day"] == got["night"]
