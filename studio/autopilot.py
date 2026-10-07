"""The autopilot's pure core: an episode's state is a function of disk.

Decision 2026-10-06 (architecture/decisions/2026-10-06_autopilot_and_brain.md):
the pipeline was already a Python job, `drive.py`; what stopped was the
layer above it, a Claude session that watched the log, read a deferral and
ended its turn.  ep19 sat for hours between four launches that way.  So the
lifetime lives in Python, and every tick is `derive(signals) -> Derived`
over what drive.jsonl, the lock, the process table, uploads.jsonl, the
episode home and the last log say.  Nothing here spawns, reads a socket or
writes a file (two helpers read a ledger and replace a JSON atomically);
the supervisor and the CLI own the side effects and build `Signals`.

The one invariant (tests/test_autopilot_derives_state_from_disk.py): after
any tick on any fixture the state is one of the enum and the reason is
non-empty.  Silence is never a state.  PARKED is a record, never a wait.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from studio import episode_drive, run_budget
from studio.command_center import procs, vitals

RELAUNCH_CAP = 2
"""Stops a plain retry may answer before the brain reads the stop (H3: ep19
refused three plan runs in a row before the wall; the third is a question)."""
CURE_CAP = 2
"""Cures (a `redo`, a refs run, an engine restart) per episode before the brain."""
BRAIN_ATTEMPTS = 3
"""Brain sessions per episode; the fourth stop parks it (ops §3)."""
ENGINE_RESTARTS = 2
"""ComfyUI restarts per episode before PARK(engine) (ops §2)."""
CRASHES_BEFORE_BRAIN = 3
"""A `start` row with no `end` after it is a crash; three ask the brain."""
KINDS = {"completed", "retry", "cure", "wait", "brain", "park"}


class State(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PUBLISHED = "PUBLISHED"
    NEEDS_BRAIN = "NEEDS_BRAIN"
    BRAIN_RUNNING = "BRAIN_RUNNING"
    WAIT_TREE = "WAIT_TREE"
    PARKED = "PARKED"
    PAUSED = "PAUSED"
    COMPLETE = "COMPLETE"


@dataclass
class Signals:
    """What one tick read from disk for episode N (ops §3, the signal column)."""
    drive_rows: list[dict]              # episodes/epNN/drive.jsonl
    exit_code: int | None               # drive.py's exit, when the supervisor saw it
    lock: dict | None                   # library/.autopilot/gpu.lock body
    proc_alive: bool                    # the lock's pid runs drive.py for this episode
    uploads_rows: list[dict]            # library/<book>/uploads.jsonl
    parked_rows: list[dict]             # library/<book>/autopilot/parked.jsonl
    home_files: set[str]                # names under episodes/epNN ('plan.json', ...)
    log_tail: str                       # last lines of the last drive_runNN.log
    porcelain: str                      # git status --porcelain
    engine_up: bool                     # ComfyUI answered /system_stats
    clock_spent_s: float                # timing.jsonl sum
    brain_attempts: int                 # episodes/epNN/brain/attempt_NN.json count
    brain_verdict: dict | None          # the verdict written after the last end row
    paused: bool                        # series.json paused or the STOP file
    head_sha: str | None                # git rev-parse HEAD
    media_spent_usd: float              # spend.unit_spent


@dataclass
class Derived:
    state: State
    reason: str
    order: tuple[str, str | None] | None = None
    packet: dict = field(default_factory=dict)


# --- the ledger ---------------------------------------------------------------

def crashes(drive_rows: list[dict]) -> int:
    """`start` rows with no `end` before the next `start`: the driver died
    (console closed, reboot) and nothing recorded the stop (ops §1 item 9)."""
    count, open_run = 0, False
    for row in drive_rows:
        if row.get("event") == "start":
            count += open_run
            open_run = True
        elif row.get("event") == "end":
            open_run = False
    return count + open_run


def stops(drive_rows: list[dict]) -> int:
    """`end` rows with a non-zero code: how many times this episode has
    already stopped and been answered -- the counter every cap reads."""
    return sum(1 for r in drive_rows if r.get("event") == "end" and r.get("code") not in (0, None))


def last_row(drive_rows: list[dict], event: str) -> dict | None:
    rows = [r for r in drive_rows if r.get("event") == event]
    return rows[-1] if rows else None


def exit_code(s: Signals) -> int | None:
    """The supervisor's own observation first; the ledger's last `end` row
    otherwise; None while the run has not ended -- and after a crash, whose
    `start` has no `end` (an older run's code is not this run's)."""
    if s.exit_code is not None:
        return s.exit_code
    end = last_row(s.drive_rows, "end")
    return None if end is None or crashed(s.drive_rows) else int(end.get("code", 1))


def crashed(drive_rows: list[dict]) -> bool:
    """The last `start` has no `end` after it."""
    for row in reversed(drive_rows):
        if row.get("event") == "end":
            return False
        if row.get("event") == "start":
            return True
    return False


def last_line(tail: str) -> str:
    lines = [ln.strip() for ln in (tail or "").splitlines() if ln.strip()]
    return lines[-1] if lines else ""


# --- the hand-back table -------------------------------------------------------

def _speech_gap(tail: str, home: set[str]) -> tuple[str, str, tuple | None]:
    """H6: a gap the trim left is the writer's to fix (redo 02) until takes
    exist; once rendered a recut would orphan them, so it parks."""
    if "takes" in home:
        return ("park", "speech_gap_rendered", None)
    return ("cure", "speech_gap", ("redo", "02"))


def _deferred_plan(tail: str, home: set[str]) -> tuple[str, str, tuple | None]:
    """H3 / H5: a CAST BOUND note wants the refs runner; any other plan
    deferral retries (each relaunch runs cure_aside_first for $0)."""
    if "CAST BOUND" in tail:
        return ("cure", "cast_unbound", ("refs", "04"))
    return ("retry", "plan_deferred", None)


TABLE: list[tuple[str, object]] = [
    (r"EPISODE completed", ("completed", "completed", None)),
    (r"^studio\.llm\.OverBudget:", ("park", "over_budget", None)),
    (r"REFUSED to start: the working tree is dirty", ("wait", "tree_dirty", None)),
    (r"title card could not be baked", ("brain", "title_card", None)),
    (r"HELD: ", ("wait", "held", None)),
    (r"^OWNER (\S+) \|", ("park", "escalated: {1}", None)),
    (r"DEFERRED PLAN \|", _deferred_plan),
    (r"ComfyUI's queue stayed busy", ("cure", "queue_busy", ("comfy_restart", None))),
    (r"REFUSED: the takes wait on the panels", ("cure", "takes_wait_on_panels", ("redo", "08"))),
    (r"REFUSED: qc FAIL", ("brain", "qc_fail", None)),
    (r"REFUSED: qc\.py left no report", ("retry", "qc_no_report", None)),
    (r"speech gap", _speech_gap),
    (r"REFUSED: the plan has no shots", ("park", "no_shots", None)),
    (r"REFUSED: no (panels|takes) under", ("retry", "no_render_output", None)),
    (r"INVALID VERDICT", ("park", "invalid_verdict", None)),
    (r"REFUSED: the takes want .* ceiling leaves", ("retry", "ceiling_refused_render", None)),
    (r"is NOT public", ("retry", "not_public", None)),
    (r"left no ledger row", ("retry", "no_ledger_row", None)),
    (r"vanished: the engine restarted|EngineLost|ConnectionError|RemoteDisconnected",
     ("retry", "engine_transient", None)),
    (r"DEFERRED", ("brain", "deferred: {line}", None)),
    (r"REFUSED", ("brain", "refused: {line}", None)),
    (r"Traceback", ("brain", "failed: {line}", None)),
]
"""Ordered: the first pattern that matches the tail (multiline, any line)
wins.  Each H-row of the integrator's §4 table is one entry; a value is a
(kind, reason, order) triple or a function of (tail, home) for the rows whose
answer depends on what is on disk."""


def classify(tail: str, home_files: set[str]) -> tuple[str, str, tuple[str, str | None] | None]:
    """(kind, reason, order) for a drive log's last lines; `brain` with the
    last line when no row knows the words (H15's fallback)."""
    text = tail or ""
    for pattern, answer in TABLE:
        hit = re.search(pattern, text, flags=re.MULTILINE)
        if not hit:
            continue
        if callable(answer):
            return answer(text, home_files)
        kind, reason, order = answer
        reason = reason.replace("{line}", _said(text, pattern)).replace("{1}", hit.group(1) if hit.groups() else "")
        return (kind, reason, order)
    return ("brain", "unclassified: " + (last_line(text) or "the log is empty"), None)


def _said(text: str, pattern: str) -> str:
    """The line the fault was announced on: the last line that carries the
    pattern's word, else the log's last line (a traceback ends on its error)."""
    if pattern == "Traceback":
        return last_line(text)
    lines = [ln.strip() for ln in text.splitlines() if re.search(pattern, ln)]
    said = lines[-1] if lines else last_line(text)
    return re.sub(r"^(SystemExit|RuntimeError): ", "", said)


# --- the state machine --------------------------------------------------------

def published(uploads_rows: list[dict], n: int) -> bool:
    return any(int(r.get("episode", -1)) == n and r.get("privacy") == "public" for r in uploads_rows)


def parked(parked_rows: list[dict], n: int) -> dict | None:
    rows = [r for r in parked_rows if int(r.get("episode", -1)) == n]
    return rows[-1] if rows else None


def packet(s: Signals, n: int, reason: str) -> dict:
    """What the brain and the parked row get: relative names, the ledger's
    last run row, the fault line.  Never a path with a drive letter."""
    run = last_row(s.drive_rows, "run") or {}
    return {"episode": f"ep{n:02d}", "home": f"episodes/ep{n:02d}", "reason": reason,
            "exit_code": exit_code(s), "drive_row": {k: run[k] for k in ("n", "sha", "outcome") if k in run},
            "last_line": last_line(s.log_tail), "home_files": sorted(s.home_files),
            "brain_attempts": s.brain_attempts, "clock_spent_s": s.clock_spent_s,
            "media_spent_usd": s.media_spent_usd, "crashes": crashes(s.drive_rows)}


def _idle(s: Signals, n: int, reason: str, order=None) -> Derived:
    """A launch is wanted: the one deliberate wait is the owner's own dirty
    tree (a brain that commits his WIP is worse than a pause)."""
    if episode_drive.dirty(s.porcelain):
        return Derived(State.WAIT_TREE, "tree_dirty", None, packet(s, n, reason))
    if not s.engine_up:
        reason += " (engine down)"
    return Derived(State.IDLE, reason, order, packet(s, n, reason))


def _brain(s: Signals, n: int, reason: str) -> Derived:
    """The brain is asked at most BRAIN_ATTEMPTS times; then the episode parks."""
    if s.brain_attempts >= BRAIN_ATTEMPTS:
        return Derived(State.PARKED, "brain_exhausted", None, packet(s, n, reason))
    return Derived(State.NEEDS_BRAIN, reason, None, packet(s, n, reason))


def _verdict(s: Signals, n: int) -> Derived:
    """The brain is trusted by its file and git, never its prose: relaunch only
    when the verdict names HEAD and the tree is clean after it."""
    v = s.brain_verdict or {}
    said = v.get("verdict")
    if said in ("retry", "cure"):
        # ep21 (2026-10-07): a triage answer short of a fix is a launch order; the
        # in-process tick placed any cure order already.  Re-read, it must not
        # become another brain turn.
        return _idle(s, n, f"brain_{said}")
    if said != "relaunch":
        return _brain(s, n, f"brain: {said or 'no verdict'}")
    if episode_drive.dirty(s.porcelain):
        return Derived(State.WAIT_TREE, "tree_dirty", None, packet(s, n, "brain_relaunch"))
    if v.get("commit") != s.head_sha:
        return _brain(s, n, "brain: head is not the verdict's commit")
    return _idle(s, n, "brain_relaunch")


def _over_budget(s: Signals, n: int) -> Derived:
    """The $3 media wall (ops §3): a signed plan with no aside relaunches ONCE
    (the rest of the chain is $0 local); anything else parks.  ep19 had the
    aside, so it parks."""
    signed = "plan.json" in s.home_files and "plan.deferred.json" not in s.home_files
    failed = sum(1 for r in s.drive_rows if r.get("event") == "run" and r.get("outcome") in ("failed", "overbudget"))
    if signed and failed <= 1:
        return _idle(s, n, "over_budget_signed_plan")
    return Derived(State.PARKED, "over_budget", None, packet(s, n, "over_budget"))


def _answer(s: Signals, n: int, kind: str, reason: str, order) -> Derived:
    """A classified stop becomes a state; retries and cures are capped by the
    ledger's stop count, then the brain reads the stop."""
    if kind == "completed":
        return _brain(s, n, "no_upload_row")
    if kind == "wait":
        return Derived(State.WAIT_TREE if reason == "tree_dirty" else State.PAUSED, reason, None, packet(s, n, reason))
    if kind == "park":
        return Derived(State.PARKED, reason, None, packet(s, n, reason))
    if kind == "brain":
        return _brain(s, n, reason)
    cap = RELAUNCH_CAP if kind == "retry" else CURE_CAP
    if stops(s.drive_rows) > cap:
        return _brain(s, n, f"{kind}_exhausted: {reason}")
    return _idle(s, n, reason, order)


def _ended(s: Signals, n: int) -> Derived:
    """The run ended with a code: 0 wants the public row, 1 and 2 are read
    from the log through the table, the wall and the clock first."""
    if exit_code(s) == 0:
        return _brain(s, n, "no_upload_row")
    if re.match(r"^studio\.llm\.OverBudget:", last_line(s.log_tail)):
        return _over_budget(s, n)
    return _answer(s, n, *classify(s.log_tail, s.home_files))


def derive(s: Signals, n: int) -> Derived:
    """One episode's state from one tick's signals (ops §3, every row).
    Order: the brakes and the records, the live process, the brain's verdict,
    the clock, a crash, then the exit code through the hand-back table."""
    if s.paused:
        return Derived(State.PAUSED, "paused", None, packet(s, n, "paused"))
    if published(s.uploads_rows, n):
        return Derived(State.PUBLISHED, "published", None, packet(s, n, "published"))
    if (row := parked(s.parked_rows, n)) is not None:
        return Derived(State.PARKED, f"parked: {row.get('reason', '?')}", None, packet(s, n, "parked"))
    if s.proc_alive:
        return Derived(State.RUNNING, "drive alive", None, packet(s, n, "running"))
    if s.brain_verdict is not None:
        return _verdict(s, n)
    if not s.drive_rows:
        return _idle(s, n, "launch")
    if s.clock_spent_s >= run_budget.EPISODE_CEILING_SECONDS:
        return Derived(State.PARKED, "clock_spent", None, packet(s, n, "clock_spent"))
    if crashed(s.drive_rows) and s.exit_code is None:
        return _idle(s, n, "relaunch") if crashes(s.drive_rows) < CRASHES_BEFORE_BRAIN else _brain(s, n, "crash_loop")
    return _ended(s, n)


# --- the lock, the series, the status ---------------------------------------------

def stale_lock(lock: dict | None, proc_rows: list[procs.ProcInfo], codex: str, n: int) -> bool:
    """A lock is stale when its pid is gone, runs another command line, or
    started after the lock did (a reused id after a reboot).  No lock is not
    stale: there is nothing to recover."""
    if not lock:
        return False
    mine = [p for p in proc_rows if p.pid == lock.get("drive_pid")]
    hit = procs.find_drive(mine, codex, n)
    return not vitals.pid_alive(hit, lock.get("started"))


def next_unit(chapters: list[int], uploads_rows: list[dict], parked_rows: list[dict], last: int | None) -> int | None:
    """The lowest chapter with no public upload and no parked row, capped at
    `last` (book.json episodes); None means the series is complete."""
    done = {int(r["episode"]) for r in uploads_rows if r.get("privacy") == "public"}
    done |= {int(r["episode"]) for r in parked_rows}
    left = [c for c in chapters if c not in done and (last is None or c <= last)]
    return min(left) if left else None


def status(derived: Derived, s: Signals, series: dict, now: str | None = None) -> dict:
    """status.json (ops §5): the contract keys, rewritten every tick.  `series`
    carries what the supervisor knows beyond one episode (pids, heartbeat,
    engine counters, events); every path in it is book-relative."""
    run = last_row(s.drive_rows, "run") or {}
    start = last_row(s.drive_rows, "start") or {}
    sha = str(start.get("sha") or run.get("sha") or "")[:8]
    n = int(derived.packet.get("episode", "ep00")[2:]) if derived.packet else series.get("n")
    return {
        "ts": now or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "supervisor_pid": series.get("supervisor_pid"),
        "heartbeat_age_s": series.get("heartbeat_age_s"),
        "engine": {"up": s.engine_up, "queue_running": series.get("queue_running", 0),
                   "restarts_today": series.get("restarts_today", 0)},
        "series": {k: series.get(k) for k in ("book", "first", "last", "published", "parked", "next", "state")},
        "episode": {"n": n, "state": derived.state.value, "reason": derived.reason, "order": derived.order,
                    "drive_pid": (s.lock or {}).get("drive_pid"), "sha": sha, "run": run.get("n"),
                    "step": run.get("step"), "clock_spent_s": s.clock_spent_s,
                    "media_spent_usd": s.media_spent_usd, "brain_attempts": s.brain_attempts},
        "last_events": list(series.get("last_events") or [])[-5:],
    }


# --- the two file helpers ----------------------------------------------------------

def read_jsonl(path: Path | str) -> list[dict]:
    """The rows of a ledger; a missing file is no rows, a bad line is skipped
    (a row half-written at a crash must not take the ledger with it)."""
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


def write_json_atomic(path: Path | str, doc: dict) -> Path:
    """tmp + os.replace: a reader sees the old status or the new one, never a
    torn file (the board polls status.json while the supervisor writes it)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    return path
