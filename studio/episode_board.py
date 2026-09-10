"""The storyboard as an INPUT: 3x3 sheets drawn by gpt-image from the plate and
the character sheets, each panel becoming one shot's first frame.

Nine panels to a sheet on a 2048x3072 canvas: a cell is 682x1024, so a 9:16
crop of it is 576x1024 and reaches H3's 768x1344 with a 1.33x upscale -- a
face survives that.  (On 1024x1536 a cell is 341x512 and does not.)  A sheet
drawn in one generation is coherent by construction; the next sheet of the
same scene gets the previous one back as a reference so wardrobe and light
chain by pixels rather than by words.

Prompt shape follows the storyboard-prompt convention (drawstory.ai): shot
type first, then subject and action, then setting, then light and style; the
same character description in every panel.  Pure functions here; the API
call and the files are in scripts/episode/storyboard.py.
"""
from __future__ import annotations

from studio.episode_spec import Shot

COLS, ROWS = 3, 3
PANELS = COLS * ROWS
CANVAS = (2048, 3072)
MODEL = "gpt-image-2.5-sunburst"
"""Owner's choice, 2026-09-10, with explicit permission to spend on it."""
STILL = ("Photoreal cinematic 35 mm film stills, 1881 London, natural film grain, muted "
         "soot-black and gaslight-amber palette. No text, no numbers, no captions, no labels, "
         "no watermark; thin white gutters are the only borders.")
ORDER = ("Panels read left to right, top to bottom: panel 1 is top-left, panel 3 top-right, "
         "panel 9 bottom-right.")


def chunks(shots: list[Shot], size: int = PANELS) -> list[list[Shot]]:
    """Shots of one setup, in cut order, spread EVENLY over as few sheets as
    hold them: ten shots are two sheets of five, not nine and one."""
    if not shots:
        return []
    count = -(-len(shots) // size)
    per = -(-len(shots) // count)
    return [shots[i:i + per] for i in range(0, len(shots), per)]


ALTERNATES = (
    "Reverse angle of the same moment as panel {k}: the camera on the other side of the "
    "same people, the same room behind them.",
    "The same moment as panel {k} from further back: a wider framing with the whole room "
    "around the people.",
    "A tight insert from the moment of panel {k}: hands, an object or a detail of costume, "
    "no face.",
    "The same moment as panel {k} from a low angle, close to the floor, looking up.",
)
"""What a spare panel becomes: an alternate of a real shot, never black.

A sheet with black cells is a sheet the owner sent back.  Alternates are
cheap here (the sheet is drawn anyway) and are what an editor asks for
first when a take fails: another angle of the same moment."""


def alternates(shots: list[Shot], size: int = PANELS) -> list[tuple[int, str]]:
    """(shot index, frame text) for every spare panel on a sheet of `shots`."""
    spare = size - len(shots)
    out = []
    for i in range(max(spare, 0)):
        shot = shots[i % len(shots)]
        text = ALTERNATES[(i // len(shots)) % len(ALTERNATES)]
        out.append((shot.index, text.format(k=shots.index(shot) + 1)))
    return out


def describe_refs(cast: list[str], physical: dict[str, str], previous: bool) -> str:
    """What each attached image is, in the order it is attached: plate first."""
    lines = ["Image 1 is the empty location: every panel is set in this exact room, "
             "with its furniture, walls, windows and light."]
    for k, who in enumerate(cast, start=2):
        name = who.replace("_", " ").title()
        lines.append(f"Image {k} is {name}: {physical.get(who, '')} Keep exactly this face, "
                     f"hair, build and these clothes in every panel that shows {name}.")
    if previous:
        lines.append(f"Image {len(cast) + 2} is the previous storyboard sheet of this same "
                     f"scene: match its light, wardrobe and staging exactly.")
    return " ".join(lines)


def prompt(shots: list[Shot], described: str, cast: list[str], physical: dict[str, str],
           previous: bool) -> str:
    frames = [shot.frame for shot in shots] + [text for _, text in alternates(shots)]
    panels = " ".join(f"Panel {k}: {frame}" for k, frame in enumerate(frames, start=1))
    return (f"A film storyboard sheet: a {COLS} by {ROWS} grid of {PANELS} equal vertical 9:16 "
            f"panels filling the whole canvas, thin white gutters between them. {ORDER} "
            f"Every panel is a frame from the same scene: {described} "
            f"{describe_refs(cast, physical, previous)} {panels} {STILL}")


def panel_box(index: int, canvas: tuple[int, int] = CANVAS) -> tuple[int, int, int, int]:
    """Pixel box of panel `index` (0-based, reading order), gutters trimmed."""
    col, row = index % COLS, index // COLS
    width, height = canvas[0] / COLS, canvas[1] / ROWS
    trim_x, trim_y = round(width * 0.015), round(height * 0.015)
    return (round(col * width) + trim_x, round(row * height) + trim_y,
            round((col + 1) * width) - trim_x, round((row + 1) * height) - trim_y)
