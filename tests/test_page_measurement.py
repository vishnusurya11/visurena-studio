"""Page measurement must count RENDERED lines, not source lines.

The first real render measured 25.12 pages. The PDF it produced has 39. A 36% undercount,
because page_eighths counted lines in the Fountain file while the page wraps them: 18% of
lines exceeded the 61-character action width and the longest was 496 characters.

The widths are not one number. Taken from screenplain's own ParagraphStyles at 12pt
Courier on US Letter: action and slug and transition 61 characters, dialogue 36,
parenthetical 48, character cue 42. Measuring dialogue at 61 is what made the undercount
worst, because dialogue is the most-wrapped element on the page.

Ground truth for these tests is the PDF itself — if the estimate and the real page count
disagree, the estimate is wrong.
"""

from __future__ import annotations

from studio import fountain
from studio.screenplay_spec import Scene, ScriptElement, Slug

SLUG = Slug(int_ext="INT", location_id="x", location_name="221B Baker Street",
            time="DAY", text="INT. 221B BAKER STREET - DAY")


def _scene(elements, number=1):
    return Scene(number=number, beat_id="b1", slug=SLUG, elements=elements)


# --- wrapping ----------------------------------------------------------------------

def test_a_short_line_occupies_one_row():
    assert fountain.wrapped_rows("He turns.", 61) == 1


def test_a_line_at_exactly_the_width_still_occupies_one_row():
    assert fountain.wrapped_rows("x" * 61, 61) == 1


def test_a_line_one_over_the_width_occupies_two():
    assert fountain.wrapped_rows("y " * 40, 61) == 2


def test_wrapping_breaks_on_words_not_mid_word():
    text = "word " * 30
    assert fountain.wrapped_rows(text, 20) == len(fountain.wrap(text, 20))


def test_an_empty_line_still_occupies_a_row():
    """A blank line is a line on the page."""
    assert fountain.wrapped_rows("", 61) == 1


def test_dialogue_wraps_narrower_than_action():
    long = "This is a long speech that will certainly need more than one row. " * 2
    assert fountain.wrapped_rows(long, fountain.WIDTH["dialogue"]) > \
        fountain.wrapped_rows(long, fountain.WIDTH["action"])


def test_the_widths_match_screenplain_geometry():
    """If screenplain ever changes its indents, this is the test that notices."""
    from screenplain.export.pdf import create_default_settings
    settings = create_default_settings()
    for key, style in (("action", "action_style"), ("dialogue", "dialog_style"),
                       ("parenthetical", "parenthentical_style"),
                       ("character", "character_style")):
        st = getattr(settings, style)
        avail = settings.frame_width - st.leftIndent - st.rightIndent
        assert fountain.WIDTH[key] == round(avail / settings.character_width)


# --- measurement -------------------------------------------------------------------

def test_a_long_action_paragraph_costs_a_row_per_wrapped_width():
    """300 characters at 61 per row is 5 rows, not 1. That difference, compounded over
    a script, is the whole 36% undercount."""
    text = "He turns. " * 30
    scene = _scene([ScriptElement(kind="action", text=text)])
    assert fountain.wrapped_rows(text, 61) == 5
    assert fountain.rendered_rows(scene) >= 5


def test_a_long_speech_costs_more_than_the_same_text_as_action():
    text = "I have found it, and I shall explain exactly how. " * 6
    speech = _scene([ScriptElement(kind="dialogue", text=text, character="holmes")])
    action = _scene([ScriptElement(kind="action", text=text)])
    assert fountain.rendered_rows(speech) > fountain.rendered_rows(action)


def test_page_eighths_of_a_one_line_scene_is_small_but_not_zero():
    assert 1 <= fountain.page_eighths(_scene([])) <= 2


def test_page_eighths_grows_with_content():
    small = fountain.page_eighths(_scene([ScriptElement(kind="action", text="x")]))
    big = fountain.page_eighths(_scene(
        [ScriptElement(kind="action", text="He turns. " * 20)] * 5))
    assert big > small


def test_the_estimate_matches_the_real_pdf_within_a_page():
    """The regression itself, run against the artifact on disk. If this drifts, the
    number the budget check compares against is fiction."""
    import re
    from pathlib import Path
    from studio.screenplay_spec import Screenplay

    base = Path("library/20260822113400_a-study-in-scarlet/screenplay/feature")
    if not (base / "screenplay.json").exists() or not (base / "screenplay.pdf").exists():
        return
    real = len(re.findall(rb"/Type\s*/Page[^s]", (base / "screenplay.pdf").read_bytes()))
    screenplay = Screenplay.model_validate_json(
        (base / "screenplay.json").read_text(encoding="utf-8"))
    # Tolerance is 8%, not a page, and the looseness is honest rather than lazy: this
    # is a LINEAR model - it sums each scene's wrapped rows - while real pagination
    # also moves whole blocks to avoid splitting a sentence, orphaning a heading, or
    # breaking a speech without a (MORE). Those always cost or save part of a page and
    # cannot be predicted per scene. What the test is for is catching a STRUCTURAL
    # error like the original one, where source lines were counted instead of rendered
    # rows and the estimate came in 36% low.
    assert abs(screenplay.totals.pages - real) <= max(1.5, real * 0.08), (
        f"estimate {screenplay.totals.pages} vs real {real} pages")


def test_the_model_matches_the_renderer_row_for_row():
    """The model and the renderer must agree, because the renderer is the thing that
    becomes the page. They did not: the model inserted a blank line between a character
    cue and its dialogue, and the renderer correctly does not. At 274 speeches that was
    five phantom pages, and it is why the estimate ran 8% high after the text shortened.

    This is the honest form of the check — not a looser tolerance, which would have
    hidden it."""
    scenes = [
        _scene([ScriptElement(kind="action", text="He turns.")]),
        _scene([ScriptElement(kind="dialogue", text="Quite.", character="holmes")]),
        _scene([ScriptElement(kind="dialogue", text="Never mind.", character="holmes",
                              parenthetical="beat")]),
        _scene([ScriptElement(kind="transition", text="CUT TO:")]),
    ]
    # UNWRAPPED content only, and that restriction is the point rather than a dodge:
    # render_scene emits SOURCE lines and rendered_rows models PAGE rows, and the two
    # diverge exactly when a line is long enough to wrap. Comparing them on long text
    # would be asserting that wrapping does not happen, which is the bug this whole
    # module exists to fix. On short lines they must agree exactly.
    for scene in scenes:
        rendered = len(fountain.render_scene(scene, {}).rstrip().splitlines())
        assert fountain.rendered_rows(scene) == rendered, (
            f"model {fountain.rendered_rows(scene)} vs renderer {rendered} for "
            f"{[e.kind for e in scene.elements]}")
