"""A model's writer output ({subjects: {id: form}, styles: {id: {style, recap}}}) is filed on the
cards as models.<model> and on the subject set as forms.<model>; a part naming nothing held is refused."""
from __future__ import annotations

import pytest

from prism.catalog import load_styles, load_subjects, write_style
from prism.writer import apply_writing
from tests.prism_fixtures import style, subjects


def library(tmp_path):
    styles = tmp_path / "styles"
    styles.mkdir()
    write_style(style(), styles)
    path = tmp_path / "subjects.json"
    path.write_text(subjects().model_dump_json(), encoding="utf-8")
    return styles, path


def writing(**over):
    said = {"model": "krea2", "subjects": {s.id: f"Form of {s.id}." for s in subjects().subjects},
            "styles": {"anime_hellsing_gothic": {"style": "Gothic cel block.", "recap": "Rendered as gothic cel."}}}
    return {**said, **over}


def test_the_parts_land_on_the_card_and_the_subjects(tmp_path):
    styles, path = library(tmp_path)
    apply_writing(writing(), styles, path)
    card = load_styles(styles)[0]
    assert card.models["krea2"].style == "Gothic cel block." and card.models["krea2"].recap == "Rendered as gothic cel."
    assert load_subjects(path).subjects[2].forms == {"krea2": "Form of arrival."}


def test_a_part_for_an_unheld_style_is_refused_and_nothing_is_filed(tmp_path):
    styles, path = library(tmp_path)
    with pytest.raises(KeyError):
        apply_writing(writing(styles={"anime_nope": {"style": "x", "recap": "y"}}), styles, path)
    assert load_styles(styles)[0].models == {}


def test_a_writing_missing_a_subject_is_refused(tmp_path):
    styles, path = library(tmp_path)
    with pytest.raises(KeyError):
        apply_writing(writing(subjects={"count": "Only one."}), styles, path)
