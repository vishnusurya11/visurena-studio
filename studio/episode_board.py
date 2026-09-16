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

from studio import episode_gutter
from studio import house_style
from studio.episode_spec import Shot

COLS, ROWS = 3, 3
PANELS = COLS * ROWS
CANVAS = (2048, 3072)
MODEL = "gpt-image-2.5-sunburst"
"""Owner's choice, 2026-09-10, with explicit permission to spend on it."""
BARE = ("No text, no numbers, no captions, no labels, no watermark; thin white gutters are "
        "the only borders.")


def still_line() -> str:
    """The style line for this run, from `studio.house_style`, plus the sheet's
    own bareness rule.

    This was a constant reading "1881 London". Episode 8 was drawn and rendered
    under it over an 1847 Utah desert, because `Episode.palette` was wired into
    the location plate alone and the fix was called done -- 13 of 13 sheet
    prompts and 28 of 28 take prompts carried the wrong place. The place is
    declared once per run now, in one module."""
    return f"{house_style.stills()} {BARE}"
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


def _person_lines(k: int, who: str, physical: dict[str, str],
                  wardrobe: dict[str, str] | None) -> list[str]:
    """What this person's attached picture -- or pair of pictures -- is.

    With cards drawn, the face and the clothes are two separate images, which
    is what MiniMax's guide and the practical H3 guide both ask for: image one
    is the face and hairstyle, image two is the wardrobe and silhouette.  The
    state sentence rides on the SECOND line, so the hat is a fact about this
    scene rather than a conditional inside the description."""
    name = who.replace("_", " ").title()
    if not wardrobe or not wardrobe.get(who):
        return [f"Image {k} is {name}: {physical.get(who, '')} Keep exactly this face, "
                f"hair, build and these clothes in every panel that shows {name}."]
    return [f"Image {k} is {name}, his face and hair: {physical.get(who, '')} "
            f"Keep exactly this face and hair in every panel that shows {name}.",
            f"Image {k + 1} is {name}'s clothes, hands and things: in this scene he "
            f"{wardrobe[who]}. Keep exactly these clothes and these things in every "
            f"panel that shows {name}."]


def describe_refs(cast: list[str], physical: dict[str, str], previous: bool,
                  wardrobe: dict[str, str] | None = None) -> str:
    """What each attached image is, in the order it is attached: plate first."""
    lines = ["Image 1 is the empty location: every panel is set in this exact room, "
             "with its furniture, walls, windows and light."]
    k = 2
    for who in cast:
        said = _person_lines(k, who, physical, wardrobe)
        lines += said
        k += len(said)
    if previous:
        lines.append(f"Image {k} is the previous storyboard sheet of this same "
                     f"scene: match its light and wardrobe; do NOT reuse its framings, each panel is "
                     f"framed only by its own text.")
    return " ".join(lines)


def prompt(shots: list[Shot], described: str, cast: list[str], physical: dict[str, str],
           previous: bool, wardrobe: dict[str, str] | None = None) -> str:
    frames = [shot.frame for shot in shots] + [text for _, text in alternates(shots)]
    panels = " ".join(f"Panel {k}: {frame}" for k, frame in enumerate(frames, start=1))
    return (f"A film storyboard sheet: a {COLS} by {ROWS} grid of {PANELS} equal vertical 9:16 "
            f"panels filling the whole canvas, thin white gutters between them. {ORDER} "
            f"Every panel is a frame from the same scene: {described} "
            f"{describe_refs(cast, physical, previous, wardrobe)} {panels} {still_line()}")


def panel_prompt(shot: Shot, described: str, cast: list[str], physical: dict[str, str],
                 wardrobe: dict[str, str] | None = None) -> str:
    """ONE panel redrawn on its own (a bad cell on an otherwise good sheet):
    the same scene, references and register, the previous sheet attached last
    so the redraw matches its light and staging.  Measured need: S19 of
    episode 1 drew three hands into a handshake (2026-09-10)."""
    return (f"A single vertical 9:16 film frame filling the whole canvas, no grid, no border, "
            f"no gutter. The scene: {described} {describe_refs(cast, physical, True, wardrobe)} "
            f"The frame: {shot.frame} {still_line()}")


GUTTER_WHITE, GUTTER_FLAT = episode_gutter.WHITE, episode_gutter.FLAT
"""What sheet paper looks like -- ASKED, never written out again.

Two places decide whether a bright flat run is paper: this, finding the gutters
ON a sheet so cells can be cut between them, and `episode_gutter.band`, finding
leaked paper IN a cell or a take so it can be cropped off. They carried the same
pair of numbers written twice, and when the guard's floor was recalibrated for
Part Two's bleached desert this kept the London one.

MEASURED, episode 9's `seq_valley_rim_0_strict.png`, a 2x2 of the valley of Utah
at sunrise. A 2x2 needs exactly one band per axis; at 30.0 this found three rows:

    rows   16-17     depth   1   mean 190.1   std 13.87   sky
    rows   18-118    depth 100   mean 196.6   std 16.40   sky, a hundred rows deep
    rows 1015-1026   depth  11   mean 247.7   std  2.12   the gutter
    cols 1018-1030   depth  12   mean 251.7   std  2.49   the gutter

So `cell_boxes` fell back to flat halves, `gutters_ok` went False, and `qc`
failed an episode whose 28 takes all scored 100/100 and whose master matched its
takes frame for frame.

`white_lines` in `seq_boards` already reaches for the guard's window for exactly
this reason -- "it owns the number and this asks for it". The floor is the same
fact about paper, so it is the same number."""


def bands(grey, axis: int) -> list[tuple[int, int]]:
    """Runs of gutter lines along `axis` (0: rows, 1: columns) as [start, end)."""
    lines = grey if axis == 0 else grey.T
    white = (lines.mean(axis=1) > GUTTER_WHITE) & (lines.std(axis=1) < GUTTER_FLAT)
    out, start = [], None
    for i, flag in enumerate(list(white) + [False]):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            out.append((start, i))
            start = None
    return out


def cell_boxes(grey, cols: int = COLS, rows: int = ROWS) -> list[tuple[int, int, int, int]]:
    """The nine cells as the regions BETWEEN the drawn gutters, reading order.
    MEASURED 2026-09-10: the corridor sheet's gutters were not at thirds, so
    the flat split left a 14 px white line 34 px inside three panels (S03-S05),
    which H3 then kept and grew.  Falls back to thirds without two per axis."""
    h, w = grey.shape
    row_bands, col_bands = bands(grey, 0), bands(grey, 1)
    if len(row_bands) != rows - 1 or len(col_bands) != cols - 1:
        return [panel_box(i, (w, h), cols, rows) for i in range(cols * rows)]
    ys = [0] + [y for band in row_bands for y in band] + [h]
    xs = [0] + [x for band in col_bands for x in band] + [w]
    return [(xs[2 * c], ys[2 * r], xs[2 * c + 1], ys[2 * r + 1])
            for r in range(rows) for c in range(cols)]


def panel_box(index: int, canvas: tuple[int, int] = CANVAS, cols: int = COLS, rows: int = ROWS) -> tuple[int, int, int, int]:
    """Pixel box of panel `index` (0-based, reading order), gutters trimmed."""
    col, row = index % cols, index // cols
    width, height = canvas[0] / cols, canvas[1] / rows
    trim_x, trim_y = round(width * 0.015), round(height * 0.015)
    return (round(col * width) + trim_x, round(row * height) + trim_y,
            round((col + 1) * width) - trim_x, round((row + 1) * height) - trim_y)
