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
from pathlib import Path

from studio import episode_home, episode_ref_official as ro, judged_gate, plan_gates, take_leak
from studio.judges import take_eye
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Ladder, Rung

COLD_S, TAKE_S, REPLAN_S = 300.0, 228.0, 720.0
SEED = Rung("seed", COLD_S + TAKE_S)
MOVE_TYPE = Rung("move_type", COLD_S + TAKE_S)
SHORTER_TAKE = Rung("shorter_take", COLD_S + TAKE_S)
HEAD_CUT = Rung("head_cut", 0.0)
REPLAN_CELL = Rung("replan_cell", REPLAN_S)
LADDER = Ladder([SEED, MOVE_TYPE, SHORTER_TAKE, HEAD_CUT, REPLAN_CELL], "keep_best")
STILL_MAX = 2
TAKES = Path("takes") / "r2v"
STILLS = "stills.json"
RENDER = "scripts/episode/takes_r2v.py"

FROZEN = frozenset({"frozen-at-start", "frozen-share"})
LAG = frozenset({"lag", "lip-sync"})
CONTENT = take_eye.HARD_CONTENT
MOTION = take_eye.GEOMETRY | FROZEN | {"churn"}
"""Faults of the MOVE: cured by another move type from the catalog."""
NEVER_SEED = LAG | {"leak"}

CAUSE_OF = {
    "frozen-at-start": "frozen", "frozen-share": "frozen",
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
    return ctx.budget.can_afford(judged_gate.step_of(ctx), cost(rung, takes))


# ---- plan edits, through write_plan ----------------------------------------------

def shot_doc(doc: dict, index: int) -> dict:
    return next(s for s in doc["shots"] if s["index"] == index)


def aim_of(motion: str, at_rest: str = "") -> str:
    """What the substitute move points at: the old camera clause's own aim,
    else the first clause of `at_rest`, else the figure."""
    cam, _ = ro.camera_clause(plan_gates.head_of(motion))
    if found := AIM.search(cam or ""):
        return found.group(1).strip(" ,.")
    return (at_rest or "").split(",")[0].strip(" .") or "the figure"


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
    kind = next(f.kind for f in faults if f.kind in CAUSE_OF)
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
    stills[str(index)] = {"panel": episode_home.relative(book, panel), "seconds": seconds, "why": why}
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
    doc = take_eye.read_json(Path(home) / "placed.json") or {}
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
    if panel is None or not can_still(index, load_stills(home), order, cap):
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


def head_cuts(ctx, wanted: dict[int, list[Fault]]) -> None:
    """The leak measured is the head cut: heads.json through take_leak.write_head, no GPU."""
    for index in wanted:
        dq = take_eye.read_json(ctx.home / TAKES / f"T{index:02d}.dq.json") or {}
        take_leak.write_head(ctx.home, index, (dq.get("measures") or {}).get("leak"))


def retake(ctx, indices: list[int], why: str, flag: str) -> None:
    """One batched round: the render, then both machine gates on those takes."""
    names = [str(i) for i in sorted(indices)]
    ctx.run_script(RENDER, "--from-refs", "--no-ends", flag, *retake_args(indices, why), gpu=True, clock="takes")
    ctx.run_script("scripts/episode/take_dq.py", *names, "--attempts", gpu=True, clock="take_dq")
    ctx.run_script("scripts/episode/take_content_check.py", *names, gpu=True, clock="take_content")


def rungs(ctx, plan, flag: str, records: dict[int, dict] | None = None) -> judged_gate.Rungs:
    """The priced ladder and how a rung is taken for this episode."""
    records = records or {}

    def take(rung: Rung, _try: int, verdict: Verdict) -> None:
        wanted = takes_for(verdict, rung.name, lambda i: take_eye.planned(plan, i)[1])
        if not wanted:
            return
        if rung.name == HEAD_CUT.name:
            return head_cuts(ctx, wanted)
        if not can_afford(ctx, rung, len(wanted)):
            return
        action = edit_plan(ctx, rung, wanted, records)
        if action == "shorten":
            ctx.run_script("scripts/episode/timeline.py", clock="timeline")
        retake(ctx, list(wanted), why_of(rung.name, [f for fs in wanted.values() for f in fs]), flag)
    return judged_gate.Rungs(LADDER, take)
