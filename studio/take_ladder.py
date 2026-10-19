"""The take ladder: cure by cause, priced in seconds, under the episode ceiling.

    seed x1 -> move_type x1 -> shorter_take x1 -> head_cut x1 -> replan_cell x1
    terminal: keep_best flagged | still (narration, HARD, cap 2, never adjacent)
              | keep_best flagged high (dialogue, turn, button, a third still)

The cure-to-cause table the skill kept in prose ("When a failure sends you
back"), as code: a moving take that froze wants a seed; a still take that
froze wants another move TYPE; a lag wants a shorter take and never a seed; a
leak is cut off the head for no GPU; a content fault back on a fresh seed
sends the cell to the plan.  Every rung is one batched retake round through
takes_r2v (`--retake=a,b --why=<rung: causes>`), then the machine gates on
those takes, then the judge reads again (judged_gate.clear).  A plan edit
goes through `episode_home.write_plan`, so a refused plan is never written.

Prices: one cold load of the video weights and 3.8 GPU min per take (decision
§2; `episode_clock.TAKE_COLD`), ~12 min for a re-planned cell.  `can_afford`
asks the context's budget for the round's real cost, not the rung's unit.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from studio import audit_rows, episode_home, episode_ref_official as ro, gait, judged_gate, plan_gates, stillness, step_attempts, step_caps, take_leak, warp_gate
from studio.judges import take_eye
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Ladder, Rung

COLD_S, TAKE_S, REPLAN_S = 300.0, 265.0, 720.0
"""TAKE_S re-priced 228 -> 265 (GPU economist, 2026-09-30): measured per-take
cost crept from 204 s (WotW ep05) to 274-281 s (ep12-14) at the same frames;
the old price let can_afford approve rounds that then overran their share."""
SEED = Rung("seed", COLD_S + TAKE_S)
MOVE_TYPE = Rung("move_type", COLD_S + TAKE_S)
SHORTER_TAKE = Rung("shorter_take", COLD_S + TAKE_S)
HEAD_CUT = Rung("head_cut", 0.0)
REPLAN_CELL = Rung("replan_cell", REPLAN_S)
BATCH = Rung("batched_cures", COLD_S + TAKE_S, tries=2)
LADDER = Ladder([BATCH], "keep_best")
"""ONE batched rung (five-expert debate, 2026-09-30; the old F1 rule as code):
the rung-serial ladder spent a round per rung and re-judged between rungs, and
the measured cure rates were seed ~0% solo (3.6 GPU-h), shorter-on-lag 0/15,
replan-content 3/21 -- while move_type ran 89-100% at ~8 min a cure.  Now a
router assigns every faulted take its own cure and the union renders in ONE
round; free cures (a timeline trim for lag, a head cut for leak) cost no round;
input-borne kinds take no render at all.  The older rungs stay defined for
their prices and the tests that name them."""
STILL_MAX = 2
TAKES = Path("takes") / "r2v"
STILLS = "stills.json"
RENDER = "scripts/episode/takes_r2v.py"

FROZEN = frozenset({"frozen-at-start", "frozen-share", "frozen-whole"})
LAG = frozenset({"lag", "lip-sync"})
CONTENT = take_eye.HARD_CONTENT
MOTION = take_eye.GEOMETRY | FROZEN | {"churn"}
"""Faults of the MOVE: cured by another move type from the catalog."""
NEVER_SEED = LAG | {"leak"}
# 'twin' is DELIBERATELY absent here (G-TWIN, 2026-10-05): it falls through
# cure_of to ONE seed retake, then repeated-evidence sends it to the terminal.
# Pinned by test_a_twin_take_routes_to_one_seed_retake.
INPUT_BORNE = frozenset({"content", "clones", "identity", "unread", "lettering", "text",
                         "look", "letterbox"})
"""Kinds that live in the panel, the prompt or the grade: no seed reroll ever
cured one (economist, 2026-09-30 -- content by take render 3/21, by panel
redraw 1/1; look constant across every seed).  They go to the terminal, and
the BOARD owns the cure."""
MOVABLE = (FROZEN | {"held", "pass-through", "last-vs-panel", "last-vs-cell", "drift",
                     "jump", "cut", "cut-vote", "cut-landing", "foreign", "churn", "zoom",
                     "face-at-end", "coherence off-board", "camera-move"})
"""Kinds a changed MOVE cures: measured 89-100% on frozen/held, 67% on
last-vs-panel; even the 'sampling' cures came from the plan edit, not the roll."""


def panel_clean(room: Path, index: int) -> bool:
    """Did this shot's PANEL pass the content check?  Then a content fault on
    its take came from the render, not the panel (ep21 T06, T14: clean panels,
    a second man and a standing man in the takes).  False when unknown."""
    path = Path(room).parents[1] / "storyboard" / "panel_content.json"
    if not path.exists():
        return False
    rows = json.loads(path.read_text(encoding="utf-8"))
    return any(r.get("shot") == index and r.get("passed") for r in rows if isinstance(r, dict))


CURE_RATES_AS_OF = "2026-10-19"
CURE_RATES = {("warp_se", "seed"): (0, 4), ("lag", "shorter_take"): (0, 15),
              ("content", "replan_cell"): (3, 21), ("motion", "move_type"): (9, 10)}
"""(hits, tries) per (fault class, cure), measured: warp_se = a warp over the Se wall alone (Jekyll ep01
T21/T24 reseeds: 0 of 4 drawn after the stale-input retake); lag shorter_take 0/15 and content replan
3/21 (ep13-ep21); move_type 89-100 % on frozen/held (9 of 10 kept as the floor).  Dated: a constant
outlives its world, so the date is read by whoever refits it."""
DEAD_BELOW, DEAD_TRIES = 0.20, 4


def dead(cls: str, cure: str) -> bool:
    """A (class, cure) under 20 % over 4+ tries is dropped for its class."""
    hits, tries = CURE_RATES.get((cls, cure), (0, 0))
    return tries >= DEAD_TRIES and hits / tries < DEAD_BELOW


def warp_scores(fault: Fault) -> tuple[float | None, float | None]:
    """(S, Se) of a warp fault: S is the row's value, Se is read from its note."""
    se = re.search(r"\bSe (-?[\d.]+)", fault.note or "")
    s = fault.evidence.get("value")
    return (None if s is None else float(s)), (float(se.group(1)) if se else None)


def warp_f2(taken: int) -> str:
    """warp_gate's cure for a failing take (K6: today's two-argument form is the shim)."""
    try:
        return warp_gate.cure("fail", taken, None)
    except TypeError:
        return warp_gate.cure("fail", taken)


def warp_cure(faults: list[Fault], taken: int) -> str:
    """'seed' for a warp over the S wall not yet retaken; '' for an Se-only warp (its seed is dead) and
    for what warp_gate sends to F2 (refine is not a take render)."""
    own = [f for f in faults if f.kind == "warp"]
    s, _se = warp_scores(own[0])
    if s is not None and s <= warp_gate.FAIL_S and dead("warp_se", "seed"):
        return ""
    if all(f.evidence.get("repeated") for f in own):
        return ""
    return "seed" if warp_f2(taken) == "seed" else ""


def gait_cure(faults: list[Fault]) -> str:
    """'gait_verb' for a measured shuffle; '' for one not measured (feet out of frame: advisory) or
    one whose identical signature already came back."""
    own = [f for f in faults if f.kind == "gait"]
    if any("not measured" in f.note or "unmeasured" in f.note for f in own):
        return ""
    return "" if all(f.evidence.get("repeated") for f in own) else "gait_verb"


EARLY_S = 0.3


def early_clones(faults: list[Fault]) -> bool:
    """Every clone row lies in the first 0.3 s: the second face is the opening frames, a head cut."""
    times = [f.evidence.get("t") for f in faults if f.kind == "clones"]
    return bool(times) and all(t is not None and float(t) <= EARLY_S for t in times)


def cure_of(faults: list[Fault], panel_clean: bool = False, taken: int = 0) -> str:
    """One cure for one take, from what its faults measure as curable.
    '' means no render buys anything: the terminal answers.  A content fault
    on a take whose panel passed content is render-borne: one seed."""
    kinds = {f.kind for f in faults}
    if kinds == {"clones"} and early_clones(faults):
        return "head_cut"                         # free: heads.json, tried before any render
    if panel_clean and kinds <= {"content", "clones"}:
        kinds = kinds - {"content", "clones"} | {"render-content"}
    if kinds & MOVABLE:
        return "move_type"
    if kinds & LAG:
        return "timeline_trim"                    # free: lag follows placed length
    if "leak" in kinds and kinds - {"leak"} <= INPUT_BORNE and any(
            f.evidence.get("covers") for f in faults if f.kind == "leak"):
        return "head_cut"                         # free: heads.json
    if "gait" in kinds:
        return gait_cure(faults)
    if "warp" in kinds:
        return warp_cure(faults, taken)
    if kinds <= INPUT_BORNE or kinds & NEVER_SEED:
        return ""                                 # an uncovered leak has no render cure
    if all(f.evidence.get("repeated") for f in faults):
        return ""                                 # a fresh seed already reproduced it
    return "seed"


def route(verdict: Verdict, room: Path, try_i: int = 1) -> dict[str, dict[int, list[Fault]]]:
    """cure -> {take index -> its faults}, capped and (on the second try)
    limited to takes whose fault signature progressed."""
    by: dict[int, list[Fault]] = {}
    for f in verdict.faults:
        by.setdefault(index_of(f.where), []).append(f)
    out: dict[str, dict[int, list[Fault]]] = {}
    for i, fs in sorted(by.items()):
        if attempts_of(room, i) >= MAX_TAKE_ATTEMPTS:
            continue
        kinds = {f.kind for f in fs}
        if try_i >= 2 and not progressed(room, i, sorted(kinds)) and not kinds <= FROZEN:
            continue        # a frozen take gets its second move type: G-DEAD never ships it (2026-10-14)
        if cure := cure_of(fs, panel_clean=panel_clean(room, i), taken=attempts_of(room, i)):
            out.setdefault(cure, {})[i] = fs
        if cure != "head_cut" and any(f.kind == "leak" and f.evidence.get("covers") for f in fs):
            # FREE and independent of the render cure: ep24 T02 shipped at 0 with
            # 8 frames of plate the move cure re-rendered and never cut
            out.setdefault("head_cut", {})[i] = [f for f in fs if f.kind == "leak"]
    return out


def renders_of(routed: dict[str, dict[int, list[Fault]]]) -> list[int]:
    """The takes a batched round actually re-renders."""
    return sorted({i for cure in ("move_type", "seed", "gait_verb") for i in routed.get(cure, {})})


def signatures(verdict: Verdict) -> dict[str, list[str]]:
    by: dict[int, set[str]] = {}
    for f in verdict.faults:
        by.setdefault(index_of(f.where), set()).add(f.kind)
    return {str(i): sorted(kinds) for i, kinds in by.items()}


def progressed(room: Path, index: int, kinds_now: list[str]) -> bool:
    """A second cure only when the fault CHANGED kind (re-routed) or shrank;
    an identical signature after its own cure is structural -- the judge or
    the input, never the seed -- and goes to the terminal (the calibrator's
    circuit-breaker, 2026-09-30)."""
    path = Path(room) / LADDER_FILE
    if not path.exists():
        return True
    rounds = json.loads(path.read_text(encoding="utf-8")).get("rounds", [])
    prev = next((r["faults"].get(str(index)) for r in reversed(rounds) if str(index) in r.get("faults", {})), None)
    return prev is None or set(kinds_now) != set(prev) or len(kinds_now) < len(prev)

CAUSE_OF = {
    "frozen-at-start": "frozen", "frozen-share": "frozen", "frozen-whole": "frozen",
    "pass-through": "anchored", "held": "anchored",
    "rotation": "rotation", "zoom": "overrun", "face-at-end": "overrun", "camera-move": "overrun",
    "coherence off-board": "board", "last-vs-cell": "board", "last-vs-panel": "board", "drift": "board",
    "churn": "board", "jump": "cut", "cut-vote": "cut", "cut": "cut", "cut-landing": "cut", "foreign": "cut",
}
SUBSTITUTE = {
    # a still take that froze: give the camera the move; a moving one: follow the actor
    "frozen": {"locked": "push_slow", "follow": "push_slow", "*": "follow"},
    # a truck on a person leaning on scenery glues him to camera and slides the world: push in or crane
    "anchored": {"track_lateral": "push_slow", "follow": "push_slow", "pan_to": "push_slow", "*": "crane_up"},
    "rotation": {"*": "locked"},
    # a push has no brake on a close
    "overrun": {"*": "locked"},
    # the moves the catalog measured as drifting off their board
    "board": {"pan_to": "locked", "tilt_down": "pull_reveal", "crane_down": "follow", "rack_focus": "locked",
              "*": "locked"},
    # a hard cut early: change the move TYPE, not its amount
    "cut": {"*": "locked"},
}
PHRASING = {
    "locked": "The camera holds a locked-off frame",
    "push_slow": "The camera pushes in toward {aim}",
    "pull_reveal": "The camera pulls back from {aim}, widening to show the place around it",
    "pan_to": "The camera pans across to {aim}",
    "tilt_up": "The camera tilts up from the ground to {aim}",
    "track_lateral": "The camera tracks sideways to the right, past {aim}",
    "follow": "The camera tracks beside {aim}",
    "crane_up": "The camera rises above {aim}, looking down over the place",
}
"""docs/calibration/camera_catalog.md, affirmative and direction only; no pace word."""
AIM = re.compile(r"\b(?:toward|towards|onto|on|at|to|from|past|beside|behind|above|around|along|over)\s+(.+)$", re.I)


# ---- the cure-to-cause table --------------------------------------------------

def still_take(motion: str) -> bool:
    return plan_gates.move_id(motion or "", "") == "locked"


def wants(fault: Fault, rung: str, motion: str = "") -> bool:
    """Whether this fault's cause is what this rung cures."""
    kind, ev = fault.kind, fault.evidence
    if rung == "seed":
        return kind not in NEVER_SEED and not ev.get("repeated") and not (kind in FROZEN and still_take(motion))
    if rung == "move_type":
        return kind in MOTION
    if rung == "shorter_take":
        return kind in LAG
    if rung == "head_cut":
        return kind == "leak" and bool(ev.get("covers"))
    if rung == "replan_cell":
        return kind in CONTENT and bool(ev.get("repeated"))
    return False


def index_of(where: str) -> int:
    return int(where[1:3])


def takes_for(verdict: Verdict, rung: str, motion_of) -> dict[int, list[Fault]]:
    """Take index -> the faults this rung answers on it."""
    out: dict[int, list[Fault]] = {}
    for f in verdict.faults:
        i = index_of(f.where)
        if wants(f, rung, motion_of(i)):
            out.setdefault(i, []).append(f)
    return out


def why_of(rung: str, faults: list[Fault]) -> str:
    return f"{rung}: " + ", ".join(sorted({f.kind for f in faults}))


def retake_args(indices: list[int], why: str) -> list[str]:
    """`--retake=a,b --why=<reason>`; a round of one declares itself `--last`
    (takes_r2v.retake_refusal): the ladder's round for a rung IS that cause's
    last round."""
    args = [f"--retake={','.join(str(i) for i in sorted(indices))}", f"--why={why}"]
    return args + ["--last"] if len(indices) == 1 else args


# ---- price ----------------------------------------------------------------------

def cost(rung: Rung, takes: int) -> float:
    """Seconds one round of this rung costs for `takes` retakes: one cold
    load, then the per-take slope; a re-planned cell is priced per cell."""
    if rung.cost_seconds == 0 or takes == 0:
        return 0.0
    if rung.name == REPLAN_CELL.name:
        return REPLAN_S * takes
    return COLD_S + (rung.cost_seconds - COLD_S) * takes


def can_afford(ctx, rung: Rung, takes: int) -> bool:
    """The step's share, else the ladders' pool (judged_gate drew the rung's
    price from it); a round neither can pay DEFERS -- it was skipped in silence
    on ep13, and shorter_take never reached T11's +1.08 s lag.  A SPENT
    CEILING is terminal instead (five-hour plan fix 1): with the episode-wide
    clock nothing ever pays again, so the best takes ship flagged."""
    price, step = cost(rung, takes), judged_gate.step_of(ctx)
    if ctx.budget.can_afford(step, price) or ctx.budget.pool_left() >= price:
        return True
    # THE DEFERRAL IS GONE (ep16, 2026-10-01): with the share and the pool
    # empty it said "run again to resume", and idling clocks nothing, so every
    # resume met the same state -- an unresolvable deferral spinning the
    # drive.  Shares are an allocation of the ceiling: remaining episode
    # headroom pays what they cannot, and true exhaustion is terminal.
    return ctx.budget.headroom() >= price


# ---- plan edits, through write_plan ----------------------------------------------

def shot_doc(doc: dict, index: int) -> dict:
    return next(s for s in doc["shots"] if s["index"] == index)


def aim_of(motion: str, at_rest: str = "") -> str:
    """What the substitute move points at: the old camera clause's own aim,
    else the first clause of `at_rest`, else the figure."""
    from studio import camera_lint                 # never cut mid-name (Jekyll ep01 "the man about")
    cam, _ = ro.camera_clause(plan_gates.head_of(motion))
    if (found := AIM.search(cam or "")) and not BARE_TITLE.match(found.group(1).strip(" ,.")):
        aim = destination(camera_lint.OLD_TAIL.sub("", found.group(1)).strip(" ,."))
        aim = camera_lint.repair_aim(" ".join(aim.split()[:AIM_WORDS])).strip(" ,.")
        if aim and not POSSESSIVE_END.search(aim):     # "to the door's" names nothing: read at_rest
            return aim
        if not at_rest:
            return aim or "the figure"
    # at_rest clauses are SEMICOLON-separated (ep16: a comma split made the
    # whole paragraph the aim and the motion lint refused the cure, M9); the
    # FOCUS tag and the subject's parenthetical are not the aim (ep19: five
    # shots were sent "pushes in toward THE FOCUS OF THE PICTURE IS")
    first = AIM_STOP.split(FOCUS_TAG.sub("", at_rest or "", count=1))[0].strip(" .")
    if (owner := POSSESSOR.match(first)) and not NOUN_AFTER.search(first[owner.end():]):
        first = owner.group(1)          # "Mr. Enfield's frank" (cut at "frank, lively face") aims at him
    return camera_lint.repair_aim(" ".join(first.split()[:AIM_WORDS])) or "the figure"


POSSESSOR = re.compile(r"^(.+?)['’]s\b")
NOUN_AFTER = re.compile(r"\b(?:face|head|hand|hands|eyes|back|shoulder|hat|door|lock|step|steps|window|lamp|cane)\b",
                        re.I)
"""A possessive whose clause still names its thing keeps it ("the lawyer's hand"); one cut off by
its adjectives' comma keeps only its owner (Jekyll ep01 v2 T19, 2026-10-15)."""


TO = re.compile(r"\b(?:to|toward|towards|onto)\s+", re.I)


def destination(aim: str) -> str:
    """Where a from-to move ENDS: the text after its last `to`/`toward`, cut at its first
    comma (Jekyll ep01 v2: "the lawyer across to the door's lock" became "... to the door's")."""
    parts = TO.split(aim or "")
    return (parts[-1] if len(parts) > 1 and parts[-1].strip() else aim).split(",")[0].strip(" .")


POSSESSIVE_END = re.compile(r"['’]s?$")


FOCUS_TAG = re.compile(r"^\s*THE FOCUS OF THE PICTURE IS\s+", re.I)
AIM_STOP = re.compile(r"[;,(]|(?<!\bMr)(?<!\bMrs)(?<!\bDr)(?<!\bSt)\.")
"""Where an at_rest aim ends: a clause mark or a full stop, never the period of a title
(Jekyll ep01 shot 1: "The camera pans across to Mr")."""
BARE_TITLE = re.compile(r"^(?:Mr|Mrs|Dr|St|Miss|Sir)\.?$", re.I)
"""A camera aim that is only a title was cut on its period: read the aim from at_rest."""


AIM_WORDS = 6
"""A substitute move aims at one short noun phrase, never a sentence."""


ACTOR_VERB = "the speaker leans toward the listener and lifts one hand as the words come"
"""What a frozen DIALOGUE take is given instead of a push: the actor's verb
(Jekyll ep01, 2026-10-13: the ladder pushed in on every frozen exchange)."""


def substitute_id(kind: str, motion: str, dialogue: bool = False) -> str:
    """The catalog move that replaces this one for this cause, never the same
    move back; a spoken line's camera stays locked -- it never travels."""
    if dialogue:      # locked with the actor's verb first; frozen again, a pan (not a travel)
        return "pan_to" if ACTOR_VERB in (motion or "") else "locked"
    table = SUBSTITUTE[CAUSE_OF[kind]]
    move = plan_gates.move_id(motion or "", "")
    new = table.get(move, table["*"])
    if new != move:
        return new
    return "locked" if move != "locked" else "push_slow"


def substitute(kind: str, motion: str, at_rest: str = "", dialogue: bool = False) -> str:
    """The motion with its camera head swapped; the subject's own clauses stay.
    A frozen dialogue take keeps a locked head and gains the actor's verb."""
    head, *rest = [c.strip() for c in (motion or "").split(";")]
    _cam, subject = ro.camera_clause(head)
    new = PHRASING[substitute_id(kind, motion, dialogue)].format(aim=aim_of(motion, at_rest))
    verb = [ACTOR_VERB] if dialogue and ACTOR_VERB not in (motion or "") else []
    return "; ".join([new] + ([subject] if subject else []) + verb + [c for c in rest if c])


def move_type(doc: dict, index: int, faults: list[Fault]) -> dict:
    shot = shot_doc(doc, index)
    kind = next((f.kind for f in faults if f.kind in CAUSE_OF), None)
    if kind is None:       # nothing a move answers (ep14 T20: letterbox, content) -- the terminal will
        return doc
    if doc.get("grammar") and CAUSE_OF[kind] == "frozen" and stillness.locked(shot["motion"]):
        return doc     # a locked grammar shot is never pushed (G-PUSH; owner 2026-10-18): a seed answers it
    spoken = any(l.get("kind") == "dialogue" and l.get("shot") == index for l in doc.get("lines") or [])
    shot["motion"] = substitute(kind, shot["motion"], shot.get("at_rest", ""), dialogue=spoken)
    return doc


def gait_edit(doc: dict, index: int) -> dict:
    """The shot's pace phrase becomes the plan's verb; the camera head stays (studio.gait.gait_verb)."""
    shot = shot_doc(doc, index)
    shot["motion"] = gait.gait_verb(shot["motion"])
    return doc


def plan_cure(doc: dict, index: int, faults: list[Fault]) -> dict:
    """The plan edit of an early or batched render cure: the plan's verb for a gait take, else its move."""
    if any(f.kind == "gait" for f in faults) and not any(f.kind in CAUSE_OF for f in faults):
        return gait_edit(doc, index)
    return move_type(doc, index, faults)


def built_for(record: dict) -> float:
    """The length a take was BUILT FOR: its record's placed seconds.  The file
    is frames_for(placed + HANDLE) long, so its measured seconds always exceed
    the placed ones and read as "the length changed" (ep01 v2 T14: 5.04 placed,
    5.88 rendered; four reseeds where the mux-lag cure was a shorter take)."""
    return float(record.get("placed_seconds") or record.get("measured_seconds") or 0.0)


def shorten(doc: dict, index: int, placed_s: float, rendered_s: float) -> tuple[dict, str]:
    """('restore', doc untouched) when the take's length was just changed
    under it -- re-render at the placed length first; ('shorten', doc) with
    the shot's beat and coda halved so the line fills more of the take;
    ('', doc) when there is nothing left to cut."""
    if abs(placed_s - rendered_s) > 0.05:
        return doc, "restore"
    shot = shot_doc(doc, index)
    beat, coda = float(shot.get("beat_s", 0.0)), float(shot.get("coda_s", 0.0))
    if not beat and not coda:
        return doc, ""
    shot["beat_s"], shot["coda_s"] = round(beat / 2, 2), round(coda / 2, 2)
    return doc, "shorten"


def replan(doc: dict, index: int, faults: list[Fault]) -> dict:
    """Re-aim the cell at what it holds: the camera locked on the subject's
    own verbs (the sharpest carrier, no invented reframe) and the sentence
    naming an unasked subject dropped.  Cell fields only; never a timing input."""
    shot = shot_doc(doc, index)
    head, *rest = [c.strip() for c in (shot["motion"] or "").split(";")]
    _cam, subject = ro.camera_clause(head)
    shot["motion"] = "; ".join([PHRASING["locked"]] + ([subject] if subject else []) + [c for c in rest if c])
    for f in faults:
        if found := re.search(r"^(?:banned from this book|unasked): (.+)$", f.note or ""):
            shot["frame"] = without(shot["frame"], found.group(1).split(",")[0].strip())
    return doc


def without(prose: str, noun: str) -> str:
    """The prose less the sentence that names `noun`; the whole prose when every sentence does."""
    kept = [s for s in re.split(r"(?<=[.!?])\s+", prose.strip()) if noun.lower() not in s.lower()]
    return " ".join(kept) if kept else prose


# ---- stills.json: which shots the cut holds as a panel ---------------------------

def stills_path(home: Path) -> Path:
    return Path(home) / TAKES / STILLS


def load_stills(home: Path) -> dict[int, dict]:
    path = stills_path(home)
    if not path.exists():
        return {}
    return {int(k): v for k, v in json.loads(path.read_text(encoding="utf-8")).items()}


def live_stills(home: Path) -> dict[int, dict]:
    """The stills the CUT holds: a take rendered again after its still was
    decided retires the still (ep12 T19).  assemble and qc both read this --
    ep16: qc read stills.json raw and failed two shots the cut had taken."""
    from studio import dead_footage
    path = stills_path(home)
    room = path.parent
    return {k: v for k, v in load_stills(home).items()
            if float(v.get("seconds") or 0.0) <= dead_footage.STILL_LIMIT_S      # G-DEAD would refuse it
            and not ((room / f"T{k:02d}.mp4").exists()
                    and (room / f"T{k:02d}.mp4").stat().st_mtime
                    > v.get("decided", path.stat().st_mtime))}


def neighbours(index: int, order: list[int]) -> set[int]:
    """The takes either side in CUT order (the numbering has holes)."""
    order = sorted(order)
    k = order.index(index)
    return {order[j] for j in (k - 1, k + 1) if 0 <= j < len(order)}


def can_still(index: int, stills: dict, order: list[int], cap: int = STILL_MAX) -> bool:
    return len(stills) < cap and not (neighbours(index, order) & set(stills))


def write_still(home: Path, index: int, panel: Path, seconds: float, why: str) -> Path:
    """One more still, keyed by take index, the panel book-relative."""
    stills = {str(k): v for k, v in load_stills(home).items()}
    book = Path(home).parents[1]
    stills[str(index)] = {"panel": episode_home.relative(book, panel), "seconds": seconds, "why": why,
                          "decided": time.time()}
    return episode_home.write_json(stills_path(home), stills)


# ---- the terminal rung ------------------------------------------------------------

def shot_kind(plan, index: int) -> str:
    """dialogue | turn | button | narration, for the take's first shot."""
    if any(line.kind == "dialogue" and line.shot == index for line in plan.lines):
        return "dialogue"
    if plan.turn().index == index:
        return "turn"
    if plan.button().shot == index:
        return "button"
    return "narration"


def hard(fault: Fault) -> bool:
    return fault.severity != "low" and (fault.kind in take_eye.HARD_CONTENT or fault.kind in take_eye.GEOMETRY)


def placed_seconds(home: Path, index: int) -> float:
    doc = episode_home.read_timeline(home)
    return float(next((s["seconds"] for s in doc.get("shots", []) if s["index"] == index), 0.0))


def still_for(home: Path, index: int, faults: list[Fault]) -> Path | None:
    """The passed panel this take would be held on, when one exists -- never a
    refs-only shot's seamed panel (owner ruling 2026-10-11)."""
    from studio import refs_only
    panel = Path(home) / "storyboard" / f"shot_{index:02d}.png"
    if index in refs_only.read(home):
        return None
    return panel if panel.exists() and any(hard(f) for f in faults) else None


def settle_take(home: Path, plan, index: int, faults: list[Fault], order: list[int], cap: int) -> str:
    """One take's terminal: `still` (and its row written), `high` or `keep_best`."""
    if shot_kind(plan, index) != "narration":
        return "high"
    panel = still_for(home, index, faults)
    # A HELD PANEL IS NEVER WORSE THAN BLACK BARS: ep14 T20 (2026-09-29) came back
    # letterboxed on every seed, the two stills were spent, and keep_best kept the bars.
    boxed = any(f.kind == "letterbox" for f in faults)
    if panel is None or not (boxed or can_still(index, load_stills(home), order, cap)):
        return "high" if panel is not None else "keep_best"
    seconds = placed_seconds(home, index)
    from studio import dead_footage
    if seconds > dead_footage.STILL_LIMIT_S:        # G-DEAD refuses a still held this long (ep01 v2 T10, T16)
        return "high"
    write_still(home, index, panel, seconds, why_of("still", faults))
    return "still"


def terminal(home: Path, plan, verdict: Verdict, order: list[int], cap: int = STILL_MAX) -> Verdict:
    """The terminal rung over every take still faulted: a still from the
    passed panel on a narration shot with a HARD fault (cap, never
    adjacent); keep_best flagged high on a dialogue, turn or button shot or
    a third still; keep_best flagged otherwise.  Never a park, never a drop.
    Every fault carries evidence['settled'] = still | keep_best | high (K5)."""
    by: dict[int, list[Fault]] = {}
    for f in verdict.faults:
        by.setdefault(index_of(f.where), []).append(f)
    faults, stilled = [], False
    for index, own in sorted(by.items()):
        outcome = settle_take(home, plan, index, own, order, cap)
        stilled = stilled or outcome == "still"
        panel = f"storyboard/shot_{index:02d}.png" if outcome == "still" else ""
        faults += [f.model_copy(update={"severity": "high" if outcome == "high" else f.severity,
                                        "evidence": {**f.evidence, "settled": outcome,
                                                     **({"still": panel} if panel else {})}})
                   for f in own]
    return verdict.model_copy(update={"faults": faults, "terminal": "still" if stilled else "keep_best"})


def dropped_class(fault: Fault) -> str:
    """The cure class the ladder dropped for this fault: an Se-only warp (its seed is dead) or a kind
    the board owns; '' for a fault with a live cure."""
    if fault.kind == "warp":
        s, _se = warp_scores(fault)
        return "warp_se" if s is not None and s <= warp_gate.FAIL_S and dead("warp_se", "seed") else ""
    return fault.kind if fault.kind in INPUT_BORNE else ""


def scores_of(fault: Fault) -> dict:
    if fault.kind == "warp":
        s, se = warp_scores(fault)
        return {"S": s, "Se": se}
    return {"value": fault.evidence.get("value")}


def watch_rows(faults: list[Fault]) -> list[dict]:
    """(take, class, scores) for every kept fault whose cure class was dropped: the owner's watch list."""
    rows = [{"take": f.where, "class": dropped_class(f), "scores": scores_of(f)} for f in faults]
    return [r for r in rows if r["class"]]


def name_watch_list(ctx, verdict: Verdict) -> None:
    """One audit row of the watch list; none when no take was kept with a dropped class."""
    if rows := watch_rows(verdict.faults):
        audit_rows.append(ctx.book_dir, {"unit": ctx.unit, "gate": GATE, "judge": verdict.signer, "terminal": "watch",
                                         "faults": [{"kind": "watch", **r} for r in rows]})


def swap_in(room: Path, index: int, best: Path, scored: dict) -> str:
    """The best draw becomes T<nn>.mp4; the last draw is archived beside the others, nothing lost."""
    current = Path(room) / f"T{index:02d}.mp4"
    n = 1
    while (archive := Path(room) / "attempts" / f"T{index:02d}_fail{n}.mp4").exists():
        n += 1
    last, won = scored[current], scored[best]
    current.replace(archive)
    best.replace(current)
    if dq := won.get("dq"):
        current.with_suffix(".dq.json").write_text(json.dumps(dq, indent=1), encoding="utf-8")
    return (f"BEST DRAW T{index:02d}: restored (hard {won['hard']}, Se {won.get('Se')}) over the last draw "
            f"(hard {last['hard']}, Se {last.get('Se')}); the last draw is {archive.name}")


def best_draw(room: Path, index: int, runner) -> str:
    """The draw with the fewest hard rows, then the lowest Se, restored to T<nn>.mp4; a tie keeps the
    current take.  `runner(path)` measures one draw: {'hard': n, 'Se': x, 'dq': optional record}."""
    current = Path(room) / f"T{index:02d}.mp4"
    draws = sorted((Path(room) / "attempts").glob(f"T{index:02d}_fail*.mp4"))
    if not draws:
        return ""
    scored = {p: runner(p) for p in [current, *draws]}
    inf = float("inf")
    best = min(scored, key=lambda p: (scored[p]["hard"], inf if scored[p].get("Se") is None else scored[p]["Se"],
                                      p != current))
    return "" if best == current else swap_in(room, index, best, scored)


def keep_best_draws(ctx, verdict: Verdict, runner) -> None:
    """Each faulted take keeps its best measured draw, said and logged."""
    for index in sorted({index_of(f.where) for f in verdict.faults}):
        if line := best_draw(Path(ctx.home) / TAKES, index, runner):
            print(line, flush=True)
            ctx.log(line, level="WARNING")


def terminal_for(ctx, plan, draws=None):
    """The `terminal` callable judged_gate.clear takes, over this episode.  `draws` is the injected
    per-draw dq+warp runner (no GPU here); without it the last draw stands."""
    def end(verdict: Verdict) -> Verdict:
        if draws:
            keep_best_draws(ctx, verdict, draws)
        order = [take_eye.index_of(t) for t in sorted((ctx.home / TAKES).glob("T??.mp4"))]
        settled = terminal(ctx.home, plan, verdict, order)
        name_watch_list(ctx, settled)
        return settled
    return end


# ---- the rungs, as one retake round each ----------------------------------------------

def edit_plan(ctx, rung: Rung, wanted: dict[int, list[Fault]], records: dict[int, dict]) -> str:
    """Apply the rung's plan edit for every take it answers, through write_plan;
    the action taken ('' when the rung edits nothing)."""
    path = Path(ctx.home) / "plan.json"
    doc, action = json.loads(path.read_text(encoding="utf-8")), ""
    for index, faults in wanted.items():
        if rung.name == MOVE_TYPE.name:
            doc, action = move_type(doc, index, faults), "move_type"
        elif rung.name == SHORTER_TAKE.name:
            doc, action = shorten(doc, index, placed_seconds(ctx.home, index),
                                  built_for(records.get(index, {})))
        elif rung.name == REPLAN_CELL.name:
            doc, action = replan(doc, index, faults), "replan_cell"
    if action and action != "restore":
        episode_home.write_plan(path, doc)
    return action


ROUNDS_CAP = step_caps.rounds("retakes")
"""Batched retake rounds an episode may take, ACROSS RESUMES -- the cap table's (stages.yaml
`episode.caps.retakes`, owner 2026-10-18; judged_gate also counts the EYE_TAKES rungs in
attempts.json, so a relaunch or a cure reads the same count).  Five-expert
debate 2026-09-30: with every cure batched into ONE round (the old F1 rule as
code), two rounds cover a first cure and one re-route; ep14 spent 14 rounds
and rounds 3-14 all ended with the identical terminal verdict.  A fault still
alive after two batched rounds is structural -- the judge or the input -- and
belongs to the terminal, not to another render."""
MAX_TAKE_ATTEMPTS = 3
"""Archived attempts after which a take is never retaken again (ep14: T19 x8,
T05 x7 -- lettering and clones live in the panel, not the seed)."""
LADDER_FILE = "ladder.json"


def rounds_of(room: Path, since: float = 0.0) -> int:
    """Rounds this episode has taken, read off the room (a resume reads the
    same file); with `since`, only the rounds taken after that epoch -- the
    owner's retry stamps the clock and the rounds before it are an earlier
    attempt's (2026-10-07: 'use the five-hour limit')."""
    path = Path(room) / LADDER_FILE
    if not path.exists():
        return 0
    rounds = json.loads(path.read_text(encoding="utf-8")).get("rounds", [])
    return sum(1 for r in rounds if float(r.get("at") or 0.0) >= since)


def count_round(room: Path, why: str, sigs: dict[str, list[str]] | None = None) -> None:
    """One round in the room's book, with each take's fault signature when
    given: `progressed` reads them back to break a circling cure."""
    import time
    path = Path(room) / LADDER_FILE
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    doc.setdefault("rounds", []).append({"why": why, "at": round(time.time(), 1)}
                                        | ({"faults": sigs} if sigs else {}))
    path.write_text(json.dumps(doc, indent=1), encoding="utf-8")


def attempts_of(room: Path, index: int) -> int:
    return len(list((Path(room) / "attempts").glob(f"T{index:02d}_fail*.mp4")))


def under_cap(room: Path, wanted: dict[int, list[Fault]]) -> dict[int, list[Fault]]:
    """The takes still allowed a retake."""
    return {i: fs for i, fs in wanted.items() if attempts_of(room, i) < MAX_TAKE_ATTEMPTS}


GATE = "EYE_TAKES"
RETAKES = "retakes"
"""The cap-table row (and attempts.json key) of the episode's retake rounds."""


def episode_spent(home: Path) -> bool:
    """The EPISODE's retake rounds or wall are used up -- read from attempts.json, so a retry's
    `since`, a relaunch, a second drive run and a master-eye redo all read the same count."""
    return step_attempts.spent(Path(home), step_caps.cap(RETAKES))


def cap_line(home: Path, advisories: int) -> str:
    """`CAP retakes: r/N rounds, mm:ss, kept best (k advisories)`."""
    return step_caps.cap_line(RETAKES, step_attempts.count(home, RETAKES), step_caps.rounds(RETAKES),
                              step_attempts.seconds(home, RETAKES), advisories)


def refuse_spent(ctx, advisories: int) -> bool:
    """At the episode's cap the takes stand: the CAP line is said and no batch renders."""
    if not episode_spent(ctx.home):
        return False
    line = cap_line(Path(ctx.home), advisories)
    print(line, flush=True)
    if hasattr(ctx, "log"):
        ctx.log(line, level="WARNING")
    return True


def still_curable(room: Path, verdict: Verdict, since: float = 0.0, home: Path | None = None) -> bool:
    """May the climb take another round?  Not past the cap (rounds since the
    clock reset), and only while the router still has a cure to assign:
    capped takes, unprogressed signatures and input-borne kinds all route to
    nothing, and the terminal (a still or the best take, flagged) answers
    those, not another render."""
    if rounds_of(room, since) >= ROUNDS_CAP or (home is not None and episode_spent(home)):
        return False
    return bool(route(verdict, room, try_i=rounds_of(room, since) + 1))


def head_cuts(ctx, wanted: dict[int, list[Fault]]) -> list[int]:
    """The leak measured is the head cut: heads.json through take_leak.write_head, no GPU.
    The takes whose head was written (a cut that covers the shot); a dialogue take is never cut."""
    spoken, written = dialogue_shots(ctx.home), []
    for index in wanted:
        if index in spoken:
            continue        # its wav is anchored in the take's first frames (ep24 T02)
        dq = take_eye.read_json(ctx.home / TAKES / f"T{index:02d}.dq.json") or {}
        if take_leak.write_head(ctx.home, index, (dq.get("measures") or {}).get("leak")):
            written.append(index)
    return written


def uncut_clones(routed: dict, written: list[int]) -> dict[int, list[Fault]]:
    """Clone takes routed to a head cut that no covering head could be written for: they fall back to
    the one seed a clean panel is owed."""
    return {i: fs for i, fs in routed.get("head_cut", {}).items()
            if i not in written and all(f.kind == "clones" for f in fs)}


def dialogue_shots(home: Path) -> set[int]:
    """Shots that carry a dialogue line: their heads are never cut."""
    path = Path(home) / "plan.json"
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return {l["shot"] for l in doc.get("lines") or [] if l.get("kind") == "dialogue"}


def clear_heads(home: Path, indices: list[int]) -> None:
    """A re-rendered take's old head goes: it was measured on other bytes."""
    path = Path(home) / "heads.json"
    if not path.exists():
        return
    heads = json.loads(path.read_text(encoding="utf-8"))
    kept = {k: v for k, v in heads.items() if int(k) not in set(indices)}
    if kept != heads:
        path.write_text(json.dumps(kept, indent=2), encoding="utf-8")


def measured(ctx, script: str, clock: str, suffix: str, *extra: str) -> None:
    """Run a take checker; a checker that FOUND faults hands them to the judge.

    ep12: a checker exits 1 when a take fails; run_script made that a refusal,
    so the judge (step 09) and this ladder's own re-check died on the fault
    they exist to handle.  Exit 1 is also a crash, so it passes only when
    every kept take has its verdict file on disk."""
    import time
    started = time.time()
    try:
        ctx.run_script(script, *extra, gpu=True, clock=clock)
    except SystemExit as refused:
        takes = sorted((ctx.home / TAKES).glob("T??.mp4"))
        verdicts = [t.with_suffix(suffix) for t in takes]
        missing = [v.name for v in verdicts if not v.exists()]
        # a leftover verdict from an earlier run is not proof this one finished
        # one second of slack: a file written in the same instant can carry a
        # timestamp a few ms before time.time() (flaky in the full suite)
        fresh = any(v.exists() and v.stat().st_mtime >= started - 1.0 for v in verdicts)
        if not str(refused).endswith("exit 1") or missing or not takes or not fresh:
            raise
        ctx.log(f"{script}: faults found; the take judge reads them")


def round_takes(room: Path, indices: list[int]) -> list[int]:
    """What the round named AND every take the render left unjudged (ep21
    16:20Z: a retake of T01 also re-rendered a stale T02, and T02 reached QC
    unjudged)."""
    from studio import judged
    left = {int(n[1:]) for n in judged.unjudged_takes(room) if re.fullmatch(r"T\d+", n)}
    return sorted(set(indices) | left)


def retake(ctx, indices: list[int], why: str, flag: str, trims: list[int] | None = None) -> None:
    """One batched round: the renders back to back on the GPU, each retake's
    CPU check beside them as it lands (decision 2026-10-14-gpu-never-waits-
    for-checks), then ONE GPU window.  The checks run --cpu-only: a ComfyUI job
    between the renders would evict the H3 stack (owner, 2026-09-30: "first run
    all model executions once"); the heads go at launch, before any re-measure."""
    from studio import take_overlap
    take_overlap.shoot(ctx, ["--from-refs", "--no-ends", flag], retake=(list(indices), why), attempts=True)
    every = round_takes(Path(ctx.home) / TAKES, indices)
    if late := [str(i) for i in take_overlap.unmeasured(Path(ctx.home) / TAKES, every)]:
        measured(ctx, "scripts/episode/take_dq.py", "take_dq", ".dq.json", *late, "--attempts")
    if trims:
        # no --attempts: a trim renders nothing, so there is nothing to archive
        measured(ctx, "scripts/episode/take_dq.py", "take_dq", ".dq.json",
                 *[str(i) for i in sorted(trims)])
    measured(ctx, "scripts/episode/take_content_check.py", "take_content", ".content.json",
             *[str(i) for i in every])


def wall() -> float:
    return time.time()


def renderable(routed: dict, room: Path, written: list[int]) -> dict[int, list[Fault]]:
    """Every take this round would render: its move, seed or gait cure, and the early clones no head
    could be cut for (one seed, on a panel that passed content)."""
    out = {**routed.get("move_type", {}), **routed.get("seed", {}), **routed.get("gait_verb", {})}
    return out | {i: fs for i, fs in uncut_clones(routed, written).items() if panel_clean(room, i)}


def trimmed(ctx, routed: dict, renders: dict, records: dict) -> tuple[dict, list[int]]:
    """The plan doc with the lag takes' timeline trims applied (free); a take whose length changed under
    it joins `renders` to be rendered at its placed length.  The trimmed takes."""
    doc, trims = json.loads((Path(ctx.home) / "plan.json").read_text(encoding="utf-8")), []
    for index, faults in routed.get("timeline_trim", {}).items():
        doc, action = shorten(doc, index, placed_seconds(ctx.home, index), built_for(records.get(index, {})))
        if action == "restore":
            renders[index] = faults
        elif action == "shorten":
            trims.append(index)
    return doc, trims


def affordable_subset(ctx, rung: Rung, renders: dict) -> dict[int, list[Fault]]:
    """The takes the budget pays for, worst (most faults) first: a big batch is trimmed, not refused."""
    order = sorted(renders, key=lambda i: (-len(renders[i]), i))
    n = len(order)
    while n and not can_afford(ctx, rung, n):
        n -= 1
    return {i: renders[i] for i in order[:n]}


def batch_of(ctx, rung: Rung, renders: dict, room: Path, since: float) -> tuple[dict, str]:
    """(the renders this round takes, why it takes fewer or none): the cap, the spent episode and the
    price each say one reason instead of returning in silence."""
    if not renders:
        return {}, "no renders"
    if rounds_of(room, since) >= ROUNDS_CAP:
        return {}, "ROUNDS_CAP"
    if refuse_spent(ctx, len(renders)):
        return {}, "refuse_spent"
    kept = affordable_subset(ctx, rung, renders)
    if kept:
        return kept, f"{len(kept)} of {len(renders)} takes afforded" if len(kept) < len(renders) else ""
    return {}, f"unaffordable: {cost(rung, 1):.0f} s for one take, budget {ctx.budget.headroom():.0f} s"


def write_edits(ctx, doc: dict, routed: dict, kept: dict, trims: list[int]) -> None:
    """The plan edits of the takes that WILL render (a dropped take keeps its plan), written once."""
    edited = False
    for index, faults in routed.get("move_type", {}).items():
        if index in kept:
            doc, edited = move_type(doc, index, faults), True
    for index in routed.get("gait_verb", {}):
        if index in kept:
            doc, edited = gait_edit(doc, index), True
    if trims or edited:
        episode_home.write_plan(Path(ctx.home) / "plan.json", doc)
    if trims:                                           # free: re-placed now, re-MEASURED after the renders
        ctx.run_script("scripts/episode/timeline.py", clock="timeline")


def render_round(ctx, rung: Rung, kept: dict, trims: list[int], flag: str, verdict: Verdict, room: Path) -> float:
    """ONE batched retake of `kept` (its round counted in the room's book); its wall seconds."""
    why = why_of(rung.name, [f for fs in kept.values() for f in fs])
    count_round(room, why, signatures(verdict))
    began = wall()
    retake(ctx, sorted(kept), why, flag, trims=trims)
    return wall() - began


def remeasure_trims(ctx, trims: list[int]) -> None:
    """No render round: the trims still re-measure."""
    if trims:
        measured(ctx, "scripts/episode/take_dq.py", "take_dq", ".dq.json", *[str(i) for i in sorted(trims)])


def rungs(ctx, plan, flag: str, records: dict[int, dict] | None = None) -> judged_gate.Rungs:
    """The priced ladder and how a rung is taken for this episode."""
    records = records or {}
    from studio import run_budget
    room = Path(ctx.home) / TAKES
    since = run_budget.clock_reset_epoch(ctx.home)       # a retry's fresh rounds

    def take(rung: Rung, _try: int, verdict: Verdict) -> judged_gate.RungResult:
        """ONE batched round: free cures first (no render, no round), then the union of renderable
        cures in a single retake.  K11: changed only when bytes changed or a render ran."""
        routed = route(verdict, room, try_i=max(_try + 1, rounds_of(room, since) + 1))
        if not routed:
            return judged_gate.RungResult(False, "not routed")
        written = head_cuts(ctx, routed.get("head_cut", {}))
        renders = renderable(routed, room, written)
        doc, trims = trimmed(ctx, routed, renders, records)
        kept, why = batch_of(ctx, rung, renders, room, since)
        write_edits(ctx, doc, routed, kept, trims)
        free = f"head cut {len(written)}, trimmed {len(trims)}"
        if not kept:
            remeasure_trims(ctx, trims)
            return judged_gate.RungResult(bool(written or trims), f"{free}; {why}")
        seconds = render_round(ctx, rung, kept, trims, flag, verdict, room)
        return judged_gate.RungResult(True, f"rendered {len(kept)} of {len(renders)}; {free}", seconds)
    return judged_gate.Rungs(LADDER, take, curable=lambda v: still_curable(room, v, since, home=ctx.home))
