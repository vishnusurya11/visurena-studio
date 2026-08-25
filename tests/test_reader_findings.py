"""Regressions from three professional script critiques, 2026-08-25.

Three readers — a studio story analyst, an adaptation specialist, and a script
supervisor — read the first generated screenplay independently. Everything in this file
is a defect all or most of them hit, reduced to a mechanical check.

The script supervisor's process finding is the one that stings and it is the reason this
file exists: `qc_report.json` logged 121 guard findings naming these exact problems, and
the document rendered and shipped anyway. "A REVIEW verdict that never gates the render
is not a QC step."
"""

from __future__ import annotations

import pytest

from studio import fountain, quotes
from studio.screenplay_spec import Scene, ScriptElement, Slug

SLUG = Slug(int_ext="INT", location_id="x", location_name="221B Baker Street",
            time="DAY", text="INT. 221B BAKER STREET - DAY")


def _scene(elements, number=1):
    return Scene(number=number, beat_id="b1", slug=SLUG, elements=elements)


# --- the title page, which I broke with scene numbering ----------------------------

def test_title_block_is_terminated_by_a_blank_line():
    """Without it Fountain swallows the title block AND the first scene heading as
    Action, so page 1 printed 'Title: ...', 'Author:' and a literal '.1.' as body."""
    text = fountain.render([_scene([])], {}, title="A Study in Scarlet", author="Doyle")
    assert "\n\n.1. INT." in text or "\n\n1. INT." in text


def test_an_empty_author_field_is_omitted_not_printed_blank():
    text = fountain.render([_scene([])], {}, title="A Study in Scarlet", author="")
    assert "Author:" not in text


def _body_text(text: str) -> str:
    import io
    from screenplain.parsers.fountain import parse
    return " ".join(str(line) for obj in parse(io.StringIO(text))
                    for line in getattr(obj, "lines", []))


def test_the_title_page_actually_parses_as_a_title_page():
    """Do the title lines stay OUT of the body? When the block failed to terminate,
    "Title:", "Author:" and the first scene heading all arrived as action on page 1."""
    text = fountain.render([_scene([])], {}, title="A Study in Scarlet", author="Doyle")
    body = _body_text(text)
    assert "A Study in Scarlet" not in body and "Doyle" not in body


def test_a_titleless_render_still_parses_its_first_heading():
    assert "INT. 221B BAKER STREET" in _body_text(fountain.render([_scene([])], {}))


# --- dialogue must contain only what the actor says --------------------------------

def test_an_attribution_tag_is_stripped_from_a_quote():
    """'"It is so," answered John Ferrier.' is a line an actor reads aloud verbatim."""
    assert quotes.clean('"It is so," answered John Ferrier.') == "It is so."


def test_narration_between_two_quoted_halves_is_removed():
    raw = ('"Kiss it and make it well," she said, with perfect gravity, showing the '
           'injured part up to him. "That\'s what mother used to do."')
    got = quotes.clean(raw)
    assert "she said" not in got and "perfect gravity" not in got
    assert "Kiss it and make it well" in got and "mother used to do" in got


def test_a_leading_attribution_is_removed():
    raw = '"Brother Ferrier," he said, taking a seat, "the true believers have been good friends."'
    got = quotes.clean(raw)
    assert got.startswith("Brother Ferrier") and "he said" not in got


def test_a_dangling_attribution_comma_becomes_a_full_stop():
    """30 speeches ended on a comma with nothing after it — the amputated 'said Holmes'."""
    assert quotes.clean("No data yet,") == "No data yet."


def test_a_dangling_comma_after_a_question_is_left_alone():
    assert quotes.clean("Is it not obvious?") == "Is it not obvious?"


def test_curly_quotes_are_stripped_from_the_ends():
    assert quotes.clean("\u201cCommonplace,\u201d") == "Commonplace."


def test_clean_leaves_an_already_clean_line_untouched():
    line = "You have been in Afghanistan, I perceive."
    assert quotes.clean(line) == line


def test_clean_never_returns_empty_for_a_nonempty_input():
    """Losing a line is worse than a messy line."""
    for raw in ('"he said."', '",', '"", said he'):
        assert quotes.clean(raw) or raw


# --- character cues: one character, one cue, and no sentinels ----------------------

SENTINELS = ("_unknowable", "_group", "_unknown", "_narrator")


def test_extraction_sentinels_are_never_characters():
    """`_unknowable` is extraction saying it could not tell who spoke. It reached the
    printed page as a speaking character and would have gone on the call sheet."""
    from scripts.screenplay.step_03_draft import canonical_cue
    registry = [{"id": "john_watson", "name": "Dr. John Watson", "aliases": []}]
    for sentinel in SENTINELS:
        assert canonical_cue(sentinel, registry) is None


def test_a_bare_surname_cue_resolves_to_the_canonical_id():
    """'Watson', 'John Watson' and 'DR. JOHN WATSON' were three cast members."""
    from scripts.screenplay.step_03_draft import canonical_cue
    registry = [{"id": "john_watson", "name": "Dr. John Watson", "aliases": ["I"]},
                {"id": "sherlock_holmes", "name": "Sherlock Holmes", "aliases": []}]
    for form in ("Watson", "John Watson", "Dr. John Watson", "john_watson"):
        assert canonical_cue(form, registry) == "john_watson", form


def test_a_plural_collective_is_not_a_speaker():
    """`THE MORMONS` delivered a line. Crowds do not speak in unison."""
    from scripts.screenplay.step_03_draft import canonical_cue
    assert canonical_cue("The Mormons", []) is None


def test_a_cue_that_states_a_plot_fact_is_rejected():
    """`THE RETIRED SERGEANT OF MARINES` printed the answer to Holmes's deduction in
    the left margin of the page on which he performs it."""
    from scripts.screenplay.step_03_draft import canonical_cue
    assert canonical_cue("The retired sergeant of Marines", []) is None


def test_an_ordinary_walk_on_cue_survives():
    """A porter with a line is still a line. Only sentinels and collectives go."""
    from scripts.screenplay.step_03_draft import canonical_cue
    assert canonical_cue("Wiggins", []) == "Wiggins"


# --- repairing scenes already paid for ---------------------------------------------

def test_repair_cleans_a_speech_carrying_its_own_attribution():
    from scripts.screenplay.step_03_draft import repair_scene
    scene = _scene([ScriptElement(kind="dialogue", character="john_ferrier",
                                  text='"It is so," answered John Ferrier.')])
    repair_scene(scene, [{"id": "john_ferrier", "name": "John Ferrier", "aliases": []}])
    assert scene.elements[0].text == "It is so."


def test_repair_resolves_a_bare_surname_cue():
    from scripts.screenplay.step_03_draft import repair_scene
    scene = _scene([ScriptElement(kind="dialogue", character="Watson", text="Quite.")])
    repair_scene(scene, [{"id": "john_watson", "name": "Dr. John Watson", "aliases": []}])
    assert scene.elements[0].character == "john_watson"


def test_repair_turns_a_sentinel_speech_into_action():
    """`_unknowable` was text pinned to a bedspread, printed as a character's line.
    It is an insert, not a speaker — and dropping the line would lose the words."""
    from scripts.screenplay.step_03_draft import repair_scene
    scene = _scene([ScriptElement(kind="dialogue", character="_unknowable",
                                  text="Twenty-nine days are given you.")])
    repair_scene(scene, [])
    assert scene.elements[0].kind == "action"
    assert "Twenty-nine days" in scene.elements[0].text


def test_repair_recomputes_the_speaking_list():
    from scripts.screenplay.step_03_draft import repair_scene
    scene = _scene([ScriptElement(kind="dialogue", character="Watson", text="Quite.")])
    scene.speaking = ["Watson"]
    repair_scene(scene, [{"id": "john_watson", "name": "Dr. John Watson", "aliases": []}])
    assert scene.speaking == ["john_watson"]


def test_repair_leaves_an_already_correct_scene_untouched():
    from scripts.screenplay.step_03_draft import repair_scene
    scene = _scene([ScriptElement(kind="dialogue", character="john_watson",
                                  text="You have been in Afghanistan.")])
    scene.speaking = ["john_watson"]
    before = scene.model_dump_json()
    repair_scene(scene, [{"id": "john_watson", "name": "Dr. John Watson", "aliases": []}])
    assert scene.model_dump_json() == before
