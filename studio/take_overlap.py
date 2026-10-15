"""Step 09's two lanes, run for real: the GPU never waits on a check.

Decision architecture/decisions/2026-10-14-gpu-never-waits-for-checks.md
(owner, 2026-10-14: "it shouldn't wait, the GPU needs running").

    GPU lane   one takes_r2v process at a time (it queues its takes on ComfyUI
               in one go, so they render back to back on warm weights); the
               first renders, then any retake a check ordered
    CPU lane   one take_dq --cpu-only process at a time over every take that
               has LANDED since the last one (its bytes complete: shots.json
               written after them) and carries no verdict by this measuring
               code; a check that dies is tried once more, then left to the
               serial catch-all pass after the lanes

A dq-borne cure -- a move or a seed, routed by take_ladder.route on the dq
rows alone -- becomes the EARLY round: the take ladder's round 1, recorded in
ladder.json (`early: true`) when its first job launches, joined by every later
job of the same pass, so ROUNDS_CAP counts it once.  Content, the eye and the
free cures (a timeline trim, a head cut) stay with the ladder, after the GPU
window step 09 runs once the lanes are idle (the VL read and any deferred
leak: they never preempt a render).  `studio.take_schedule` is the policy.
"""
from __future__ import annotations

import json
import subprocess
import time
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path

from studio import boundary, episode_clock, episode_home, judged_gate, take_ladder
from studio.judges import take_eye
from studio.judges.verdict import Fault, Verdict
from studio.take_schedule import FIRST, RETAKE, Job, enqueue, next_job

TAKES = Path("takes") / "r2v"
RENDER = "scripts/episode/takes_r2v.py"
CHECK = "scripts/episode/take_dq.py"
POLL_S = 5.0
CPU_TRIES = 2
WAIT_CAP = 7200.0
RENDER_CURES = ("move_type", "seed")


def measuring_code() -> str:
    """take_dq's measuring-code fingerprint (a lazy import: the script loads PIL)."""
    from scripts.episode import take_dq
    return take_dq.measures_sha8()


def popen(cmd: list[str]):
    return subprocess.Popen(cmd)


# ---- what has landed ---------------------------------------------------------------

def read_doc(path: Path) -> dict | list | None:
    """A JSON file another process may be writing this instant: None on a torn read."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def fresh(take: Path, code: str, any_code: bool = False) -> bool:
    """The take has a dq verdict newer than its bytes, by this measuring code."""
    dq = take.with_suffix(".dq.json")
    if not take.exists() or not dq.exists() or dq.stat().st_mtime < take.stat().st_mtime:
        return False
    doc = read_doc(dq)
    return isinstance(doc, dict) and (any_code or doc.get("measures_sha8") == code)


def landed(room: Path, code: str, any_code: bool = False, skip: set[int] = frozenset()) -> list[int]:
    """Takes whose bytes are complete -- takes_r2v writes shots.json AFTER the
    video -- and that no verdict by this code describes yet."""
    sheet = Path(room) / "shots.json"
    rows = read_doc(sheet) if sheet.exists() else None
    if not isinstance(rows, list):
        return []
    at, out = sheet.stat().st_mtime, []
    for i in sorted({int(r["index"]) for r in rows}):
        take = Path(room) / f"T{i:02d}.mp4"
        if i not in skip and take.exists() and take.stat().st_mtime <= at and not fresh(take, code, any_code):
            out.append(i)
    return out


# ---- the early round ---------------------------------------------------------------

def last_round(room: Path) -> dict:
    doc = read_doc(Path(room) / take_ladder.LADDER_FILE)
    rounds = (doc or {}).get("rounds") or [] if isinstance(doc, dict) else []
    return rounds[-1] if rounds else {}


def early_open(room: Path, since: float = 0.0) -> bool:
    """No round taken since the clock's reset, or only the early one."""
    n = take_ladder.rounds_of(room, since)
    return n == 0 or (n == 1 and bool(last_round(room).get("early")))


def early_taken(room: Path, since: float = 0.0) -> set[int]:
    """The takes the early round already cured: never cured early twice."""
    if take_ladder.rounds_of(room, since) == 0 or not last_round(room).get("early"):
        return set()
    return {int(k) for k in (last_round(room).get("faults") or {})}


def join_early(room: Path, why: str, sigs: dict[str, list[str]], since: float = 0.0) -> None:
    """Open the early round in ladder.json, or fold this job into it."""
    path = Path(room) / take_ladder.LADDER_FILE
    doc = read_doc(path) if path.exists() else {}
    rounds = doc.setdefault("rounds", [])
    if take_ladder.rounds_of(room, since) == 0:
        rounds.append({"why": why, "at": round(time.time(), 1), "faults": {}, "early": True})
    rounds[-1]["faults"].update(sigs)
    if why not in rounds[-1]["why"]:
        rounds[-1]["why"] += f"; {why}"
    path.write_text(json.dumps(doc, indent=1), encoding="utf-8")


def dq_verdict(room: Path, indices: list[int]) -> Verdict:
    """The take eye's dq rows alone, over these takes."""
    faults: list[Fault] = []
    for i in indices:
        if isinstance(dq := read_doc(Path(room) / f"T{i:02d}.dq.json"), dict):
            faults += take_eye.dq_faults(i, dq)
    return Verdict(judge=take_eye.NAME, version=take_eye.VERSION, passed=not faults, faults=faults,
                   confidence=1.0, reads=len(indices))


def early_cures(room: Path, indices: list[int], since: float = 0.0) -> dict[int, tuple[str, list[Fault]]]:
    """take -> (cure, faults) for the render cures the dq rows alone order."""
    if not indices or not early_open(room, since):
        return {}
    routed, taken = take_ladder.route(dq_verdict(room, indices), room, try_i=1), early_taken(room, since)
    return {i: (cure, fs) for cure in RENDER_CURES for i, fs in routed.get(cure, {}).items() if i not in taken}


def early_affordable(ctx, takes: int) -> bool:
    """The round's price leaves the firsts their reserve and the budget pays it."""
    budget = getattr(ctx, "budget", None)
    if budget is None or takes <= 0:
        return False
    price = take_ladder.cost(take_ladder.BATCH, takes)
    return budget.leaves_reserve(judged_gate.step_of(ctx), price) and take_ladder.can_afford(
        ctx, take_ladder.BATCH, takes)


def cure_plan(home: Path, moves: dict[int, list[Fault]]) -> None:
    """The move cures, through write_plan (a refused plan is never written)."""
    if not moves:
        return
    path = Path(home) / "plan.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    for index, faults in moves.items():
        doc = take_ladder.move_type(doc, index, faults)
    episode_home.write_plan(path, doc)


# ---- the two lanes -----------------------------------------------------------------

@dataclass
class Lane:
    proc: object
    takes: tuple[int, ...]
    started: float
    note: str


class Shop:
    """The GPU queue and the CPU lane over one take room, polled every POLL_S."""

    def __init__(self, ctx, base: list[str], *, extra: tuple[str, ...] = (), early: bool = False,
                 attempts: bool = False, retake: tuple[list[int], str] | None = None,
                 check_flags: tuple[str, ...] = (), spawn=None, sleep=time.sleep, now=time.time,
                 code: str | None = None):
        self.ctx, self.base, self.extra = ctx, list(base), tuple(extra)
        self.room = Path(ctx.home) / TAKES
        self.early, self.attempts, self.check_flags = early, attempts, tuple(check_flags)
        self.spawn = spawn or getattr(ctx, "spawn", None) or popen
        self.sleep, self.now = sleep, now
        self.code = code or measuring_code()
        self.queue = [Job(RETAKE, tuple(sorted(retake[0])), retake[1])] if retake else [Job(FIRST)]
        self.gpu: Lane | None = None
        self.cpu: Lane | None = None
        self.retaken: set[int] = set(retake[0]) if retake else set()
        self.cures: dict[int, tuple[str, list[Fault]]] = {}
        self.tries: dict[int, int] = {}
        self.failed, self.waited, self.moved = "", 0.0, False
        self.since = since_of(ctx.home)

    def run(self) -> None:
        with self.clocked():
            while self.tick():
                if not self.moved:
                    self.sleep(POLL_S)
        if self.failed:
            raise SystemExit(self.failed)
        boundary.check(self.ctx.home, "step 09 when its lanes stopped")   # the end of the lanes is a boundary

    def tick(self) -> bool:
        """One poll of both lanes; `moved` when a lane started or ended (the
        next poll then follows at once, no sleep between a reap and a launch)."""
        before = (self.gpu, self.cpu)
        self.reap_gpu()
        self.reap_cpu()
        self.feed_gpu()
        self.feed_cpu()
        self.moved = (self.gpu, self.cpu) != before
        return bool(self.gpu or self.cpu or (self.queue and not self.stopped()))

    def stopped(self) -> bool:
        return bool(self.failed) or boundary.requested(self.ctx.home)

    def clocked(self):
        """The takes row around the whole pass; the CPU rows are stamped within it."""
        if getattr(self.ctx, "number", None) is None:
            return nullcontext()
        return episode_clock.timed(self.ctx.book_dir, self.ctx.number, "takes", note=self.note())

    def note(self) -> str:
        """The row's note names the takes the pass was launched for, as run_script's did
        (`episode_clock.row_norm` prices a retake round by the takes it names)."""
        head = self.queue[0] if self.queue else Job(FIRST)
        if head.kind == RETAKE:
            return " ".join(self.base + take_ladder.retake_args(list(head.takes), head.why))
        return " ".join(self.first_args())

    def first_args(self) -> list[str]:
        return self.base + list(self.extra)

    # -- GPU ---------------------------------------------------------------------

    def feed_gpu(self) -> None:
        if self.gpu or self.stopped() or (job := next_job(self.queue, self.cpu is not None)) is None:
            return
        if self.engine_busy():
            return
        self.queue.remove(job)
        args = self.first_args() if job.kind == FIRST else self.retake_args(job)
        self.gpu = Lane(self.spawn(self.ctx.command(RENDER, tuple(args))), job.takes, self.now(), " ".join(args))
        self.ctx.log(f"GPU lane: {RENDER} {' '.join(args)}")

    def engine_busy(self) -> bool:
        """Another production holds ComfyUI: the render waits, the CPU lane does not."""
        if not self.ctx.busy():
            return False
        self.waited += POLL_S
        if self.waited >= getattr(self.ctx, "wait_cap", WAIT_CAP):
            self.failed = f"REFUSED: ComfyUI's queue stayed busy for {self.waited:.0f} s; {RENDER} was not started"
        return True

    def retake_args(self, job: Job) -> list[str]:
        """A retake job's argv; an early cure is written into the plan and the
        early round in ladder.json at LAUNCH, so a pause never strands one."""
        early = {i: self.cures.pop(i) for i in job.takes if i in self.cures}
        if early:
            cure_plan(self.ctx.home, {i: fs for i, (cure, fs) in early.items() if cure == "move_type"})
            join_early(self.room, job.why, {str(i): sorted({f.kind for f in fs}) for i, (_, fs) in early.items()},
                       self.since)
            self.learn(job)
        take_ladder.clear_heads(self.ctx.home, list(job.takes))   # measured on other bytes
        self.retaken |= set(job.takes)
        return self.base + take_ladder.retake_args(list(job.takes), job.why)

    def learn(self, job: Job) -> None:
        """The early round's learning, as judged_gate writes one per rung."""
        if hasattr(self.ctx, "learn"):
            from studio.learnings import Learning
            self.ctx.learn(Learning(step=judged_gate.step_of(self.ctx), gate="EYE_TAKES", measured=len(job.takes),
                                    action="early_cures", attempt=1, note=job.why))

    def reap_gpu(self) -> None:
        if not self.gpu or self.gpu.proc.poll() is None:
            return
        lane, self.gpu = self.gpu, None
        if lane.proc.returncode:
            self.failed = self.failed or f"REFUSED: {RENDER} exit {lane.proc.returncode}"

    # -- CPU ---------------------------------------------------------------------

    def feed_cpu(self) -> None:
        if self.cpu or self.stopped():
            return
        ready = landed(self.room, self.code, "--ceiling-spent" in self.check_flags, self.gave_up())
        if not ready:
            return
        attempts = [i for i in ready if self.attempts or i in self.retaken]
        plain = [i for i in ready if i not in attempts]
        takes, flag = (plain, ()) if plain else (attempts, ("--attempts",))
        args = (*map(str, takes), "--cpu-only", *flag, *self.check_flags)
        self.cpu = Lane(self.spawn(self.ctx.command(CHECK, args)), tuple(takes), self.now(), " ".join(args))

    def gave_up(self) -> set[int]:
        return {i for i, n in self.tries.items() if n >= CPU_TRIES}

    def reap_cpu(self) -> None:
        if not self.cpu or self.cpu.proc.poll() is None:
            return
        lane, self.cpu = self.cpu, None
        self.stamp(lane)
        done = [i for i in lane.takes if fresh(self.room / f"T{i:02d}.mp4", self.code, True)]
        for i in set(lane.takes) - set(done):
            self.tries[i] = self.tries.get(i, 0) + 1
        if self.early and done:
            self.order(done)

    def stamp(self, lane: Lane) -> None:
        if getattr(self.ctx, "number", None) is not None:
            episode_clock.stamp(self.ctx.book_dir, self.ctx.number, "take_dq", lane.started, self.now(),
                                ok=lane.proc.returncode == 0, note=lane.note, within="takes")

    def order(self, measured: list[int]) -> None:
        """The render cures these checks found, queued behind the first renders."""
        queued = {i for j in self.queue for i in j.takes} | set(self.cures)
        cures = {i: c for i, c in early_cures(self.room, measured, self.since).items() if i not in queued}
        if not cures or not early_affordable(self.ctx, len(cures)):
            return
        self.cures.update(cures)
        why = take_ladder.why_of(take_ladder.BATCH.name, [f for _, fs in cures.values() for f in fs])
        self.queue = enqueue(self.queue, Job(RETAKE, tuple(sorted(cures)), why))
        self.ctx.log(f"CPU lane: {why} on {sorted(cures)} -- queued behind the renders")


def unmeasured(room: Path, indices: list[int], code: str | None = None) -> list[int]:
    """Takes the lanes left without a whole verdict: none by this code, or one
    that still owes its deferred GPU rows."""
    code = code or measuring_code()
    out = []
    for i in indices:
        take = Path(room) / f"T{i:02d}.mp4"
        doc = read_doc(take.with_suffix(".dq.json")) if take.with_suffix(".dq.json").exists() else None
        if not fresh(take, code) or (isinstance(doc, dict) and doc.get("deferred")):
            out.append(i)
    return out


def since_of(home: Path) -> float:
    from studio import run_budget
    return run_budget.clock_reset_epoch(home)


def shoot(ctx, base: list[str], **kw) -> Shop:
    """Run the two lanes to idle; the shop is handed back for its record."""
    shop = Shop(ctx, base, **kw)
    shop.run()
    return shop
