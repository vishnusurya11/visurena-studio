"""Fountain rendering — and the lint that exists because Fountain cannot reject.

Verified on this machine: the parser falls back to Action on anything unrecognised, so
a syntactically broken screenplay parses "fine" and renders a wrong PDF. Two elements
misparsed, no error, no warning:

    INT. HALL - DAY          -> Slug     ok
    THE DOOR BURSTS OPEN     -> swallowed as the CHARACTER CUE
    Anna stands there,       -> Dialog   wrong

No Fountain linter exists in any language. So the emitter knows the intended type of
every line it writes, parses its own output, and asserts the two agree.
"""

from __future__ import annotations

import io
import textwrap

from studio.screenplay_spec import Scene

LINES_PER_PAGE = 55          # US Letter, 12pt Courier, industry margins
EIGHTH = LINES_PER_PAGE / 8


def cue(character: str | None, display: dict) -> str:
    """The name printed above a line. Canonical id in, screen cue out."""
    if not character:
        return ""
    return display.get(character, character.replace("_", " ")).upper()


def _dialogue_block(element, display: dict, contd: bool) -> list[str]:
    name = cue(element.character, display)
    head = f"{name} (CONT'D)" if contd else name
    block = [head]
    if element.parenthetical:
        block.append(f"({element.parenthetical.strip('()')})")
    block.append(element.text)
    return block


def render_scene(scene: Scene, display: dict, bold_heading: bool | None = None) -> str:
    """One scene as Fountain. Every line's intended type is knowable from the source."""
    bold = BOLD_SCENE_HEADINGS if bold_heading is None else bold_heading
    # Fountain's #n# syntax parses but screenplain's PDF exporter never prints it, so
    # the number goes in the heading TEXT via a forced scene heading: the leading dot
    # is consumed as the force marker and the page reads "4. INT. HALL - DAY".
    # The number is NOT stored in slug.text — it lives on Scene.number, and one fact
    # true in two places is the drift the slug re-derivation already had to fix once.
    heading = scene.slug.text.upper()
    numbered = f"{scene.number}. {heading}" if scene.number else heading
    # A forced heading (leading dot) is needed for the number; the emphasis marks go
    # INSIDE it so the number and the heading bold together, as one line.
    line = f".**{numbered}**" if bold else (f".{numbered}" if scene.number else heading)
    out = [line, ""]
    last_speaker = None
    for element in scene.elements:
        if element.kind == "dialogue":
            out += _dialogue_block(
                element, display,
                # `is not None` matters: two unnamed lines are not the same speaker,
                # and the first line of a scene is never a continuation.
                contd=element.character is not None
                and element.character == last_speaker)
            last_speaker = element.character
        elif element.kind == "transition":
            out.append(f"> {element.text.upper().rstrip()}"
                       if not element.text.upper().rstrip().endswith("TO:")
                       else element.text.upper().rstrip())
            last_speaker = None
        else:
            out.append(element.text)
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def intended_types(scene: Scene, display: dict) -> list[str]:
    """The type we MEANT each non-blank line to be, in render order."""
    kinds = ["Slug"]
    for element in scene.elements:
        if element.kind == "dialogue":
            kinds.append("Dialog")
        elif element.kind == "transition":
            kinds.append("Transition")
        else:
            kinds.append("Action")
    return kinds


def parsed_types(text: str) -> list[str]:
    """What screenplain's parser actually makes of it."""
    from screenplain.parsers.fountain import parse
    return [type(obj).__name__ for obj in parse(io.StringIO(text))]


# Characters per rendered row, per element, at 12pt Courier on US Letter. Derived from
# screenplain's own ParagraphStyle indents rather than from a style guide, because these
# are the widths the PDF we actually ship is laid out at.
# test_the_widths_match_screenplain_geometry notices if that ever changes.
WIDTH = {"action": 61, "slug": 61, "transition": 61,
         "dialogue": 36, "parenthetical": 48, "character": 42}

BLANK_AFTER = 1          # every element is followed by a blank line on the page

# Bold scene headings are CONTESTED, so this is an option and not a rule. Trottier:
# "perfectly okay, but completely unnecessary - the standard is still ordinary,
# unadorned scene headings." Brown: "Do not bold or underscore scene headings."
# Produced scripts split down the middle. What no reference book endorses is bold AND
# underline together, which is exactly what screenplain's strong_slugs setting applies
# as a pair - so this is done through Fountain emphasis, which gives bold alone.
BOLD_SCENE_HEADINGS = False


def wrap(text: str, width: int) -> list[str]:
    """Break on words, exactly as the page does. Never mid-word."""
    return textwrap.wrap(text or "", width=width) or [""]


def wrapped_rows(text: str, width: int) -> int:
    """How many rows this string occupies. A blank line still occupies one."""
    return len(wrap(text, width))


def rendered_rows(scene: Scene) -> int:
    """Rows this scene costs on the page.

    Counting SOURCE lines instead of rendered rows undercounted the first real
    screenplay by 36% — 25.12 estimated against a 39-page PDF — because 18% of lines
    exceeded their width and the longest was 496 characters. Dialogue is the worst case
    and the most common: it wraps at 36 characters, not 61.
    """
    rows = wrapped_rows(scene.slug.text, WIDTH["slug"]) + BLANK_AFTER
    for element in scene.elements:
        if element.kind == "dialogue":
            # The cue sits DIRECTLY above its line — no blank between them. Counting one
            # there added a phantom row per speech, which at 274 speeches was five pages.
            rows += 1                                     # the character cue
            if element.parenthetical:
                rows += wrapped_rows(element.parenthetical, WIDTH["parenthetical"])
            rows += wrapped_rows(element.text, WIDTH["dialogue"])
        elif element.kind == "transition":
            rows += wrapped_rows(element.text, WIDTH["transition"])
        else:
            rows += wrapped_rows(element.text, WIDTH["action"])
        rows += BLANK_AFTER
    # The renderer strips the blank after the LAST element; the blank that separates
    # this scene from the next belongs to the document, not to the scene. Removing it
    # here is what makes rendered_rows exactly equal render_scene's line count, which
    # is the property test_the_model_matches_the_renderer_row_for_row pins down.
    return rows - BLANK_AFTER


SCENE_SEPARATOR = 1      # the blank line between one scene and the next


def page_eighths(scene: Scene) -> int:
    """Rendered length in eighths of a page. Code measures; agents are never asked."""
    return max(1, round((rendered_rows(scene) + SCENE_SEPARATOR) / EIGHTH))


def lint(text: str, intended: list[str]) -> list[str]:
    """Compare what we MEANT each element to be against what the parser makes of it.

    This signature is the whole design. Fountain cannot reject, so there is no error to
    catch — the only available evidence of a misparse is the disagreement between the
    emitter's intent and the parser's typing. Linting raw text alone is impossible:
    'THE DOOR BURSTS OPEN' and 'SHERLOCK HOLMES' are the same string shape, and only
    the writer knows which one is a character.
    """
    got = parsed_types(text)
    problems = []
    for index, want in enumerate(intended):
        have = got[index] if index < len(got) else "(missing)"
        if have != want:
            problems.append(f"element {index}: intended {want}, parsed {have}"
                            f" — near {_near(text, index)!r}")
    if len(got) > len(intended):
        problems.append(f"parser produced {len(got)} elements, we wrote {len(intended)}")
    return problems


def _near(text: str, index: int) -> str:
    """A locating snippet for a problem report — the reader needs a place, not a count."""
    blocks = [b.strip() for b in text.split(chr(10) + chr(10)) if b.strip()]
    return blocks[index][:48] if index < len(blocks) else ""


def lint_scene(scene: Scene, display: dict, bold_heading: bool | None = None) -> list[str]:
    """Render one scene and assert the parser agrees with the emitter about every line."""
    return lint(render_scene(scene, display, bold_heading), intended_types(scene, display))


def title_page(title: str = "", author: str = "", **fields) -> str:
    """A Fountain title block, or nothing.

    Two rules, both learned by shipping a broken page 1: a key with an EMPTY value is
    not a title field, it is a line of body text; and the block must be closed by a
    BLANK LINE or Fountain keeps reading and swallows the first scene heading too. The
    first render printed "Title: ...", "Author:" and a literal ".1." as three lines of
    action, because both rules were broken at once.
    """
    rows = [(key.replace("_", " ").title(), value)
            for key, value in (("title", title), ("author", author), *fields.items())
            if str(value or "").strip()]
    if not rows:
        return ""
    return "".join(f"{k}: {v}\n" for k, v in rows) + "\n"


def render(scenes: list[Scene], display: dict, title: str = "",
           author: str = "", bold_heading: bool | None = None, **fields) -> str:
    """The whole screenplay. A projection of screenplay.json, never the source."""
    body = "\n\n".join(
        render_scene(s, display, bold_heading) for s in scenes)
    # The bookends a script department expects and the first render had none of:
    # FADE IN: opens, THE END closes. Brown: "Standard practice is to begin the script
    # with the words FADE IN:" and to end with FADE OUT. then THE END, centered.
    opening = "FADE IN:\n\n"
    closing = "\n\n> FADE OUT.\n\n> THE END"
    return title_page(title, author, **fields) + opening + body + closing


def to_pdf(text: str, path) -> None:
    """Industry geometry via screenplain. NOTE: `python -m screenplain` does NOT work —
    the package has no __main__. The API is the only entry point."""
    from screenplain.export.pdf import to_pdf as _to_pdf
    from screenplain.parsers.fountain import parse
    with open(path, "wb") as out:
        _to_pdf(parse(io.StringIO(text)), out)
