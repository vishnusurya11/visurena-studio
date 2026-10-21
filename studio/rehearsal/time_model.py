"""The episode time model and its back-test (2026-10-21_ep02_proof DESIGN 4.7, package P7; skeptic R15, R16).

A predictor from an episode's INPUTS only (the plan's shots and setups, the placed lines, each take's
frames and planned faces) prices every step with the studio's own models -- `episode_clock`'s scaled
norms, the VL read fit (`library/vlm_calls.jsonl`, seconds = a + b * tokens), and for step 09's render
and refine the GPU costs measured on the real engine on 2026-10-21 (measured_costs.json beside this
file: a take, a refined face, a cold load) -- and corrects each step by the measured/prior ratio of the
OTHER episodes (leave one out; the band is `eta.band`).  The measure is timing.jsonl step totals of the
first pass (to the first dossier), contended rows marked, repair windows apart.  The refine is priced and
measured only where a first-pass refine row carries its GPU clock; otherwise its rows timed an older refine
than the price, so both sides leave it out and its Gap alone carries it (never twice).  A step the current code
runs that no record measures is a Gap with its p90 bound; Q5 cannot be PROVEN while any Gap's share of
the p90 is above 5 hundredths, or unknown.  Inputs are REAL records only: a path under a sandbox is
refused, because a rehearsal's clock is the fake's recording, never a measure."""
from __future__ import annotations

import json
import math
import os
import statistics
from dataclasses import dataclass, field
from pathlib import Path

from studio import episode_clock, eta, settings, step_caps
from studio.run_budget import OWNER_LIMIT_SECONDS

STEPS = ("02", "03", "04", "07", "08", "09", "10", "11", "13", "small")
"""The steps the back-test scores; `small` holds 01, 05, 06 and 12 (seconds each, never minutes)."""
PREDICTED = tuple(s for s in STEPS if s != "13")
"""Step 13 (publish) has no timed row in any era: it is a Gap bounded by its wall, never predicted."""
MARK = "mark"
TOLERANCE, NEED, HELD_OUT = 0.15, 3, 4
"""Pre-registered (DESIGN 4.7): total |error| <= 0.15 on >= 3 of 4 held-out episodes."""
SHARE_LIMIT = 0.05
PROOF_SANDBOX = settings.REPO / "docs" / "audit" / "2026-10-21_ep02_proof" / "sandbox"
SANDBOX_DIR = "visurena_rehearsal"
"""`sandbox.default_base()`'s folder name: every built sandbox lives under one."""
COSTS = Path(__file__).with_name("measured_costs.json")
"""The GPU costs measured on the real engine (2026-10-21_ep02_proof gpu/COSTS.md, FACE.md), committed."""


class SandboxInput(ValueError):
    """A time input under a rehearsal sandbox: its clock is a recording, never a measure (R15)."""


class UnmappedStage(KeyError):
    """A timing stage (or an era) the reviewed per-era map does not name."""


# ---- the sandbox refusal ----

def _within(path: Path, root: Path) -> bool:
    p, r = (Path(os.path.normcase(os.path.abspath(x))) for x in (path, root))
    return p == r or r in p.parents


def under_sandbox(path) -> bool:
    """True under a built sandbox, the proof folder's sandbox, or any folder a manifest sits in."""
    p = Path(os.path.abspath(path))
    if any(part.lower() == SANDBOX_DIR for part in p.parts) or _within(p, PROOF_SANDBOX):
        return True
    return any((d / settings.MANIFEST).is_file() for d in p.parents)


def refuse_sandbox(paths) -> None:
    bad = [str(p) for p in paths if under_sandbox(p)]
    if bad:
        raise SandboxInput("time inputs must be real records; refused under a sandbox: " + ", ".join(bad))


# ---- the reviewed per-era step map ----

@dataclass(frozen=True)
class Era:
    name: str
    since: str
    stages: dict
    refine: bool


WOTW_STAGES = {
    "bind": "small", "plan": "02", "places": "03", "sheets": "03", "cast": "03", "lines": "04",
    "speaker_check": "04", "respot": "small", "timeline": "small", "prompts": "small", "no_last_frame": "small",
    "frames": "07", "grids": "07", "panels": "08", "panel_dq": "08", "panel_content": "08", "panel_eye": "08",
    "takes": "09", "take_dq": "09", "take_content": "09", "take_eye": "09", "strip": "09", "assemble": "10",
    "title": "10", "qc": "11", "master_eye": "11", "eye_review": "11", "dossier": "small", "publish": "13"}
"""Reviewed 2026-10-21 on WotW ep21-27's timing.jsonl: every stage they hold, under the step that runs it
(eta.SUB_STEP's map, plus the legacy `frames`, `title`, `eye_review` and `publish` norms)."""
GRAMMAR_STAGES = {**WOTW_STAGES, "face_refine": "09", "take_render": "09", "upscale": "10", "cut": "10",
                  "bed": "10", "sfx": "10", "mix": "10", "grid_lint": "small"}
"""Reviewed 2026-10-21 on Jekyll ep01's timing.jsonl: the face refine and the render span inside 09, the
master upscale and the sound layer inside assemble, the grid lint in 06; `step_NN` rows are marks."""
ERAS = (Era("wotw-self-curing", "2026-10-06", WOTW_STAGES, refine=False),
        Era("grammar-face-refine", "2026-10-17", GRAMMAR_STAGES, refine=True))


def era_for(rows: list[dict]) -> Era:
    """The era of the episode's first row; a date before every reviewed era refuses."""
    first = min(str(r["started"]) for r in rows)[:10]
    named = [e for e in ERAS if e.since <= first]
    if not named:
        raise UnmappedStage(f"no reviewed era map for an episode started {first}")
    return named[-1]


def step_of(stage: str, era: Era) -> str:
    if stage.startswith("step_"):
        return MARK
    if stage not in era.stages:
        raise UnmappedStage(f"stage {stage!r} is not in the reviewed {era.name} map")
    return era.stages[stage]


def unmapped(rows: list[dict], era: Era) -> list[str]:
    return sorted({r["stage"] for r in rows if not r["stage"].startswith("step_") and r["stage"] not in era.stages})


# ---- the measure ----

def first_master_end(rows: list[dict]) -> float | None:
    """The end of the first dossier row: the first master is delivered."""
    ends = [span[1] for r in rows if r["stage"] == "dossier" and (span := episode_clock.epochs(r))]
    return min(ends) if ends else None


def repair_windows(rows: list[dict]) -> list[tuple[float, float]]:
    return [(float(r["opened_at"]), float(r.get("closed_at") or math.inf)) for r in rows]


def first_pass(rows: list[dict], repairs: list[tuple[float, float]]) -> tuple[list[dict], list[dict]]:
    """(the first pass, the rest): a row after the first master, or inside a repair window, is apart."""
    end = first_master_end(rows) or math.inf
    keep, apart = [], []
    for r in rows:
        start = (episode_clock.epochs(r) or (math.inf, math.inf))[0]
        late = start > end or any(lo <= start < hi for lo, hi in repairs)
        (apart if late else keep).append(r)
    return keep, apart


REFINE_STAGE = "face_refine"


def refine_clocked(rows: list[dict]) -> bool:
    """A refine row carries its GPU clock (907616f): only then does it time the refine face_refine.price prices."""
    return any(r["stage"] == REFINE_STAGE and r.get("gpu_busy_s") is not None for r in rows)


def measured(rows: list[dict], era: Era, refine: bool = True) -> dict[str, float]:
    """Seconds per step: each row's `seconds`, so a netted parent and its nested rows sum to its wall.  With
    refine False the refine rows are left out: their refine is unmeasured, and its Gap carries it."""
    out = dict.fromkeys(STEPS, 0.0)
    for r in rows:
        step = step_of(r["stage"], era)
        if step != MARK and (refine or r["stage"] != REFINE_STAGE):
            out[step] += float(r.get("seconds") or 0)
    return out


def contended(rows: list[dict], era: Era) -> dict[str, list[float]]:
    """The seconds of every row another run overlapped (`episode_clock.contended`), by step."""
    out: dict[str, list[float]] = {}
    for r in rows:
        step = step_of(r["stage"], era)
        if step != MARK and episode_clock.contended(r, rows):
            out.setdefault(step, []).append(float(r["seconds"]))
    return out


def _clocked(runs: list[dict], end: float | None) -> list[dict]:
    return [r for r in runs if end is not None and not r.get("repair") and float(r["started"]) <= end]


def clock_to_first_master(runs: list[dict], end: float | None) -> float | None:
    """The machine time to the first master: clock.jsonl's non-repair runs that began before it."""
    got = _clocked(runs, end)
    return sum(float(r["seconds"]) for r in got) if got else None


def uncovered_s(runs: list[dict], rows: list[dict], end: float | None) -> float:
    """Seconds of those runs no timing row covers: drive overhead, waits, a killed run's lost rest."""
    return sum((float(r["ended"]) - float(r["started"]))
               - episode_clock.covered(float(r["started"]), float(r["ended"]), rows) for r in _clocked(runs, end))


# ---- the inputs and the priors ----

@dataclass(frozen=True)
class Inputs:
    shots: int
    setups: int
    lines: int
    frames: tuple[int, ...]
    faces: tuple[int, ...]


def inputs_from(shots_rows: list[dict], placed: dict, plan: dict) -> Inputs:
    """What the plan, the placed lines and the take list say before anything renders."""
    omit = set(plan.get("omit") or [])
    return Inputs(shots=sum(1 for s in plan["shots"] if s.get("index") not in omit),
                  setups=len(plan.get("setups") or {}), lines=len(placed.get("lines") or []),
                  frames=tuple(int(r["frames"]) for r in shots_rows),
                  faces=tuple(len(r.get("faces") or []) for r in shots_rows))


def least_squares(xy: list[tuple[float, float]]) -> tuple[float, float]:
    """(a, b) of y = a + b * x."""
    mx, my = (statistics.fmean(v) for v in zip(*xy))
    var = sum((x - mx) ** 2 for x, _ in xy)
    b = sum((x - mx) * (y - my) for x, y in xy) / var if var else 0.0
    return my - b * mx, b


def vl_fit(calls: list[dict]) -> dict:
    """seconds = a + b * answer_tokens, least squares over the logged reads; `tokens` is their median.  A
    negative b is no model (a read never gets cheaper with a longer reply, and it prices a read at or below
    zero): it is kept as `refused_b` and a read is priced at the median read seconds whatever its tokens."""
    xy = [(float(c["answer_tokens"]), float(c["seconds"])) for c in calls
          if c.get("seconds") is not None and c.get("answer_tokens") is not None]
    if not xy:
        return {"a": 0.0, "b": 0.0, "n": 0, "tokens": 0.0}
    a, b = least_squares(xy)
    got = {"a": a, "b": b, "n": len(xy), "tokens": statistics.median(x for x, _ in xy),
           "median_s": statistics.median(y for _, y in xy)}
    return got | {"a": got["median_s"], "b": 0.0, "refused_b": b} if b < 0 else got


def vl_read_s(fit: dict, tokens: float | None = None) -> float:
    return fit["a"] + fit["b"] * (fit["tokens"] if tokens is None else tokens)


def costs() -> dict:
    """measured_costs.json: the GPU seconds the real engine took per take, refined face and load."""
    return json.loads(COSTS.read_text(encoding="utf-8"))


def _line(fit: dict, frames: float) -> float:
    return float(fit["intercept_s"]) + float(fit["s_per_frame"]) * float(frames)


def take_s(frames: int) -> float:
    """One warm H3 take's GPU seconds: the Wuli graph's measured line (the dearer graph, 24 of ep01's 28)."""
    return _line(costs()["take_wuli"], frames)


def refine_face_s(frames: int) -> float:
    """One refined face's GPU seconds: the measured line (frames set it, face size does not: COSTS.md)."""
    return _line(costs()["refine_face"], frames)


def render_s(frames) -> float:
    return float(costs()["take_cold_s"]) + sum(take_s(f) for f in frames)


def priors(inp: Inputs, read_s: float, refine: bool) -> dict[str, float]:
    """Each step's prior seconds (a unit of 1 where the step does not scale with an input); step 09's
    render and refine at the GPU costs measured on the real engine."""
    takes = len(inp.frames)
    render = render_s(inp.frames)
    checks = episode_clock.norm_for("take_dq", count=takes) + takes * read_s
    priced = sum(n * refine_face_s(f) for n, f in zip(inp.faces, inp.frames)) if refine else 0.0
    return {"02": 1.0, "03": float(max(inp.setups, 1)), "04": episode_clock.norm_for("lines", count=inp.lines),
            "07": float(inp.shots), "08": inp.shots * read_s, "09": render + checks + priced, "10": 1.0,
            "11": episode_clock.norm_for("qc", count=inp.lines) + read_s, "small": 1.0}


# ---- leave one out ----

@dataclass
class Episode:
    name: str
    era: str
    refine: bool
    inputs: Inputs
    measured: dict
    clock_s: float | None = None
    evidence: tuple = ()
    contended: dict = field(default_factory=dict)
    apart_s: float = 0.0
    uncovered_s: float | None = None


def fit(train: list[Episode], read_s: float) -> dict[str, tuple[float, float, float, int]]:
    """Per step, the (p10, p50, p90) of measured/prior over the training episodes, and their count."""
    out = {}
    for step in PREDICTED:
        xs = [e.measured[step] / p for e in train if (p := priors(e.inputs, read_s, e.refine)[step]) > 0]
        if xs:
            out[step] = (*eta.band(xs), len(xs))
    return out


def predict(inp: Inputs, refine: bool, rates: dict, read_s: float) -> dict[str, tuple[float, float]]:
    """(p50, p90) seconds per step: the prior times the training ratio."""
    pri = priors(inp, read_s, refine)
    return {s: (rates[s][1] * pri[s], max(rates[s][1], rates[s][2]) * pri[s]) for s in PREDICTED if s in rates}


def held_out(episodes: list[Episode], i: int, read_s: float) -> dict:
    target, train = episodes[i], episodes[:i] + episodes[i + 1:]
    pred = predict(target.inputs, target.refine, fit(train, read_s), read_s)
    got = sum(target.measured[s] for s in STEPS)
    p50 = sum(v[0] for v in pred.values())
    return {"episode": target.name, "pred": pred, "measured": target.measured, "pred_s": p50,
            "p90_s": sum(v[1] for v in pred.values()), "measured_s": got, "error": (p50 - got) / got if got else math.inf}


def leave_one_out(episodes: list[Episode], read_s: float) -> list[dict]:
    return [held_out(episodes, i, read_s) for i in range(len(episodes))]


def verdict(results: list[dict], tol: float = TOLERANCE, need: int = NEED) -> dict:
    within = sum(1 for r in results if abs(r["error"]) <= tol)
    return {"passed": len(results) >= HELD_OUT and within >= need, "within": within, "n": len(results)}


def step_error(r: dict, step: str) -> float | None:
    """(predicted p50 - measured) / measured for one held-out step; None where it measured nothing."""
    got = r["measured"][step]
    return (r["pred"].get(step, (0.0, 0.0))[0] - got) / got if got else None


def step_errors(results: list[dict], steps=PREDICTED, tol: float = TOLERANCE) -> dict[str, dict]:
    """Per step, each held-out episode's signed error, and on how many of the measured ones it is within tol."""
    out = {}
    for s in steps:
        errs = {r["episode"]: step_error(r, s) for r in results}
        known = [e for e in errs.values() if e is not None]
        out[s] = {"errors": errs, "n": len(known), "within": sum(1 for e in known if abs(e) <= tol)}
    return out


def step_mae(results: list[dict], steps=PREDICTED) -> dict[str, float]:
    """Per step, the mean |predicted p50 - measured| over the held-out episodes, in minutes."""
    return {s: statistics.fmean(abs(r["pred"].get(s, (0.0, 0.0))[0] - r["measured"][s]) for r in results) / 60
            for s in steps}


# ---- the unmeasured steps (R16) ----

@dataclass(frozen=True)
class Gap:
    name: str
    step: str
    why: str
    measured: bool
    p90_s: float | None
    source: str


MASTER_EYE_SINCE = "2026-10-21T02:04:50"
"""b008100: the master eye's read cache keyed on the take's bytes and frame (its current form)."""


def refine_p90_s(target: Inputs) -> float:
    """The first-pass refine's p90 wall: each planned face at the measured line plus its largest residual,
    times the wall/GPU ratio the real first pass took (FACE.md: 927 s over 652 s, pipelined)."""
    c = costs()
    gpu = sum(n * (refine_face_s(f) + float(c["refine_face"]["max_abs_residual_s"]))
              for n, f in zip(target.faces, target.frames))
    return gpu * float(c["refine_wall_per_gpu_s"])


def _refine_gap(first: list[dict], target: Inputs) -> Gap:
    seen = refine_clocked(first)
    return Gap("first-pass face refine", "09", "no first-pass refine row carries its GPU clock (907616f)",
               seen, refine_p90_s(target), "measured on the real engine 2026-10-21 (measured_costs.json: the refine "
               "line + its largest residual per planned face, x the first pass's wall/GPU ratio)")


def _tiny_chain(every: list[dict]) -> float | None:
    """The tiny-face rung's seconds wherever it ran: its takes row and the rows after it to the next mark."""
    for i, r in enumerate(every):
        if r["stage"] == "takes" and "--tiny-face" in (r.get("note") or ""):
            rest = next((j for j in range(i + 1, len(every)) if every[j]["stage"].startswith("step_")), len(every))
            return sum(float(x.get("seconds") or 0) for x in every[i:rest])
    return None


def _tiny_gap(first: list[dict], every: list[dict]) -> Gap:
    seen = any(r["stage"] == "takes" and "--tiny-face" in (r.get("note") or "") for r in first)
    return Gap("tiny-face 1024 rung", "09", "the rung ran only inside a repair window", seen, _tiny_chain(every),
               "the one recorded rung chain (any window)")


def _eye_gap(first: list[dict], every: list[dict]) -> Gap:
    seen = any(r["stage"] == "master_eye" and str(r["started"]) >= MASTER_EYE_SINCE for r in first)
    xs = [float(r.get("seconds") or 0) for r in every if r["stage"] == "master_eye"]
    return Gap("master eye (b008100)", "11", "no master_eye row since its cache moved to the take's bytes", seen,
               eta.band(xs)[2] if xs else None, "p90 of every recorded master_eye row (any window)")


def gaps(first: list[dict], every: list[dict], target: Inputs, uncovered: list[float]) -> list[Gap]:
    """The declared steps the current code runs that the training rows may not measure."""
    publish = any(r["stage"] == "publish" and float(r.get("seconds") or 0) > 0 for r in first)
    return [_refine_gap(first, target), _tiny_gap(first, every), _eye_gap(first, every),
            Gap("GPU whisper worker", "11", "no row times the worker (b8c6ba1)", False, None, "none: unbounded"),
            Gap("publish (step 13)", "13", "step 13 stamps a mark, never a timed row", publish,
                step_caps.step_wall_s("13"), "step 13's wall cap (stages.yaml)"),
            Gap("uncovered clock (drive overhead + killed runs)", "all", "the predictor has no term for it", False,
                max(uncovered) if uncovered else None, "clock.jsonl less every timing row (clocked episodes)")]


def unseen_steps(train: list[Episode]) -> list[Gap]:
    """A predicted step no training episode measured a second of: found by the map, not declared."""
    return [Gap(f"step {s} (no training row)", s, "no training episode measured it", False, None, "none")
            for s in PREDICTED if not any(e.measured.get(s) for e in train)]


def share_denominator(found: list[Gap], p90_total: float) -> float:
    """The predicted p90 plus each unmeasured bound once (an unclocked refine is out of the p90: its Gap only)."""
    return p90_total + sum(g.p90_s or 0.0 for g in found if not g.measured)


def shares(found: list[Gap], p90_total: float) -> list[tuple[Gap, float | None]]:
    """Each Gap's share of the p90: its bound over the predicted p90 plus every unmeasured bound."""
    denom = share_denominator(found, p90_total)
    return [(g, None if g.p90_s is None else (0.0 if g.measured else g.p90_s / denom)) for g in found]


def provable(shared: list[tuple[Gap, float | None]]) -> bool:
    return all(g.measured or (s is not None and s <= SHARE_LIMIT) for g, s in shared)


# ---- the base rate and the result rows ----

def base_rate(episodes: list[Episode]) -> tuple[int, int]:
    """(clocked episodes whose first master came under the owner's 6 h, clocked episodes)."""
    clocked = [e for e in episodes if e.clock_s is not None]
    return sum(1 for e in clocked if e.clock_s < OWNER_LIMIT_SECONDS), len(clocked)


def _row(check: str, kind: str, passed: bool, k: int, n: int, evidence: list[str], **extra) -> dict:
    return {"check": check, "question": "Q5", "passed": passed, "n_points": n, "n_distinct": n, "n_pass": k,
            "evidence": evidence, "match_classes": [], "instrument": "timing.jsonl", "instrument_state": "n/a",
            "kind": kind, "clock": "measured", **extra}


def result_rows(results: list[dict], shared: list[tuple[Gap, float | None]], base: tuple[int, int],
                episodes: list[Episode]) -> list[dict]:
    """The rows confidence.py reads: the back-test, one per Gap, and the base rate."""
    evidence = [p for e in episodes for p in e.evidence]
    v = verdict(results)
    rows = [_row("time_backtest_loo", "quality", v["passed"], v["within"], v["n"], evidence,
                 errors={r["episode"]: round(r["error"], 4) for r in results})]
    rows += [_row(f"unmeasured:{g.name}", "gap", g.measured or (s is not None and s <= SHARE_LIMIT),
                  int(g.measured), 1, evidence, p90_s=g.p90_s, p90_share=s, source=g.source) for g, s in shared]
    return rows + [_row("base_rate_under_6h", "baseline", base[0] == base[1] and base[1] > 0, base[0], base[1],
                        evidence)]


def ep02_row(p90_s: float, uncovered_s: float | None, evidence: list[str]) -> dict:
    """AUDIT A6: ep02's predicted p90 clock to the first master (the step p90s plus the uncovered-clock bound)
    against the owner's 6 h.  A PREDICTION (clock `predicted`), so a mechanism row and the map's predictor."""
    total = None if uncovered_s is None else p90_s + uncovered_s
    said = ("uncovered-clock bound unknown" if total is None else
            f"predicted p90 clock {total / 3600:.2f} h = steps {p90_s / 3600:.2f} h + uncovered {uncovered_s / 3600:.2f} h")
    return {**_row("ep02_p90_clock", "mechanism", total is not None and total < OWNER_LIMIT_SECONDS, 0, 1, evidence),
            "n_pass": int(total is not None and total < OWNER_LIMIT_SECONDS), "clock": "predicted",
            "detail": f"{said} against {OWNER_LIMIT_SECONDS / 3600:.0f} h"}


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
