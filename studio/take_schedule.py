"""The take stage's two lanes: the GPU queue and the CPU check lane beside it.

Owner, 2026-10-14 (Jekyll ep01 sat at 6 % GPU while the CPU measured its
takes): "it shouldn't wait, the GPU needs running, and the DQ checks should be
done after all videos are done, or in parallel if the GPU is not needed."
Decision: architecture/decisions/2026-10-14-gpu-never-waits-for-checks.md.

THE GPU QUEUE holds three kinds of job, in this order:

    render      the first renders, back to back (one takes_r2v process)
    retake      a cure a CPU check ordered: behind every first render still
                queued, ahead of any GPU check; retakes ordered while one
                waits join it (one process, one weights load)
    gpu_checks  the reads that need ComfyUI (the VL content read, the DINO
                leak): only when no render is queued AND the CPU lane is idle.
                They never preempt a render, and a check still running on the
                CPU may yet order a retake -- a retake after the VL batch pays
                the video weights' cold load, which costs more than any check.

THE CPU LANE measures each take as it lands (take_dq --cpu-only).

`serial`, `overlapped` and `overlap_only` project an episode's wall clock
from measured per-take seconds (scripts/episode/take_schedule_replay.py reads
them off an episode's timing.jsonl and phases.jsonl).  Pure: no process, no
GPU, no file.
"""
from __future__ import annotations

from dataclasses import dataclass

FIRST, RETAKE, REFINE, CHECKS = "render", "retake", "refine", "gpu_checks"
RANK = {FIRST: 0, RETAKE: 1, REFINE: 2, CHECKS: 3}
"""A REFINE (the wide-shot face refine, owner 2026-10-17) re-renders the face crops
of a take that PASSED its dq: behind every render and retake, ahead of the GPU checks."""
JOINS = (RETAKE, REFINE)


@dataclass(frozen=True)
class Job:
    kind: str
    takes: tuple[int, ...] = ()
    why: str = ""


def joined(a: Job, b: Job) -> Job:
    """Two retakes (or two refines) as one job: the union of their takes and of their reasons."""
    whys = [w for w in dict.fromkeys(a.why.split("; ") + b.why.split("; ")) if w]
    return Job(a.kind, tuple(sorted(set(a.takes) | set(b.takes))), "; ".join(whys))


def enqueue(queue: list[Job], job: Job) -> list[Job]:
    """The queue with `job` placed by kind: behind every job of its rank or
    better, ahead of the rest.  A retake joins a retake already waiting, a
    refine a refine."""
    if job.kind in JOINS and (waiting := next((j for j in queue if j.kind == job.kind), None)):
        return [joined(waiting, job) if j is waiting else j for j in queue]
    at = next((k for k, j in enumerate(queue) if RANK[j.kind] > RANK[job.kind]), len(queue))
    return queue[:at] + [job] + queue[at:]


def next_job(queue: list[Job], cpu_busy: bool) -> Job | None:
    """The GPU's next job: a render or retake whenever one waits; the GPU
    checks only once the CPU lane is idle."""
    if not queue:
        return None
    head = queue[0]
    return None if head.kind == CHECKS and cpu_busy else head


# ---- the projection ------------------------------------------------------------------

@dataclass(frozen=True)
class Costs:
    """Measured seconds: a CPU check per first take and per retake (with its
    attempts), a VL content read per take, the VL model's load per batch, the
    eye, the strip, the gap between render processes, the video weights'
    reload after a VL batch (0 when the per-take seconds already carry it)."""
    dq_s: float
    dq_retake_s: float
    content_s: float
    vl_load_s: float
    eye_s: float
    strip_s: float = 0.0
    launch_s: float = 0.0
    cold_s: float = 0.0


@dataclass(frozen=True)
class Rounds:
    """The renders an episode took: the firsts in render order, today's round
    1 and round 2 as (take, render seconds), and which round-1 takes a CPU
    check alone ordered (`early`: a move or seed cure read off the dq rows)."""
    first: tuple[tuple[int, float], ...]
    round1: tuple[tuple[int, float], ...]
    round2: tuple[tuple[int, float], ...]
    early: frozenset[int]


@dataclass(frozen=True)
class Projection:
    wall_s: float
    gpu_s: float

    @property
    def idle_s(self) -> float:
        return self.wall_s - self.gpu_s


def window(start: float, takes: int, c: Costs) -> float:
    """The GPU checks over `takes` (one VL load), then the strip and the eye."""
    return start + c.vl_load_s + c.content_s * takes + c.strip_s + c.eye_s


def rendered_s(renders) -> float:
    return sum(s for _, s in renders)


def serial_cycle(start: float, renders, dq_each: float, c: Costs, cold: float = 0.0) -> float:
    """Today: every render, then every check, then the VL batch and the eye."""
    rendered = start + cold + c.launch_s + rendered_s(renders)
    return window(rendered + dq_each * len(renders), len(renders), c)


def serial(r: Rounds, c: Costs) -> Projection:
    """Today's step 09: render all, check all, read, judge -- per round."""
    t = serial_cycle(0.0, r.first, c.dq_s, c)
    for later in (r.round1, r.round2):
        t = serial_cycle(t, later, c.dq_retake_s, c, c.cold_s) if later else t
    return Projection(t, rendered_s(r.first + r.round1 + r.round2) + gpu_cycles(r, c))


def gpu_cycles(r: Rounds, c: Costs) -> float:
    """The VL batches today's three cycles run."""
    rounds = [x for x in (r.first, r.round1, r.round2) if x]
    return sum(c.vl_load_s + c.content_s * len(x) for x in rounds)


def lanes(start: float, renders, dq_each: float, cpu: float = 0.0) -> tuple[float, float]:
    """(GPU end, CPU end): renders back to back, each one's check as it lands."""
    gpu = start
    for _, s in renders:
        gpu += s
        cpu = max(cpu, gpu) + dq_each
    return gpu, cpu


def overlap_cycle(start: float, renders, dq_each: float, c: Costs, cold: float = 0.0) -> float:
    gpu, cpu = lanes(start + cold + c.launch_s, renders, dq_each, start)
    return window(max(gpu, cpu), len(renders), c)


def overlap_only(r: Rounds, c: Costs) -> Projection:
    """Today's rounds, each with its checks overlapped on its renders."""
    t = overlap_cycle(0.0, r.first, c.dq_s, c)
    for later in (r.round1, r.round2):
        t = overlap_cycle(t, later, c.dq_retake_s, c, c.cold_s) if later else t
    return Projection(t, rendered_s(r.first + r.round1 + r.round2) + gpu_cycles(r, c))


def first_lanes(r: Rounds, c: Costs) -> tuple[float, float, dict[int, float]]:
    """The firsts with their checks; when each early cure became known."""
    gpu = cpu = 0.0
    ready: dict[int, float] = {}
    for take, s in r.first:
        gpu += s
        cpu = max(cpu, gpu) + c.dq_s
        if take in r.early:
            ready[take] = cpu
    return gpu, cpu, ready


def early_lanes(gpu: float, cpu: float, ready: dict[int, float], seconds: dict[int, float],
                c: Costs) -> tuple[float, float]:
    """The early retakes: each job takes every cure known when the GPU frees;
    the GPU waits for a cure only when nothing else could run."""
    pending = sorted(ready, key=ready.get)
    while pending:
        start = max(gpu, ready[pending[0]])
        batch = [t for t in pending if ready[t] <= start]
        gpu, cpu = lanes(start + c.launch_s, [(t, seconds[t]) for t in batch], c.dq_retake_s, cpu)
        pending = [t for t in pending if t not in batch]
    return gpu, cpu


def overlapped(r: Rounds, c: Costs) -> Projection:
    """The new step 09: firsts and early retakes streamed with their checks,
    one VL batch, then the late retakes and round 2 as one render job."""
    early = tuple((t, s) for t, s in r.round1 if t in r.early)
    late = tuple((t, s) for t, s in r.round1 if t not in r.early) + r.round2
    gpu, cpu, ready = first_lanes(r, c)
    gpu, cpu = early_lanes(gpu, cpu, ready, dict(early), c)
    t = window(max(gpu, cpu), len(r.first) + len(early), c)
    t = overlap_cycle(t, late, c.dq_retake_s, c, c.cold_s) if late else t
    batches = c.vl_load_s * (1 + bool(late)) + c.content_s * (len(r.first) + len(early) + len(late))
    return Projection(t, rendered_s(r.first + early + late) + batches)
