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

from studio import episode_home, episode_ref_official as ro, judged_gate, plan_gates, take_leak
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
INPUT_BORNE = frozenset({"content", "clones", "identity", "unread", "lettering", "text",
                         "look", "letterbox"})
"""Kinds that live in the panel, the prompt or the grade: no seed reroll ever
cured one (economist, 2026-09-30 -- content by take render 3/21, by panel
redraw 1/1; look constant across every seed).  They go to the terminal, and
the BOARD owns the cure."""
MOVABLE = (FROZEN | {"held", "pass-through", "last-vs-panel", "last-vs-cell", "drift",
                     "jump", "cut", "cut-vote", "cut-landing", "foreign", "churn", "zoom",
                     "face-at-end", "coherence off-board"})
"""Kinds a changed MOVE cures: measured 89-100% on frozen/held, 67% on
last-vs-panel; even the 'sampling' cures came from the plan edit, not the roll."""


def cure_of(faults: list[Fault]) -> str:
    """One cure for one take, from what its faults measure as curable.
    '' means no render buys anything: the terminal answers."""
    kinds = {f.kind for f in faults}
    if kinds & MOVABLE:
        return "move_type"
    if kinds & LAG:
        return "timeline_trim"                    # free: lag follows placed length
    if "leak" in kinds and kinds - {"leak"} <= INPUT_BORNE and any(
            f.evidence.get("covers") for f in faults if f.kind == "leak"):
        return "head_cut"                         # free: heads.json
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
        if try_i >= 2 and not progressed(room, i, sorted({f.kind for f in fs})):
            continue
        if cure := cure_of(fs):
            out.setdefault(cure, {})[i] = fs
    return out


def renders_of(routed: dict[str, dict[int, list[Fault]]]) -> list[int]:
    """The takes a batched round actually re-renders."""
    return sorted({i for cure in ("move_type", "seed") for i in routed.get(cure, {})})


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
    "rotation": "rotation", "zoom": "overrun", "face-at-end": "overrun",
    "coherence off-board": "board", "last-vs-cell": "board", "last-vs-panel": "board", "drift": "board",
    "churn": "board", "jump": "cut", "cut-vote": "cut", "cut": "cut", "cut-landing": "cut", "foreign": "cut",
}
SUBSTITUTE = {
    # a still take that froze: give the camera the move; a moving one: follow the actor
    "frozen": {"locked": "push_slow", "*": "follow"},
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
    cam, _ = ro.camera_clause(plan_gates.head_of(motion))
    if found := AIM.search(cam or ""):
        return " ".join(found.group(1).strip(" ,.").split()[:AIM_WORDS])
    # at_rest clauses are SEMICOLON-separated (ep16: a comma split made the
    # whole paragraph the aim and the motion lint refused the cure, M9)
    first = re.split(r"[;,.]", at_rest or "")[0].strip(" .")
    return " ".join(first.split()[:AIM_WORDS]) or "the figure"


AIM_WORDS = 6
"""A substitute move aims at one short noun phrase, never a sentence."""


def substitute_id(kind: str, motion: str) -> str:
    """The catalog move that replaces this one for this cause, never the same move back."""
    table = SUBSTITUTE[CAUSE_OF[kind]]
    move = plan_gates.move_id(motion or "", "")
    new = table.get(move, table["*"])
    if new != move:
        return new
    return "locked" if move != "locked" else "push_slow"


def substitute(kind: str, motion: str, at_rest: str = "") -> str:
    """The motion with its camera head swapped; the subject's own clauses stay."""
    head, *rest = [c.strip() for c in (motion or "").split(";")]
    _cam, subject = ro.camera_clause(head)
    new = PHRASING[substitute_id(kind, motion)].format(aim=aim_of(motion, at_rest))
    return "; ".join([new] + ([subject] if subject else []) + [c for c in rest if c])


def move_type(doc: dict, index: int, faults: list[Fault]) -> dict:
    shot = shot_doc(doc, index)
    kind = next((f.kind for f in faults if f.kind in CAUSE_OF), None)
    if kind is None:       # nothing a move answers (ep14 T20: letterbox, content) -- the terminal will
        return doc
    shot["motion"] = substitute(kind, shot["motion"], shot.get("at_rest", ""))
    return doc


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
    path = stills_path(home)
    room = path.parent
    return {k: v for k, v in load_stills(home).items()
            if not ((room / f"T{k:02d}.mp4").exists()
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
    """The passed panel this take would be held on, when one exists."""
    panel = Path(home) / "storyboard" / f"shot_{index:02d}.png"
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
    write_still(home, index, panel, placed_seconds(home, index), why_of("still", faults))
    return "still"


def terminal(home: Path, plan, verdict: Verdict, order: list[int], cap: int = STILL_MAX) -> Verdict:
    """The terminal rung over every take still faulted: a still from the
    passed panel on a narration shot with a HARD fault (cap, never
    adjacent); keep_best flagged high on a dialogue, turn or button shot or
    a third still; keep_best flagged otherwise.  Never a park, never a drop."""
    by: dict[int, list[Fault]] = {}
    for f in verdict.faults:
        by.setdefault(index_of(f.where), []).append(f)
    faults, stilled = [], False
    for index, own in sorted(by.items()):
        outcome = settle_take(home, plan, index, own, order, cap)
        stilled = stilled or outcome == "still"
        panel = f"storyboard/shot_{index:02d}.png" if outcome == "still" else ""
        faults += [f.model_copy(update={"severity": "high" if outcome == "high" else f.severity,
                                        "evidence": {**f.evidence, **({"still": panel} if panel else {})}})
                   for f in own]
    return verdict.model_copy(update={"faults": faults, "terminal": "still" if stilled else "keep_best"})


def terminal_for(ctx, plan):
    """The `terminal` callable judged_gate.clear takes, over this episode."""
    def end(verdict: Verdict) -> Verdict:
        order = [take_eye.index_of(t) for t in sorted((ctx.home / TAKES).glob("T??.mp4"))]
        return terminal(ctx.home, plan, verdict, order)
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
                                  float(records.get(index, {}).get("measured_seconds") or 0.0))
        elif rung.name == REPLAN_CELL.name:
            doc, action = replan(doc, index, faults), "replan_cell"
    if action and action != "restore":
        episode_home.write_plan(path, doc)
    return action


ROUNDS_CAP = 2
"""Batched retake rounds an episode may take, ACROSS RESUMES.  Five-expert
debate 2026-09-30: with every cure batched into ONE round (the old F1 rule as
code), two rounds cover a first cure and one re-route; ep14 spent 14 rounds
and rounds 3-14 all ended with the identical terminal verdict.  A fault still
alive after two batched rounds is structural -- the judge or the input -- and
belongs to the terminal, not to another render."""
MAX_TAKE_ATTEMPTS = 3
"""Archived attempts after which a take is never retaken again (ep14: T19 x8,
T05 x7 -- lettering and clones live in the panel, not the seed)."""
LADDER_FILE = "ladder.json"


def rounds_of(room: Path) -> int:
    """Rounds this episode has taken, read off the room (a resume reads the same file)."""
    path = Path(room) / LADDER_FILE
    return len(json.loads(path.read_text(encoding="utf-8")).get("rounds", [])) if path.exists() else 0


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


def still_curable(room: Path, verdict: Verdict) -> bool:
    """May the climb take another round?  Not past the cap, and only while
    the router still has a cure to assign: capped takes, unprogressed
    signatures and input-borne kinds all route to nothing, and the terminal
    (a still or the best take, flagged) answers those, not another render."""
    if rounds_of(room) >= ROUNDS_CAP:
        return False
    return bool(route(verdict, room, try_i=rounds_of(room) + 1))


def head_cuts(ctx, wanted: dict[int, list[Fault]]) -> None:
    """The leak measured is the head cut: heads.json through take_leak.write_head, no GPU."""
    for index in wanted:
        dq = take_eye.read_json(ctx.home / TAKES / f"T{index:02d}.dq.json") or {}
        take_leak.write_head(ctx.home, index, (dq.get("measures") or {}).get("leak"))


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


def retake(ctx, indices: list[int], why: str, flag: str, trims: list[int] | None = None) -> None:
    """One batched round: ALL renders first, then ONE measure window (owner,
    2026-09-30: "first run all model executions once then do the dq check to
    avoid cold starts").  The H3 stack stages ~40 GB and evicts the judge's
    weights, so a measure between renders pays a cold load both ways; the
    trimmed takes' re-measures ride the same window, never their own."""
    names = [str(i) for i in sorted(indices)]
    ctx.run_script(RENDER, "--from-refs", "--no-ends", flag, *retake_args(indices, why), gpu=True, clock="takes")
    measured(ctx, "scripts/episode/take_dq.py", "take_dq", ".dq.json", *names, "--attempts")
    if trims:
        # no --attempts: a trim renders nothing, so there is nothing to archive
        measured(ctx, "scripts/episode/take_dq.py", "take_dq", ".dq.json",
                 *[str(i) for i in sorted(trims)])
    measured(ctx, "scripts/episode/take_content_check.py", "take_content", ".content.json", *names)


def rungs(ctx, plan, flag: str, records: dict[int, dict] | None = None) -> judged_gate.Rungs:
    """The priced ladder and how a rung is taken for this episode."""
    records = records or {}

    room = Path(ctx.home) / TAKES

    def take(rung: Rung, _try: int, verdict: Verdict) -> None:
        """ONE batched round: free cures first (no render, no round), then the
        union of renderable cures in a single retake."""
        routed = route(verdict, room, try_i=max(_try + 1, rounds_of(room) + 1))
        if not routed:
            return
        if leaks := routed.get("head_cut"):
            head_cuts(ctx, leaks)                       # free: heads.json
        renders = dict(routed.get("move_type", {})) | dict(routed.get("seed", {}))
        path = Path(ctx.home) / "plan.json"
        doc, trims = json.loads(path.read_text(encoding="utf-8")), []
        for index, faults in routed.get("timeline_trim", {}).items():
            doc, action = shorten(doc, index, placed_seconds(ctx.home, index),
                                  float(records.get(index, {}).get("measured_seconds") or 0.0))
            if action == "restore":                     # length changed under it: render at the placed length
                renders[index] = faults
            elif action == "shorten":
                trims.append(index)
        for index, faults in routed.get("move_type", {}).items():
            doc = move_type(doc, index, faults)         # a seed-routed take keeps its plan
        if trims or routed.get("move_type"):
            episode_home.write_plan(path, doc)
        if trims:                                       # free: re-placed now, re-MEASURED after the
            ctx.run_script("scripts/episode/timeline.py", clock="timeline")   # renders (one window)
        if not renders or rounds_of(room) >= ROUNDS_CAP or not can_afford(ctx, rung, len(renders)):
            if trims:                                   # no render round: the trims still re-measure
                measured(ctx, "scripts/episode/take_dq.py", "take_dq", ".dq.json",
                         *[str(i) for i in sorted(trims)])
            return
        why = why_of(rung.name, [f for fs in renders.values() for f in fs])
        count_round(room, why, signatures(verdict))
        retake(ctx, sorted(renders), why, flag, trims=trims)
    return judged_gate.Rungs(LADDER, take, curable=lambda v: still_curable(room, v))
