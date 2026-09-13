"""The PRE-SPEND storyboard gate: every fault that can be read in WORDS.

Owner, 2026-09-11: "dq check before generating images".  This is that rung.
It runs on the built sheet prompt and on the panel texts behind it, at the
last free moment before `images.edit` is called, so a sheet that cannot come
back right is refused for $0 instead of being discovered on a $0.13-$0.20
sheet and then animated for GPU-hours (the ladder's rule: a check belongs at
the last free moment before the irreversible spend it can prevent).

HARD or ADVISORY, and why.  A check is HARD when the fault makes the draw
unable to come back right and the detector has a measured true positive on
disk -- refusing costs nothing, because the fix is a sentence.  A check is
ADVISORY when it measures texture rather than correctness, or when the
detector is a heuristic over nouns and a false refusal would cost more than
the fault it prevents.

    AFFIRMATIVE    HARD      a negated noun is still that noun in the prompt
                             (`studio/affirm.py`, three measured draws)
    TWINS          HARD      two panels asking for one picture cannot both be
                             the DIFFERENT PICTURE the sheet demands
    INSTANT BEFORE HARD      the panel's OWN motion found finished in the
                             picture it draws, or an outright "has just" /
                             "at full height": a panel drawn at its end state
                             leaves the render nothing to do (T02, T07, T12,
                             T17 froze on exactly these)
      (watch)      advisory  "already", "about to", "the last word", and a
                             perfect tense the motion never names -- "a porter
                             HAS SET his barrow down" is the crowd at rest
    END PANEL      HARD      an `end` picture with no `changed`: told only "the
                             same place", the drawer drew the same picture
                             (0.951, 0.890, 0.821 on disk)
      (shape)      advisory  12-17 words, one sentence, a frame edge and an
                             apparent size -- all 27 `changed` strings on the
                             live plan pass, so the rule has caught no real
                             fault yet and may not stop a draw
    CAMERA         HARD      a panel is a still; a move word in `camera` is a
                             video instruction leaking into a still prompt
    GEOMETRY       HARD      a relational preposition governing a vehicle part
                             with no frame edge anywhere in the panel: the
                             documented weak spot, and the owner's fault #2
    CROWD          advisory  background life sells the place; a missing crowd
                             still draws a usable panel
    WARDROBE       advisory  the contract phrase; the one fault that spends
                             ("glove") is already a HARD refusal in the spec
    PROPS          advisory  noun matching cannot tell a prop that moves from
                             a place named in passing ("turns toward the doors")
    GRID           HARD      the panel count, the grid and the sentence must
                             agree or `cell_boxes()` cuts the wrong cells

Nothing here opens an image, calls an API or spends.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from studio import episode_seq_board as sq
from studio.affirm import negations
from studio.episode_spec import SHEET_TEXT, Setup


@dataclass(frozen=True)
class Finding:
    """One fault, named, with the panel to fix and the words to fix."""
    check: str
    panel: str
    text: str
    hard: bool = True
    note: str = ""

    def as_dict(self) -> dict:
        return {"check": self.check, "panel": self.panel, "text": self.text,
                "hard": self.hard, "note": self.note}

    def row(self) -> str:
        return f"{'FAIL' if self.hard else 'watch'} {self.check:<14} {self.panel:<8} {self.text[:70]}"


def panel_key(seg: dict) -> str:
    """The cell the owner reads on the contact sheet: `Q09_1`, `Q02_0E`."""
    return sq.cell_name(seg["shot"], seg["sub"], bool(seg.get("end")))[:-4]


def drawn_text(seg: dict) -> str:
    """The words the DRAWER is shown for this panel.  An END panel is printed as
    its own picture plus "the same camera position as panel j", so its `camera`
    and `at_rest` never reach the sheet and are not its to answer for."""
    if seg.get("end"):
        return (seg.get("frame") or "").strip()
    return " ".join(f for f in (seg.get("frame", ""), seg.get("camera", ""), seg.get("at_rest", "")) if f).strip()


def panel_source(seg: dict) -> str:
    """Every model-facing string this panel contributes to the sheet."""
    fields = [seg.get(name if name != "end" else "end_frame", "") for name in SHEET_TEXT]
    return " ".join(f for f in fields if f)


# ---- AFFIRMATIVE ----------------------------------------------------------

def owner(phrase: str, segs: list[dict]) -> str:
    """The panel whose own text carries this phrase; the sheet when no panel does."""
    pattern = re.compile(rf"(?<![\w-]){re.escape(phrase)}(?![\w-])", re.IGNORECASE)
    return next((panel_key(s) for s in segs if pattern.search(panel_source(s))), "sheet")


def affirmative(prompt: str, segs: list[dict]) -> list[Finding]:
    """Zero negation in the BUILT prompt: the drawer draws the noun either way."""
    return [Finding("AFFIRMATIVE", owner(bad, segs), bad, True,
                    "name what occupies that place instead") for bad in negations(prompt)]


# ---- TWINS ----------------------------------------------------------------

TWIN = 0.72
WATCH = 0.62
"""CALIBRATED on the six real sheets (153 within-sheet pairs, `frame` + `camera`
as content-word cosine).  Reviewer 3 measured the corridor pair S09/S11 at
**0.731** before it was rewritten; after the rewrite the same pair measures
0.707 and every other pair on the fixed plan sits at median 0.367, p90 0.561.
So the floor is 0.72: the one known text twin fails, its own fix passes.  The
0.62 watch band is the margin -- it prints, it does not refuse."""

STOP = frozenset("""the a an of in on at to and or with his her its from by for over under into out up down is are
was were be been through across along beside near past as that this these those one two three four five whole same
own it he she they them their there here where what when while so then than each every all both and not""".split())


def content(text: str) -> list[str]:
    """The words that carry the picture: no stop words, nothing under three letters."""
    return [w for w in re.findall(r"[a-z']+", (text or "").lower()) if w not in STOP and len(w) > 2]


def overlap(a: str, b: str) -> float:
    """Normalised token overlap (cosine over content-word counts), 0 to 1."""
    ca, cb = Counter(content(a)), Counter(content(b))
    top = sum(ca[k] * cb[k] for k in set(ca) | set(cb))
    size = math.sqrt(sum(v * v for v in ca.values())) * math.sqrt(sum(v * v for v in cb.values()))
    return top / size if size else 0.0


def picture(seg: dict) -> str:
    """What this panel asks to be DRAWN: the end picture, or the frame and camera."""
    if seg.get("end"):
        return seg.get("frame") or seg.get("end_frame") or ""
    return f"{seg.get('frame', '')} {seg.get('camera', '')}"


def twins(segs: list[dict], floor: float = TWIN, watch: float = WATCH) -> list[Finding]:
    """Every pair of panels on one sheet that describes the same picture."""
    out = []
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            score = overlap(picture(segs[i]), picture(segs[j]))
            if score > watch:
                out.append(Finding("TWINS", panel_key(segs[j]), picture(segs[j]).strip(), score > floor,
                                   f"overlap {score:.3f} with {panel_key(segs[i])}"))
    return out


# ---- INSTANT BEFORE -------------------------------------------------------

OVER = re.compile(r"\b(?:has|have)\s+just\s+\w+|\bjust finished\b|\bat full (?:height|stretch)\b"
                  r"|\bfully (?:extended|raised|open)\b|\balready (?:raised|lifted|up|open|closed|done)\b",
                  re.IGNORECASE)
"""The action over, said outright, whatever the panel's own motion is."""

DONE = re.compile(r"\b(?:has|have)\s+(?:just\s+)?(\w+?)(?:en|ed|n|t)?\b(?=\s)", re.IGNORECASE)
"""`has climbed`, `have risen` -- a perfect tense, with its verb stem captured."""

WATCHING = re.compile(r"\balready\b|\babout to\b|\bthe last word\b", re.IGNORECASE)
"""Words that are a finished action as often as a state at rest: "his weight
already down on the stick" is frame zero; "already raised" is not.  Reviewer 3
called S18's "lips just closed on the last word" a fault and S22's identical
phrasing correct, so no text rule separates them: the gate prints, the eye
decides."""


def end_state(motion: str, text: str) -> str | None:
    """The panel's OWN motion, found finished in the picture it draws: `motion`
    says "climbs the last three steps" and `frame` says "has climbed"."""
    stems = set(re.findall(r"\b(\w{3,})(?:s|es)\b", (motion or "").lower()))
    return next((m.group(0) for m in DONE.finditer(text)
                 if m.group(1).lower().rstrip("e") in {s.rstrip("e") for s in stems}), None)


def instant_before(seg: dict) -> list[Finding]:
    """A start panel is frame zero.  An END panel is exempt: showing the action
    finished is the whole job of an END panel."""
    if seg.get("end"):
        return []
    text = f"{seg.get('frame', '')} {seg.get('at_rest', '')}"
    if found := OVER.search(text) or end_state(seg.get("motion", ""), text):
        phrase = found if isinstance(found, str) else found.group(0)
        return [Finding("INSTANT BEFORE", panel_key(seg), phrase, True,
                        "the render has nothing left to do; draw the instant before it")]
    if found := WATCHING.search(text) or DONE.search(text):
        return [Finding("INSTANT BEFORE", panel_key(seg), found.group(0), False,
                        "check this is a state at rest and not the action finished")]
    return []


# ---- END PANEL ------------------------------------------------------------

CHANGED_WORDS = (12, 17)
"""Reviewer 3's band.  The five `changed` strings that were actually drawn ran
7 to 117 words; a 117-word list contradicts the "everything else is unchanged"
sentence printed straight after it."""

EDGE = re.compile(r"\b(?:left|right|top|bottom|centre|center|middle|upper|lower)\b(?:\s+\w+){0,2}"
                  r"\s+\b(?:frame|edge|third|thirds|half|corner|side)\b"
                  r"|\b(?:edge|corner|side|third|half)\s+of\s+(?:the\s+)?frame\b"
                  r"|\b(?:top|bottom|upper|lower)\s+(?:left|right|centre|center|middle)\b", re.IGNORECASE)
SHOUTED = re.compile(r"\b(LEFT|RIGHT|TOP|BOTTOM|CENTRE|CENTER|MIDDLE|UPPER|LOWER)\b")
"""Two ways the plan names a place in the FRAME: the phrase ("at the left of
frame", "the LEFT two thirds of frame", "TOP RIGHT") and the house convention,
a positional word SHOUTED ("one red bead stands at the CENTRE").  A bare
lower-case "his left hand" is anatomy and counts as neither."""


def names_edge(text: str) -> bool:
    """True when this text puts something at a named place in the frame."""
    return bool(EDGE.search(text or "") or SHOUTED.search(text or ""))
SIZE = re.compile(r"\b(fill|fills|filling|half|third|thirds|quarter|sixth|tall|taller|height|high|wide|"
                  r"width|long|larger|smaller|shorter|nearer|thumbnail|pinhead|fingernail|hand's)\b", re.I)


def shape(changed: str) -> list[str]:
    """What the one-sentence rule is missing from this `changed` string."""
    words = len(changed.split())
    bad = [] if CHANGED_WORDS[0] <= words <= CHANGED_WORDS[1] else [f"{words} words"]
    if len(re.findall(r"[.!?](?:\s|$)", changed.strip())) > 1:
        bad.append("more than one sentence")
    if not names_edge(changed):
        bad.append("no frame edge")
    if not SIZE.search(changed):
        bad.append("no apparent size")
    return bad


def end_findings(seg: dict) -> list[Finding]:
    """An END panel exists only with the one change it shows, said in a sentence."""
    end, changed = seg.get("end_frame") or "", seg.get("changed") or ""
    if not end:
        return []
    if not changed:
        return [Finding("END PANEL", panel_key(seg), end, True,
                        "an end picture with no named change is drawn as a copy of its start panel")]
    faults = shape(changed)
    return [Finding("END PANEL", panel_key(seg), changed, False, "; ".join(faults))] if faults else []


# ---- CAMERA ---------------------------------------------------------------

MOVE = re.compile(r"\b(pan|pans|panning|tilt|tilts|tilted|tilting|track|tracks|tracking|dolly|dollies|"
                  r"zoom|zooms|zooming|crane|cranes|craning|handheld|steadicam|orbit|orbits|orbiting|"
                  r"push in|pushes in|pulls back|pull back|whip pan)\b", re.IGNORECASE)


def camera_still(seg: dict) -> list[Finding]:
    """A panel is a STILL.  `motion` may move the camera -- it is written for
    MiniMax and the sheet never sees it -- but `camera` says where it STANDS."""
    if seg.get("end"):
        return []
    if found := MOVE.search(seg.get("camera") or ""):
        return [Finding("CAMERA", panel_key(seg), found.group(0), True,
                        "a panel is one photograph; say where the camera stands")]
    return []


# ---- GEOMETRY -------------------------------------------------------------

OBJECT = (r"hansom|cab|wheel|wheels|horse|shafts|hood|side-lamp|lamp|stick|glass|tube|stool|slab|vessel|"
          r"bodkin|bowler|barrow|trolley|tray|basket|carriage|axle|hub|tyre")
PLACE = r"wall|counter|window|arch|archway|gateway|gate|door|doorway|passage|railings|shelves|pillar|steps|kerb"
RELATION = re.compile(rf"\b(?:ahead of|in front of|beside|behind)\s+(?:the|a|an|his|her|its|their|two\s+\S+\s+)?"
                      rf"(?:\w+[- ]){{0,2}}(?:{OBJECT})\b", re.IGNORECASE)
"""A relation whose object is a THING.  Used of a wall it is how a room is
described; used of a wheel it is the relation `Q03_1` drew as a horse level
with a wheel, three times, in three different arrangements."""

BIG = re.compile(rf"\b(hansom|cab|wheel|horse|shafts|{PLACE})\b", re.IGNORECASE)


def geometry(seg: dict) -> list[Finding]:
    """A vehicle or a landmark placed by a preposition and by no frame edge."""
    text = drawn_text(seg)
    if not BIG.search(text) or names_edge(text):
        return []
    return [Finding("GEOMETRY", panel_key(seg), found.group(0), True,
                    "say which frame edge it sits at, and how big it stands there")
            for found in RELATION.finditer(text)]


# ---- CROWD ----------------------------------------------------------------

MANY = re.compile(r"\b(two|three|four|five|six|seven|eight|nine|ten|several|many|[2-9]|\d\d+)\b|"
                  r"\b(men|women|students|porters|drinkers|pedestrians|walkers|waiters|clerks|nurses|"
                  r"people|figures|passers-by)\b", re.IGNORECASE)
COUNT = re.compile(r"\b(a|an|one|two|three|four|five|six|seven|eight|nine|ten|several|\d+)\b", re.IGNORECASE)
ACTIVITY = re.compile(r"\b\w+(?:ing|ed)\b", re.IGNORECASE)


def public(setup: Setup) -> bool:
    """A public place is the one whose own crowd names MORE THAN ONE person.
    Derived from the plan, never a hard-coded list of setup names: the live
    plan's lab and bench carry "one student ... with his back turned", the
    other four carry two deep at a counter, three men under an arch."""
    return bool(MANY.search(setup.crowd or ""))


def crowd_findings(seg: dict, setup: Setup) -> list[Finding]:
    """A public setup's panels carry their own background life; a private one
    does not pretend to.  A crowd named once for a location is averaged away."""
    crowd = seg.get("crowd") or ""
    if seg.get("size") == "insert":
        return []
    if not public(setup):
        return [Finding("CROWD", panel_key(seg), crowd, False,
                        "the setup names one person in this private place; this panel draws a crowd")] \
            if MANY.search(crowd) else []
    if not crowd:
        return [Finding("CROWD", panel_key(seg), setup.crowd, False,
                        "this panel names no background life of its own")]
    missing = [name for name, found in (("a count", COUNT.search(crowd)), ("an activity", ACTIVITY.search(crowd)))
               if not found]
    return [Finding("CROWD", panel_key(seg), crowd, False,
                    f"the crowd wants {' and '.join(missing)} of its own")] if missing else []


# ---- WARDROBE -------------------------------------------------------------

CONTRACTS = {
    "hand": (re.compile(r"\bhand\b|\bhands\b|knuckle|finger|fist", re.I),
             re.compile(r"bare sunburnt|bare skin|bare hand|bare (?:left|right)|plaster", re.I),
             "the bare sunburnt hand, or the plastered forefinger"),
    "hat": (re.compile(r"\bbowler\b|\bhat\b|\bbrim\b", re.I), re.compile(r"brown bowler|black bowler", re.I),
            "whose bowler it is, brown or black"),
    "jacket": (re.compile(r"\bvelvet\b|\bjacket\b", re.I), re.compile(r"bottle-green velvet", re.I),
               "the bottle-green velvet jacket"),
}


def wardrobe(seg: dict) -> list[Finding]:
    """A panel that shows a hand, a hat or Holmes's jacket names the contract.
    The sheet's WARDROBE block states it once; a panel that says "his hand"
    invites the drawer to dress it (a tan glove, 2026-09-11)."""
    text = drawn_text(seg)
    return [Finding("WARDROBE", panel_key(seg), shown.search(text).group(0), False, f"{kind}: name {says}")
            for kind, (shown, named, says) in CONTRACTS.items()
            if shown.search(text) and not named.search(text)]


# ---- PROPS ----------------------------------------------------------------

PROPS = ("stick", "bowler", "glass", "tube", "bodkin", "door", "wheel", "stool", "vessel", "pipette",
         "tray", "basket", "lamp", "hansom", "reins", "trolley", "bottle", "knob", "barrow", "umbrella",
         "broom", "sheet", "slab", "paper", "cork", "apron")
SAME = {"cab": "hansom", "hat": "bowler", "brim": "bowler", "tumbler": "glass", "test-tube": "tube",
        "walking stick": "stick", "burner": "lamp", "flame": "lamp"}


def prop_words(text: str) -> set[str]:
    """The props this text draws, under one name each."""
    low = (text or "").lower()
    for other, canon in SAME.items():
        low = re.sub(rf"\b{re.escape(other)}s?\b", canon, low)
    return {w for w in PROPS if re.search(rf"\b{w}s?\b", low)}


def props(seg: dict) -> list[Finding]:
    """A noun the motion moves that the frame never drew.  The drawer draws the
    frame text alone, so a prop that first appears in `motion` is invented."""
    drawn = prop_words(drawn_text(seg))
    return [Finding("PROPS", panel_key(seg), word, False, "the motion moves it; the frame never drew it")
            for word in sorted(prop_words(seg.get("motion", "")) - drawn)]


# ---- GRID -----------------------------------------------------------------

SAYS = re.compile(r"(\d+) by (\d+) grid of (\d+)")


def grid_findings(segs: list[dict], prompt: str, grid: tuple) -> list[Finding]:
    """The panel count, the grid the packer chose and the sentence on the sheet
    all say one number, or `cell_boxes()` cuts cells nobody asked for."""
    cols, rows = grid[0], grid[1]
    said = SAYS.search(prompt)
    counted = (int(said.group(3)), int(said.group(1)) * int(said.group(2))) if said else (cols * rows, cols * rows)
    if len({cols * rows, len(segs), *counted}) == 1:
        return []
    return [Finding("GRID", "sheet", prompt.splitlines()[1] if said else prompt[:70], True,
                    f"{cols}x{rows} holds {cols * rows} panels, the sheet says {counted[0]}, "
                    f"the packer sent {len(segs)}")]


# ---- the sheet ------------------------------------------------------------

def sheet_findings(segs: list[dict], setup: Setup, prompt: str, grid: tuple) -> list[Finding]:
    """Every check, over every panel of one sheet, in the order they are read."""
    found = affirmative(prompt, segs) + twins(segs) + grid_findings(segs, prompt, grid)
    for seg in segs:
        found += (instant_before(seg) + end_findings(seg) + camera_still(seg) + geometry(seg)
                  + crowd_findings(seg, setup) + wardrobe(seg) + props(seg))
    return found


def verdict(findings: list[Finding]) -> dict:
    """One sheet's answer: a hard finding refuses the draw, a watch prints."""
    hard = [f for f in findings if f.hard]
    return {"passed": not hard, "hard": len(hard), "watch": len(findings) - len(hard),
            "checks": dict(Counter(f.check for f in findings))}


def contract_faults(physicals: dict[str, str]) -> list[dict]:
    """A character contract that the 220-character trim would cut short.

    The episode reads the WHOLE description, but a book whose refs were written
    against the trimmed reader can still carry facts nothing ever sees, and that
    silence is what cost 23 panels their stick (owner, 2026-09-11)."""
    from studio.trailer_refs import contract_description, dropped_by_limit, visual_description
    out = []
    for who, physical in sorted(physicals.items()):
        if dropped_by_limit(physical):
            lost = contract_description(physical)[len(visual_description(physical)):].strip()
            out.append({"check": "CONTRACT", "panel": who,
                        "detail": f"the 220-character trim would drop: {lost[:160]}"})
    return out
