"""A Prism prompt is the model's template over the style, the subject and the camera: across
styles only the style words change, so the board compares looks and nothing else."""
from __future__ import annotations

import json

from prism.catalog import ModelWords
from prism.compose import compose, style_text, too_long, writer_messages
from tests.prism_fixtures import WORDS, guide, style, subjects


def test_the_shared_style_words_serve_a_model_without_its_own():
    assert style_text(style(), "krea2") == WORDS


def test_a_models_own_words_outrank_the_shared():
    card = style(models={"krea2": ModelWords(style="Own krea words.")})
    assert style_text(card, "krea2") == "Own krea words."
    assert style_text(card, "flux3_klein") == WORDS


def test_compose_follows_the_guides_order():
    subject = subjects().subjects[0]
    said = compose(style(), guide(template="{camera} {subject} {style}"), subject)
    assert said.startswith("Wide shot. The count.") and said.endswith(WORDS)


def test_two_styles_share_every_word_but_their_own():
    subject, g = subjects().subjects[2], guide()
    one = compose(style(), g, subject)
    two = compose(style("anime_b", "B", style_words=WORDS.replace("Hellsing", "Berserk")), g, subject)
    assert one.replace("Hellsing", "Berserk") == two


def test_a_prompt_over_the_guides_ceiling_is_flagged():
    subject = subjects().subjects[0]
    assert not too_long(compose(style(), guide(), subject), guide())
    assert too_long(compose(style(), guide(max_words=10), subject), guide(max_words=10))


def test_the_writer_is_told_the_guides_system_prompt_and_the_card():
    system, user = writer_messages(style(), guide(system_prompt="Be Krea."), subjects().subjects[3])
    asked = json.loads(user)
    assert system == "Be Krea."
    assert asked["style"]["id"] == "anime_hellsing_gothic" and asked["camera"] == "Wide shot."
    assert asked["subject"] == "The diary."


def test_a_models_recap_closes_the_prompt_when_its_template_asks():
    card = style(models={"krea2": ModelWords(style="Cel anime of:", recap="Rendered throughout as flat cel.")})
    said = compose(card, guide(template="{style} {subject} {camera} {recap}"), subjects().subjects[0])
    assert said == "Cel anime of: The count. Wide shot. Rendered throughout as flat cel."


def test_a_card_without_a_recap_leaves_no_gap():
    said = compose(style(), guide(template="{style} {subject} {camera} {recap}"), subjects().subjects[0])
    assert said.endswith("Wide shot.")


def test_a_subjects_own_form_for_the_model_replaces_its_prose_and_carries_its_camera():
    subject = subjects().subjects[0].model_copy(update={"forms": {"krea2": "A long Krea form, framed wide."}})
    said = compose(style(), guide(template="{style} {subject} {camera} {recap}"), subject)
    assert said == WORDS + " A long Krea form, framed wide."
    assert compose(style(), guide("flux3_klein"), subject).endswith("The count. Wide shot.")
