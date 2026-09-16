"""The one line that tells every drawer and the renderer WHERE this is and
WHAT LIGHTS IT.

MEASURED, episode 8. `Episode.palette` was added because the book's palette
ends "1881 London" and put Georgian terraced streets into the Utah desert. It
reached the location plate alone; "1881 London" stayed in 13 of 13 sheet
prompts and 28 of 28 take prompts because the sentence was a hard-coded
constant in four modules. So the place lives HERE, set once per run from the
plan (`adopt`), the pattern of `canvas.adopt`.

MEASURED, episode 9 (docs/analysis/ep08_ep09_why_worse.md). The fix pasted
the whole palette paragraph into the line: the sheet style line went to 46
words and the take style line to 48 ("only., 35 mm") where ep05-08 had 13.
Cause 2: "The black floor is gone. 5th-percentile luma 4-7 (ep05-07) -> 16.5
... the palette sentence replaced the London clause that made the series
look like film -- 'deep shadow; practical period light sources' -- with
'sunlight only' and a colour inventory. The drawer obeys light-direction
words; 'hard blue shadow' never arrives. And it is one hue: 94 % orange."
Cause 8: "The palette's objects stamped a gold wheat foreground into five of
six plates, including the bare rock shoulder."

So one field is two.  `where` is the place and the date, six words.  `light`
is a DIRECTION that throws shadow into frame and a named BLACK -- never a
colour inventory, never an object.  The rendered line keeps the length that
worked, and the vocabulary below is closed so the gate can read it.
"""
from __future__ import annotations

import re

from studio.affirm import negations

HOUSE_WHERE = "1881 London"
HOUSE_LIGHT = "gaslight from one side, deep shadow"
"""The book this pipeline was built for, and the floor when a plan says nothing.

The report's own words for what made ep04-07 look like film: "deep shadow;
practical period light sources" -- one source with a direction and a true
black.  Seven episodes were made against London and stay unchanged."""

MAX_WHERE_WORDS = 6
"""`where` is 3-6 words, place and date (report, proposal 4)."""
MAX_STYLE_WORDS = 16
"""The rendered line's wall.  ep05-08's sheet line was 13-16 words and looked
like film; ep09's was 46 and 48 and did not.  `light` gets whatever the
photographic frame and `where` leave, which is the discipline the report asks
for: a direction and a black, not a paragraph."""

STILLS = "Photoreal 35 mm still, {where}, {light}, film grain."
LIVE = "Photoreal live-action, {where}, {light}, 35 mm film grain."
"""<photographic>, <where>, <light>, <grain>.  Six fixed words each."""

# ---- the closed vocabulary ----------------------------------------------------

DIRECTIONS = re.compile(
    r"\bfrom (?:the |one )?(?:left|right|far end|near end|side|behind|ahead|west|east|"
    r"north|south|windows?|doorway)\b"
    r"|\b(?:low|level|raking|slanting|sidelong|side-?lit)\b"
    r"|\b(?:behind|ahead)\b|\bdown the \w+\b"
    r"|\bthrough (?:the |a )?(?:\w+ )?(?:windows?|doorway|shutters?|blinds?|glass)\b", re.I)
"""A direction that throws shadow INTO the frame.  "The drawer obeys
light-direction words" (report, cause 2): a low or side source, or light
coming from a named edge, is what puts a black in the picture."""

PRACTICALS = re.compile(
    r"\b(?:lamps?|lamplight|gaslight|gas|candles?|candlelight|fire|firelight|hearth|"
    r"grate|coals?|embers?|smoulder|lanterns?|torch(?:es)?|stove|forge|windows?|"
    r"doorway|skylight)\b", re.I)
"""A practical period light source, or the opening the light comes through.
It has a place, so it IS a direction:
"the lamplit parlour cells sit at luma 40 with true black -- the pipeline
can still do it; the sunlit setups lost the shadow" (report, cause 2)."""

SKY = re.compile(r"\b(?:sun|sunlight|sunshine|daylight|moon|moonlight|dawn|dusk|light)\b", re.I)
"""A source with no place of its own: it needs a DIRECTION beside it, or it
is ep09's "hard morning sunlight" -- a brightness, not a light."""

LIT = re.compile(r"\b(?:lights?|lit|burn\w*|glow\w*|smoulder\w*|shin\w*|flam\w*|beams?|gleam\w*)\b", re.I)
"""What a practical must be doing in its clause to count as the light: a
spirit lamp in a furniture list is not lighting the room."""

BLACKS = re.compile(r"\b(?:shadows?|shadowed|black|dark|darkness|silhouettes?|soot-black)\b", re.I)
"""The named black.  "The histogram simply lifted off the floor" (report):
near-black share .29-.45 -> .14 when no sentence asked for one."""

NO_SHADOW = re.compile(r"\b(?:overhead|straight down|directly above|at noon|high noon|noon sun)\b", re.I)
"""An overhead sun throws its shadow under the thing, out of frame: refused
outdoors.  ep08's "shadows straight down off every rock" drew the flattest,
greyest sheets in the series (report, ep08 cause 1)."""

OBJECTS = ("wheat", "dust", "pine", "sky", "grass", "stubble", "sagebrush", "cottonwood",
           "adobe", "palette")
"""Nouns the palette put into the light line, and the word that announces an
inventory.  Each one was drawn: "a gold wheat foreground into five of six
plates including the bare rock shoulder" (report, cause 8)."""

INVENTORY_ITEMS = 3
"""A comma list of this many items with no direction and no black in them is
a colour inventory, whatever the nouns."""

_where, _light = HOUSE_WHERE, HOUSE_LIGHT


# ---- the run declares its world ------------------------------------------------

def _clause(text: str) -> str:
    """A clause, not a sentence: the trailing full stop that ep09 pasted
    mid-line ("only., 35 mm") comes off here."""
    return (text or "").strip().rstrip(".").strip()


def adopt(where: str, light: str = "") -> None:
    """Declare the place and the light for this run.  Both empty puts the
    book's own back.  Called once, from the script's `main`, off
    `episode.where` and `episode.light`.

    A palette paragraph handed in as the place is refused, not rendered: the
    callers that still pass `episode.palette` must not build ep08/09's line."""
    global _where, _light
    where, light = _clause(where), _clause(light)
    if not where and not light:
        _where, _light = HOUSE_WHERE, HOUSE_LIGHT
        return
    if bad := where_faults(where) + light_faults(light) + style_faults(where, light):
        raise ValueError("; ".join(bad))
    _where, _light = where, light


def where() -> str:
    return _where


def light() -> str:
    return _light


def stills() -> str:
    """The style line for a DRAWN sheet or board."""
    return STILLS.format(where=_where, light=_light)


def live() -> str:
    """The style line for a RENDERED take."""
    return LIVE.format(where=_where, light=_light)


# ---- the validators -------------------------------------------------------------

def _objects(text: str) -> list[str]:
    return [w for w in OBJECTS if re.search(rf"\b{w}\b", text, re.I)]


def _inventory(text: str) -> list[str]:
    """Why this reads as a colour inventory, if it does."""
    out = []
    if found := _objects(text):
        out.append(f"`light` is an inventory, not a light: it names {', '.join(found)} "
                   f"-- the palette's objects were drawn into five of six ep09 plates")
    items = [i for i in re.split(r",|;|\band\b", text) if i.strip()]
    bare = [i.strip() for i in items if not (DIRECTIONS.search(i) or PRACTICALS.search(i)
                                             or BLACKS.search(i) or SKY.search(i))]
    if len(bare) >= INVENTORY_ITEMS:
        out.append(f"`light` is an inventory: a list of {len(bare)} things ({'; '.join(bare)}) "
                   f"with no direction and no black in them")
    return out


def _form(text: str, field: str) -> list[str]:
    """One clause, lower-case, affirmative."""
    out = []
    if "." in text:
        out.append(f"`{field}` carries a full stop; it is a clause, not a paragraph")
    if bad := negations(text):
        out.append(f"`{field}` asks for an absence the drawer cannot draw ({bad})")
    return out


def light_faults(light: str) -> list[str]:
    """Every reason `light` fails the vocabulary: missing, an inventory,
    directionless, shadowless, overhead."""
    light = _clause(light)
    if not light:
        return ["`light` is missing: name a direction that throws shadow into frame and a black"]
    out = _form(light, "light")
    if light[0].isupper():
        out.append("`light` starts with a capital: it sits mid-line after the place")
    out += _inventory(light)
    if hit := NO_SHADOW.search(light):
        out.append(f"{hit.group(0)!r} throws no shadow into frame: overhead light is refused outdoors")
    elif not (DIRECTIONS.search(light) or PRACTICALS.search(light)):
        out.append("`light` has no direction: the drawer obeys light-direction words and "
                   "'hard blue shadow' never arrives without one")
    if not BLACKS.search(light):
        out.append("`light` names no black: without one the histogram lifts off the floor")
    return out


def where_faults(where: str) -> list[str]:
    """`where` is a place and a date in six words or fewer."""
    where = _clause(where)
    if not where:
        return ["`where` is missing: the place and the date, six words or fewer"]
    out = _form(where, "where")
    if (n := len(where.split())) > MAX_WHERE_WORDS:
        out.append(f"`where` is {n} words; a place and a date are {MAX_WHERE_WORDS} or fewer "
                   f"(a palette paragraph is not a place)")
    if _objects(where):
        out.append(f"`where` names objects ({', '.join(_objects(where))}); it is a place and a date")
    return out


def style_faults(where: str, light: str) -> list[str]:
    """The rendered line stays under the wall that worked."""
    longest = max(len(STILLS.format(where=where, light=light).split()),
                  len(LIVE.format(where=where, light=light).split()))
    if longest > MAX_STYLE_WORDS:
        return [f"`where` + `light` render a {longest}-word style line; the wall is "
                f"{MAX_STYLE_WORDS} (ep05-08 had 13, ep09 had 48)"]
    return []


def setup_faults(described: str, outdoors: bool) -> list[str]:
    """A setup names its own light: a practical that is burning, or a sky
    source with a direction, in one clause; and outdoors, never overhead."""
    clauses = re.split(r"[,;:.]", described or "")
    lit = [c for c in clauses if (PRACTICALS.search(c) and LIT.search(c))
           or (SKY.search(c) and DIRECTIONS.search(c))]
    out = []
    if not lit:
        out.append("`described` names no light source with a direction -- ep09's 'hard morning "
                   "sunlight' is a brightness, not a light; say where it comes from")
    if outdoors and (hit := NO_SHADOW.search(described or "")):
        out.append(f"{hit.group(0)!r}: an overhead sun throws its shadow under the thing, out "
                   f"of frame -- ep08 drew the flattest sheets in the series under one")
    return out


# ---- G-LIGHT -----------------------------------------------------------------------

def _plan_faults(episode) -> list[str]:
    where, light = _clause(getattr(episode, "where", "")), _clause(getattr(episode, "light", ""))
    palette = (getattr(episode, "palette", "") or "").strip()
    if not where and not light:
        if not palette:
            return []
        why = "; ".join(light_faults(palette))
        return [f"G-LIGHT: `light` is missing; the plan carries only a palette, and a palette "
                f"is not a light ({why}). Write `where` (place, date) and `light` (a direction "
                f"and a black); ep09 drew 94 % of its colour in one orange band under this one"]
    return [f"G-LIGHT: {why}" for why in where_faults(where) + light_faults(light)
            + style_faults(where, light)]


def faults(episode) -> list[str]:
    """G-LIGHT.  Every reason this plan must not be drawn or rendered: a
    `light` that is missing, directionless, shadowless or an inventory, and
    every setup whose `described` names no light source with a direction.

    A QUERY, NOT A VALIDATOR, for the reason `Episode.long_shots` records:
    ep08 and ep09 are published under a palette and must keep loading.  The
    refusal belongs at the steps that spend."""
    out = _plan_faults(episode)
    for name, setup in episode.setups.items():
        out += [f"G-LIGHT: setup {name!r}: {why}"
                for why in setup_faults(setup.described, setup.outdoors)]
    return out
