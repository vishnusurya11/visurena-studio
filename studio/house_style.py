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
from studio.book_look import PANEL_HOUSE

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
    r"\bfrom (?:the |one )?(?:upper |lower )?(?:left|right|far end|near end|side|behind|ahead|west|east|"
    r"north|south|windows?|doorway)\b"
    r"|\b(?:low|level|raking|slanting|sidelong|side-?lit)\b"
    r"|\b(?:behind|ahead)\b|\bdown the \w+\b"
    r"|\bthrough (?:the |a )?(?:\w+ ){0,2}(?:windows?|doorway|shutters?|blinds?|glass)\b", re.I)
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
_look = ""
_atmosphere = ""
_panel_look = PANEL_HOUSE
_places: dict[str, str] = {}
"""{location id: its name}, from the book's location rows, set per run: the
style line names the SETUP's place. It said "Horsell, Surrey" at Woking
junction and in a railway carriage while the place was the episode's."""


def adopt_places(places: dict[str, str]) -> None:
    """Declare the names of this book's places for the run."""
    global _places
    _places = dict(places)


def where_for(setup=None) -> str:
    """The setup's own place with the episode's year -- "Woking junction, 1894"
    -- or the episode's place when the setup has none, or when its name will
    not fit the style line's place wall."""
    name = _places.get(getattr(setup, "location", "") or "", "")
    year = re.search(r"\b(1[5-9]\d\d|20\d\d)\b", _where or "")
    if not name or not year:
        return _where
    said = f"{name}, {year.group(1)}"
    return _where if where_faults(said) else said
"""The book's own look for a RENDERED take, when it is not photoreal.  The War
of the Worlds pack is drawn in an angular stylised 3D look (Krea2 + the
cinematic artstyle LoRA); a take told "Photoreal live-action" over those
references is told to be something its pictures are not.  Empty keeps LIVE."""


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


def stills(setup=None) -> str:
    """The style line for a DRAWN sheet or board; with a setup, under ITS light."""
    return STILLS.format(where=_where, light=light_for(setup, rendered=False))


def adopt_look(look: str) -> None:
    """Declare the book's look for rendered takes; empty puts `LIVE` back."""
    global _look
    _look = _clause(look)


def adopt_atmosphere(words: str) -> None:
    """Declare the book's atmosphere (book_look.atmosphere) for rendered takes; empty
    puts every line back byte for byte."""
    global _atmosphere
    _atmosphere = _clause(words)


def adopt_panel_look(words: str) -> None:
    """Declare what the storyboard panel is drawn as (book_look.panel_look); empty is the house."""
    global _panel_look
    _panel_look = _clause(words) or PANEL_HOUSE


def panel_look() -> str:
    return _panel_look


def live(setup=None) -> str:
    """The style line for a RENDERED take; with a setup, under ITS light (the start-frame route)."""
    return _rendered(setup, light_for(setup))


def take_line(setup=None, shot=None) -> str:
    """The ref2v take's style line: the setup's HOUR (`shot` may override it) and its black.  The
    source and its direction are the block's light sentence's alone: said here too they were said
    twice on 28 of 28 ep01 takes, and on 8 night takes as a sun (craft ruling A17)."""
    return _rendered(setup, style_light(setup, shot))


def _rendered(setup, light: str) -> str:
    from studio.book_look import under_sky        # fog outdoors only (2026-10-13)
    if _atmosphere and under_sky(setup):
        return _aired(setup, light)
    line = _live_line(where_for(setup), light)
    # A place name that pushes the line past its wall gives way to the
    # episode's place: the wall held on ep05-08 and a long name broke it.
    return line if len(line.split()) <= MAX_STYLE_WORDS else _live_line(_where, light)


def _live_line(where: str, light: str) -> str:
    if _look:
        return f"{_look}, {where}, {light}."
    return LIVE.format(where=where, light=light)


# ---- the book's atmosphere: words reserved before the light gets any ------------
#
# Jekyll ep01 (2026-10-13): "Photoreal live-action, The Sunday walks of London, 1886,
# gas, black shadows, 35 mm film grain" -- the wall took the fog.  With an atmosphere
# declared the line keeps it whole and the PLACE and the LIGHT give way, in that order
# of preference: the fullest light that fits, under the setup's place, else the episode's.

def _aired_line(where: str, light: str) -> str:
    if _look:
        return f"{_look}, {where}, {_atmosphere}, {light}."
    return f"Photoreal live-action, {where}, {_atmosphere}, {light}, 35 mm film grain."


def compact_lights(light: str) -> list[str]:
    """The light, then its first clause, then its direction and black alone, then the black."""
    first = clauses(light)[0].strip() if clauses(light) else light
    direction, black = direction_of(light), black_of(light)
    bare = ", ".join(p for p in (direction, black) if p)
    return list(dict.fromkeys(p for p in (light, first, bare, black) if p))


def _aired(setup, light: str) -> str:
    """The first line under the wall, fullest light first; the shortest when none fits."""
    lines = [_aired_line(where, said) for said in compact_lights(light)
             for where in dict.fromkeys((where_for(setup), _where))]
    return next((l for l in lines if len(l.split()) <= MAX_STYLE_WORDS),
                min(lines, key=lambda l: len(l.split())))


def place_words() -> set[str]:
    """Every word of this run's declared place names: they are names, so a
    capital on one of them is not a stray (the take lint's L20)."""
    return {w.lower().strip(",.") for name in _places.values() for w in name.split()}


# ---- the setup's own light ----------------------------------------------------------
#
# MEASURED, episode 10 (dq10/C.md §5, J.md §6): the episode `light` -- "low side
# sun, deep black shadow" -- reached 8/8 sheets and 30/30 take blocks INCLUDING
# the moon, lamp and candle setups.  It cost nothing there because every
# `described` names its own source and the drawer weighted it; it is the exact
# configuration that failed on ep08 ("1881 London, gaslight-amber" over a noon
# desert, cause #1) when the setup was weaker.  So the line takes the setup's
# own source when the setup names one, in the words the style wall leaves.

SOURCES = re.compile(
    r"\b(?:lamps?|lamplight|gaslight|gas|candles?|candlelight|fire|firelight|hearth|coals?|embers?|"
    r"grate|lanterns?|torch(?:es)?|stove|forge|windows?|skylight|sun|sunlight|moon|moonlight|"
    r"daylight|flame)\b", re.I)
"""The noun the light line is built on: a practical or a sky source.  `light`
is not one -- "the light comes from the left window" is the window's clause."""

COMPOUNDS = ("bracket", "jet", "lamp", "flame", "light", "slab", "fire")
"""A source noun's own second word: "gas bracket", "window light", "coal fire"."""

SKIP_WORDS = ("a", "an", "the", "one", "two", "its", "his", "her", "of", "and", "in", "on", "at",
              "left", "right", "near", "nearest", "far", "only", "same",
              # verbs and pointers: every ep08 take read "1894, is gaslight" and
              # "that lamp" before these were here (audit 2026-09-22, item 17)
              "is", "was", "are", "were", "be", "that", "this", "these", "those", "which",
              "by", "with", "from", "under", "through")
"""Never the source's adjective: a determiner, a side (the side is the
direction's business) or a filler."""

SIDE = re.compile(r"\b(?:from|at|to|on|along)\s+(?:the\s+|one\s+|(?:behind|above|below) and the\s+)?"
                  r"(left|right)\b", re.I)
"""A FRAME side the source stands at: "from the right", "behind the ridge to the
right", "from above and the left".  `his right cheek` never matches: the side
here follows a preposition of place, not a possessive."""

LIGHT_ADJECTIVES = ("low", "level", "raking", "slanting", "sidelong")
"""The DIRECTIONS words that are adjectives: they prefix a sky source ("low sun")."""

GAS_PARTS = ("lamp", "light", "flame")
"""A gas lamp is a lamp: the one compound whose first word is no adjective to keep."""

FIXED_STYLE_WORDS = 6
"""What `STILLS` / `LIVE` add around the place and the light."""


def clauses(text: str) -> list[str]:
    return [c for c in re.split(r"[,;:.]", text or "") if c.strip()]


def is_lit(clause: str) -> bool:
    """The rule `setup_faults` reads: a practical that is burning, or a sky
    source with a direction."""
    return bool((PRACTICALS.search(clause) and LIT.search(clause))
                or (SKY.search(clause) and DIRECTIONS.search(clause)))


def lit_clause(described: str) -> str:
    """The first clause of a setup's `described` that names its light, a DIRECTED one before a
    glint ("gleaming window glass" lit the Sunday street while "low sun falls from the left" sat
    two clauses on: Jekyll Kawajiri ep01, 2026-10-18)."""
    lit = [c for c in clauses(described) if is_lit(c)]
    return next((c for c in lit if DIRECTIONS.search(c)), lit[0] if lit else "")


WINDOWS = re.compile(r"^windows?$", re.I)


def source_of(clause: str) -> str:
    """The source noun with one qualifying word: "oil lamp", "low moon",
    "gas bracket", "candle".

    A WINDOW is the source only when nothing else in the clause lights the
    place: "lit sash windows and a gas lamp at the kerb" is lit by the lamp,
    and every ep08 street take said "sash windows" (audit item 17)."""
    hits = list(SOURCES.finditer(clause))
    lamps = [h for h in hits if not WINDOWS.match(h.group(0))]
    hit = (lamps or hits or [None])[0]
    if not hit:
        return ""
    before = clause[:hit.start()].split()
    after = clause[hit.end():].split()
    noun = hit.group(0).lower()
    if after and after[0].lower() in COMPOUNDS:
        noun = f"{noun} {after[0].lower()}"
    if before and before[-1].isalpha() and before[-1].lower() not in SKIP_WORDS:
        return f"{before[-1].lower()} {noun}"
    return noun


def side_of(text: str) -> str:
    hit = SIDE.search(text or "")
    return hit.group(1).lower() if hit else ""


def direction_of(clause: str, source: str = "") -> str:
    """How the source's direction is said: a frame side first, else the
    bearing or the opening the clause names, else -- for a SKY source only --
    its adjective (`low sun`).  A practical has a place of its own, and "a low
    fire burning in the hearth" is the fire's word, not the hearth's."""
    if side := side_of(clause):
        return f"from the {side}"
    found = [m.group(0).lower() for m in DIRECTIONS.finditer(clause)]
    for word in found:
        if word in ("behind", "ahead"):
            return f"from {word}"
        if word not in LIGHT_ADJECTIVES:
            return word
    if found and SKY.search(source or ""):
        return found[0]
    return ""


def black_of(text: str) -> str:
    """The named black in `text`, two words where the text gives them ("black
    shadows", "deep shadow"), else the first black word, else nothing."""
    found = []
    for hit in BLACKS.finditer(text or ""):
        before, after = text[:hit.start()].split(), text[hit.end():].split()
        word = hit.group(0).lower()
        if after and BLACKS.fullmatch(after[0].strip(",.;")):
            return f"{word} {after[0].strip(',.;').lower()}"
        if before and before[-1].lower() in ("deep", "hard", "true", "soot"):
            return f"{before[-1].lower()} {word}"
        found.append(word)
    return found[0] if found else ""


def compose(source: str, direction: str, black: str) -> str:
    """`<direction> <source>` for an adjective, `<source> <direction>` for a
    bearing, then the black -- a direction and a black, the house rule.  A
    source that is the direction's own noun ("windows" / "through the two
    windows") is said once: the light through it."""
    noun = source.split()[-1] if source else ""
    if direction in LIGHT_ADJECTIVES:
        head = source if source.startswith(direction) else f"{direction} {source}"
    elif direction and re.search(rf"\b{re.escape(noun)}\b", direction):
        head = f"light {direction}"
    else:
        head = f"{source} {direction}".strip()
    return f"{head}, {black}" if black else head


def shorter(phrase: str) -> str:
    """The phrase without its adjective: "morning sun" -> "sun", "deep shadow"
    -> "shadow".  A compound noun ("gas bracket") keeps both words."""
    words = phrase.split()
    if len(words) == 2 and (words[1] not in COMPOUNDS or words[0] == "gas" and words[1] in GAS_PARTS):
        return words[1]
    return phrase


def budget(where: str, setup=None, rendered: bool = True) -> int:
    """The words the wall leaves the light, for the branch that PRINTS the line: a rendered take
    with a look spends the look's own words (not six), and the atmosphere only where `live`
    says it (under the sky); a drawn sheet's STILLS line has neither."""
    from studio.book_look import under_sky
    fixed = len(_look.split()) if rendered and _look else FIXED_STYLE_WORDS
    air = len(_atmosphere.split()) if rendered and _atmosphere and under_sky(setup) else 0
    return MAX_STYLE_WORDS - fixed - len(where.split()) - air


def fit(source: str, direction: str, black: str, where: str, setup=None, rendered: bool = True) -> str:
    """The phrase in the words the style wall leaves after the place: the source's adjective
    goes first, then the black's, then the direction; past that, nothing."""
    room = budget(where, setup, rendered)
    short = shorter(source)
    for src, way, blk in ((source, direction, black), (short, direction, black),
                          (short, direction, shorter(black)), (short, "", shorter(black))):
        said = compose(src, way, blk)
        if len(said.split()) <= room:
            return said
    return ""


def sentence_of(described: str, clause: str) -> str:
    """The sentence of `described` that holds `clause` ("..., throwing hard yellow light down
    from the upper right": the lamp is named a clause before)."""
    return next((s for s in re.split(r"[;.]", described or "") if clause and clause in s), "")


def sky_free_light() -> str:
    """The episode light for a NIGHT setup that names no source: its sun and daylight words go
    (`lamplight` stands in), because a sun on a street at three in the morning is a fault."""
    if not SKY_SOURCE.search(_light):
        return _light
    return f"lamplight, {black_of(_light)}" if black_of(_light) else "lamplight"


def light_for(setup, rendered: bool = True) -> str:
    """The setup's own light phrase -- its source, its direction and a black --
    with the episode `light` as the fallback for a setup that names no source,
    or whose phrase would fail the vocabulary or the style wall.  A NIGHT setup never falls
    back to a sky source: it keeps its lamp, bare if the wall leaves no room for more."""
    described = getattr(setup, "described", "") or ""
    clause, night = lit_clause(described), time_of(setup) == "night"
    source = source_of(clause) or source_of(sentence_of(described, clause)) or (night and source_of(described))
    if not source:
        return sky_free_light() if night else _light
    black = black_of(described[described.find(clause):]) if clause else ""
    if len(black.split()) < 2:
        black = black_of(_light) or black
    phrase = fit(source, direction_of(clause, source), black, _where, setup, rendered)
    if phrase and not light_faults(phrase):
        return phrase
    return compose(shorter(source), "", shorter(black)) if night else _light


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


SKY_SOURCE = re.compile(r"\b(?:sun|sunlight|sunshine|daylight|dawn)\b", re.I)
"""What may not light a night setup (L28)."""

NIGHT = re.compile(r"(?<!\blast )\b(?:nights?(?![-\w])|midnight|moon(?:light|lit|rise)?|small hours|after dark|"
                   r"(?:in|after) the dark(?=\s*(?:[,.;:…]|in\b|$))|o'clock of a (?:black )?(?:\w+ )?morning|"
                   r"(?:one|two|three|four) in the morning)\b", re.I)
"""The one night vocabulary, `time_of`'s and L33's (wave-2 review: L33 knew "moon" and the reader did not, so
a moonlit road was "day" and L33 refused its words; "night-watchman" and "last night" are no hour)."""


def is_night(setup) -> bool:
    """A setup the hour reader puts at night (`time_of`): QC, the census and L28 read the writer's hour."""
    return time_of(setup) == "night"


DUSK = re.compile(r"\b(?:dusk|sunset|sundown|twilight|gloaming|nightfall)\b", re.I)
EVENING = re.compile(r"\bevening\b(?! dress)", re.I)
"""Dusk when no lamp lights the place: an evening parlour by its fire stays interior-lamp."""
DAWN = re.compile(r"\b(?:dawn|daybreak|sunrise|first light)\b", re.I)
DAYLIT_TEXT = re.compile(r"\b(?:sun|sunlit|sunlight|sunshine|daylight|day|morning|noon|afternoon)\b", re.I)
TIME_SAID = {"night": "at night", "dawn": "at dawn", "day": "by day", "dusk": "at dusk", "interior-lamp": "indoors"}
"""How the take's style line says the hour (craft ruling A17): a time, never a source."""


def clock_of(text: str) -> str:
    """The hour a text names, night first, else ''."""
    for hour, said in (("night", NIGHT), ("dusk", DUSK), ("dawn", DAWN)):
        if said.search(text or ""):
            return hour
    return ""


def time_of(setup, shot=None) -> str:
    """The one hour of a take: the shot's own `time`, else the setup's, else read from the setup's
    `described` and `place_state` (craft ruling A17); "" when no word names one -- an unread hour,
    never a guessed "day" (wave-2 review: four WotW night setups were lit "by day")."""
    said = getattr(shot, "time", "") or getattr(setup, "time", "")
    if said or setup is None:
        return said or ""
    text = f"{getattr(setup, 'described', '') or ''} {getattr(setup, 'place_state', '') or ''}"
    return clock_of(text) or lamp_hour(setup, text) or ("dusk" if EVENING.search(text) else "") \
        or ("day" if DAYLIT_TEXT.search(text) else "")


def lamp_hour(setup, text: str) -> str:
    """A place lit by a burning practical and no day word: interior-lamp indoors, night under the sky."""
    if DAYLIT_TEXT.search(text) or not any(LAMPS.search(c) and LIT.search(c) for c in clauses(text)):
        return ""
    return "night" if getattr(setup, "outdoors", False) else "interior-lamp"


LAMPS = re.compile(r"\b(?:lamps?|lamplight|gaslight|gas|candles?|candlelight|fire|firelight|hearth|grate|coals?|"
                   r"embers?|lanterns?|torch(?:es)?|stove|forge)\b", re.I)
"""A practical that burns: PRACTICALS without the openings (a lit window is daylight's)."""


def style_light(setup=None, shot=None) -> str:
    """What the take's style line says of the light: the hour and a black, never a source or a
    direction -- the block's light sentence owns those (ep01: 28 of 28 takes said the light twice)."""
    black = black_of(light_for(setup)) or black_of(_light)
    return ", ".join(p for p in (TIME_SAID.get(time_of(setup, shot), "") if setup is not None else "", black) if p)


DAYLIT = re.compile(r"\b(?:daylight|sunlight)\b", re.I)
"""A night setup lit by daylight (Jekyll Kawajiri ep01, 2026-10-18): the light cure appended
'Grey daylight through the window' to a street at three in the morning."""


def lit_clauses(described: str) -> list[str]:
    """Comma clauses that light the place: a burning practical, a sky source with a direction,
    or a burning clause right after its practical's ("gas lamps ..., their flames burning")."""
    out = []
    for sentence in re.split(r"[;:.]", described or ""):
        parts = sentence.split(",")
        for k, c in enumerate(parts):
            before = parts[k - 1] if k else ""
            if (PRACTICALS.search(c) and LIT.search(c)) or (SKY.search(c) and DIRECTIONS.search(c)) \
                    or (LIT.search(c) and PRACTICALS.search(before)):
                out.append(c)
    return out


def setup_faults(described: str, outdoors: bool) -> list[str]:
    """A setup names its own light: a practical that is burning, or a sky
    source with a direction, in one clause; and outdoors, never overhead."""
    out = []
    if not lit_clauses(described):
        out.append("`described` names no light source with a direction -- ep09's 'hard morning "
                   "sunlight' is a brightness, not a light; say where it comes from")
    if NIGHT.search(described or "") and (hit := DAYLIT.search(described or "")):
        out.append(f"{hit.group(0)!r} lights a night setup -- the cure's daylight clause drew a lit "
                   f"window into a street at three in the morning")
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
