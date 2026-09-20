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
        said += (f" In this panel: {', '.join(who)}; no other named person is in it."
                 if who else " NO NAMED CHARACTER appears in this panel at all.")
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
    blocks = [panel_block(i, where, s["size"], s["body"], s["cut"],
                          who=s.get("who"), absent=everyone)
              for i, (where, s) in enumerate(zip(cells, shots), start=1)]
    parts = [geometry(cols, rows, style, numbered), place_clause(*place)]
    if cast:
        parts.append(cast_clause(cast))
    return "\n\n".join(parts + blocks)


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
