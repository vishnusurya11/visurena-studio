"""ONE storyboard per setup, drawn as a sequence (owner, 2026-09-11 00:30).

Take sheets drawn one take at a time let the men reach the door in take 4
and approach it again in take 5.  So the storyboard is drawn FIRST for the
whole setup: every shot and sub-shot in story order, each cell stating where
on the setup's route the people are, in chained sheets.  Takes are windows on
this board: their pins are its cells, their reference is a strip of its
cells.  No take has a sheet of its own.

THE PROMPT (rewritten 2026-09-11 from `docs/calibration/storyboard_prompt_spec.md`).
A 5 kB paragraph became short LABELLED BLOCKS, because that is the shape both
OpenAI guides ask for on a complex request.  Every rule on the sheet is the
conversion of something gpt-image obeys badly into something it obeys well:

    a relation ("the horse ahead of the wheel")  -> GEOMETRY: which frame edge,
                                                    at what apparent size
    an implied camera                            -> the 180-degree line: one side
                                                    of the travel, every panel
    a conditional ("the hat on his head outdoors,
     in his hand indoors")                       -> WARDROBE: one flat fact
    a crowd named once for nine panels           -> BACKGROUND LIFE, per panel
    "the instant before: <verb phrase>"          -> what is still AT REST
    "identical to panel 1"                       -> the END panel's own complete
                                                    picture, with its one change
    "Static shot;" (an instruction to MiniMax)   -> deleted; the sheet is a still

And every sentence says what IS: a negated noun is still that noun in the
prompt (`studio/affirm.py`), so the sheet carries no negation at all -- the
"NO TWO PANELS" headline included, which is now stated as the affirmative law
`DIFFERENT`.
"""
from __future__ import annotations

import re
from pathlib import Path

from studio import canvas as cv, prop_refs
from studio import house_style
from studio.episode_spec import Setup, Shot

COLS, ROWS = 3, 3
CELLS = COLS * ROWS


def cast_sheet(book, who: str, setup: str, state: str = ""):
    """The picture that binds this character HERE: the wardrobe card, else the bust.

    Tried in order: the STATE card (`char-<who>_indoor.png`, the contract's own
    naming, `cast_refs.STATES`), then episode 1's per-SETUP variant
    (`char-<who>_lab.png`), then the identity bust.

    THERE IS NO "ANY OTHER CARD" RUNG.  There was, and it was
    `sorted(glob("char-<who>_*.png"))[0]` -- an ALPHABETICAL choice among
    semantically incompatible wardrobes, and alphabetical order has no opinion
    about clothes.  MEASURED on this book: no `char-*_outdoor.png` exists for
    anyone (the prompts were written, the cards never drawn), so every outdoor
    setup silently resolved to whatever sorted first -- Watson and Holmes to
    `_bench`, an indoor card, Holmes's being the muffler one.  Episode 3's `cab`
    and `garden_path` are both outdoors, so two paid sheets and four rendered
    takes drew the wrong clothes while `hat_line` printed "the bowler hat is on
    his head in every panel of this sheet".

    The bust is the honest floor, and for an outdoor setup it is also the closer
    picture: the bust is the one drawn with the hat on.  What it never does is
    claim to be a wardrobe it is not.

    This used to try the per-setup name ALONE, which stopped existing when the
    contract moved to one card per wardrobe state -- so every episode 2 take fell
    through to the bust, and the bust is the picture with the hat on. All 19 takes
    referenced Holmes in a deerstalker and Watson in his bowler while their own
    prose said "bare-headed". The reference and the words have to be one
    statement; that is the whole point of the cast gate."""
    chars = book / "refs" / "characters"
    for name in (f"char-{who}_{state}.png" if state else "", f"char-{who}_{setup}.png"):
        if name and (chars / name).exists():
            return chars / name
    return chars / f"char-{who}.png"


WIDE_ENOUGH = {"medium", "full", "wide"}
"""The cell sizes that show enough room to place a location plate against.
The same ladder `GEO_SIZES` uses for the route, and for the same reason: below
it you are looking at a person, not at a place."""


def places_the_plate(sizes) -> bool:
    """Does this take ever show a cell wide enough to anchor its own room?

    MEASURED, episode 2: 13 of the episode's 14 foreign frames are the take's OWN
    plate at 0.988-0.998, and every one came from a close or insert segment with
    no wider cell before it (Fisher p = 0.0072; 0 of 64 wider frame samples).
    A take with nothing but tight cells cannot place a room, so the plate stops
    being a definition and becomes the only whole picture it can fall back on."""
    return any(size in WIDE_ENOUGH for size in sizes)


def props_block(props: list[dict]) -> str:
    """The PROPS block: every object on this sheet, with its three measures.

    Episode 2's sheets had no such block at all -- a prop's size lived only
    inside whichever panel happened to mention it, late in an 18 kB prompt, and
    nine props came back between 0.36x and 3.0x of the size they were asked for.
    Here every size is stated once, near the top, beside the reference picture
    that shows the same object in a hand, so the words and the picture say one
    thing.

    Sizes are stated against a BODY, never in units: `studio.prop_refs.Prop`
    refuses a measure in centimetres, because a model has no ruler and the one
    thing in a photograph that carries absolute size is a person."""
    if not props:
        return ""
    lines = [f"PROPS -- every object below is drawn at the size stated, and the size is "
             f"stated against a body because a body is the ruler in the frame."]
    for row in props:
        lines.append(f"- {row['physical']}")
    return "\n".join(lines)

def route_ok(shots: list[Shot]) -> bool:
    """Positions never go backwards through the shots and sub-shots of one setup."""
    last = -1.0
    for shot in shots:
        for p in [shot.path] + [c.path for c in shot.cuts]:
            if p is None:
                continue
            if p < last - 1e-9:
                return False
            last = p
    return True


def cell(seg, shot: int, sub: int, path: float | None) -> dict:
    """One drawable panel: the picture half of a shot or sub-shot, plus its place."""
    return {"shot": shot, "sub": sub, "frame": seg.frame, "motion": seg.motion, "path": path,
            "faces": list(seg.faces), "size": seg.size, "camera": seg.camera, "at_rest": seg.at_rest,
            "end_frame": seg.end, "changed": seg.changed, "crowd": seg.crowd}


def segments(shots: list[Shot], setup: str) -> list[dict]:
    """Every shot and sub-shot of `setup`, in story order, as a drawable cell."""
    out = []
    for shot in shots:
        if shot.setup != setup:
            continue
        out.append(cell(shot, shot.index, 0, shot.path))
        for k, cut in enumerate(shot.cuts, start=1):
            out.append(cell(cut, shot.index, k, cut.path if cut.path is not None else shot.path))
    return out


def chunks(segs: list[dict], size: int = CELLS) -> list[list[dict]]:
    """Split into the FEWEST sheets that hold them, as evenly as possible.

    A greedy split leaves the remainder on its own: ten panels became nine and
    ONE, the one picked up whatever END cells were going and landed at two in a
    2x2 grid -- so the drawer was told "a 2 by 2 grid of 4 equal panels", drew
    four, and the packer used two.  A full $0.13 for half a picture, and the
    GRID gate refused the setup for it (episode 4's parlour, measured).

    Evenly, the same ten are 5 and 5, and each half fills its 3x3 from the END
    cells `end_choices` already ranks."""
    if not segs:
        return []
    sheets = -(-len(segs) // size)                    # ceil
    base, extra = divmod(len(segs), sheets)
    out, at = [], 0
    for k in range(sheets):
        take = base + (1 if k < extra else 0)
        out.append(segs[at:at + take])
        at += take
    return out


ALIKE = 0.70
"""Two panels on one sheet are the same picture above this. MEASURED over the 40
cells of iteration 4: the highest legitimate pair anywhere is 0.584 (two bench
close-ups), sub-shots of one shot top out at 0.47, and the copies the owner
caught sit at 0.821, 0.890 and 0.951. No pair is skipped: a panel and its own
END panel are the pair that slipped through when END panels were exempt."""


END_FLOOR, END_CEILING = 0.45, 0.80
"""A panel and its OWN END panel are the same picture after ONE SIMPLE CAMERA
MOVE, so they are judged in a BAND, not under a ceiling.

`ALIKE` alone is a ceiling with no floor -- right for two different panels,
exactly backwards here.  It rewarded making an END a different picture and
punished obeying the movement rule.  MEASURED on episode 2: 9 of 12 start/END
pairs are re-stages (median 0.307, minimum -0.019, two unrelated pictures of one
segment) and the three that obey the rule (0.553, 0.569, 0.602) were among the
five most-alike pairs in the episode -- the nearest to being refused as copies.

This is the DRIFT fault seen from the drawing side: `take_verdict.drift_gate`
asks whether the render reached its END cell, and a re-staged END cannot be
reached by a camera move.  Seven takes failed drift; nine ENDs are re-stages.
CALIBRATION. The two populations do not overlap: the pairs that obey the
movement rule measure 0.553-0.602, and every copy the owner ever caught -- told
"identical to panel 1", the drawer drew panel 1 again -- measures 0.821, 0.890
or 0.951. The ceiling is 0.80, under the lowest known copy and well clear of the
highest legitimate pair; the floor is 0.45, under every obeying pair and over
every re-stage (the highest re-stage measured 0.44)."""


SUBJECT_FILLS = ("insert",)
"""Sizes whose subject IS the frame, so a whole-frame score measures the SUBJECT.

The END floor asks one question -- did the camera travel somewhere no simple
move reaches -- and answers it by how different the two pictures look.  That
works while the frame holds a room.  On an insert there is no room: episode 4's
shot 10 is a half-sovereign between finger and thumb which turns over to show
its face, the same lens and hand and distance, and it scores 0.166.  The gate
called it re-staged, gave the take no END cell, and H3 invented the reveal --
minting a coin that reads "SOLVUNT EF . CENOWLEBH" around a figure who is not
Victoria, while the correct face sat drawn and unused in Q10_0E.png."""


BLOCK_GRID = (7, 4)
BLOCK_FLOOR = 0.2
"""Reading an END pair WHERE IT CHANGED, not over the whole frame.

The ceiling asks "did anything move" and answers it globally, which works while
the camera moves and fails on a locked-off one: most of the frame is SUPPOSED to
be identical and the change sits in one part of it.  Episode 4's shot 21 -- the
same room, the same table, the same man in the foreground, and in the END cell
the two visitors have turned and are walking out of the door -- scores 0.856 and
was called a copy.  The take got no destination and invented one, cutting to
plate_rance_parlour.png at frame 128 and reproducing it at 0.999.

Blocks of 7 x 4 over the thumbnail, counting those under 0.2, across all eleven
of episode 4's END pairs:

    Q08_0 0.982 global   0 blocks   a copy, and it looks like one
    Q00_0 0.935          0          a copy
    Q11_0 0.945          0          a head tilt; a copy
    Q15_0 0.938          4          leans in and re-gestures -- NOT a copy
    Q21_0 0.856          3          the two men walk out -- NOT a copy
    Q20_0 0.856          3
    Q09_0 0.807          3

0 against 3 with nothing between, verified by eye on Q21 and Q15 (kept) and Q11
and Q08 (still copies).  So ONE block of real change is enough; the count is not
tuned to the eleven pairs that happened to be measured."""


def changed_blocks(start, end, grid: tuple[int, int] = BLOCK_GRID,
                   floor: float = BLOCK_FLOOR) -> int:
    """How many blocks of the frame hold a real change between the two cells."""
    import numpy as np

    a, b = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    if a.ndim == 3:
        a, b = a.mean(2), b.mean(2)
    ny, nx = grid
    h, w = a.shape
    n = 0
    for j in range(ny):
        for i in range(nx):
            p = a[h * j // ny:h * (j + 1) // ny, w * i // nx:w * (i + 1) // nx].ravel()
            q = b[h * j // ny:h * (j + 1) // ny, w * i // nx:w * (i + 1) // nx].ravel()
            p, q = p - p.mean(), q - q.mean()
            if float(p @ q / ((np.linalg.norm(p) * np.linalg.norm(q)) + 1e-9)) < floor:
                n += 1
    return n


def end_pair_verdict(score: float, size: str = "", changed: int | None = None,
                     motion: str = "") -> str:
    """"ok", "restaged" (no camera move can travel it) or "copy" (nothing moved).

    THE FLOOR IS A QUESTION ABOUT A CAMERA THAT WAS TOLD TO STAY.  It was fair
    while `end_text` said "from the same camera", and it caught a real fault:
    episode 2's 9 of 13 END cells answered "the shot ends here" by moving to a
    different setup.  Episode 7's END panels are told where the camera FINISHED,
    and the floor immediately threw away four correct ones -- all seven drawn
    that day were looked at, one by one:

        Q10_0E  0.757  kept     the lane, camera tracked along, boy further off
        Q21_0E  0.489  kept     Holmes's head up off his chest
        Q22_0E  0.855  kept     the doorway, barely moved
        Q23_0E  0.380  DROPPED  Holmes and the cabman both bent over the strap
        Q24_0E  0.410  DROPPED  Lestrade nearer, the cuffs held out to camera
        Q11_0E  0.340  DROPPED  the same ladder and window, curtain blown out
        Q14_0E  0.240  DROPPED  camera pulled back two strides, Watson walked in

    Every one of the four is right.  Their similarity is low because the framing
    changed, and the framing changed because the plan said to change it.  The
    measurement asks how far the camera moved; a camera TOLD to move cannot be
    judged by how far it moved.

    THE CEILING GETS SHARPER, not weaker.  On a locked camera a high score is
    what an obeyed END cell looks like, which is why `changed` overturns it.  On
    a travelling camera a high score means the travel was ignored, and nothing
    overturns that -- Q22_0E at 0.855 is that panel, and it is the one of the
    seven a person would also call barely moved.

    A caller that names no motion cannot know the camera travelled, so it gets
    the stricter rule.  Nothing loosens in silence."""
    travels = bool(camera_end(motion))
    excused = bool(changed) and not travels
    if score < END_FLOOR and size not in SUBJECT_FILLS and not travels:
        return "restaged"
    if score > END_CEILING and not excused:
        return "copy"
    return "ok"


def reaches(start: "Path", end: "Path", size: str = "", motion: str = "") -> bool:
    """Can one simple camera move travel from this cell to its own END cell?

    MEASURED, episode 2: 9 of 13 drawn END cells score below `END_FLOOR` against
    their own start cell (Q05_0 -> Q05_0E at 0.072, Q19_1 -> Q19_1E at -0.019).
    The drawer answered "the shot ends here" by moving to a different camera
    setup.  Aiming the take at one of those is aiming it at a cut, and `drift`
    then fails the take for the sheet's fault -- all seven hard drift failures.

    A `copy` (over the CEILING) is no destination either, and aiming a take at
    one is WORSE than aiming it at nothing: it says end where you began, which
    is the stillness the owner banned outright.  With no END cell the take
    follows the motion described in words and `drift` has no aimed segment.

    MEASURED three ways on the same 9 cells: the sheet's prose re-stages them
    (0.072-0.406); attaching the start cell as a reference makes the drawer copy
    it (0.984-0.997); demoting that reference in prose to "the angle and the
    side" still copies (0.981).  With a dominant reference this drawer copies,
    and without one it re-stages -- so only a cell that measures INSIDE the band
    is a destination, however it was drawn."""
    from pathlib import Path

    from studio import frame_match as fm

    start, end = Path(start), Path(end)
    if not (start.exists() and end.exists()):
        return False
    a, b = fm.load(start), fm.load(end)
    return end_pair_verdict(fm.similarity(a, b), size, changed_blocks(a, b), motion) == "ok"


def is_end_pair(a: dict, b: dict) -> bool:
    """Are these two panels one segment and its own END panel?"""
    return (a["shot"], a["sub"]) == (b["shot"], b["sub"]) and a.get("end") != b.get("end")


def duplicates(cells: list, segs: list[dict], floor: float = ALIKE) -> list[tuple[str, str]]:
    """Every pair of panels on a sheet that is the same picture. Owner's rule,
    2026-09-11: no two panels of a storyboard may ever be the same.

    A panel and its OWN END panel are judged in a BAND instead (`END_FLOOR`,
    `END_CEILING`): they are one picture after one camera move, so being alike is
    what they are FOR. Under the ceiling alone this pair was rewarded for being a
    different picture, which is the re-stage the render cannot travel."""
    from studio import frame_match as fm
    images = [fm.load(p) for p in cells]
    out = []
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            score = fm.similarity(images[i], images[j])
            a, b = segs[i], segs[j]
            pair = (named(a)[:-4], named(b)[:-4])
            if is_end_pair(a, b):
                # BOTH RULES, at the site that SPENDS.  The insert exemption and
                # the changed-block override reached `reaches()` -- which decides
                # whether a TAKE may aim at an END cell -- and never reached here,
                # the site that costs a STRICT redraw and retires the cell.
                # Measured on episode 4's own sheet report: 8 END pairs refused,
                # 2 STRICT redraws, and 5 of the 8 are not copies under the rule
                # this module already states -- Q09 (0.807, 3 changed blocks),
                # Q15 (0.938, 4), Q20 (0.856, 3), Q21 (0.856, 3), and Q10, the
                # half-sovereign insert at 0.166 the exemption exists for.
                # The START seg carries the shot's motion; the END seg has it
                # blanked by `end_panel`, which is why the motion is taken from
                # whichever of the pair is not the END.
                said = (b if a.get("end") else a).get("motion", "")
                if end_pair_verdict(score, a.get("size", ""),
                                    changed_blocks(images[i], images[j]), said) != "ok":
                    out.append(pair)
            elif score > floor:
                out.append(pair)
    return out


def label(seg: dict) -> str:
    return f"{seg['shot']}.{seg['sub']}{'E' if seg.get('end') else ''}" if seg["sub"] or seg.get("end") else str(seg["shot"])


def cell_name(shot: int, sub: int, end: bool = False, alt: bool = False) -> str:
    """`Q03_0.png` the panel, `Q03_0E.png` its END panel, `Q03_0A.png` an ALTERNATE
    angle of it. Only the bare name is ever staged in a take."""
    return f"Q{shot:02d}_{sub}{'E' if end else 'A' if alt else ''}.png"


def named(seg: dict) -> str:
    """The cell name a panel dict is cut to, whichever kind it is."""
    return cell_name(seg["shot"], seg["sub"], bool(seg.get("end")), bool(seg.get("alt")))


def plate_name(setup: str) -> str:
    return f"plate_{setup}.png"


def sheet_name(setup: str, k: int, strict: bool = False) -> str:
    return f"seq_{setup}_{k}{'_strict' if strict else ''}.png"


# ---- where each kind of picture lives under `boards/` ----------------------
# One room per kind (owner, 2026-09-13). `frames/` held plates, sheets, prompts,
# dq reports, cells, END cells, superseded drafts and redraw working files under
# one name; at fourteen episodes that stops you re-rolling one stage and leaving
# the rest alone. The NAMES are unchanged so nothing else has to be re-learned.

def cell_path(boards: Path, shot: int, sub: int, end: bool = False) -> Path:
    return boards / "cells" / cell_name(shot, sub, end)


def plate_path(boards: Path, setup: str) -> Path:
    return boards / "plates" / plate_name(setup)


def sheet_path(boards: Path, setup: str, k: int, strict: bool = False) -> Path:
    return boards / "sheets" / sheet_name(setup, k, strict)


def picture_path(boards: Path, book: Path, name: str) -> Path:
    """Where a reference NAMED IN A RECORD actually lives, routed by its prefix.

    A record stores bare names (`Q11_0.png`, `plate_hall.png`,
    `char-john_rance_indoor.png`) and they no longer share one folder.  Routing
    is done HERE, once, because the alternative is the same three-way `if` copied
    into every reader -- and a reader that gets it wrong resolves to a file that
    does not exist, or worse, to a different one that does."""
    if name.startswith("char-"):
        return Path(book) / "refs" / "characters" / name
    if name.startswith("plate_"):
        return plates_in(boards) / name
    if name.startswith("panel_") or ".before." in name:
        return panels_in(boards) / name
    if name.startswith("seq_"):
        return sheets_in(boards) / name
    return cells_in(boards) / name


def cells_in(boards: Path) -> Path:
    return boards / "cells"


def plates_in(boards: Path) -> Path:
    return boards / "plates"


def sheets_in(boards: Path) -> Path:
    return boards / "sheets"


def panels_in(boards: Path) -> Path:
    return boards / "panels"


def grid(n: int, aspect: str = "9:16") -> tuple[int, int, tuple[int, int]]:
    """The smallest sheet that holds n cells, at the plan's delivery aspect.

    The table itself lives in `studio/canvas.py`, because the sheet's grid is a
    consequence of the delivery shape: a square episode draws square cells
    (2048x2048) and a vertical one draws vertical cells (2048x3072 at nine)."""
    return cv.grid(n, aspect)


def end_choices(segs: list[dict], spare: int, setup: Setup | None = None) -> list[dict]:
    """The panels that earn an END panel, best first: the ones the PLAN gives an
    end picture to, then the walk, then anything with a named camera move; at
    most `spare` of them."""
    told = [s for s in segs if s.get("end_frame")]
    walk = [s for s in segs if s not in told and on_route(s, setup)]
    moving = [s for s in segs if s not in told and s not in walk
              and not s["motion"].lower().startswith(("static", "locked"))]
    rest = [s for s in segs if s not in told and s not in walk and s not in moving]
    return (told + walk + moving + rest)[:spare]


STAYS = re.compile(r"\b(stay|stays|stayed|hold|holds|holding|held|remain|remains|steady|keeps?|kept|unmoved|motionless|static|still|unchanged)\b", re.I)
"""Clauses that say something did NOT move.

They were passed through as the END panel's change, so the drawer was told to
draw a still in which "his hands stay folded on the head of his stick" -- and it
drew the same hands.  Episode 4's three copied END cells are all of this shape or
its cousin, a verb with no destination."""


def moved_clause(motion: str) -> str:
    """The first clause of a motion that names something ARRIVING SOMEWHERE.

    An END panel is judged by whether a viewer can point at one thing and say
    where it went, so the change has to have a destination.  Measured over all
    eleven of episode 4's END pairs: every keeper names a body or object at a new
    place -- "lifts one hand OFF HIS KNEE", "straightens OFF THE TABLE", "lays the
    half-sovereign down ON THE CHECKED CLOTH" -- and every copy names a verb with
    none."""
    for clause in re.split(r"[;,] and |[;,]| and then ", still(motion or "")):
        said = clause.strip().rstrip(". ")
        if said and not STAYS.search(said):
            return said
    return ""


def end_panel(seg: dict, number: int) -> dict:
    """The END panel of `seg`: its own COMPLETE picture, one action later.

    IT INHERITS THE START PANEL'S OWN NOUNS rather than pointing at them.  It used
    to read "the same place, the same camera and the same light as panel N, drawn
    afresh with <verb>", which fired on 24 of 24 shots in episode 4 because the
    plan's `end` is empty on every one -- so the start panel named nouns at frame
    fractions and edges and the END panel named no framing noun at all.  A delta
    with no base, whose only base was the panel six inches away on the same
    canvas, which is what the drawer copied.

    The word 'identical' went for the same reason one revision earlier (owner
    2026-09-11: told 'identical', it drew the identical panel)."""
    moved = seg.get("changed") or moved_clause(seg.get("motion", ""))
    # WHERE THE CAMERA FINISHED rides on its own key, because `motion` is blanked
    # here on purpose -- the END panel draws a state, not a movement, and the
    # motion prose printed into it makes the drawer draw the movement.  Blanking
    # it also took away the one fact `end_text` needs, and every END cell in
    # episode 7 was drawn "from the same camera" while eight green tests said
    # otherwise.
    went = camera_end(seg.get("motion", ""), number)
    # A TRAVELLING CAMERA'S REFRAMING IS THE PANEL.  `keeps_camera` deletes it,
    # which is right when the camera held and wrong when it did not.
    said = stop(seg.get("frame", "")).rstrip(". ")
    carried = said if went else keeps_camera(said)
    return dict(seg, end=True, of=number, motion="", moved_from=went,
                frame=seg.get("end_frame") or (
                    f"{carried}, with {moved}" if moved else carried),
                changed=moved)


def end_panels(segs: list[dict], spare: int) -> list[dict]:
    """END panels for the spare cells of a sheet, in the order they were chosen."""
    return [end_panel(s, segs.index(s) + 1) for s in end_choices(segs, spare)]


GEO_SIZES = {"medium", "full", "wide"}
LADDER = ((0.2, "is the height of a thumbnail"), (0.4, "is the height of a finger"), (0.6, "is the height of a hand"),
          (0.8, "is half the height of the frame"), (1.01, "fills the frame"))


RUNGS = tuple(word for _, word in LADDER)
START, FAR_END = "start", "far_end"


def nearness(path: float, landmark_at: str = FAR_END) -> float:
    """How near this panel stands to the landmark, 0 at the far side of the route
    and 1 at the landmark itself.  A landmark at the route's FAR end is reached by
    walking; one at its START is left behind."""
    return path if landmark_at == FAR_END else 1.0 - path


def door_size(path: float, landmark_at: str = FAR_END, largest: str = "") -> str:
    """Concrete apparent size of the landmark from a route position (research
    2026-09-11: models obey camera-anchored size words, not percentages), capped
    at the biggest size THIS landmark ever reaches."""
    if largest and largest not in RUNGS:
        raise ValueError(f"{largest!r} is outside the size ladder; say one of {RUNGS}")
    rung = next(k for k, (limit, _) in enumerate(LADDER) if nearness(path, landmark_at) < limit)
    return RUNGS[min(rung, RUNGS.index(largest) if largest else len(RUNGS) - 1)]


def on_route(seg: dict, setup: Setup | None = None) -> bool:
    """A panel that shows the walk: a wide framing with a place on a route the
    setup actually names."""
    if setup is not None and not setup.route:
        return False
    return seg["size"] in GEO_SIZES and seg.get("path") is not None


def sheets(segs: list[dict], setup: Setup | None = None,
           aspect: str = "9:16") -> list[tuple[list[dict], list[int], tuple]]:
    """The sheets of a setup as (panels, route panel numbers, grid).  STORY ORDER
    (owner 2026-09-11): the plan already refuses a route that goes backwards, so
    story order is also order of distance travelled.  Each END panel sits straight
    after its own start panel; spare cells take END panels, never repeats."""
    out = []
    for chunk in chunks(segs):
        cols, rows, canvas = grid(len(chunk), aspect)
        panels = with_ends(chunk, cols * rows - len(chunk), setup)
        cols, rows, canvas = grid(len(panels), aspect)
        out.append((panels, [k for k, s in enumerate(panels, start=1) if on_route(s, setup)],
                    (cols, rows, canvas)))
    return out


ALTERNATES = (
    ("Reverse angle on {who}, the camera round on the other side of the same moment as "
     "panel {k}: their faces where their backs were, the far side of the place behind them.",
     "The camera stands opposite its position in panel {k}, at the same height, a 35mm lens."),
    ("A wide establishing view of the same moment as panel {k}, {who} small in the middle "
     "distance with the whole place open around them, floor to roof in frame.",
     "The camera stands well back from panel {k}, at a standing eye, a 24mm lens."),
    ("A tight insert from the moment of panel {k}: hands, cuffs and one held object filling "
     "the frame, no face above the collar.",
     "The camera stands an arm's length from the hands, looking down, a 90mm lens."),
    ("A low angle on {who} at the same moment as panel {k}, the camera near the ground "
     "looking up past them to the roof or the sky.",
     "The camera stands at knee height below panel {k}, tilted up, a 28mm lens."),
)
"""Four alternates, each its OWN picture in its own words.

The first draft inherited the base panel's whole `frame` and appended one
sentence, which the TWINS gate measured at 0.836 against its base and refused --
correctly. Two panels asking for one picture cannot both be the different
picture the sheet demands. So an alternate states a camera and a framing the
base panel does not have, and borrows only the people."""


def _who(seg: dict) -> str:
    """Who the alternate is of, in three words, so it shares no prose with its base."""
    faces = [f.replace("_", " ").title() for f in seg.get("faces") or []]
    return " and ".join(faces[:2]) if faces else "the place"
"""What a spare cell becomes. The four are the angles an editor asks for first.

The grid table is coarse -- 3, 6 or 9 cells at 9:16 -- so a setup almost never
fills its sheet exactly, and a sheet with black cells is a sheet the owner sent
back. Spares used to be END panels; they are alternates now, because an
alternate is a picture of a moment the episode really has, and nothing
downstream can mistake it for a destination the way an END cell was."""


def alt_panel(seg: dict, number: int) -> dict:
    """An ALTERNATE angle of panel `number`: the same instant, another camera.

    It carries the start panel's own nouns, like `end_panel`, so the drawer has a
    base to vary rather than a relation to satisfy -- the lesson of the three END
    panel attempts on episode 2, which is about the drawer and outlives the END
    panel itself."""
    frame, camera = ALTERNATES[(number - 1) % len(ALTERNATES)]
    who = _who(seg)
    return dict(seg, alt=True, end=False, of=number, end_frame="", changed="",
                frame=frame.format(k=number, who=who), camera=camera.format(k=number),
                motion="The camera holds a static shot; a hand shifts a finger's breadth.")


def alt_panels(segs: list[dict], spare: int) -> list[dict]:
    """One alternate per spare cell, spread over the sheet's own panels."""
    return [alt_panel(segs[k % len(segs)], k % len(segs) + 1) for k in range(max(spare, 0))]


DRAW_ENDS = False
"""THE OWNER'S RULE, 2026-09-16: no sheet draws an END panel.

A take is given its first frame and the arrival in words (`takes_r2v.NO_ENDS`),
so nothing downstream consumes an END cell. Drawing them anyway is waste -- and
worse, it leaves a drawn, apparently-usable last frame sitting beside every
start cell, which is exactly what got pinned again in episode 8 after the rule
was already written down. The cell cannot be pinned if the cell does not exist.

Kept as a switch, like `NO_ENDS`, so the comparison in
`docs/calibration/end_frames.md` stays reproducible. Nothing asks for it.

The spare cells are simply left to the grid, which chooses a smaller one."""


def with_ends(segs: list[dict], spare: int, setup: Setup | None = None) -> list[dict]:
    """The panels with an END panel inserted straight after each start panel that
    earns one, walks and moving shots first, up to `spare` of them.

    Under the owner's rule no END panel is inserted: the spare cells take
    ALTERNATES instead. See `DRAW_ENDS` and `ALTERNATES`."""
    if not DRAW_ENDS:
        return list(segs) + alt_panels(segs, spare)
    chosen = end_choices(segs, spare, setup)
    out = []
    for s in segs:
        out.append(s)
        if s in chosen:
            out.append(end_panel(s, len(out)))  # its number ON THE SHEET, after the ends already inserted
    return out


def where(seg: dict) -> str:
    return f"{round((seg['path'] or 0.0) * 100)}% along the route" if seg.get("path") is not None else "in place"


# ---- the sentences a drawer obeys -----------------------------------------

MOVE_WORD = (r"static|locked|handheld|track\w*|push\w*|pull\w*|tilt\w*|pan\w*|"
             r"doll\w*|cran\w*|zoom\w*|orbit\w*|swing\w*|truck\w*|pedestal\w*|arc\w*")
CAMERA_MOVE = re.compile(rf"^(?:the\s+camera\s+)?(?:{MOVE_WORD})\b[^;]*;\s*", re.I)
"""The camera instruction at the head of a motion line.  It is written FOR
MiniMax; on a still prompt it is noise that gets drawn (reviewer 3: "Static
shot; ... the Bunsen flame" put a blue flame on Watson's cravat stud).

IT MATCHED NOTHING FROM EPISODE 2 TO EPISODE 6.  The old pattern was
`^(static|tracking|track|push|...)` -- a BARE, UNINFLECTED verb at the start of
the line.  Episode 1 wrote "Static shot; ..." and it matched 23 of 23.  Every
plan since writes "The camera pushes in on his face across the whole shot; ...",
which begins with "The" and inflects the verb, and matched 0 of 25, 0 of 24,
0 of 26.

So `still()` stripped nothing and `moved_clause()` handed the CAMERA CLAUSE to
the drawer as the END panel's one named change.  The paid prompt on disk,
`ep06/boards/sheets/seq_window_street_0.prompt.txt`:

    "PANEL 3 ONE ACTION LATER, FROM THE SAME CAMERA.  What a viewer sees at a
     different place than in panel 3: The camera pushes in on his face across
     the whole shot."

One sentence, two contradictory instructions.  The drawer moved the camera, and
all seven of episode 6's END panels came back re-staged (0.330 down to -0.007
against their own start cells, every one under the 0.45 floor), leaving ONE END
cell in the episode.

AND THE CAMERA-MOVE RULE IS WHAT SET IT OFF.  Earlier plans led with the camera
on 7 to 13 motions; episode 6 leads with it on 26 of 26, so every END panel got
a camera instruction where it used to get a subject action.  The regex had been
wrong since episode 2 and cost nothing until the prose changed shape."""


def still(motion: str) -> str:
    """A motion line with its camera move removed: the sheet draws a STILL.

    The camera clause is not always first -- 41 of episode 2's 42 motions put
    the subject first with the camera trailing ("his hand comes up as the camera
    pushes in") -- so the trailing form is cut out of the head clause too."""
    said = CAMERA_MOVE.sub("", (motion or "").strip())
    head, semi, rest = said.partition(";")
    trimmed = CAMERA_LEAD.split(head, maxsplit=1)[0].strip(" ,.")
    if semi and trimmed and trimmed != head.strip(" ,."):
        said = f"{trimmed}{semi}{rest}"
    elif not semi and trimmed:
        said = trimmed
    return stop(said)


CAMERA_LEAD = re.compile(r"\b(?:as|while|and)\s+(?=the\s+camera\b)", re.I)
"""Where a motion hands over from the subject's action to the camera's move.
Mirrors `episode_ref_official.CAMERA_LEAD`, which the take builder uses to find
the same clause."""


def stop(text: str) -> str:
    """One sentence, closed.  A frame that ends bare runs into the clause after it
    ("...where that action leaves them Behind them, eight or nine men...")."""
    text = text.strip()
    return text if not text or text[-1] in ".!?\"" else text + "."


CONDITIONAL = re.compile(r"\b(indoors|outdoors|gloves?)\b", re.I)
"""What a character description says only sometimes: the hat that moves with the
weather, and the glove clause, which is written as a negation ("no gloves").
Both are the WARDROBE block's job, which states ONE flat fact per sheet."""


def steady(physical: str) -> str:
    """The half of a character's description that holds in EVERY panel of any
    sheet: the conditional clauses go to WARDROBE, so nothing conditional and no
    negation reaches the drawer."""
    parts = [p.strip() for p in re.split(r"[;,]", physical or "") if p.strip()]
    kept = [p for p in parts if not CONDITIONAL.search(p)]
    return ", ".join(kept).rstrip(". ") + "." if kept else ""


HEADGEAR = re.compile(r"\b(a|an|the)\s+((?:\w+[- ]){0,3}?"
                      r"(?:top hat|silk hat|bowler hat|felt hat|straw hat|deerstalker|boater|bonnet|"
                      r"bowler|cap|hat))\b", re.I)


def hat_of(physical: str) -> str:
    """The headgear phrase in a character description ("a brown bowler hat")."""
    found = HEADGEAR.search(physical or "")
    return found.group(0) if found else ""


def hat_line(name: str, physical: str, outdoors: bool) -> str:
    """The hat rule FLATTENED for this sheet: one place, stated positively.  The
    conditional form was half-obeyed -- Q08_0E kept the bowler on although its own
    text said the hat had come off."""
    hat = hat_of(physical)
    if not hat:  # a description that names no headgear is a bare head, and says so
        return f" {name} is bareheaded in every panel of this sheet."
    noun = re.sub(r"^(a|an|the)\s+", "", hat, flags=re.I)
    return f" {name}'s {noun} is {'on his head' if outdoors else 'in his hand'} in every panel of this sheet."


SIZE_WORDS = {"insert": "INSERT", "extreme_close": "EXTREME CLOSE-UP", "close": "CLOSE",
              "medium_close": "MEDIUM CLOSE-UP", "medium": "MEDIUM", "full": "FULL SHOT", "wide": "WIDE"}


def size_word(seg: dict) -> str:
    return SIZE_WORDS.get(seg.get("size", ""), "MEDIUM")


# The law is stated affirmatively on purpose: a negated noun is still that noun, and our own
# board drew CRISTERION from a "no signage" clause.  The duplicate gate (ALIKE) enforces it.
DIFFERENT = "Every panel on this sheet is a DIFFERENT photograph."
def style_line() -> str:
    """The style line for this run, from `studio.house_style`.

    This was a constant reading "1881 London". Episode 8 was drawn and
    rendered under it over an 1847 Utah desert, because `Episode.palette`
    was wired into the location plate alone and the fix was called done --
    13 of 13 sheet prompts and 28 of 28 take prompts carried the wrong
    place. The place is declared once per run now, in one module.
    """
    return house_style.stills()
CONSTRAINTS = ("The whole canvas is photograph and thin white gutter, edge to edge, and those thin white "
               "gutters are its only borders.\nEvery surface in every panel stays wordless: signs, labels, "
               "glass and paper carry plain tone and grain alone.\nEach panel stands as its own photograph, "
               "one a viewer tells from every other panel at a glance.\nEvery hand in every panel is bare skin.")


WORDLESS = ("Every surface in every panel stays wordless: signs, labels, "
            "glass and paper carry plain tone and grain alone.")
"""The one line of CONSTRAINTS that `wordless_law` opens up, quoted here so the
carve-out and the law can never drift apart by a comma."""


def wordless_law(props: list[dict] | None = None) -> str:
    """CONSTRAINTS, with the wordless line opened up for props that HAVE a picture
    of their words.

    The blanket law is right about the thing it was written for.  gpt-image
    INVENTS lettering: our own board drew CRISTERION off a "no signage" clause,
    and one seed with one blank card gave us both "Number 3 Lauriston Gardens."
    and "Vinisitien of 3 Lauriston Gardens".

    But what is a coin-flip is GENERATION.  PROPAGATION from an attached picture
    measured near-lossless, 6 of 6, including a word at 14 % of frame width,
    defocused, under a moving camera.  So the law's real content is NO INVENTED
    WORDS, and a word with a reference picture is not invented -- it is copied.

    Said affirmatively, and pointing at the picture rather than at the spelling,
    because a negated noun is still that noun and because a model asked to spell
    RACHE out of its own memory hands back RAHE."""
    rows = prop_refs.lettered(props or [])
    if not rows:
        return CONSTRAINTS
    said = "; ".join(f'{r["name"]} carries the words "{r["words"]}"' for r in rows)
    return CONSTRAINTS.replace(
        WORDLESS,
        f"Exactly these surfaces carry writing, and they carry it copied letter for letter from "
        f"their own reference photograph: {said}. Every other surface in every panel stays "
        f"wordless: signs, labels, glass and paper carry plain tone and grain alone.")


END_CONSTRAINTS = "\n".join(l for l in CONSTRAINTS.split("\n") if "every other panel" not in l)
"""The sheet's laws MINUS "one a viewer tells from every other panel at a glance".

That line is the same instruction as "a DIFFERENT photograph", and between them
they are why 9 of episode 2's 13 END cells came back re-staged to a new camera.
An END cell is drawn alone against its own start cell: there is no other panel
for it to differ from, so the line has nothing to buy here and a moved camera to
pay for."""


def sheet_block(cols: int, rows: int, shape: str = "vertical 9:16") -> str:
    """The grid itself.  Unchanged in substance: `cell_boxes()` finds these drawn
    gutters on all six sheets on disk and `gutters_ok` is true in every dq.json."""
    n = cols * rows
    return (f"A film storyboard sheet: a {cols} by {rows} grid of {n} equal {shape} panels filling "
            f"the whole canvas, thin white gutters between them and those gutters as its only borders.\n"
            f"Panels read left to right, top to bottom: panel 1 is top-left, panel {cols} is top-right, "
            f"panel {n} is bottom-right.")


def different_pictures() -> str:
    """The owner's rule, unconditional and near the top, as a law about the SET."""
    return (f"{DIFFERENT} Each panel differs from every other panel on this sheet in camera position, in "
            f"subject size, or in what stands behind the subject. Laid side by side, a viewer can say in "
            f"one word how each panel differs from every other panel. Draw every panel fresh, and keep "
            f"each one far enough from the others that a viewer tells them apart at a glance.")


def span(numbers: list[int]) -> str:
    if len(numbers) == 1:
        return f"Panel {numbers[0]}"
    return "Panels " + ", ".join(str(k) for k in numbers[:-1]) + f" and {numbers[-1]}"


def grows(setup: Setup) -> str:
    """Which way the landmark's apparent size runs along the route: toward a
    landmark at the far end it is larger panel by panel; away from one at the
    route's start it is smaller."""
    return "larger" if setup.landmark_at == FAR_END else "smaller"


def order_block(n: int, ladder: list[int], setup: Setup) -> str:
    """ONE ordering law (story order), plus the distance ladder as explicit panel
    numbers.  The geography-first sort made panel 1 of the criterion sheet shot 2,
    and the sheet then carried two contradictory ordering sentences."""
    text = (f"The panels are in story order: panel 1 happens first, panel {n} happens last, and each panel "
            f"is a later moment than the one before it.")
    if setup.route and ladder:
        far = setup.landmark or "the far door"
        text += f" The people travel {setup.route}."
        if len(ladder) > 1:
            text += (f" {span(ladder)} look along that path, each of them farther along it than the one "
                     f"before, so {far} is {grows(setup)} in each of them than in the one before.")
        else:
            text += f" {span(ladder)} looks along that path, with {far} at the size that panel names."
    return text


def references_block(setup: Setup, physical: dict[str, str], props: list[dict] | None = None) -> str:
    """What each attached image is, by index and role, in the order it is attached:
    the plate, the prop plates, the cast, then the OBJECT cards.

    Every attached picture must be numbered here or it reaches the model as an
    unlabelled image with no law on it -- which is how a silver-knobbed walking
    stick came back drawn as an iron poker.  The one prop that held its size in
    episode 2 (the envelope, 1.25x against 0.36-3.0x for the rest) was the one
    that was both INDEXED and MEASURED in a single sentence; the failures had at
    most two of picture, index and measure."""
    lines = ["Image 1 is the empty location: every panel is set in this exact place, with its "
             "architecture, furniture, windows and light."]
    for prop in setup.props:
        lines.append(f"Image {len(lines) + 1} is the {prop}: this exact vehicle -- the same body, wheels, "
                     f"lamp, harness and animal -- in every panel of every sheet that shows a {prop}. It "
                     f"is the same {prop} all afternoon.")
    for who in setup.cast:
        name = who.replace("_", " ").title()
        lines.append(f"Image {len(lines) + 1} is {name}: {steady(physical.get(who, ''))} Keep exactly this "
                     f"face, hair, build and these clothes in every panel that shows {name}.")
    for row in (props or []):
        # picture, INDEX and measure in ONE sentence: the single episode 2 prop that
        # held its size (the envelope, 1.25x against 0.36-3.0x for the rest) was the
        # one that had all three.  A lettered prop needs the same three for its WORDS.
        copy = (f' Its writing reads "{row["words"]}" and is copied from that photograph letter for '
                f'letter, at that size and on that surface, rather than spelled afresh.'
                ) if row.get("words") else ""
        lines.append(f"Image {len(lines) + 1} is {row['name']}, photographed beside a hand so that its "
                     f"size reads against the fingers: {row['physical']} Draw it at exactly that size "
                     f"against the body it touches, in every panel that shows it.{copy}")
    return "\n".join(lines)


def line_sentence(setup: Setup) -> str:
    """The 180-degree line, as which frame edge things move toward.  Q03_0 was a
    lateral pass and Q03_1 receded down the street: a 90-degree mismatch, because
    nothing fixed which side of the street the camera stands on."""
    return (f"In every panel of this sheet the camera keeps to ONE side of the line the people travel "
            f"along -- they travel {setup.route} -- and it stays on that side for every panel. So "
            f"whoever leads stays on the same side of the frame throughout, whatever moves keeps moving "
            f"the same way across the frame, and the far end of the route stays in the same part of the "
            f"frame in every panel. Which side of the frame each thing lives on is stated above, and it "
            f"holds for every panel of this sheet.")


def geometry_block(setup: Setup) -> str:
    """How the fixed things stand: each relation as a frame edge at an apparent
    size, plus the camera line.  "Ahead of" is the documented weak spot; "which
    edge, at what size" is the documented strength (research, spec section 3)."""
    parts = [setup.geometry] if setup.geometry else []
    if setup.route:
        parts.append(line_sentence(setup))
    return "\n".join(parts)


def wardrobe_block(setup: Setup, physical: dict[str, str]) -> str:
    """The preservation list, standalone and repeated on every sheet, with every
    conditional flattened to one fact.  Buried inside "Image 2 is John Watson: ..."
    it read as a description of the reference, not as a law over the sheet."""
    lines = ["These stay the same in every panel of this sheet."]
    for who in setup.cast:
        name = who.replace("_", " ").title()
        lines.append(f"{name.upper()}: {steady(physical.get(who, ''))}"
                     f"{hat_line(name, physical.get(who, ''), setup.outdoors)}")
    lines.append("Every hand in every panel is bare skin.")
    return "\n".join(lines)


def crowd_block(setup: Setup) -> str:
    """The sheet-level half of the owner's "background folks having regular work"."""
    if not setup.crowd:
        return ""
    return ("This is a public place in a working city and people fill it in every panel. The people behind "
            "the action are different people in different postures in every panel, a fresh group drawn for "
            "each panel. They are busy with their own business, their eyes on their own work.")


def crowd_clause(seg: dict, setup: Setup) -> str:
    """This panel's own background life, with a count and an activity.  A crowd
    named once for a whole location is averaged away: the criterion two-shot and
    its END drew an empty bar although the location text says "two deep"."""
    crowd = seg.get("crowd") or setup.crowd
    # A CROWD IS PART OF THE PLACE, so it needs a panel wide enough to hold a
    # place -- the same ladder `places_the_plate` uses, for the reason stated
    # there: below it you are looking at a person, not at a place.  This used to
    # exclude `insert` alone, so episode 3 drew a constable and four loafers into
    # a MEDIUM_CLOSE on Watson's face, where people can only be smears at the
    # frame edge (owner, 2026-09-13: "a blur human on the side").
    if not crowd or seg.get("size") not in WIDE_ENOUGH:
        return ""
    return f" Behind them, {crowd}, out of focus."


def ladder_clause(seg: dict, setup: Setup) -> str:
    """How big the far landmark is from HERE (research: camera-anchored size words,
    never percentages)."""
    far = setup.landmark or "the far door"
    size = door_size(seg.get("path") or 0.0, setup.landmark_at, setup.landmark_size)
    return f" {far[0].upper() + far[1:]} {size}."


def before_clause(seg: dict) -> str:
    """What is still AT REST.  "The instant before: <verb phrase>" was drawn as the
    finished action -- Q02_0 came back with the glass already raised."""
    if seg.get("at_rest"):
        return f"This is the instant BEFORE the action: {seg['at_rest']}"
    return (f"This is the instant BEFORE the action. What follows this panel: {still(seg['motion'])} Draw "
            f"the moment just before that begins, with everything that moves still at rest.")


def start_text(k: int, seg: dict, ladder: str, crowd: str) -> str:
    """A start panel: size, where the CAMERA stands, the nouns in frame, the
    landmark ladder, this panel's crowd, and what is still at rest."""
    head = f"Panel {k} - {size_word(seg)}"
    head += f", camera {seg['camera'].rstrip('. ')}." if seg.get("camera") else "."
    return f"{head} In frame: {stop(seg['frame'])}{ladder}{crowd} {before_clause(seg)}".strip()


REFRAMING = re.compile(
    r"(?:, )?(?:from )?(?:a )?(?:stride |pace |step |foot |hand's breadth )?"
    r"(?:nearer|closer|further back|farther back|pulled back|drawn back)[^,.;:]*"
    r"|(?:a )?(?:tighter|wider|looser|closer|nearer) (?:framing|shot|angle|view)[^,.;:]*"
    r"|from a (?:lower|higher|steeper|flatter) angle[^,.;:]*"
    r"|the camera has (?:moved|pushed|pulled|risen|dropped)[^,.;:]*"
    r"|(?:has|have) grown to [^,.;:]*",
    re.I)
"""Phrases in an END panel that re-specify the CAMERA it was told to keep.

`end_text` promises "the same camera position, the same lens" and then prints
the plan's own end prose, which the authors wrote as a complete fresh picture --
and a fresh picture renames the framing.  The model resolves the contradiction
in favour of the prose every time: "END keeps the same camera position" was
obeyed 4 times in 12 (0.33), the worst rate in the sheet prompt bar the dead
landmark ladder.  These cells are the takes' END references, so a moved camera
becomes a jump inside one shot that survives to the master.

Frame-edge assertions are NOT reframing and are kept: they say where a thing is,
not how the camera moved to see it, and they are the instruction this model
obeys best (0.83).  Written without a single backslash on purpose -- this
pattern has been mangled twice by escape processing on its way to disk."""


def keeps_camera(text: str) -> str:
    """The END picture with its camera re-specification removed.

    OpenAI's image-editing guidance for exactly this case: say "change only X"
    and list the details to preserve.  The change and the picture stay; the new
    framing goes."""
    out = REFRAMING.sub("", text or "")
    out = re.sub("  +", " ", out)
    out = re.sub(" ([,.;:])", lambda m: m.group(1), out)
    out = re.sub("([,;:]) *([,;:])", lambda m: m.group(1), out)
    return out.strip().lstrip(",;: ").strip()


TRAVEL = re.compile(r"\btravell?(?:ing|s|ed)?\s+(?:about\s+|roughly\s+)?([^;,.]+)", re.I)
"""How far the camera goes, in the plan's own body-scale words.

Every motion line the plan writes carries one: "travelling two long strides",
"travelling a hand's breadth", "travelling a forearm".  `episode_spec` already
requires it -- a move with no distance is a move the renderer sizes itself."""

HOLD_WORD = (r"static|locked|lock(?:ed)?[- ]off|holds?|held|holding|stays?|"
             r"remains?|does not move|never moves")
HOLDS = re.compile(rf"\b(?:{HOLD_WORD})\b", re.I)
"""A camera that does not travel, however the plan says so.

This knew "static" and "locked" only, so ep05 shot 21 -- "the camera holds level
with its hub" -- read as a move whose distance could not be found."""

BODY = (r"(?:an?|one|two|three|four|half a)\s+(?:whole\s+|long\s+|short\s+)?"
        r"(?:hand's breadth|hand's width|thumb's width|finger's breadth|arm's length|"
        r"head's height|forearm|strides?|paces?|steps?|treads?)")
GAIT = (r"at an? (?:normal|walking|trotting|running|strolling|steady|brisk)"
        r"(?: walking| running)? pace")
DISTANCE = re.compile(rf"\b({BODY}|{GAIT})", re.I)
"""How far, in the owner's body-scale words -- the standing rule for every
amount in this pipeline: no percentages, no metres, no "slowly".

Only DIMENSIONAL forms are listed. A bare "a hand" is a hand, not a distance,
and ep04 shot 2's "the camera pushes straight in on the hand" would otherwise
have been read as travelling one hand."""

# Where the camera ENDS, per move word.  The tilt/crane pair splits on its own
# direction word; everything that travels across the scene rather than toward
# or away from it ends "along its own travel", which is the only thing that can
# be said without knowing the geography.
NEARER = r"push\w*|dolly[- ]?in|dollies in|zoom\w*\s+in|creep\w*\s+in"
FURTHER = r"pull\w*|dolly[- ]?out|dollies out|zoom\w*\s+out|withdraw\w*"
VERTICAL = r"tilt\w*|cran\w*|pedestal\w*|boom\w*|ris\w*"


def camera_clause(motion: str) -> str:
    """The part of a motion line that belongs to the CAMERA, in either shape.

    The plan writes the camera first ("The camera pushes in ...; his hand comes
    down") or last ("his hand comes down as the camera pushes in"), and both
    shapes are in episode 7."""
    # THE CAMERA HAS TO BE THE ONE DOING SOMETHING.  "her eyes fix on the
    # camera" and "the paper turns toward the camera" both name the camera and
    # neither moves it; reading them as camera moves made ep05 shots 16 and 17
    # into moves with no distance.
    doing = re.compile(rf"\bthe\s+camera\s+(?:{MOVE_WORD}|{HOLD_WORD}|is|are|was)\b", re.I)
    for part in re.split(r"[;.]", motion or ""):
        if doing.search(part):
            return part.strip()
    return ""


def camera_end(motion: str, j: int = 0) -> str:
    """Where the camera stands in the shot's LAST frame; "" if it never left.

    MEASURED, episode 7 take 22: the plan pushes the camera in two long strides
    across the whole shot, the take does it cleanly, and the drawn END cell sits
    at the START camera because `end_text` told it to -- so `drift_gate` scored
    the last frame at 0.397 against a picture taken from a place the camera had
    left, and HARD-failed a good take.

    "From the same camera" was true of episodes 2 to 5, which mostly hold still.
    Episode 6 cured the stillness by moving the camera across the whole of every
    shot, and the sentence became false for every END panel in the episode."""
    said = camera_clause(motion)
    if not said or HOLDS.search(said):
        return ""
    # "travelling <how far>" if the plan wrote it that way, else the body-scale
    # amount wherever in the clause it stands.  Eleven shots across episodes 6
    # and 7 use the second shape.
    far = TRAVEL.search(said) or DISTANCE.search(said)
    if not far:
        return ""
    how, at = far.group(1).strip(), f"panel {j}" if j else "the start panel"
    # EACH DIRECTION TAKES ITS OWN PREPOSITION.  A push is comparative and takes
    # "than"; a rise is positional and takes "above".  A prompt the model has to
    # repair is a prompt it may repair the wrong way.
    if re.search(NEARER, said, re.I):
        return f"{how} NEARER than in {at}"
    if re.search(FURTHER, said, re.I):
        return f"{how} FURTHER BACK than in {at}"
    if re.search(VERTICAL, said, re.I):
        fallen = re.search(r"\b(?:down|downward\w*)\b", said, re.I)
        side = "DROPPED" if fallen else "RISEN"
        return f"a camera {side} {how} {'below' if fallen else 'above'} {at}"
    return f"a camera {how} ALONG its own travel from {at}"


def end_text(k: int, seg: dict, crowd: str) -> str:
    """An END panel: THE CHANGE FIRST, then its own complete picture.

    This used to say "same" eight times and carry a six-noun "Unchanged since
    panel J" list against one change clause stated last -- while every start
    panel on the same sheet said "same" zero times.  Four of its six sentences
    asserted sameness.  Sameness is now SHOWN, by the inherited inventory in
    `frame`, instead of asserted; what the prompt spends its words on is the one
    thing that moved and where it moved to."""
    j, moved = seg["of"], (seg.get("changed") or "").rstrip(". ")
    turn = (f"What a viewer sees at a different place than in panel {j}: {moved}. "
            f"Draw that finished and at rest, at its new place in the frame. "
            if moved else f"Panel {j} one action later. ")
    # WHERE THE CAMERA STANDS NOW.  A shot whose camera travels ends somewhere
    # else, and the panel that says "the same camera" is a picture the take can
    # never arrive at.  `keeps_camera` is right for a locked-off shot and wrong
    # for a travelling one for the same reason: it deletes the reframing, and
    # when the camera really did reframe, the reframing IS the panel.
    went = seg.get("moved_from") or camera_end(seg.get("motion", ""), j)
    where = f"from {went}" if went else "from the same camera"
    picture = seg["frame"] if went else keeps_camera(seg["frame"])
    return (f"Panel {k} - PANEL {j} ONE ACTION LATER, {where}. {turn}"
            f"In frame: {stop(picture)}{crowd} Panel {k} is its own photograph: "
            f"laid beside panel {j}, a viewer points at one thing and says where it went.")


def panel_text(k: int, seg: dict, route: list[int], setup: Setup) -> str:
    """One panel, start or END."""
    crowd = crowd_clause(seg, setup)
    if seg.get("end"):
        return end_text(k, seg, crowd)
    ladder = ladder_clause(seg, setup) if k in route else ""
    return start_text(k, seg, ladder, crowd)


def panels_block(segs: list[dict], route: list[int], setup: Setup) -> str:
    return "\n\n".join(panel_text(k, s, route, setup) for k, s in enumerate(segs, start=1))


def route_numbers(geography: bool | int | list[int], n: int) -> list[int]:
    """The panel numbers that look along the route (True = all, False = none)."""
    if geography is True:
        return list(range(1, n + 1))
    if geography is False:
        return []
    if isinstance(geography, int):
        return list(range(1, geography + 1))
    return list(geography)


def strict_prefix(dupes: list[tuple[str, str]], regress: list[int], setup: Setup) -> str:
    """The retry NAMES the offender.  It used to be one of two fixed strings, so a
    second attempt was told that some panel was a copy and never which one."""
    lines = []
    for a, b in dupes:
        lines.append(f"STRICT: panels {a} and {b} came back as one picture drawn twice. Draw {b} afresh as "
                     f"its own photograph, so a viewer seeing the two side by side reads one clear "
                     f"difference at a glance.")
    if regress:
        far = setup.landmark or "the far door"
        lines.append(f"STRICT: one walk, one direction. {far[0].upper() + far[1:]} is {grows(setup)} in every "
                     f"route panel than in the route panel before it, on every panel of this sheet.")
    return " ".join(lines)


BLOCKS = ("SHEET", "DIFFERENT PICTURES", "ORDER", "REFERENCES", "LOCATION", "GEOMETRY", "WARDROBE",
          "PROPS", "BACKGROUND LIFE", "PANELS", "STYLE", "CONSTRAINTS")
"""Scene, subject, details, constraints -- the order both OpenAI guides give for
a complex request, with the two sheet-wide laws hoisted above the panel list."""


def prompt(segs: list[dict], setup: Setup, physical: dict[str, str], previous: bool, first: bool,
           geography: bool | int | list[int] = True, aspect: str = "9:16",
           props: list[dict] | None = None) -> str:
    """The sheet prompt as labelled blocks.  `geography` is the panel numbers that
    sit on the walk (True = all).  `previous` and `first` are kept for the caller's
    signature: the previous sheet is no longer attached (reviewer 3 item 7, it
    copied framings), so nothing on the sheet depends on them."""
    route = route_numbers(geography, len(segs))
    ladder = [k for k in route if not segs[k - 1].get("end")]
    cols, rows, _ = grid(len(segs), aspect)
    bodies = (sheet_block(cols, rows, cv.words(aspect)), different_pictures(), order_block(len(segs), ladder, setup),
              references_block(setup, physical, props or []), setup.described, geometry_block(setup),
              wardrobe_block(setup, physical), props_block(props or []),
              crowd_block(setup), panels_block(segs, route, setup),
              style_line(), wordless_law(props or []))
    return "\n\n".join(f"{head}\n{body}" for head, body in zip(BLOCKS, bodies) if body)


def single_block(shape: str = "vertical 9:16") -> str:
    """One panel drawn alone: the same law as a sheet, at the plan's own shape."""
    return (f"A film storyboard frame: one single {shape} photograph filling the whole canvas, "
            f"its own plain edges the only borders.")


SINGLE = single_block()


def single(seg: dict, setup: Setup, physical: dict[str, str], aspect: str = "9:16") -> str:
    """One panel drawn alone, under the same laws its sheet was drawn under.

    A sheet costs $0.20 and redraws every panel on it, including the ones that
    came back right; one panel costs $0.08 and touches only the picture that was
    wrong.  The location, geometry and wardrobe blocks come across unchanged so
    the replacement still belongs to its sheet."""
    heads = ("FRAME", "REFERENCES", "LOCATION", "GEOMETRY", "WARDROBE", "BACKGROUND LIFE",
             "THE PICTURE", "STYLE", "CONSTRAINTS")
    bodies = (single_block(cv.words(aspect)), references_block(setup, physical),
              setup.described, geometry_block(setup),
              wardrobe_block(setup, physical),
              # the crowd needs room here for the same reason `crowd_clause` does:
              # a panel redrawn alone is still a panel, and a medium close on one
              # man's head has no street in it to fill with people
              crowd_block(setup) if seg.get("size") in WIDE_ENOUGH else "",
              single_picture(seg, setup),
              style_line(), CONSTRAINTS)
    return "\n\n".join(f"{head}\n{body}" for head, body in zip(heads, bodies) if body)


def end_key(key: str) -> tuple[int, int, bool]:
    """`Q19_1E`, `S19.1E`, `19.1E` or a filename -> (19, 1, True).

    IT TAKES THE NAME ON DISK.  It used to strip a leading "S" and split on ".",
    which was the i2v-era naming, while every cell written by `cell_name` is
    `Q19_1E.png`.  `redraw_panel.py` -- the $0.08 repair for one wrong cell --
    documents itself as `... S14.1 --approved`, so handing it the name a reader
    can actually see raised `invalid literal for int(): 'Q13_0'`.  Measured when
    episode 5's doorway wide needed a walking stick taken out of it.

    A trailing E names a segment's END cell."""
    body = key.upper().strip()
    for tail in (".PNG", ".JPG", ".JPEG"):
        if body.endswith(tail):
            body = body[:-len(tail)]
    body = body.lstrip("SQ")
    end = body.endswith("E")
    head, _, sub = body.rstrip("E").replace("_", ".").partition(".")
    return int(head), int(sub) if sub else 0, end


def end_single(seg: dict, setup: Setup, physical: dict[str, str], aspect: str = "9:16") -> str:
    """One END cell drawn alone, FROM ITS OWN START CELL as Image 1.

    MEASURED, episode 2: 9 of 13 END cells came back re-staged to a different
    camera setup.  The sheet's own prose already asked for the same camera, lens
    and light -- and lost, because the same block closes with "a DIFFERENT
    photograph ... a viewer can say what happened in between" and the sheet-wide
    no-duplicates law pushes the same way.  Told to be the same and to be
    different, the drawer moved the camera.

    So the camera is not argued for here, it is SHOWN: the start cell is the
    first attached image and the only instruction is what changed inside it.
    Every reference keeps its place behind it, one index later."""
    if not seg.get("end"):
        raise ValueError(f"not an END panel: {cell_name(seg['shot'], seg['sub'])}")
    from studio.episode_ref_official import lower_lead

    changed = lower_lead((seg.get("changed") or still(seg.get("motion", ""))).rstrip(". "))
    start = (f"Image 1 is this same shot ONE MOMENT EARLIER. Take from it the place, the people, "
             f"their wardrobe, the light, and the camera's ANGLE and SIDE -- the camera has not "
             f"been re-positioned, it has not crossed to another part of the room, another angle "
             f"or another subject, and the same lens is on it. Do not take the framing from Image "
             f"1. The camera has travelled straight in or out along its own axis, or tilted, so "
             f"that in the picture you draw: {changed}. "
             f"The picture you draw is not a copy of Image 1 -- the framing has changed by exactly "
             f"that much -- and it is not a new camera position either. Everything else in frame "
             f"stands where Image 1 leaves it.")
    later = shift_indices(references_block(setup, physical))
    heads = ("FRAME", "REFERENCES", "LOCATION", "GEOMETRY", "WARDROBE", "BACKGROUND LIFE",
             "THE PICTURE", "STYLE", "CONSTRAINTS")
    bodies = (single_block(cv.words(aspect)), f"{start}\n{later}", setup.described,
              geometry_block(setup), wardrobe_block(setup, physical), crowd_block(setup),
              f"The same frame as Image 1, one action later: {changed}.", style_line(), END_CONSTRAINTS)
    return "\n\n".join(f"{head}\n{body}" for head, body in zip(heads, bodies) if body)


def shift_indices(block: str) -> str:
    """Every `Image N` in a references block becomes `Image N+1`.

    The start cell takes slot 1, so the plate, the props and the cast all move
    down one.  An unrenumbered block would label the plate as the start cell,
    which is the fault that drew a walking stick as an iron poker."""
    return re.sub(r"\bImage (\d+)\b", lambda m: f"Image {int(m.group(1)) + 1}", block)


def single_picture(seg: dict, setup: Setup) -> str:
    """The one panel's own text, with its panel number taken off."""
    parts = [seg["frame"]]
    if seg.get("camera"):
        parts.append(f"The camera stands {seg['camera']}.")
    if seg.get("at_rest"):
        parts.append(seg["at_rest"])
    if seg.get("crowd") and seg.get("size") in WIDE_ENOUGH:
        parts.append(seg["crowd"])
    return " ".join(p.rstrip() for p in parts)


def drop_reason(end: str, start: str, sim: float, motion: str = "") -> str:
    """Why this END cell was retired, in the words of what was MEASURED.

    It used to be the hardcoded string "still a copy of {start} after strict",
    written for BOTH outcomes -- and `duplicates()` flags a pair when
    `end_pair_verdict() != "ok"`, which is a copy OR a re-staging, two opposite
    faults.  All seven of episode 6's retired END cells scored 0.330, 0.253,
    0.321, 0.315, 0.407, 0.176 and -0.007 against their own start: every one a
    RE-STAGING, every one recorded as a copy.

    The string was not the cost.  The false fact was quoted into the skill's
    stated mechanism, into a reviewer's brief and into a report to the owner
    before anyone measured the cells."""
    if sim > END_CEILING:
        return f"a copy of {start} at {sim:.2f}, over the {END_CEILING} ceiling"
    # A PANEL IS NEVER TOLD IT BROKE A RULE THAT DID NOT JUDGE IT.  The floor
    # does not apply to a shot whose camera was told to travel, so naming it
    # here would quote a number that never ran -- which is how episode 6's seven
    # re-stagings came to be recorded as copies.
    if sim < END_FLOOR and not (motion and camera_end(motion)):
        return f"re-staged from {start} at {sim:.2f}, under the {END_FLOOR} floor"
    return f"in band against {start} at {sim:.2f} -- dropped for another pair's sake"


def stale_cells(boards) -> list[str]:
    """Cells on disk that no sheet in this episode's reports claims to have cut.

    A cell is named by SHOT INDEX -- `Q19_0E.png` is shot 19's END panel -- and a
    plan may be renumbered.  Episode 8 was: five shots were spliced in so every
    shot carried one line, and everything from the fifth onward moved up.  The
    sheets were redrawn and wrote the new cells beside the old ones, and nothing
    removed the old ones.

    MEASURED: four survived -- Q09_0E, Q16_0E, Q19_0E, Q23_0E -- as pictures of
    shots that no longer carry those numbers.  Old shot 19 was the scouts
    climbing the bluff; new shot 19 is Ferrier and the child asleep against the
    boulder.  `takes_r2v` attached the old picture as the new shot's
    destination, and `drift` failed three takes for not arriving at a photograph
    of some horsemen -- three of the episode's five failures, every one looking
    exactly like a renderer that could not reach its mark.

    THE SHEET REPORT IS THE TRUTH: `seq_<setup>.dq.json` lists the cells each
    attempt actually cut.  An episode whose boards are not drawn yet has no
    reports, and then nothing is judged -- there is no truth to check against,
    and calling every cell stale would be worse than saying nothing."""
    import json

    room = cells_in(boards)
    if not room.exists():
        return []
    claimed: set[str] = set()
    for report in sheets_in(boards).glob("seq_*.dq.json"):
        try:
            doc = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for sheet in doc.get("sheets", []):
            claimed |= set(sheet.get("cells", []))
    if not claimed:
        return []
    return sorted(p.name for p in room.glob("*.png") if p.name not in claimed)
