"""Lettering is a recognised string, judged: a cast id printed into a picture is
a leak, a plan word is the prompt bleeding through, anything else is
gibberish.  An insert excuses gibberish and nothing else."""
import json
from pathlib import Path

from studio.measure import ocr

FIX = Path(__file__).parent / "fixtures" / "measures"
CAST = ["elias_marrow", "the_widow"]
PLAN = "a lantern on the sill, the widow at the door"


def _rows():
    return ocr.rows(json.load((FIX / "ocr_cast_id.json").open()))


def test_a_cast_id_in_the_lettering_is_a_leak():
    kinds = {r["text"]: r["kind"] for r in ocr.lettering(_rows(), CAST, PLAN, width=512)}
    assert kinds == {"MARROW": "cast_id", "lantern": "plan_word", "QXZVB": "gibberish"}


def test_an_insert_excuses_gibberish_but_not_a_leak():
    kinds = [r["kind"] for r in ocr.lettering(_rows(), CAST, PLAN, insert=True, width=512)]
    assert kinds == ["cast_id", "plan_word"]


def test_a_short_id_token_does_not_match_inside_a_word():
    assert ocr.kind("thermos", ocr.cast_tokens(["the_widow"]), set()) == "gibberish"
