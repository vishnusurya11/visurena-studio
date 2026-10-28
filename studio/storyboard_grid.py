"""Build the prompt for a multi-panel storyboard: one place, bound people, and
a framing every panel states in the only terms the drawer obeys.

MEASURED 2026-09-20 on Qwen-Image-2.1 (WotW ep05 shots 5-8, four panels, 211 s
at 2048x2048 with 4 references on the fp8 text encoder):

  HELD -- one face per man across four panels, one striped blazer, one sunset,
  one heath; and shot 8 drawn with the two men correctly and differently
  dressed, which is the take H3 returned as one man twice at DQ 100/100.
  DID NOT HOLD -- the head fractions, and the two hats.

So the module says framing as A CUT, not a fraction, and says each wardrobe
item by its SHAPE AND AGAINST THE OTHER MAN'S.
"""
from __future__ import annotations

import re

from studio import cast_alias

ROWS = ("top", "bottom")
COLS = ("left", "right")
COUNTS = {1: "one", 2: "two", 3: "three", 4: "four", 6: "six", 8: "eight",
          9: "nine", 10: "ten", 12: "twelve", 16: "sixteen"}


def cell_names(cols: int, rows: int) -> list[str]:
    """Where each panel sits, said the way a person would say it.

    Two rows have words ('top', 'bottom'); more than two do not, and inventing
    one ('upper-middle') names a cell the drawer cannot place."""
    if rows == 2 and cols == 2:
        return [f"{r}-{c}" for r in ROWS for c in COLS]
    out = []
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            side = COLS[c - 1] if cols == 2 else f"column {c}"
            out.append(f"row {r} {side}")
    return out


def geometry(cols: int, rows: int, style: str, numbered: bool = False) -> str:
    """`numbered` letters a label into each corner, and defaults OFF.

    MEASURED 2026-09-20: asked for "the panel number drawn small in the
    top-left corner", Qwen drew the SHOT SIZE there instead -- WIDE, MEDIUM,
    INSERT lettered into the picture. On a page a person reads, that is a help.
    These panels go on to be H3 ref2va references, and lettering in a reference
    is lettering in the video -- so the default forbids it in the POSITIVE
    prompt rather than hoping the negative catches it, which it did not."""
    n = cols * rows
    if n == 1:
        # A GRID OF ONE IS NOT A GRID. MEASURED 2026-09-20 on the full ep05
        # board: six groups held a single shot -- 8, 13, 14, 25, 26, 27 -- and
        # this said "a strict grid of 1 columns and 1 rows, one panels in all".
        # All six came back MOSAICS, three-by-three sheets of the same picture
        # repeated small with borders and gutters. The arithmetic was ignored
        # and the words "storyboard" and "grid" were obeyed.
        return ("ONE SINGLE PICTURE that fills the whole image edge to edge. It is not a "
                "storyboard, not a grid, not a sheet and not a collage: there are no panels, "
                "NO BORDERS, NO GUTTERS, no dividing lines and no repeated or tiled copies of "
                "anything. NO TEXT, NO LETTERING, no numbers, no words, no labels and no "
                f"captions anywhere in it. The picture is {style}.")
    said = (f"A storyboard drawn as a strict grid of {cols} columns and {rows} rows, "
            f"{COUNTS.get(n, n)} panels in all, every panel exactly the same size and shape, "
            f"thin white gutters between the panels and a thin black border around each one. ")
    said += ("The panel number is drawn small in the top-left corner of its own panel. "
             if numbered else
             "There is NO TEXT, NO LETTERING, no numbers, no words, no labels and no captions "
             "anywhere in the image or in any panel. ")
    return said + f"Every panel is {style}."


def place_clause(slots: list[int], described: str) -> str:
    """One location, named by every reference slot that shows it."""
    refs = " and ".join(f"<image{n}>" for n in slots)
    return (f"THE PLACE. Every panel happens at the same single location, shown in {refs}: "
            f"{described}. The location is identical in every panel and never changes -- the same "
            f"ground, the same horizon, the same weather and the same hour of light in all of them.")


def cast_clause(people: list[dict]) -> str:
    """Each person bound to a slot, and told apart from the others by SHAPE.

    `against` is what the item is NOT, and it is not decoration: the neighbour's
    soft panama came back as the narrator's flat boater, and a hat named without
    a shape is a hat the drawer replaces with the commonest one in the scene."""
    said = []
    for p in people:
        # A person with no sheet is described in WORDS and cited to no slot.
        # MEASURED 2026-09-20 on ep05 `dusk`: shot 13 names the newspaper boy,
        # the hand-written cast dict had no entry, the binding dropped him
        # without a word, and the panel came back a man selling apples. A
        # person the panels name reaches the prompt drawn or not.
        where = (f"the person in <image{p['ref']}>" if p.get("ref") is not None
                 else "a person with no reference picture, drawn from these words alone")
        said.append(f"{p['name']} is {where}: {p['wear']} -- "
                    f"{p['against']}. Every panel {p['name']} appears in gives him exactly this "
                    f"face and exactly these clothes.")
    if len(people) > 1:
        names = " and ".join(p["name"] for p in people)
        said.append(f"{names} are never dressed alike and never wear the same hat, in any panel, "
                    f"without exception.")
    if people:
        said.append("Each of these people stands ONLY IN THE PANELS THAT NAME THEM below, and in "
                    "no other panel. A panel that names nobody has nobody in it.")
    return "\n".join(said)


def peopling_clause(who: list[str]) -> str:
    """Who stands in the panel -- or, for an empty panel, what it is instead.

    MEASURED 2026-09-20 on ep06 `beam`: "NO NAMED CHARACTER appears in this
    panel at all" put `character` in the sentence and took nothing out of the
    picture. An empty panel is described by what it holds.
    """
    if not who:
        return "This panel is a picture of the place alone: ground, growth, sky and built things."
    return f"In this panel: {', '.join(who)}; no other named person is in it."


def panel_block(number: int, where: str, size: str, body: str, cut: str,
                who: list[str] | None = None, absent: list[str] | None = None) -> str:
    """One panel: its cell, its size, its own words, where the frame cuts, and
    WHO STANDS IN IT.

    The size is said twice because said once it lost to the prose -- panel 1
    asked MEDIUM and came back a full-length wide.

    `who` exists because binding a person to a slot says WHO HE IS and says
    nothing about WHERE HE IS. MEASURED 2026-09-20 on ep05 `dusk`: with the
    binding finally correct, one boy with one face and one corduroy jacket
    stood in four of six panels, when only shot 13 names him. The cast clause
    promised "every panel he appears in" and no line anywhere said which those
    were, so he appeared in all of them."""
    said = f"PANEL {number}, {where} -- {size}. {body} The framing: {cut}."
    if who is not None:
        said += " " + peopling_clause(who)
        for name in (absent or []):
            if name not in (who or []):
                said += f" {name} does not appear in this panel."
    return said + f" This panel is a {size}."


def grid_prompt(shots: list[dict], cols: int, rows: int, place: tuple[list[int], str],
                cast: list[dict], style: str, numbered: bool = False) -> str:
    """The whole prompt. Refuses a shot list that leaves a cell empty."""
    cells = cell_names(cols, rows)
    if len(shots) != len(cells):
        raise ValueError(f"{len(shots)} shots for {len(cells)} cells: a blank cell is a cell "
                         f"the drawer fills with its own invention")
    everyone = [p["name"] for p in cast]
    if len(shots) == 1:
        # One shot is one picture: "PANEL 1, row 1 column 1" invites the sheet
        # straight back in, so the block loses its heading and its cell.
        s = shots[0]
        blocks = [f"{s['size']}. {s['body']} The framing: {s['cut']}. "
                  f"This picture is a {s['size']}."]
    else:
        blocks = [panel_block(i, where, s["size"], s["body"], s["cut"],
                              who=s.get("who"), absent=everyone)
                  for i, (where, s) in enumerate(zip(cells, shots), start=1)]
    parts = [geometry(cols, rows, style, numbered), place_clause(*place)]
    if cast:
        parts.append(cast_clause(cast))
    return "\n\n".join(parts + blocks)


# ---- v2: the subject first (audit 2026-09-22, Tier 3 item 19) ------------------

STYLE_V2 = ("Drawn in the art style of <image{n}>: angular stylised 3D shapes, visible "
            "brush-stroke colour texture, flat high-chroma colour.")
"""18 words where v1 spent 70, mostly negations. v1's own docstring measured
that pointing at the slot works and describing the style in words bought
nothing."""

GRID_PANEL = re.compile(r"\b(the|this|every|each|a|one|that|any|its own|no other)\s+panel\b(?!s)(?!\s+of\b)", re.I)
""""panel" where it means the grid's cell: a determiner right before the singular.
Jekyll ep01 (G1): the blind `\\bpanels?\\b` made the door's panels "a match on the
picture of the blistered door" and "its picture streaked black" -- a door
"picture" is how a painting or a placard grows on it.  "its panels", "the panels
of the door" and "blistered brown panels" are the scene's and stay."""


def _one_picture(text: str) -> str:
    """A single picture never hears "panel" or "storyboard" for its own cell: the
    model obeys the word over the arithmetic (ep05's six 1x1 groups came back
    mosaics).  A noun of the scene is never touched."""
    text = GRID_PANEL.sub(lambda m: f"{m.group(1)} picture", text)
    return re.sub(r"\bstoryboard\b", "picture", text, flags=re.I)


def _who_v2(who: list[str], extras: int) -> str:
    """Who is in it: the named, else the declared unnamed, else the place alone."""
    noun = "person" if extras == 1 else "people"
    if who and extras:
        return f"In it: {'; '.join(who)}; and {extras} unnamed distant {noun}, none of them a named person."
    if who:
        return f"In it: {'; '.join(who)}."
    if extras:
        return f"In it: {extras} unnamed {noun}, none of them a named person."
    return "It is a picture of the place alone: ground, growth, sky and built things."


def worn_items(wear: str, most: int = 5) -> list[str]:
    """The row's clothes after "Wearing:": each sentence cut at a colon (what
    follows one is parts of the same garment), then split on commas. The face
    is the sheet's; these are what a panel drops (ep09 A/B: bound by name alone
    the wife lost her shawl; cut at the first comma she lost her skirt's green,
    which moved to her blouse)."""
    _, _, clothes = wear.partition("Wearing:")
    items = [i.strip().rstrip(".") for s in clothes.split(". ") for i in re.split(r"[,;]", s.split(":", 1)[0])]
    return [i for i in items if i and not PHYSIQUE.search(i)][:most]


PHYSIQUE = re.compile(r"\b(?:compact|upright|broad-shouldered|narrow-shouldered|narrow-chested|heavy-set|"
                      r"heavy jaw|jaw|slight|frame|lean|corded|knuckly|man about town|well-dressed|build|"
                      r"stature|dwarfish|pallor|physique|hands?|limbs|handsome)\b", re.I)
"""Body words a look's `top` layer carried as clothes (Jekyll ep01 G5): Enfield
"wears: ... compact; upright; ... heavy jaw", Hyde "wears: respectable; well-fitting
clothing on a small; slight; narrow-shouldered frame; lean; corded"."""
BODY_TAIL = re.compile(r"\s+(?:on|of)\s+(?:a|an|his|her)\b.*$", re.I)


def garment(clause: str) -> str:
    """One `top` clause as clothes alone: a body tail ("on a small, slight frame")
    cut, then every comma part that names the body dropped."""
    tail = BODY_TAIL.search(clause)
    if tail and PHYSIQUE.search(tail.group(0)):
        clause = clause[:tail.start()]
    parts = [p.strip() for p in clause.split(",") if p.strip() and not PHYSIQUE.search(p)]
    return ", ".join(parts).strip().rstrip(".")


def clothes_of(layers: dict) -> list[str]:
    """What a person WEARS, read off the look's layers: headwear, then each `top`
    clause as a garment.  Never hair, face or build -- the sheet carries those."""
    head = [(layers.get("headwear") or "").strip().rstrip(".")]
    tops = [garment(c) for c in re.split(r";\s*", layers.get("top") or "")]
    return [c for c in head + tops if c]


HEADWEAR = re.compile(r"\b(?:hat|boater|cap|bonnet|toque|helmet|bowler|busby)\b", re.I)
BAREHEADED = re.compile(r"\bbare-?headed\b", re.I)


def bareheaded(name: str, shots: list[dict]) -> bool:
    """Does a panel this person is in say they are bareheaded? ep09 shot 11
    put the boater in his hand while the binding put it on his head: both drawn."""
    return any(BAREHEADED.search(s["body"]) for s in shots if name in (s.get("who") or []))


BELOW_CHEST = re.compile(r"\b(?:trousers|breeches|boots?|shoes|socks|stockings|stockinged|feet|"
                         r"skirt|petticoats?|gaiters|hips|knees?)\b", re.I)


def chest_up(name: str, shots: list[dict]) -> bool:
    """Is every picture this person is in a close of some kind? ep13: six closes
    drew whole seated figures, the binding line having listed trousers and socks."""
    mine = [s for s in shots if name in (s.get("who") or [])]
    return bool(mine) and all("CLOSE" in s["size"] for s in mine)


def hands_only(name: str, shots: list[dict]) -> bool:
    """Is every picture this person is in an INSERT?  Then only his hands are in
    it (Jekyll ep01 G6: shots 9 and 10, inserts on a hand, came back full-length)."""
    mine = [s for s in shots if name in (s.get("who") or [])]
    return bool(mine) and all(s.get("size") == "INSERT" for s in mine)


def noun_of(p: dict) -> str:
    """man, woman, boy, girl or creature (grids.person_noun); 'person' when unknown."""
    return p.get("noun") or "person"


def slot_phrase(p: dict) -> str:
    """How a staged person is said: "the girl in <image1>", never "the person"
    for someone whose row says who she is (Jekyll ep01 G3)."""
    return f"the {noun_of(p)} in <image{p['ref']}>"


def _items(p: dict, bare: bool, chest: bool) -> list[str]:
    """The clothes a binding lists: the look's (`clothes`) else the row's worn
    items; a bareheaded panel drops the hat, a chest-up one what is below it."""
    items = list(p["clothes"]) if p.get("clothes") is not None else worn_items(p.get("wear", ""))
    if chest:
        items = [", ".join(x for x in (LEG_LENGTH.sub("", y) for y in i.split(", ")) if not BELOW_CHEST.search(x))
                 for i in items]
    return [i for i in items if i and not (bare and HEADWEAR.search(i))]


LEG_LENGTH = re.compile(r"\b(?:knee|ankle|calf|thigh|hip|floor)-(?:length|high|deep)\s+", re.I)
"""A garment's length said by a leg word: the word goes, the garment stays.  BELOW_CHEST read "knee" in
Hyde's "knee-length black double-breasted coat" and the chest-up binding dropped his coat while the panel
gripped its collar (ep01 s09, craft ruling A21)."""


HAND_WEAR = re.compile(r"\b(?:gloves?|mittens?|cuffs?|sleeves?|rings?)\b", re.I)


def sleeves_of(items: list[str]) -> list[str]:
    """What a hands-only insert shows of a person's clothes: the first garment's
    head (the coat its sleeves belong to) and anything worn on the hand."""
    parts = [x.strip() for i in items for x in i.split(",") if x.strip()]
    coat = [parts[0]] if parts and not HAND_WEAR.search(parts[0]) else []
    return coat + [x for x in parts if HAND_WEAR.search(x)]


def _binding(p: dict, bare: bool = False, chest: bool = False, hands: bool = False) -> str:
    who, ref = slot_phrase(p), p["ref"]
    if hands:
        his = "her" if noun_of(p) in ("woman", "girl") else "his"
        worn = " and ".join(f"{his} {s}" for s in sleeves_of(_items(p, True, False)))
        return f"Only the hands of {who} are in the picture{', in the sleeves of ' + worn if worn else ''}, as drawn on <image{ref}>."
    items = _items(p, bare, chest)
    # ep16 shot 19: a wide naming one woman drew all four poses of her
    # turnaround sheet as four women; the sheet is one person, drawn once.  The staged picture is the
    # one-figure front crop since ep16, so "a reference sheet ... seen from several angles" was false (A21)
    once = f" <image{ref}> shows one {noun_of(p)}, drawn exactly once in each picture."
    head = who[0].upper() + who[1:]
    return (f"{head} wears: {'; '.join(items)}." if items else f"{head}.") + once


UNWRITTEN = "No name, word or label is written anywhere in the picture."
"""ep14 (2026-09-29): "In it: GEORGE" and "NEWSPAPER BOY is the person in <image2>"
came back as a placard lettered GEORGE NEWSPAPER GEORGE and a paper lettered
NENSPAPER BOY on the last shot: the drawer letters a capitalised name.  People are
named by their slot; a person with no sheet by plain lower-case words."""

BLANK = "Every plate, sign and paper in the picture is plain and blank, unlettered."
"""The affirmative half of UNWRITTEN, said only when the words hold a thing that
carries lettering (Jekyll ep01 G8: "polished brass plates" on three setups, a
folded cheque in shot 10)."""
BAIT = re.compile(r"\b(?:plates?|signs?|signboards?|cheques?|letters?|placards?|notices?|posters?|"
                  r"bills?|newspapers?)\b", re.I)


def plain_plates(text: str) -> str:
    """'(well-)polished brass plate(s)' -> 'plain (well-)polished brass plate(s)', once;
    a doubled 'plain plain' (a plan edited by hand) said once."""
    text = re.sub(r"(?i)(?<![\w-])(?<!plain )((?:well-)?polished brass plate)", r"plain \1", text or "")
    return re.sub(r"(?i)\b(plain)(?:\s+plain\b)+", r"\1", text)


def bait_in(shots: list[dict], described: str) -> bool:
    return bool(BAIT.search(" ".join([described or ""] + [s.get("body", "") for s in shots])))


def called(cast: list[dict]) -> dict[str, str]:
    """How the prompt says each person: their slot, never their name.

    A face with NO sheet carries its WHOLE row in the same plain lower-case
    words (ep16: "a mrs. elphinstone" with no wardrobe drew as a purple clone of
    the sheeted sister; ep17: three fragments of the Martian row drew a naked
    humanoid)."""
    out = {}
    for p in cast:
        words = re.sub(r"\s+", " ", str(p["name"])).strip().lower()
        if p.get("ref"):
            out[p["name"]] = slot_phrase(p)
            continue
        if p.get("line"):                  # the look layers, short, naming nobody (Jekyll ep01 G2)
            out[p["name"]] = p["line"]
            continue
        whole = " ".join(str(p.get("wear", "")).split()).rstrip(". ").lower()
        sep = (": ", "") if p.get("noun") == "creature" else (" (", ")")
        out[p["name"]] = f"a {words}{sep[0]}{whole}{sep[1]}" if whole else f"a {words}"
    return out


def _phrases(cast: list[dict]) -> dict[str, dict]:
    """{phrase lower-cased: person} for every way the plan says someone: epithets,
    display, name.  A phrase two people share stays with the first."""
    from studio.scene_cast import COMMON
    out: dict[str, dict] = {}
    for p in cast:
        for said in [*(p.get("aliases") or []), p.get("display") or "", p.get("name") or ""]:
            if said.strip() and said.strip().lower() not in COMMON:   # "CHILD" is a noun, not a name
                out.setdefault(said.strip().lower(), p)
    return out


def _said_as(p: dict, phrase: str, aliases: set) -> str:
    """A matched phrase as the prompt says it: the slot; else an epithet's own
    words; else a name in plain lower-case words (ep14: the drawer letters a name)."""
    if p.get("ref"):
        return slot_phrase(p)
    epithet = phrase.lower() in aliases and not TITLED.match(phrase)
    return phrase if epithet or not p.get("plain") else p["plain"]


TITLED = re.compile(r"(?i)(?:mr|mrs|dr|miss|sir|lady|lord)\b")
"""A tag "Mr. Enfield (...)" is a name, not an epithet: said plain when unstaged."""


def _slotted(body: str, cast: list[dict]) -> str:
    """A STAGED person's names AND epithets in the panel prose become their slot
    phrase, and the description in brackets after them goes: the sheet and its
    wears line are the one description (owner 2026-10-15; ep16 attempt 4 drew
    two brothers from 'the person in <image1>' beside 'the brother').  An
    unstaged person keeps his words without the brackets (the who-line dresses
    him).  One pass, longest phrase first, so no slot phrase is re-read."""
    table = _phrases(cast)
    if not table:
        return body
    alts = "|".join(re.escape(s) for s in sorted(table, key=len, reverse=True))
    said = re.compile(rf"(?i)\b({alts})(?!\w)(?:\s*\([^()]*\))?")
    epithets = {a.lower() for p in cast for a in p.get("aliases") or []}
    body = said.sub(lambda m: _said_as(table[m.group(1).lower()], m.group(1), epithets), body)
    body = cast_alias.strip_labelled(body)
    body = re.sub(r"(?i)\b(?:the|a|an) (the \w+ in <image\d+>)", r"\1", body)
    return re.sub(r"(^|[.!?]\s+)the (\w+ in <image\d+>)", r"\1The \2", body)


def _who_said(name: str, p: dict | None, say: dict, seen: set, insert: bool) -> str:
    """One who-line entry: the slot (its hands in an insert), else the words once."""
    said = say.get(name, name.lower())
    if p is not None and p.get("ref"):
        return f"the hands of {said}" if insert else said
    if p is not None and p.get("line") and name in seen:
        return f"the same {noun_of(p)} again"
    seen.add(name)
    return said


def _unnamed(shots: list[dict], cast: list[dict]) -> list[dict]:
    """The shots with every named person said by slot, in the who-line AND the
    prose; an unstaged person's layers line is said once per prompt."""
    say, by, seen = called(cast), {p["name"]: p for p in cast}, set()
    return [{**s, "who": [_who_said(n, by.get(n), say, seen, s.get("size") == "INSERT")
                          for n in (s.get("who") or [])],
             **({"body": _slotted(s["body"], cast)} if "body" in s else {})} for s in shots]


def _block_v2(label: str, s: dict) -> str:
    return (f"{label}{s['size']}: {s['body']} Framing: {s['cut']}. "
            f"{_who_v2(s.get('who') or [], s.get('extras', 0))}")


TIGHT = ("MEDIUM CLOSE", "BIG CLOSE-UP", "CLOSE", "INSERT")
"""Sizes whose picture is a subject, not a place. ep10 shot 1, a medium close on
the wife, drew the whole house front five seeds running (her face 0.02-0.04 of
the frame) under a 100-word description of that house."""


def place_head(described: str) -> str:
    """The place's name: its first clause.  ep14's writer wrote inventories with
    no colon and no light clause, and `split(":")` handed a 1x1 close the whole
    attic-and-street list (2026-09-28)."""
    return re.split(r"[:;,]", described, 1)[0].strip()


def brief_place(described: str, light: str = "") -> str:
    """The place's name and its light: the staged picture carries the rest."""
    head = place_head(described)
    if not light and "; the light is" in described:
        light = described[described.find("; the light is") + 2:]
    if light and not light.lower().startswith("the light"):
        light = f"the light is {light}"
    return f"{head}; {light}" if light else head


ROOM_V2 = ("<image{n}> is this exact room, already drawn: every panel is set in it, with the "
           "same walls, furniture, windows and light.")
"""A chained grid's room -- the setup's first-drawn panel (studio/grid_room)."""
PLACE_V2 = ("<image{n}> is this exact place, already drawn: every panel is set in it, with the "
            "same ground, buildings and light.")
"""ROOM_V2 under the sky (`Setup.outdoors`): 16 of ep01's 22 grids called a street a room with furniture (A21)."""
DOUBLE_STOP = re.compile(r"(?<!\.)\.\.(?!\.)")
"""A clause that ends in a stop, joined by a template that adds one (7 of ep01's 22 grids)."""
CONSTANT_V2 = ("The location is identical in every panel and never changes -- the same ground, "
               "the same horizon, the same weather and the same hour of light in all of them.")
"""v1's sentence, dropped by v2 on 2026-09-22 and back on 2026-09-28: nothing else
in the prompt said the place may not change between panels."""


def grid_prompt_v2(shots: list[dict], cols: int, rows: int, place: tuple[list[int], str],
                   cast: list[dict], style_slot: int, props: list[dict] | None = None, *,
                   room: int | None = None, geometry: str = "", light: str = "",
                   style: str = "", medium: str = "illustration", outdoors: bool = False) -> str:
    """Layout (one line), the room when the grid is chained, the panels SUBJECT
    FIRST, one binding line per person, the place with its geometry, the style.
    No description is truncated -- the sheet in the slot carries the face and
    the panel prose carries the tag -- and a single picture never says
    storyboard, grid or panel."""
    cells = cell_names(cols, rows)
    if len(shots) != len(cells):
        raise ValueError(f"{len(shots)} shots for {len(cells)} cells")
    single = len(shots) == 1
    shots = [{**s, "body": plain_plates(s["body"])} if "body" in s else s for s in shots]
    place, geometry = (place[0], plain_plates(place[1])), plain_plates(geometry)
    said = _unnamed(shots, cast)
    if single:
        layout = f"One full-frame {medium}, edge to edge, with no lettering anywhere."
        blocks = [_one_picture(_block_v2("", said[0]))]
    else:
        layout = (f"A storyboard of {len(shots)} panels in {cols} columns and {rows} rows, all the "
                  f"same size, thin white gutters between them, no lettering anywhere.")
        blocks = [_block_v2(f"PANEL {i} ({where}), ", s)
                  for i, (where, s) in enumerate(zip(cells, said), start=1)]
    binding = [_binding(p, bareheaded(p["name"], shots), chest_up(p["name"], shots), hands_only(p["name"], shots))
               for p in cast if p.get("ref")]
    # A PROP IS AN OBJECT, bound to its sheet: ep10's tripod drawn from words
    # alone would differ in every panel (ep10 prep audit, 2026-09-23).
    binding += [f"{p['name']} is the object in <image{p['ref']}>, exactly as drawn there."
                for p in props or [] if p.get("ref")]
    people = [f"<image{p['ref']}>" for p in cast if p.get("ref")]
    if len(people) > 1:
        binding.append(f"The people in {' and '.join(people)} are never dressed alike.")
    binding.append(UNWRITTEN + (" " + BLANK if bait_in(shots, place[1]) else ""))
    slots = list(place[0]) + ([room] if room is not None and room not in place[0] else [])
    refs = " and ".join(f"<image{n}>" for n in slots)
    said = brief_place(place[1], light) if all(s["size"] in TIGHT for s in shots) else place[1]
    where = (f"The picture is set at {refs}: {said}." if single else
             f"Every panel is set at {refs}, at the same hour: {said}. {CONSTANT_V2}")
    if geometry.strip():
        where += " " + geometry.strip()
    lead = [(PLACE_V2 if outdoors else ROOM_V2).format(n=room)] if room is not None else []
    parts = [layout] + lead + blocks + binding + [where, (style or STYLE_V2).format(n=style_slot)]
    return "\n\n".join(DOUBLE_STOP.sub(".", _one_picture(x) if single else x) for x in parts)


def grid_shape(n: int) -> tuple[int, int]:
    """(cols, rows) for n panels, as square as n allows and never with a hole.

    A blank cell is a cell the drawer fills with its own invention, so the
    product must be exactly n -- a prime count gets a single strip."""
    best = (n, 1)
    for cols in range(1, n + 1):
        if n % cols:
            continue
        rows = n // cols
        if abs(cols - rows) < abs(best[0] - best[1]):
            best = (cols, rows)
    return best


def grid_groups(shots: list[dict]) -> list[dict]:
    """Split shots into grids by WHO IS IN THEM, keeping plan order.

    MEASURED 2026-09-20, ep05 `dusk`, and the finding this module was written
    for: A STAGED CHARACTER REFERENCE IS CAST INTO ANY PANEL WHOSE PROSE CALLS
    FOR UNNAMED PEOPLE -- a crowd, a band of figures on a skyline, a
    washerwoman -- however plainly that panel says he is not in it.

    Three wordings failed in a row: binding him to a slot, naming who stands in
    each panel, then forbidding him by name in every panel he was absent from.
    He stood in four panels of six, and only one shot named him.

    Dropping his sheet from the staging, with the words left exactly as they
    were, emptied him out of every one of them -- and the crowd came back
    individuated, an old bearded man, a woman in a shawl, a younger man, no two
    alike, which is the clone fault that has dogged every H3 crowd shot.

    With this model the references are stronger than the prose. Presence is
    decided by WHAT IS PASSED, not by what is written. So shots that name
    nobody are drawn in a grid with no character sheet staged at all, and shots
    are otherwise grouped by the exact cast they share.
    """
    order, groups = [], {}
    for shot in shots:
        key = tuple(shot.get("faces") or ())
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(shot)
    return [{"faces": key, "shots": groups[key]} for key in order]


def style_clause(anchors, described: str) -> str:
    """The look, POINTED AT a reference slot rather than described in words.

    MEASURED 2026-09-20, and the owner saw it before any gate did: the panels
    were not in the book's style. The Krea2 house anchor had been passed as
    <image1> from the first render, and Qwen took the HEATH out of it -- the
    pines, the sand ring, the purple-brown heather -- while rendering all of it
    in its own default look: photographic depth of field, soft cinematic light,
    photoreal skin and cloth.

    A reference is used for CONTENT unless the prompt says to use it for STYLE.
    Four renders of description bought nothing; naming the slot flipped it on
    the first try at the same seed and the same 60 s.

    It matters past the storyboard: H3 ref2va conditions on its references and
    takes their look, which is why the delivered episodes are in the Krea2
    style at all. A panel drawn in the wrong style drags the video with it.

    ANCHOR IT ON A CAST SHEET, NOT ON THE LOCATION. Owner, 2026-09-20: "the
    style of the ref images is not getting transferred into the storyboard
    pieces." Naming a slot had got most of the way and not all of it, and the
    slot named was the location wide -- itself a fairly flat painted landscape,
    so flat painted landscape is what came back. The CAST SHEETS carry the
    house look unmistakably: modelled three-dimensional figures with brush
    texture over solid surfaces. Anchored there, at the same seed and the same
    25 steps, the figures come back modelled the way the sheet models them and
    the poster flatness goes. Raising the encoder to 1536 and the sampler to 40
    steps on top of that bought very little for the extra time."""
    slots = [anchors] if isinstance(anchors, int) else list(anchors)
    cited = " and ".join(f"<image{n}>" for n in slots)
    return (f"DRAWN IN EXACTLY THE ART STYLE OF {cited}, copied from it and not invented: "
            f"{described}. Match its palette, its brush texture and its level of stylisation "
            f"exactly. NO photographic depth of field, no camera blur, no photoreal skin or "
            f"cloth, no film grain.")


def whole_subject(subject: str, focus: str) -> str:
    """An insert on PART of a living thing still contains the whole thing.

    OWNER 2026-09-20, on ep05 shot 14: "just horse head can't exist, it should
    be whole horse, we need to focus on the horse head."

    The plan asks for "the black shape of a cab horse's head down in a nosebag",
    and `insert` was carried through as "the panel holds the object alone, close
    and filling the frame". A nosebag is an object; a horse is not. The panel
    came back a head with no body over the gravel, the hansom's shafts barely
    reading behind it.

    The part is what the framing ATTENDS to. The creature is what the panel
    CONTAINS. They are two different statements and only one of them was made."""
    return (f"The panel contains {subject} WHOLE and unbroken -- the entire body inside the "
            f"frame, standing on visible ground, never a cropped part on its own and never a "
            f"detail floating with no body attached. The framing attends to {focus}: that is "
            f"where the light falls, that is what is sharpest and nearest the centre, and the "
            f"rest of {subject} reads clearly around it.")


def cover(group: list[int], before: list[int] | None = None, size: int = 4) -> list[list[int]]:
    """Cover `group` with windows of EXACTLY `size`, overlapping where it must.

    OWNER 2026-09-20: "i donno why you did 1*1 it is useless. we do only
    storyboards .. 2*2 min."

    Right twice over. A single picture is not a storyboard, and asking for one
    as a 1x1 grid produced six mosaics on the ep05 board -- tiled sheets of the
    same picture repeated small -- because the words "storyboard" and "grid"
    beat the arithmetic of "1 columns and 1 rows".

    A group that does not divide by `size` gets an OVERLAPPING last window
    rather than a short one, and a group shorter than `size` reaches back into
    `before` for its remainder. The overlap is not waste: a shot drawn twice is
    a second take of it, for nothing.
    """
    before = list(before or [])
    if len(group) < size:
        short = size - len(group)
        if len(before) < short:
            raise ValueError(f"{len(group)} shots and only {len(before)} before them: "
                             f"fewer than {size} to draw, and a short grid is not a grid")
        return [before[-short:] + list(group)]
    out, start = [], 0
    while start + size <= len(group):
        out.append(list(group[start:start + size]))
        start += size
    if start < len(group):                       # a tail: slide the last window back
        out.append(list(group[-size:]))
    return out


def no_duplicates(names: list[str]) -> str:
    """Say the duplication out loud, which the vendor guidance asks for.

    MEASURED 2026-09-20 and RESEARCHED the same day: reference images duplicate
    their subject, and the published method for multi-reference work says to
    state it -- "no duplicated product, no duplicated helmet" -- rather than
    hope. ep05 put two identical neighbours side by side in one panel and three
    men in shot 8 where the plan names two."""
    if not names:
        # A GRID WITH NO CAST SAYS NOTHING ABOUT PEOPLE. This used to emit
        # "every person in the picture is a different person ... no figure is
        # repeated", which names a person, a face, a build, an outfit and a
        # figure into a picture that has none -- and MiniMax reads no negation,
        # so what arrives is person, figure, outfit. ep05 shot 21 and ep06
        # shots 2, 15, 16 and 17 all came back with the same pink cartoon doll,
        # and all five are grids with no cast.
        return ""
    said = ", ".join(f"no duplicated {n}" for n in names)
    return (f"{said}. Each of these people appears EXACTLY ONCE in a panel, never twice, never "
            f"as a pair and never as a reflection; and no other figure copies their face or "
            f"their clothes.")


BEAT_CELLS = ("top-left", "top-right", "bottom-left", "bottom-right")


def take_board(size: str, at_rest: str, beats: list[str], cut: str, panels: int = 4,
               strict: bool = True, pose: bool = False) -> str:
    """ONE take, broken into beats: the storyboard a ref2v call is given.

    OWNER 2026-09-20: "i need a storyboard of each shot .. or take .. every
    ref2v call to have a storyboard to generate direction."

    The first board built was one PANEL PER SHOT across a whole setup -- a page
    to read, which he said looks right for an episode and is not what a take
    needs. A take needs its OWN shot in time order, first frame to last, so the
    grid carries the camera move and the action into the render. That is what
    direction is.

    Every panel is the same shot: same camera position, same lens, same place,
    same people, same light. Only the action advances. Four different framings
    would be four shots.

    MEASURED 2026-09-20, AND IT DOES NOT WORK. Four ways of asking, on ep05
    shot 5, one variable at a time: strict with the motion's own verbs; loose,
    with "EACH PANEL IS VISIBLY DIFFERENT FROM THE ONE BEFORE IT"; the beats
    rewritten as the pose the body is in at the END of each action; and loose
    and pose together. All four returned the same man standing the same way
    four times -- no lean onto the stick, no ferrule driven into the sand, no
    blazer swinging open, no head shaken, in any of them.

    The vendor's own sentence says why, and I read past it first: the model
    "turns a three-view character reference into a complete storyboard",
    composing DIFFERENT SCENES. Panels differ when the panels are different
    shots -- another size, another subject -- which is exactly why the
    multi-shot grid works. "The same shot one second later" gives it nothing to
    vary.

    KEPT, NOT DELETED, so the next person does not spend the GPU finding this
    out again. The owner chose the other route: one panel per take out of a
    multi-shot grid, with the direction left in the ref2v prompt.
    """
    hold = ("the SAME CAMERA POSITION, the SAME LENS, the same place, the same people and the "
            "same light in all four panels. Nothing moves between the panels except what each "
            "beat below says moves."
            if strict else
            "the same place, the same people and the same light in all four panels, and one "
            "continuous action running through them. EACH PANEL IS VISIBLY DIFFERENT FROM THE "
            "ONE BEFORE IT: the body has moved, the pose has changed, the camera has travelled. "
            "Four panels that look alike are four copies, not a shot.")
    said = [f"FOUR PANELS OF ONE CONTINUOUS SHOT, in time order, left to right and top to "
            f"bottom: panel 1 is the FIRST FRAME of the shot and panel 4 is its LAST FRAME. "
            f"It is one {size} shot throughout -- {hold} The framing {cut}."]
    ordered = list(beats)[:panels - 1]
    while len(ordered) < panels - 1:                # a blank cell invites invention
        ordered.append("the action of the beat before it continues, a little further on")
    said.append(f"BEAT 1, {BEAT_CELLS[0]} -- the shot at rest, before anything moves: {at_rest}")
    for i, beat in enumerate(ordered, start=2):
        # A drawer draws a POSE, not a verb: "he leans his weight onto the stick
        # and drives the ferrule into the sand" is a second of motion, and what
        # a panel can hold is the body at the END of it.
        body = (f"the exact moment this has just finished happening, drawn as the pose the body "
                f"is in at the END of it: {beat}" if pose else beat)
        said.append(f"BEAT {i}, {BEAT_CELLS[i - 1]} -- {body}")
    return "\n\n".join(said)


def beats_of(motion: str) -> list[str]:
    """The actions in a shot's motion line, in the order they happen.

    The plan writes a take's motion as clauses joined by semicolons -- the
    camera's travel, then what the subject does, then what settles -- which is
    already a beat list; it has only never been read as one."""
    return [b.strip().rstrip(".") for b in (motion or "").split(";") if b.strip()]


SEAM_PALE, SEAM_FLAT, SEAM_MOST = 235.0, 8.0, 0.25
"""A seam row is paler than `SEAM_PALE`, varies by less than `SEAM_FLAT` along
its length, and no more than `SEAM_MOST` of a side may be shaved: a picture
that is genuinely pale all over is a picture, not a gutter."""


def seam_box(frame) -> tuple:
    """(left, top, right, bottom) with the panel's pale gutter measured off.

    `panel_box` sheds a FIXED number of pixels, which was enough for every grid
    drawn before ep09 and was not enough for its own: shot 18 kept a pale seam
    along its top and right edges and the ink gate caught it, correctly -- a
    white seam is a picture element as far as H3 is concerned, and it renders
    what it is given.

    A fixed trim is a guess about a number the picture already knows. The seam
    is however many edge rows and columns are pale AND flat along their length,
    so that is what comes off, and never more than a quarter of a side.
    """
    import numpy as np
    grey = np.asarray(frame).mean(axis=2) if np.asarray(frame).ndim == 3 else np.asarray(frame)
    height, width = grey.shape
    top = _seam_depth(grey, int(height * SEAM_MOST))
    bottom = _seam_depth(grey[::-1], int(height * SEAM_MOST))
    # A SIDE gutter may sit a quarter in (ep13 shot 7: a 2x1 split off-centre
    # left 229 columns of the neighbour); top and bottom keep SEAM_REACH, which
    # protects the white rail across ep09's garden.
    side = int(width * SEAM_MOST)
    left = _seam_depth(grey.T, side, reach=side)
    right = _seam_depth(grey.T[::-1], side, reach=side)
    return (left, top, width - right, height - bottom)


SEAM_THIN = 24
"""The widest gutter found INSIDE the edge band. ep09's measured 7 columns; a
broader pale band is a wall or a sky, and a picture keeps it."""


SEAM_EDGE, SEAM_REACH = 48, 120
"""The deepest gutter AT the edge, and how far in a gutter may sit. Measured:
real edge gutters 5-20 px, ep09 shot 14's spill 93-97 px; a hazy sky ran 260
rows at the edge and a white rail sat at row 150, and both were shaved as
gutter before these limits (grid-stage audit, 2026-09-23)."""


def _is_seam(line) -> bool:
    return line.mean() > SEAM_PALE and line.std() < SEAM_FLAT


def _seam_depth(grey, most: int, reach: int = SEAM_REACH) -> int:
    """How many leading rows of `grey` are gutter, capped at `most`: the pale,
    flat run at the edge, or -- when the model drew the panel narrower than its
    cell -- a thin pale run inside the band, with the neighbour's spill outside
    it (ep09 shot 14: 93 columns of spill, then a 7-column gutter)."""
    seam = [_is_seam(grey[i]) for i in range(most)]
    depth = 0
    while depth < most and seam[depth]:
        depth += 1
    if depth > SEAM_EDGE:          # a pale band this deep is sky, not a gutter
        depth = 0
    for i in range(depth, min(most, reach)):
        if seam[i] and (i == 0 or not seam[i - 1]):
            end = next((j for j in range(i, most) if not seam[j]), most)
            if end - i <= SEAM_THIN and end < most and _between_picture(grey, i, end):
                depth = end
    return depth


def _between_picture(grey, start: int, end: int) -> bool:
    """A gutter has darker picture on BOTH sides. A sky grading across the pale
    line makes thin 'seam' runs too, with sky on either side (ep09 shots 1-3
    lost 98-166 rows of morning sky to the rule without this)."""
    darker = SEAM_PALE - 35
    return start > 0 and grey[start - 1].mean() < darker and grey[end].mean() < darker


def panel_box(n: int, cols: int, rows: int, size, trim: int = 16) -> tuple:
    """The crop box for panel `n` (0-based, reading order) out of a grid.

    `size` is the grid's (width, height), or one number when it is square.
    Every grid before ep09 was N x N and this took one number and divided it by
    cols for the width and by rows for the height, which is only the same thing
    on a square. ep09's setups hold 2, 3, 5 and 8 shots and its grids are 2x1,
    3x1 and 4x2: on a 2048x1024 grid the old arithmetic asked for a cell 1024
    wide and 2048 tall, half of it below the bottom of the picture.

    `trim` sheds the gutter and border the geometry clause asks for. They are a
    help on a page and a fault in a reference: H3 renders what it is given, and
    a white seam down one edge is a picture element."""
    width, height = size if isinstance(size, (tuple, list)) else (size, size)
    cell_w, cell_h = width // cols, height // rows
    r, c = divmod(n, cols)
    return (c * cell_w + trim, r * cell_h + trim,
            (c + 1) * cell_w - trim, (r + 1) * cell_h - trim)


# A size word carries a body with it. MEASURED 2026-09-20 on ep06 `beam`: a
# grid with an EMPTY cast came back with a man standing in exactly the three
# panels whose framing named a figure, a head, feet or hands -- and clean in
# the one that named a subject instead. Saying "no character appears here"
# under that does not cancel it.
BODY_WORDS = ("figure", "head", "hands", "feet", "shoulders", "face", "mid-thigh", "chest")

PEOPLED_CUT = {
    "wide": "the whole figure stands well inside the panel with open ground below the feet and "
            "sky above the head; the horizon is visible across the panel",
    "full": "the whole figure stands inside the panel from head to feet, the feet just above "
            "the bottom edge and a little room above the head; the room behind is close",
    "medium": "the panel cuts the figure at mid-thigh; the head sits in the upper third and the "
              "hands are visible",
    "medium_close": "the panel cuts the figure at the middle of the chest; head and shoulders "
                    "fill the centre and the background is far behind",
    "close": "the panel cuts at the shoulders; the face fills the panel",
    "extreme_close": "the panel cuts inside the face; the eyes fill the panel edge to edge",
    "insert": "the panel comes in close on one subject, which fills most of the frame",
}

EMPTY_CUT = {
    "wide": "the camera stands far back across open ground, the horizon running the width of the "
            "panel and a wide sky above it",
    "full": "the camera stands a few paces off, the main thing of the panel seen whole from top "
            "to bottom with the floor below it and the wall close behind",
    "extreme_close": "the camera is pressed against one detail of the main thing of the panel, "
                     "which fills the frame past its edges",
    "medium": "the camera stands a few paces off, the main thing of the panel filling the middle "
              "band of the frame with ground below it and sky behind",
    "medium_close": "the camera stands close in, the main thing of the panel filling the centre "
                    "and the distance falling away far behind it",
    "close": "the camera is right up against the main thing of the panel, which fills the frame "
             "corner to corner",
    "insert": "the panel comes in close on one subject, which fills most of the frame",
}


def cut_clause(size: str, peopled: bool) -> str:
    """How the panel is framed, said against what the panel actually holds."""
    table = PEOPLED_CUT if peopled else EMPTY_CUT
    return table[size]


INSERT_THING = re.compile(r"\b(hands?|fingers|fist|lock|keyhole|key|cheque|coins|letter|glove|cane|"
                          r"boots?|handle|knocker)\b", re.I)
OVER_SHOULDER = re.compile(r"\bover\s+(?:the\s+|his\s+|her\s+|[\w.' <>]{1,40}?'s\s+)?(?:near\s+|left\s+|right\s+)?"
                           r"shoulder\b", re.I)
OTS_CUT = {
    "wide": "the far figure stands whole and well inside the panel with open ground below the feet; the near "
            "shoulder at the edge is cut by the frame",
    "full": "the far figure stands whole inside the panel from head to feet; the near shoulder at the edge is "
            "cut by the frame, close to the camera",
}
"""Jekyll ep01 G6: shot 3 said "the whole figure stands inside the picture from head to
feet" while Enfield was only a shoulder in the BOTTOM LEFT corner."""


def framing(size: str, peopled: bool, body: str, move: str = "") -> str:
    """The cut, said against what the cell holds: an insert is filled by its thing
    (the hands, the lock), never a whole figure (Jekyll ep01 shots 9 and 10 came
    back full-length); an over-the-shoulder wide or full keeps its near shoulder cut;
    a rise from a wide or full draws the room it rises into (`RISE_ROOM`)."""
    if size == "insert" and (thing := INSERT_THING.search(body or "")):
        return f"the frame is filled by the {thing.group(1).lower()}, close, from edge to edge"
    if peopled and size in OTS_CUT and OVER_SHOULDER.search(body or ""):
        return OTS_CUT[size]
    cut = cut_clause(size, peopled)
    if peopled and size in FACE_TAILS and not face_focus(body):
        cut = cut.split(";")[0]                    # the cut alone: its tail names a face the focus is not
    return cut + (RISE_ROOM if move == "crane_up" and size in RISE_ROOM_SIZES else "")


FACE_TAILS = ("medium", "medium_close", "close", "extreme_close")
"""The sizes whose PEOPLED_CUT tail puts a head, a face or the eyes in the middle of the panel."""
FOCUS = re.compile(r"FOCUS OF THE PICTURE IS\s+(.*?)(?=\s+(?:at|in|on) the (?-i:[A-Z]{3,})|[;:]|"
                   r"(?<!\bMr)(?<!\bMrs)(?<!\bDr)\.(?:\s|$)|$)", re.I | re.S)
FACE_WORDS = re.compile(r"\b(?:faces?|heads?|eyes?|profile|expression|mouth|lips|jaw|chin|cheeks?|cheekbones?|"
                        r"brows?|forehead|nose|beard|moustache|whiskers|grin|gaze|stare|hair)\b", re.I)
PERSON = re.compile(r"\b(?:man|men|woman|women|boy|girl|child|children|gentlem[ae]n|figures?|people|pair|"
                    r"walkers?|tramps?|strangers?|constables?|policem[ae]n|servants?)\b", re.I)
PART = re.compile(r"\b(?:hands?|fists?|fingers|knuckles|palms?|wrists?|arms?|boots?|feet|foot|legs?|knees?|"
                  r"gloves?|collar|sleeve|cuff|coat|cane|stick|key|keyhole|lock|door|knocker|handle|letter|"
                  r"cheque|coins|sovereigns|gold)\b", re.I)
"""A part or a thing: a FOCUS on it under a person's name is no face (s09's fist, night_door P1's hand)."""


def face_focus(body: str) -> bool:
    """Is the panel's named FOCUS a face or a person (or is no focus named)?  ep01 s09 and night_door P1
    put "head and shoulders fill the centre" under a FOCUS on a fist and a hand (craft ruling A21); a jaw,
    a gaze or "the two men" keep the framing tail (wave-2 review: s23 and night_door P2 lost it)."""
    hit = FOCUS.search(body or "")
    said = hit.group(1) if hit else ""
    return not hit or bool(FACE_WORDS.search(said)) or bool(PERSON.search(said) and not PART.search(said))


RISE_ROOM, RISE_ROOM_SIZES = ("; the place the camera rises over fills the top third of the panel, and the "
                              "people stand in the lower half"), ("wide", "full")
"""Shot framework A1 / B-5 (2026-10-21): H3 obeys the first-frame cell, and a move pointed past what the cell
holds invents contradictory content, so a rise opens on the room it rises into.  ep01 shot 18 (shipped,
verdict 95; bench T18 rose 4 of 4) was drawn with its walkers in the BOTTOM half under a sky in the TOP quarter."""


COUNTED = re.compile(
    r"\b(two|three|four|five|six|seven|eight|nine|ten)\s+"
    r"((?:\w+\s+){0,2}?)"
    r"(men|women|boys|girls|lads|people|figures|policemen|constables|soldiers|"
    r"labourers|shopmen|of them)\b", re.I)


GROUP_COUNTS = {w: n for n, w in enumerate(("two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"), 2)}


def varied_group(body: str, named: int = 0, extras: int = 0) -> str:
    """Tell a counted group of walk-ons that its members differ from each other.

    MEASURED 2026-09-20 on ep06 shot 10: "three young men ... in cheap dark
    suits and bowlers" is three men and ONE wardrobe, and came back as one man
    drawn three times. `no_duplicates` binds the NAMED cast; a walk-on has no
    name to bind, so the count is the hook.  A count no larger than the shot's
    `named` staged faces is that cast ("the two men" on ep01 night_door's bound
    pair, craft ruling A21): their sheets bind them, so nothing is said -- unless the plan's own `extras`
    holds that many walk-ons ("two constables" in a two-face shot, the ep06 duplicate class).
    """
    found = COUNTED.search(body or "")
    count = GROUP_COUNTS.get(found.group(1).lower(), 0) if found else 0
    if not found or (count <= named and (extras < count or bound_pair(found.group(3)))):
        return ""
    count, _, noun = found.groups()
    who = f"{count} {noun}".lower()
    their = pronoun_of(noun)
    return (f"The {who} are {count.lower()} different individuals: each one has {their} own face, "
            f"own build, own hair and own hat, each wears the clothes a little differently, "
            f"and each stands and gestures in a way of {their} own.")


def bound_pair(noun: str) -> bool:
    """A generic noun ('men', 'women', 'people', 'figures') counted within the staged faces is
    the bound cast, whatever the extras hold -- grid_lint's TWIN refuses the clause on it (Jekyll
    ep04 shot 17: the lawyer and the inspector beside eight walk-ons at a gin palace)."""
    from studio import grid_lint
    return noun.lower() in grid_lint.GENERIC


def pronoun_of(noun: str) -> str:
    """'his' for a group of men, 'her' of women, else 'his or her' (Jekyll ep01:
    "his or her own face" for two men)."""
    noun = noun.lower()
    if noun in ("women", "girls"):
        return "her"
    return "his or her" if noun in ("people", "figures", "of them") else "his"
