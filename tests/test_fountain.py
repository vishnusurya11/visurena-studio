"""Fountain render + the round-trip lint.

Fountain falls back to Action on anything it does not recognise, so a parser NEVER
rejects our output. Silent misparse is the normal failure, not the exotic one. The
emitter therefore knows the intended type of every line it writes, parses its own
output, and asserts the parser's typing matches the intent.
"""

from __future__ import annotations

from studio import fountain
from studio.screenplay_spec import Scene, ScriptElement, Slug

SLUG = Slug(int_ext="INT", location_id="221b", location_name="221B Baker Street",
            time="NIGHT", text="INT. 221B BAKER STREET - NIGHT")


def _scene(elements, number=1):
    return Scene(number=number, beat_id="b1", slug=SLUG, elements=elements,
                 cast=["sherlock_holmes"], speaking=["sherlock_holmes"])


def test_slugline_is_upper_case():
    out = fountain.render_scene(_scene([]), {})
    assert out.splitlines()[0] == "INT. 221B BAKER STREET - NIGHT"


def test_action_renders_as_a_plain_paragraph():
    scene = _scene([ScriptElement(kind="action", text="He turns.")])
    assert "He turns." in fountain.render_scene(scene, {})


def test_dialogue_renders_cue_then_line():
    scene = _scene([ScriptElement(kind="dialogue", text="I've found it!",
                                  character="sherlock_holmes")])
    lines = [ln for ln in fountain.render_scene(scene, {}).splitlines() if ln]
    assert lines[1] == "SHERLOCK HOLMES" and lines[2] == "I've found it!"


def test_cue_uses_the_display_name_when_one_is_known():
    scene = _scene([ScriptElement(kind="dialogue", text="Quite.",
                                  character="john_watson")])
    out = fountain.render_scene(scene, {"john_watson": "Dr. John Watson"})
    assert "DR. JOHN WATSON" in out


def test_parenthetical_sits_between_cue_and_line():
    scene = _scene([ScriptElement(kind="dialogue", text="Never mind.",
                                  character="sherlock_holmes", parenthetical="beat")])
    lines = [ln for ln in fountain.render_scene(scene, {}).splitlines() if ln]
    assert lines[2] == "(beat)" and lines[3] == "Never mind."


def test_consecutive_lines_by_one_speaker_get_contd():
    scene = _scene([
        ScriptElement(kind="dialogue", text="One.", character="sherlock_holmes"),
        ScriptElement(kind="action", text="He steps closer."),
        ScriptElement(kind="dialogue", text="Two.", character="sherlock_holmes")])
    assert "SHERLOCK HOLMES (CONT'D)" in fountain.render_scene(scene, {})


def test_transition_renders_right_aligned_and_upper():
    scene = _scene([ScriptElement(kind="transition", text="cut to:")])
    assert "CUT TO:" in fountain.render_scene(scene, {})


# --- the lint ----------------------------------------------------------------------

MISPARSE = "INT. HALL - DAY" + chr(10) * 2 + "THE DOOR BURSTS OPEN" + chr(10) + "Anna stands there." + chr(10)


def test_lint_passes_a_well_formed_scene():
    scene = _scene([ScriptElement(kind="action", text="He turns."),
                    ScriptElement(kind="dialogue", text="Quite.",
                                  character="sherlock_holmes")])
    assert fountain.lint_scene(scene, {}) == []


def test_lint_catches_an_action_line_swallowed_as_a_character_cue():
    """THE DOOR BURSTS OPEN is Action to a human and a CHARACTER cue to the parser.
    Nothing errors - the parser is perfectly happy. Only intent-vs-parse sees it."""
    text = MISPARSE
    assert fountain.lint(text, ["Slug", "Action", "Action"]) != []


def test_lint_reports_where_the_misparse_happened():
    problems = fountain.lint(MISPARSE, ["Slug", "Action", "Action"])
    assert any("THE DOOR" in problem for problem in problems)


def test_lint_flags_a_scene_the_parser_reads_as_fewer_elements():
    """The swallow costs an element: three written, two parsed."""
    assert any("elements" in p or "intended" in p
               for p in fountain.lint(MISPARSE, ["Slug", "Action", "Action"]))


def test_page_eighths_of_an_empty_scene_is_never_zero():
    """A slugline occupies the page even with nothing under it."""
    assert fountain.page_eighths(fountain.render_scene(_scene([]), {})) >= 1
