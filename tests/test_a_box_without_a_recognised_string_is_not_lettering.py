"""CRAFT hallucinates boxes on letter-like shapes.  A box counts only with a
recognised string: two or more letters, recogniser confidence at MIN_CONF, and
a box at least MIN_HEIGHT of the picture's width tall."""
import json
from pathlib import Path

from studio.measure import ocr

FIX = Path(__file__).parent / "fixtures" / "measures"


def test_a_box_without_a_recognised_string_is_not_lettering():
    rows = ocr.rows(json.load((FIX / "ocr_no_string.json").open()))
    assert ocr.recognised(rows, width=512) == []
    assert ocr.lettering(rows, ["someone"], "some plan", width=512) == []


def test_a_recognised_string_is_kept():
    rows = ocr.rows(json.load((FIX / "ocr_cast_id.json").open()))
    assert [r["text"] for r in ocr.recognised(rows, width=512)] == ["MARROW", "lantern", "QXZVB"]


def test_the_reader_is_injected_never_built_here():
    asked = []
    text = ocr.read("panel.png", reader=lambda path: asked.append(path) or [])
    assert text == [] and asked == ["panel.png"]
