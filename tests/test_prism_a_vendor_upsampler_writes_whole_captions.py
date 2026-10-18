"""A model fed by its vendor's prompt upsampler (FLUX 3 Klein's PUP) gets one whole caption per
(style, subject): the request is the card's style words + the subject + its camera, as a person
would type it; the upsampler's caption is filed on the card and rendered as written."""
from __future__ import annotations

from prism.catalog import ModelWords, load_styles, write_style
from prism.compose import compose
from prism.plan import jobs
from prism.upsample import file_captions, request, requests
from tests.prism_fixtures import WORDS, guide, style, subjects


def test_the_request_is_style_words_then_subject_then_camera():
    said = request(style(), subjects().subjects[0])
    assert said == f"{WORDS} The count. Wide shot."


def test_requests_cover_only_the_asked_styles():
    rows = requests([style(), style("anime_b", "B")], subjects(), ["anime_b"])
    assert {r["style"] for r in rows} == {"anime_b"} and len(rows) == 5


def test_a_whole_caption_is_rendered_as_written():
    card = style(models={"flux3_klein_pup": ModelWords(style="", captions={"count": "The PUP caption."})})
    assert compose(card, guide("flux3_klein_pup"), subjects().subjects[0]) == "The PUP caption."


def test_a_captions_only_model_plans_only_what_has_a_caption():
    card = style(models={"pup": ModelWords(style="", captions={"count": "c", "chase": "d"})})
    planned = jobs([card, style("anime_b", "B")], subjects(), {"pup": guide("pup", captions_only=True)})
    assert [(j.style, j.subject) for j in planned] == [("anime_hellsing_gothic", "count"),
                                                        ("anime_hellsing_gothic", "chase")]


def test_captions_are_filed_on_their_cards(tmp_path):
    write_style(style(), tmp_path)
    file_captions([{"style": "anime_hellsing_gothic", "subject": "count", "caption": "Cap."}], tmp_path, "pup")
    assert load_styles(tmp_path)[0].models["pup"].captions == {"count": "Cap."}
