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

PANEL_WORD = re.compile(r"\bpanels?\b", re.I)


def _one_picture(text: str) -> str:
    """A single picture never hears "panel": the model obeys the word over the
    arithmetic (measured on ep05's six 1x1 groups, which came back mosaics)."""
    return PANEL_WORD.sub("picture", text)


def _who_v2(who: list[str], extras: int) -> str:
    """Who is in it: the named, else the declared unnamed, else the place alone."""
    if who:
        return f"In it: {', '.join(who)}."
    if extras:
        return f"In it: {extras} unnamed {'person' if extras == 1 else 'people'}, none of them a named person."
    return "It is a picture of the place alone: ground, growth, sky and built things."


def worn_items(wear: str, most: int = 5) -> list[str]:
    """The row's clothes after "Wearing:": each sentence cut at a colon (what
    follows one is parts of the same garment), then split on commas. The face
    is the sheet's; these are what a panel drops (ep09 A/B: bound by name alone
    the wife lost her shawl; cut at the first comma she lost her skirt's green,
    which moved to her blouse)."""
    _, _, clothes = wear.partition("Wearing:")
    items = [i.strip().rstrip(".") for s in clothes.split(". ") for i in s.split(":", 1)[0].split(",")]
    return [i for i in items if i][:most]


HEADWEAR = re.compile(r"\b(?:hat|boater|cap|bonnet|toque|helmet|bowler|busby)\b", re.I)
BAREHEADED = re.compile(r"\bbare-?headed\b", re.I)


def bareheaded(name: str, shots: list[dict]) -> bool:
    """Does a panel this person is in say they are bareheaded? ep09 shot 11
    put the boater in his hand while the binding put it on his head: both drawn."""
    return any(BAREHEADED.search(s["body"]) for s in shots if name in (s.get("who") or []))


def _binding(p: dict, bare: bool = False) -> str:
    items = [i for i in worn_items(p.get("wear", "")) if not (bare and HEADWEAR.search(i))]
    worn = f", wearing: {'; '.join(items)}" if items else ""
    return f"{p['name']} is the person in <image{p['ref']}>{worn}."


def _block_v2(label: str, s: dict) -> str:
    return (f"{label}{s['size']}: {s['body']} Framing: {s['cut']}. "
            f"{_who_v2(s.get('who') or [], s.get('extras', 0))}")


def grid_prompt_v2(shots: list[dict], cols: int, rows: int, place: tuple[list[int], str],
                   cast: list[dict], style_slot: int) -> str:
    """Layout (one line), the panels SUBJECT FIRST, one binding line per person,
    the place, the style. No description is truncated -- the sheet in the slot
    carries the face and the panel prose carries the tag -- and a single
    picture never says storyboard, grid or panel."""
    cells = cell_names(cols, rows)
    if len(shots) != len(cells):
        raise ValueError(f"{len(shots)} shots for {len(cells)} cells")
    single = len(shots) == 1
    if single:
        layout = "One full-frame illustration, edge to edge, with no lettering anywhere."
        blocks = [_one_picture(_block_v2("", shots[0]))]
    else:
        layout = (f"A storyboard of {len(shots)} panels in {cols} columns and {rows} rows, all the "
                  f"same size, thin white gutters between them, no lettering anywhere.")
        blocks = [_block_v2(f"PANEL {i} ({where}), ", s)
                  for i, (where, s) in enumerate(zip(cells, shots), start=1)]
    binding = [_binding(p, bareheaded(p["name"], shots)) for p in cast if p.get("ref")]
    if len(binding) > 1:
        binding.append(f"{' and '.join(p['name'] for p in cast if p.get('ref'))} are never dressed alike.")
    refs = " and ".join(f"<image{n}>" for n in place[0])
    where = (f"The picture is set at {refs}: {place[1]}." if single else
             f"Every panel is set at {refs}, at the same hour: {place[1]}.")
    parts = [layout] + blocks + binding + [where,
                                                                            STYLE_V2.format(n=style_slot)]
    return "\n\n".join(_one_picture(x) if single else x for x in parts)


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
    left = _seam_depth(grey.T, int(width * SEAM_MOST))
    right = _seam_depth(grey.T[::-1], int(width * SEAM_MOST))
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


def _seam_depth(grey, most: int) -> int:
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
    for i in range(depth, min(most, SEAM_REACH)):
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
    "medium": "the panel cuts the figure at mid-thigh; the head sits in the upper third and the "
              "hands are visible",
    "medium_close": "the panel cuts the figure at the middle of the chest; head and shoulders "
                    "fill the centre and the background is far behind",
    "close": "the panel cuts at the shoulders; the face fills the panel",
    "insert": "the panel comes in close on one subject, which fills most of the frame",
}

EMPTY_CUT = {
    "wide": "the camera stands far back across open ground, the horizon running the width of the "
            "panel and a wide sky above it",
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


COUNTED = re.compile(
    r"\b(two|three|four|five|six|seven|eight|nine|ten)\s+"
    r"((?:\w+\s+){0,2}?)"
    r"(men|women|boys|girls|lads|people|figures|policemen|constables|soldiers|"
    r"labourers|shopmen|of them)\b", re.I)


def varied_group(body: str) -> str:
    """Tell a counted group of walk-ons that its members differ from each other.

    MEASURED 2026-09-20 on ep06 shot 10: "three young men ... in cheap dark
    suits and bowlers" is three men and ONE wardrobe, and came back as one man
    drawn three times. `no_duplicates` binds the NAMED cast; a walk-on has no
    name to bind, so the count is the hook.
    """
    found = COUNTED.search(body or "")
    if not found:
        return ""
    count, _, noun = found.groups()
    who = f"{count} {noun}".lower()
    return (f"The {who} are {count} different individuals: each one has his or her own face, "
            f"own build, own hair and own hat, each wears the clothes a little differently, "
            f"and each stands and gestures in a way of their own.")
