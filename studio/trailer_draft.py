"""Writing the trailer's page from the book — inputs in, a script out.

THE ONE RULE THIS MODULE EXISTS TO ENFORCE: the page may only ask for what the
pipeline can deliver.  The strongest argument against writing a trailer in
advance is that an authored page specifies shots nobody can render and lines
nobody said, and unattended there is no editor to catch it.  So the brief IS
the inventory — the cast that has sheets, the scenes the book has, the lines
the finder actually found — and anything that comes back naming something
outside it is refused (`NotInTheBook`).  That is the same shape as the
published systems that work this way: REGen writes a script of PLACEHOLDERS
that retrieval fills, and Derek Lieu's paper edit reorders transcribed selects
rather than inventing them.

The genre decides the TYPE, and the type decides the moves: what the trailer
opens on, what it withholds, and whether dialogue or sound carries it.  A
mystery withholds the answer; horror withholds the creature.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

from studio import llm, trailer_script
from studio.trailer_script import RUNTIME, TrailerScript

TIER = "reasoning"

GENRE_NOTES = {
    "detective mystery": (
        "MYSTERY. One voice is the engine: let the lead's dialogue drive the cut, "
        "used like percussion. Withhold THE ANSWER — the culprit's face stays turned "
        "away until the last act. Open on the crime, never on the explanation."),
    "gothic horror": (
        "HORROR. Withhold THE CREATURE — show its effect, never it. Sound design over "
        "score, and silence immediately before the hit: the ear notices absence faster "
        "than volume. Open on the ordinary world, wide and slow to unsettle."),
    "adventure": (
        "ADVENTURE. Withhold THE DESTINATION. Open on a hero moment, escalate by "
        "raising what it costs, and let scope carry the last act — the size of the "
        "world is the promise."),
    "literary drama": (
        "DRAMA. Withhold THE OUTCOME. Open on a sharp exchange between two people, "
        "spend two thirds on character and stakes, and let cards carry the theme."),
}
DEFAULT_NOTE = ("Withhold the OUTCOME. Open on the strongest image in the book and pose "
                "the story as a question rather than explaining it.")


TRIES = 3
"""How many times a refused page is asked again before the run gives up."""


def violation_of(why: Exception) -> str:
    """The refusal in the words the contract used, for quoting back."""
    return "; ".join(e.get("msg", "").replace("Value error, ", "")
                     for e in getattr(why, "errors", lambda: [])()) or str(why)


class NotInTheBook(ValueError):
    """The page asked for something the pipeline cannot deliver."""


def genre_note(genre: str) -> str:
    """The moves this genre's trailer type makes."""
    return GENRE_NOTES.get((genre or "").lower(), DEFAULT_NOTE)


def speakable(lines: list[dict], cast: dict[str, str]) -> list[dict]:
    """The lines a speaker with a cast sheet actually said.  Run 19 slated a
    line by "Police Inspector", who has no sheet, and the trailer spoke 4 of 5:
    a line the voice step cannot clone must never reach the page."""
    return [line for line in lines if line.get("speaker") in cast]


def line_menu(lines: list[dict], cast: dict[str, str]) -> str:
    return "\n".join(f'- {cast[l["speaker"]]} ({l["speaker"]}), scene {l.get("scene")}: '
                     f'"{l["text"]}"{"  [ICONIC]" if l.get("kept") else ""}'
                     for l in speakable(lines, cast))


def scene_number(scene: dict) -> int | None:
    """A scene's number, whatever the analysis stage called the field."""
    return scene.get("number", scene.get("scene"))


def scene_menu(scenes: list[dict]) -> str:
    """Each scene as one line -- where it is, what happens, who is in it -- so
    the page can only draw beats from scenes the book actually has."""
    return "\n".join(
        f'- scene {scene_number(s)} ({s.get("location_text") or s.get("location_id", "")}): '
        f'{s.get("summary", "")} [{", ".join(s.get("characters", []))}]'
        for s in scenes)


SPEECH_SHARE = 0.45
"""How much of the runtime may have somebody speaking.  The first Scarlet draft
came back at 72% -- closer to a radio play than a trailer -- because the brief
never said.  Measured practice sits at 41-45% for a dialogue-led cut."""


def brief(story: dict, scenes: list[dict], lines: list[dict], cast: dict[str, str],
          genre: str, title: str = "") -> str:
    """What the model is shown: the job, the format, and the inventory."""
    named = title or story.get("setting", "")
    return (
        f"Write the SCREENPLAY for a {RUNTIME:.0f}-second trailer for the book "
        f"'{named}', set in {story.get('setting', '')} — a {genre}. Its only job is "
        f"to make someone watch episode 1 of the series. It plays vertically, 9:16, "
        f"in a social feed where the viewer can swipe away at any moment.\n\n"
        f"{genre_note(genre)}\n\n"
        f"THE SHAPE. The beats must total {RUNTIME:.0f} seconds in total, within two "
        f"seconds. Act I is 25% of that, Act II 45%, Act III 30%, spent in SECONDS. "
        f"Open on the strongest image — never on a logo, never on a slow build. Put "
        f"the words '{named.upper()}' on screen as a CARD inside the first 7 seconds, "
        f"and hold that same title card again on the music's biggest hit near the end. "
        f"Close on the story's reopened question, then one card giving the next "
        f"action. No shot may run longer than "
        f"{trailer_script.HOLD_CEILING['M1']} seconds.\n\n"
        f"HOW MUCH IS SPOKEN. At most {SPEECH_SHARE:.0%} of the runtime may carry a "
        f"line — roughly {RUNTIME * SPEECH_SHARE / 3.0:.0f} of the beats. The rest "
        f"play on picture and sound alone. A trailer that talks the whole way through "
        f"is a radio play.\n\n"
        f"THE LEAD is {cast.get(story.get('lead'), story.get('lead'))}. THE FIGURE the "
        f"trailer withholds is {cast.get(story.get('figure'), story.get('figure'))}.\n\n"
        f"SCENES YOU MAY DRAW ON:\n{scene_menu(scenes)}\n\n"
        f"LINES YOU MAY USE — copy one VERBATIM or leave the beat silent. Do not write "
        f"new dialogue; a line that is not on this list cannot be spoken:\n"
        f"{line_menu(lines, cast)}\n\n"
        f"For every beat give: what we SEE, what we HEAR, the line and its speaker if "
        f"it speaks, the card if it holds text, and WHY the beat is there. A beat "
        f"without a reason to exist is decoration — cut it.")


def check(page: TrailerScript, lines: list[dict], cast: dict[str, str]) -> TrailerScript:
    """The page against the inventory: every spoken line is one the book wrote,
    and every speaker has a sheet to be rendered and cloned from."""
    said = {line["text"] for line in speakable(lines, cast)}
    for beat in page.beats:
        if beat.speaker and beat.speaker not in cast:
            raise NotInTheBook(f"{beat.id}: {beat.speaker} has no cast sheet")
        if beat.line and beat.line not in said:
            raise NotInTheBook(f"{beat.id}: nobody in the book says “{beat.line}”")
    return page


def write(out_dir: Path, story: dict, scenes: list[dict], lines: list[dict],
          cast: dict[str, str], genre: str, model: Callable | None = None,
          title: str = "") -> TrailerScript:
    """Draft the page, check it against the book, and write both files.

    A page the CONTRACT refuses -- too talky, wrong act shares, a shot held too
    long -- is refused inside the model's own parse, where the model never
    hears it.  So the refusal is quoted back and the page asked again, which is
    what every other ladder in this repo does with a violation."""
    ask = model or llm.structured
    page, refused = None, ""
    for _ in range(TRIES):
        text = brief(story, scenes, lines, cast, genre, title)
        try:
            page = ask(TIER, "\n\n".join(filter(None, (text, refused))), TrailerScript)
            break
        except ValidationError as why:
            refused = (f"Your previous page was REFUSED: {violation_of(why)}. "
                       f"Write it again with that fixed.")
    if page is None:
        raise ValidationError.from_exception_data(
            "TrailerScript", [{"type": "value_error", "loc": (), "input": {},
                               "ctx": {"error": refused}}])
    page = check(page, lines, cast)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / "trailer_script.json").write_text(page.model_dump_json(indent=2),
                                                       encoding="utf-8")
    (Path(out_dir) / "trailer_script.txt").write_text(trailer_script.render(page),
                                                      encoding="utf-8")
    return page


def book_title(book_dir: Path) -> str:
    """The book's own title, from the source record the intake wrote.  The
    first draft's title card read "1881 LONDON" because the brief passed the
    story's SETTING as its name."""
    path = Path(book_dir) / "source/book.json"
    if not path.exists():
        return ""
    return json.loads(path.read_text(encoding="utf-8")).get("title", "")


def inputs_for(book_dir: Path, out_dir: Path) -> tuple[dict, list[dict], list[dict], dict]:
    """What the drafter reads off a book that has been analysed and stepped."""
    book, out = Path(book_dir), Path(out_dir)
    story = json.loads((out / "story.json").read_text(encoding="utf-8"))
    scenes = json.loads((book / "analysis/scenes.json").read_text(encoding="utf-8"))
    lines = json.loads((out / "lines.json").read_text(encoding="utf-8"))
    cast = {p.stem: json.loads(p.read_text(encoding="utf-8")).get("name", p.stem)
            for p in sorted((book / "analysis/characters").glob("*.json"))}
    found = scenes.get("scenes", scenes) if isinstance(scenes, dict) else scenes
    return story, found, lines.get("pool", []) + lines.get("lines", []), cast
