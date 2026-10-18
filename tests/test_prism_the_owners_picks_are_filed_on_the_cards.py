"""The board's "Copy picks" JSON ({style_id: model_id}) is filed on each card as its verdict."""
from __future__ import annotations

import pytest

from prism.catalog import load_styles, write_style
from prism.verdicts import apply_picks
from tests.prism_fixtures import style


def test_a_pick_sets_the_best_model_and_marks_the_card_tested(tmp_path):
    write_style(style(), tmp_path)
    assert apply_picks({"anime_hellsing_gothic": "krea2"}, tmp_path, {"krea2"}) == ["anime_hellsing_gothic"]
    card = load_styles(tmp_path)[0]
    assert card.verdict.best_model == "krea2" and card.verdict.status == "tested"


def test_a_pick_of_an_unknown_style_or_model_is_refused(tmp_path):
    write_style(style(), tmp_path)
    with pytest.raises(KeyError):
        apply_picks({"anime_nope": "krea2"}, tmp_path, {"krea2"})
    with pytest.raises(KeyError):
        apply_picks({"anime_hellsing_gothic": "sdxl"}, tmp_path, {"krea2"})
