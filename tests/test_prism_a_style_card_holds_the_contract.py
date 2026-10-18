"""A Prism style card is one JSON per style; the pydantic contract refuses a card that drifts."""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from prism.catalog import SubjectSet, load_guides, load_styles, read_style, write_style
from tests.prism_fixtures import WORDS, guide, style, subjects


def test_a_card_round_trips_through_its_own_file(tmp_path):
    path = write_style(style(), tmp_path)
    assert path.name == "anime_hellsing_gothic.json"
    assert read_style(path) == style()


def test_an_id_names_its_family():
    with pytest.raises(ValidationError):
        style(sid="anime_x", family="live_action")


def test_an_id_is_snake_case_with_a_family_prefix():
    with pytest.raises(ValidationError):
        style(sid="Hellsing Gothic")


def test_style_words_name_no_filler_and_hold_a_sentence_length():
    with pytest.raises(ValidationError):
        style(style_words="anime")
    with pytest.raises(ValidationError):
        style(style_words=WORDS + " masterpiece, best quality")


def test_a_card_cites_a_source():
    with pytest.raises(ValidationError):
        style(sources=[])


def test_an_unknown_field_is_refused():
    with pytest.raises(ValidationError):
        style(colour="red")


def test_the_library_loads_every_card_sorted(tmp_path):
    write_style(style("anime_b", "B"), tmp_path)
    write_style(style("anime_a", "A"), tmp_path)
    assert [s.id for s in load_styles(tmp_path)] == ["anime_a", "anime_b"]


def test_a_guide_template_must_hold_the_style_and_the_subject():
    with pytest.raises(ValidationError):
        guide(template="{style} {camera}")


def test_guides_load_by_id(tmp_path):
    (tmp_path / "krea2.json").write_text(guide().model_dump_json(), encoding="utf-8")
    assert list(load_guides(tmp_path)) == ["krea2"]


def test_a_subject_set_is_one_character_one_location_three_scenes():
    rows = subjects().model_dump()
    rows["subjects"][1]["kind"] = "scene"
    with pytest.raises(ValidationError):
        SubjectSet(**rows)


def test_subject_ids_are_unique():
    rows = subjects().model_dump()
    rows["subjects"][4]["id"] = "diary"
    with pytest.raises(ValidationError):
        SubjectSet(**json.loads(json.dumps(rows)))


def test_a_template_may_name_only_known_parts():
    with pytest.raises(ValidationError):
        guide(template="{style} {subject} {camera} {mood}")
    assert guide(template="{style} {subject} {camera} {recap}")


def test_a_camera_line_names_no_lens_millimetres():
    rows = subjects().model_dump()
    rows["subjects"][0]["camera"] = "Close-up, 85mm lens."
    with pytest.raises(ValidationError):
        SubjectSet(**rows)
