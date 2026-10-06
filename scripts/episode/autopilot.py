#!/usr/bin/env python
"""The autopilot: the supervisor that launches, watches, and never stops silently.

    uv run --no-sync python scripts/episode/autopilot.py run  [--book <codex>] [--every 30]
    uv run --no-sync python scripts/episode/autopilot.py tick  --book <codex>      one pass, prints status
    uv run --no-sync python scripts/episode/autopilot.py status [--book <codex>]
    uv run --no-sync python scripts/episode/autopilot.py install [--every 5] [--book <codex>]
    uv run --no-sync python scripts/episode/autopilot.py uninstall | pause | resume
    uv run --no-sync python scripts/episode/autopilot.py retry N | park N --why "..."

Decision 2026-10-06 (architecture/decisions/2026-10-06_autopilot_and_brain.md):
the interactive session that watched a run, read a deferral and relaunched was
the one thing that ended; so the lifetime lives here, in Python, re-armed by
Task Scheduler (`install`), and every tick is a function of disk: `gather`
reads the ledgers, `studio.autopilot.derive` names the state, `act` takes ONE
action -- launch, cure, wait, restart the engine, call the brain, park, note a
publish, or say the series is complete.  PARKED is a record, never a wait; the
series moves to N+1 on the same tick.  Telegram speaks only on PUBLISHED,
PARKED, SERIES_COMPLETE, and a tree dirty past six hours.

Every outward call (Popen, the process table, git, the engine, the brain, the
work-orders desk, Telegram) is a `Deps` field, so the tests inject fakes and
spend nothing.  The pure core (`studio.autopilot`), the engine recipes
(`studio.engine_ops`) and the brain (`studio.brain`) are imported lazily where
they are used.  Nothing written under `library/` holds an absolute path.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio.command_center import procs  # noqa: E402

ProcRow = procs.ProcInfo
LIBRARY = ROOT / "library"
TASK = "visurena-autopilot"
ENGINE_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
HUNG_S = 3600.0
"""A run log quiet this long while /queue shows the same prompt is a hung
engine (memory: run 18 lost 11 h to a Qwen3-VL read nobody killed)."""
TREE_TOLD_S = 6 * 3600
DEAD_BEAT_S = 600
BRAIN_TIMEOUT_S = 45 * 60
BRAIN_ATTEMPTS = 3
ENGINE_RESTARTS = 2
LOG_LINES = 40
log = logging.getLogger("autopilot")


# ---- outward calls, injectable ------------------------------------------------

class Lazy:
    """A module imported on first attribute read, so a lane not yet on disk
    does not stop the CLI from loading (or its tests from running)."""

    def __init__(self, module: str):
        self._module = module

    def __getattr__(self, name: str):
        return getattr(importlib.import_module(self._module), name)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def notify(text: str) -> None:
    """Telegram through drive.py's tested path; a failed send is never fatal there."""
    from scripts.episode import drive
    drive.notify(text)


def drive_argv(codex: str, n: int) -> list[str]:
    return ["uv", "run", "--no-sync", "python", "scripts/episode/drive.py", codex, str(n)]


def chapters_of(book: Path) -> list[int]:
    from scripts.episode import titles_batch
    return titles_batch.chapters_of(book)


def spent_usd(codex: str, n: int) -> float:
    """The episode's media spend from the usage table; 0.0 when the table is absent."""
    import sqlite3
    from studio import db, spend
    try:
        return float(spend.unit_spent(db.get_connection(), codex, f"ep{n:02d}") or 0.0)
    except (sqlite3.Error, OSError):
        return 0.0


def parse_order(order: Any) -> tuple[str, str | None]:
    """A cure as the desk takes it: `"redo 08"` or `{"kind": .., "step_id": ..}`."""
    if isinstance(order, dict):
        return str(order.get("kind")), order.get("step_id")
    words = str(order).split()
    return words[0], (words[1] if len(words) > 1 else None)


def cure_order(codex: str, n: int, order: Any) -> int:
    """One orders row addressed to the episode unit, by the autopilot."""
    from studio import db, work_orders
    kind, step = parse_order(order)
    return work_orders.order(db.get_connection(), kind, "unit", codex_id=codex, stage="episode",
                             unit=f"ep{n:02d}", step_id=step, by="autopilot")


def core_derive(signals, n: int):
    """Lane A's pure `derive`, imported when first needed."""
    return importlib.import_module("studio.autopilot").derive(signals, n)


def core_next_unit(chapters: list[int], uploads: list[dict], parked: list[dict], last: int) -> int | None:
    return importlib.import_module("studio.autopilot").next_unit(chapters, uploads, parked, last)


def brain_evidence(home: Path) -> tuple[list[str], list[dict]]:
    """What the brief reads off disk: the aside's fault notes, the last learnings rows."""
    aside = read_json(home / "plan.deferred.json", {}) or {}
    faults = [str(f.get("note", f)) for f in aside.get("faults", []) if isinstance(f, (dict, str))]
    return faults[-12:], rows_of(home / "learnings.jsonl")[-5:]


def brain_prompt(core, book: Path, n: int, packet: dict) -> str:
    """`studio.brain.brief` from the packet and the episode home, relative paths only."""
    home = home_of(book, n)
    faults, learnings = brain_evidence(home)
    tail = " | ".join(str(packet.get(k, "")) for k in ("reason", "last_line") if packet.get(k))
    return core.brief(packet.get("home", f"episodes/ep{n:02d}"), tail, faults, learnings,
                      float(packet.get("media_spent_usd") or 0.0), ["redo", "retry", "requeue"])


def verdict_doc(verdict: Any, meta: Any) -> dict:
    """The brain's Verdict (response, reason, ...) as the dict the supervisor judges (verdict, why, ...)."""
    raw = verdict.model_dump() if hasattr(verdict, "model_dump") else dict(verdict)
    doc = {"verdict": raw.get("response") or raw.get("verdict"), "why": raw.get("reason") or raw.get("why", ""),
           "commit": raw.get("commit"), "order": raw.get("order"), "finding_row": raw.get("finding_row", ""),
           "proposed_diff": raw.get("proposed_diff", "")}
    doc["meta"] = meta if isinstance(meta, dict) else str(meta)
    return doc


def ledger_conn():
    """The studio db for the brain's spend rows; None when it cannot open (never fatal)."""
    try:
        from studio import db
        return db.get_connection()
    except Exception:
        return None


def ledger_brain(core, codex: str, n: int, meta: Any) -> None:
    """One `stage='brain'` usage row for the episode's unit (the first live turn
    left none, 2026-10-06); a ledger failure never loses the verdict."""
    conn = ledger_conn()
    if conn is None or not isinstance(meta, dict):
        return
    try:
        core.ledger(conn, codex, f"ep{n:02d}", "triage", getattr(core, "TRIAGE_MODEL", "claude-sonnet-5-5"), 0.0, meta)
    except Exception as why:
        log.warning("brain ledger failed: %s", scrub(repr(why)))


def run_brain(book: Path, codex: str, n: int, packet: dict, attempt: Path) -> dict:
    """One triage session of the brain under the 45-min leash; its verdict as a dict."""
    core = importlib.import_module("studio.brain")
    prompt = brain_prompt(core, book, n, packet)
    verdict, meta = asyncio.run(asyncio.wait_for(core.turn(prompt, core.triage_options(ROOT)), BRAIN_TIMEOUT_S))
    ledger_brain(core, codex, n, meta)
    if hasattr(core, "allowed") and hasattr(verdict, "model_dump"):
        verdict = core.allowed(verdict, core.episode_step_ids())
    return verdict_doc(verdict, meta)


@dataclass
class Deps:
    popen: Callable = subprocess.Popen
    drive_argv: Callable[[str, int], list[str]] = drive_argv
    procs: Callable[[], list] = procs.list_processes
    git: Callable[..., str] = git
    engine: Any = field(default_factory=lambda: Lazy("studio.engine_ops"))
    notify: Callable[[str], None] = notify
    derive: Callable = core_derive
    next_unit: Callable = core_next_unit
    chapters: Callable[[Path], list[int]] = chapters_of
    brain: Callable = run_brain
    order: Callable[[str, int, Any], int] = cure_order
    spent_usd: Callable[[str, int], float] = spent_usd
    now: Callable[[], float] = time.time
    sleep: Callable[[float], None] = time.sleep
    pid: int = field(default_factory=os.getpid)
    root: Path = LIBRARY / ".autopilot"


def default_deps() -> Deps:
    return Deps()


# ---- files -----------------------------------------------------------------------

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def scrub(text: str) -> str:
    """No absolute path leaves this process into a ledger: the repo root
    becomes `.` in either slash style."""
    root = str(ROOT)
    return str(text).replace(root, ".").replace(root.replace("\\", "/"), ".")


def rows_of(path: Path) -> list[dict]:
    """A jsonl file as rows; blank and broken lines are skipped, not fatal."""
    if not Path(path).exists():
        return []
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def append_row(path: Path, row: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_atomic(path: Path, doc: Any) -> Path:
    """Write beside, then replace: a reader never sees half a status."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    return path


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def paths_of(book: Path) -> SimpleNamespace:
    folder = Path(book) / "autopilot"
    return SimpleNamespace(dir=folder, status=folder / "status.json", events=folder / "events.jsonl",
                           series=folder / "series.json", parked=folder / "parked.jsonl", stop=folder / "STOP")


def home_of(book: Path, n: int) -> Path:
    return Path(book) / "episodes" / f"ep{n:02d}"


def event(book: Path, row: dict) -> dict:
    """One audit row in events.jsonl, scrubbed, and the same line in the log."""
    row = {"ts": utc_now(), **{k: (scrub(v) if isinstance(v, str) else v) for k, v in row.items()}}
    append_row(paths_of(book).events, row)
    log.info("%s", json.dumps(row, ensure_ascii=False))
    return row


def load_series(book: Path, codex: str, chapters: Callable[[Path], list[int]]) -> dict:
    """The goal: first..last chapter and the pause flag; made from the
    chapters once, read from disk after."""
    path = paths_of(book).series
    if (doc := read_json(path)) and doc.get("last"):
        return doc
    numbers = chapters(book) or [1]
    doc = {"book": codex, "first": min(numbers), "last": max(numbers), "paused": False}
    write_atomic(path, doc)
    return doc


def set_paused(book: Path, codex: str, paused: bool) -> dict:
    doc = load_series(book, codex, lambda b: chapters_of(b))
    doc["paused"] = paused
    write_atomic(paths_of(book).series, doc)
    event(book, {"event": "pause" if paused else "resume"})
    return doc


# ---- locks and the heartbeat -----------------------------------------------------

def write_lock(path: Path, body: dict) -> bool:
    """O_EXCL: the first writer wins, a second gets False and launches nothing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(body, f)
    return True


def clear_stale_lock(book: Path, codex: str, n: int, deps: Deps, rows: list) -> bool:
    """A gpu.lock whose drive is not in the process table is removed and logged."""
    lock = deps.root / "gpu.lock"
    if not lock.exists() or procs.find_drive(rows, codex, n) is not None:
        return False
    body = read_json(lock, {})
    lock.unlink()
    event(book, {"event": "stale_lock", "episode": n, "drive_pid": body.get("drive_pid")})
    return True


def claim_supervisor(deps: Deps) -> bool:
    """Our pid into supervisor.lock, unless a live other instance holds it."""
    lock = deps.root / "supervisor.lock"
    held = read_json(lock, {}).get("pid")
    alive = {p.pid for p in deps.procs()}
    if held and held != deps.pid and held in alive:
        return False
    lock.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(lock, {"pid": deps.pid, "started": utc_now()})
    return True


def heartbeat(deps: Deps, tick_no: int, state: str, n: int | None) -> None:
    write_atomic(deps.root / "heartbeat.json", {"ts": deps.now(), "tick": tick_no, "state": state, "episode": n})


def adopt(book: Path, deps: Deps) -> None:
    """A new instance that finds a heartbeat older than ten minutes says the
    last one died, once, in the event log."""
    beat = read_json(deps.root / "heartbeat.json", {})
    age = deps.now() - float(beat.get("ts") or deps.now())
    if beat and age > DEAD_BEAT_S:
        event(book, {"event": "supervisor_died_at", "heartbeat_age_s": round(age), "tick": beat.get("tick")})


# ---- signals --------------------------------------------------------------------

def log_tail_of(home: Path) -> str:
    logs = sorted(Path(home).glob("drive_run*.log"))
    if not logs:
        return ""
    text = logs[-1].read_text(encoding="utf-8", errors="replace")
    return scrub("\n".join(text.strip().splitlines()[-LOG_LINES:]))


def quiet_s(home: Path, now: float) -> float | None:
    """Seconds since the newest run log grew; None when there is no log."""
    logs = sorted(Path(home).glob("drive_run*.log"))
    return max(0.0, now - logs[-1].stat().st_mtime) if logs else None


def brain_attempts_of(home: Path) -> list[Path]:
    return sorted((Path(home) / "brain").glob("attempt_*.json"))


def signals_of(fields: dict):
    """The contract's `Signals` when lane A is on disk, else the same fields
    as a namespace (the fakes' derive reads attributes either way)."""
    try:
        from studio.autopilot import Signals
        return Signals(**fields)
    except (ImportError, TypeError):
        return SimpleNamespace(**fields)


def retried_since(book: Path, n: int, drive_rows: list[dict]) -> bool:
    """A `retry` event for N later than the drive ledger's last `end` row: the
    old failure is history, not today's state (ep20, 2026-10-06)."""
    retries = [r.get("ts", "") for r in rows_of(paths_of(book).events)
               if r.get("event") == "retry" and r.get("episode") == n]
    ends = [r.get("ts", "") for r in drive_rows if r.get("event") == "end"]
    if not retries or not drive_rows:
        return False
    return not ends or when(retries[-1]) > when(ends[-1])


def when(stamp: str) -> datetime:
    """An ISO stamp as a datetime; an unreadable one sorts first."""
    try:
        return datetime.fromisoformat(str(stamp))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def gather(book: Path, codex: str, n: int, deps: Deps, series: dict):
    """Every signal `derive` reads, off disk and the process table, nothing spent."""
    home, rows = home_of(book, n), deps.procs()
    clear_stale_lock(book, codex, n, deps, rows)
    drive_rows = rows_of(home / "drive.jsonl")
    if retried_since(book, n, drive_rows):
        drive_rows = []                      # a retry newer than the last end row: launch again
    ends = [r for r in drive_rows if r.get("event") == "end"]
    attempts = brain_attempts_of(home)
    from studio import run_budget
    return signals_of({
        "drive_rows": drive_rows, "exit_code": ends[-1].get("code") if ends else None,
        "lock": read_json(deps.root / "gpu.lock"), "proc_alive": procs.find_drive(rows, codex, n) is not None,
        "uploads_rows": rows_of(Path(book) / "uploads.jsonl"), "parked_rows": rows_of(paths_of(book).parked),
        "home_files": sorted(p.name for p in home.iterdir()) if home.exists() else [],
        "log_tail": log_tail_of(home), "porcelain": deps.git("status", "--porcelain"),
        "engine_up": bool(deps.engine.alive(ENGINE_URL)), "clock_spent_s": run_budget.spent_before(home),
        "brain_attempts": len(attempts), "brain_verdict": read_json(attempts[-1]) if attempts else None,
        "paused": bool(series.get("paused")) or paths_of(book).stop.exists(),
        "head_sha": deps.git("rev-parse", "HEAD").strip(), "media_spent_usd": deps.spent_usd(codex, n)})


# ---- the actions ---------------------------------------------------------------

def launch(book: Path, codex: str, n: int, deps: Deps, why: str) -> dict:
    """ONE detached drive.py, its stdout to drive_launchNN.log, and the gpu.lock."""
    home = home_of(book, n)
    home.mkdir(parents=True, exist_ok=True)
    k = len(list(home.glob("drive_launch*.log"))) + 1
    out = (home / f"drive_launch{k:02d}.log").open("w", encoding="utf-8")
    flags = (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS) if sys.platform == "win32" else 0
    proc = deps.popen(deps.drive_argv(codex, n), cwd=ROOT, env={**os.environ, "DRIVE_QUIET": "1"},
                      stdout=out, stderr=subprocess.STDOUT, creationflags=flags)
    body = {"drive_pid": proc.pid, "started": utc_now(), "book": codex, "episode": n}
    if not write_lock(deps.root / "gpu.lock", body):
        event(book, {"event": "lock_held", "episode": n, "drive_pid": proc.pid})
    event(book, {"event": why, "episode": n, "drive_pid": proc.pid, "log": f"episodes/ep{n:02d}/drive_launch{k:02d}.log"})
    return {"action": why, "state": "RUNNING", "drive_pid": proc.pid}


def running_id(queue: Any) -> str | None:
    """The prompt /queue says is running, in whichever shape engine_ops hands it."""
    if isinstance(queue, dict):
        queue = queue.get("queue_running") or []
    if isinstance(queue, (list, tuple)):
        if not queue:
            return None
        head = queue[0]
        return str(head[1]) if isinstance(head, (list, tuple)) and len(head) > 1 else str(head)
    return str(queue) if queue else None


def hung(book: Path, n: int, deps: Deps) -> bool:
    """Quiet past HUNG_S while /queue has shown the same prompt that long."""
    quiet = quiet_s(home_of(book, n), deps.now())
    prompt = running_id(deps.engine.queue(ENGINE_URL))
    seen, path = read_json(deps.root / "engine.json", {}), deps.root / "engine.json"
    if prompt is None or quiet is None:
        return False
    if seen.get("prompt_id") != prompt:
        write_atomic(path, {"prompt_id": prompt, "since": deps.now()})
        return False
    return quiet >= HUNG_S and deps.now() - float(seen.get("since", deps.now())) >= HUNG_S


def restarts_of(book: Path, n: int) -> int:
    return sum(1 for r in rows_of(paths_of(book).events) if r.get("event") == "engine_restart" and r.get("episode") == n)


def rescue_engine(book: Path, codex: str, n: int, deps: Deps) -> dict:
    """Kill the run tree, kill and restart ComfyUI, relaunch; past the cap the
    tree is still killed (the GPU is freed for N+1) and the episode parks."""
    before, rows = restarts_of(book, n), deps.procs()
    deps.engine.kill_run_tree(rows, codex, n)
    deps.engine.kill_engine(rows)
    lock = deps.root / "gpu.lock"
    if lock.exists():
        lock.unlink()
    deps.engine.restart()
    event(book, {"event": "engine_restart", "episode": n})
    if before >= ENGINE_RESTARTS:
        return park(book, codex, n, "engine", {"restarts": before}, deps)
    return launch(book, codex, n, deps, "relaunch")


def park(book: Path, codex: str, n: int, reason: str, evidence: dict, deps: Deps) -> dict:
    """The row, once; the Telegram, once; the series moves on the next tick."""
    parked = paths_of(book).parked
    if any(r.get("episode") == n for r in rows_of(parked)):
        return {"action": "parked_already", "state": "PARKED"}
    sha = deps.git("rev-parse", "HEAD").strip()[:8]
    row = {"ts": utc_now(), "episode": n, "sha": sha, "reason": scrub(reason),
           "evidence": json.loads(scrub(json.dumps(evidence, ensure_ascii=False)))}
    append_row(parked, row)
    event(book, {"event": "parked", "episode": n, "reason": reason})
    deps.notify(f"ep{n:02d} PARKED ({scrub(reason)}) on {sha}; the series moves on")
    return {"action": "park", "state": "PARKED"}


def note_published(book: Path, n: int, uploads: list[dict], deps: Deps) -> dict:
    """One event and one Telegram with the youtu.be URL, the first time only."""
    if any(r.get("event") == "published" and r.get("episode") == n for r in rows_of(paths_of(book).events)):
        return {"action": "published_already", "state": "PUBLISHED"}
    rows = [r for r in uploads if r.get("episode") == n and r.get("privacy") == "public"]
    video = rows[-1].get("video_id", "") if rows else ""
    event(book, {"event": "published", "episode": n, "video_id": video})
    deps.notify(f"ep{n:02d} PUBLISHED https://youtu.be/{video}")
    return {"action": "published", "state": "PUBLISHED"}


def complete(book: Path, series: dict, parked: list[dict], uploads: list[dict], deps: Deps) -> dict:
    """SERIES_COMPLETE: one Telegram, then the loop idles at its ticks."""
    if not any(r.get("event") == "complete" for r in rows_of(paths_of(book).events)):
        public = sorted({r["episode"] for r in uploads if r.get("privacy") == "public"})
        event(book, {"event": "complete", "published": len(public), "parked": [r["episode"] for r in parked]})
        deps.notify(f"SERIES COMPLETE {len(public)}/{series['last']} public; parked: {[r['episode'] for r in parked]}")
    return {"action": "complete", "state": "COMPLETE"}


def brain(book: Path, codex: str, n: int, derived, signals, deps: Deps) -> dict:
    """One brain attempt; the verdict FILE and git are trusted, never the prose."""
    home = home_of(book, n)
    attempt = home / "brain" / f"attempt_{len(brain_attempts_of(home)) + 1:02d}.json"
    heartbeat(deps, -1, "BRAIN_RUNNING", n)
    event(book, {"event": "brain", "episode": n, "attempt": attempt.name, "reason": str(derived.reason)})
    try:
        doc = deps.brain(book, codex, n, dict(derived.packet or {}), attempt)
    except Exception as why:                                   # the leash: a dead brain is an attempt
        doc = {"verdict": "error", "why": scrub(repr(why))}
    if not attempt.exists():
        write_atomic(attempt, doc)
    return judge_verdict(book, codex, n, read_json(attempt, {}), deps)


def judge_verdict(book: Path, codex: str, n: int, verdict: dict, deps: Deps) -> dict:
    """relaunch only on a clean tree at the commit the file names; park parks."""
    said, head = str(verdict.get("verdict")), deps.git("rev-parse", "HEAD").strip()
    from studio import episode_drive
    clean = not episode_drive.dirty(deps.git("status", "--porcelain"))
    if said == "park":
        return park(book, codex, n, f"brain: {verdict.get('why', '')}", verdict, deps)
    if said == "relaunch" and clean and str(verdict.get("commit")) == head:
        event(book, {"event": "brain_relaunch", "episode": n, "commit": head[:8]})
        return {"action": "brain_relaunch", "state": "IDLE"}
    if said in ("retry", "cure") and clean:
        return triage_action(book, codex, n, said, verdict, deps)
    event(book, {"event": "brain_rejected", "episode": n, "verdict": said, "clean": clean})
    return {"action": "brain_rejected", "state": "NEEDS_BRAIN"}


def triage_action(book: Path, codex: str, n: int, said: str, verdict: dict, deps: Deps) -> dict:
    """A triage answer short of a fix: retry relaunches; cure places the desk order first."""
    if said == "cure" and verdict.get("order"):
        deps.order(codex, n, verdict["order"])
    event(book, {"event": f"brain_{said}", "episode": n, "order": verdict.get("order")})
    return {"action": f"brain_{said}", "state": "IDLE"}


def wait_tree(book: Path, deps: Deps) -> dict:
    """The one deliberate wait: the owner's own edit; told once after six hours."""
    waits = [r for r in rows_of(paths_of(book).events) if r.get("event") in ("wait_tree", "tree_told")]
    if not waits or waits[-1].get("event") == "tree_told":
        event(book, {"event": "wait_tree", "since": deps.now()})
        return {"action": "wait_tree", "state": "WAIT_TREE"}
    if deps.now() - float(waits[-1].get("since", deps.now())) >= TREE_TOLD_S:
        event(book, {"event": "tree_told"})
        deps.notify("tree dirty for 6 h, autopilot waiting; commit or stash the code")
    return {"action": "wait_tree", "state": "WAIT_TREE"}


def cure(book: Path, codex: str, n: int, derived, deps: Deps) -> dict:
    deps.order(codex, n, derived.order)
    event(book, {"event": "cure", "episode": n, "order": str(derived.order)})
    return launch(book, codex, n, deps, "relaunch")


def act_idle(book: Path, codex: str, n: int, derived, signals, deps: Deps) -> dict:
    """IDLE: the engine up and no live lock -> launch; a dead engine is restarted first."""
    if not signals.engine_up:
        deps.engine.restart()
        event(book, {"event": "engine_restart", "episode": n, "why": "down"})
        return {"action": "restart_engine", "state": "IDLE"}
    if signals.lock and signals.proc_alive:
        return {"action": "wait", "state": "RUNNING"}
    return launch(book, codex, n, deps, "relaunch" if signals.drive_rows else "launch")


def act_needs_brain(book: Path, codex: str, n: int, derived, signals, deps: Deps) -> dict:
    if derived.order:
        return cure(book, codex, n, derived, deps)
    if signals.brain_attempts >= BRAIN_ATTEMPTS:
        return park(book, codex, n, "brain_exhausted", {"reason": str(derived.reason)}, deps)
    return brain(book, codex, n, derived, signals, deps)


def act(book: Path, codex: str, n: int, derived, signals, deps: Deps) -> dict:
    """ONE action per tick, by the derived state; returns the state it leaves."""
    state = getattr(derived.state, "name", str(derived.state))
    if state == "PAUSED":
        return {"action": "wait", "state": "PAUSED"}
    if state == "IDLE":
        return act_idle(book, codex, n, derived, signals, deps)
    if state == "RUNNING":
        return rescue_engine(book, codex, n, deps) if hung(book, n, deps) else {"action": "wait", "state": "RUNNING"}
    if state == "NEEDS_BRAIN":
        return act_needs_brain(book, codex, n, derived, signals, deps)
    if state == "PARKED":
        return park(book, codex, n, str(derived.reason or "parked"), {"tail": signals.log_tail[-800:]}, deps)
    if state == "PUBLISHED":
        return note_published(book, n, signals.uploads_rows, deps)
    if state == "WAIT_TREE":
        return wait_tree(book, deps)
    return {"action": "wait", "state": state}


# ---- the tick --------------------------------------------------------------------

def status_doc(book: Path, codex: str, n: int | None, derived, signals, series: dict, done: dict, deps: Deps) -> dict:
    """§5: the series, the episode, the engine and the last events; relative paths only."""
    uploads, parked = rows_of(Path(book) / "uploads.jsonl"), rows_of(paths_of(book).parked)
    beat = read_json(deps.root / "heartbeat.json", {})
    public = sorted({r["episode"] for r in uploads if r.get("privacy") == "public"})
    return {"ts": utc_now(), "supervisor_pid": deps.pid,
            "heartbeat_age_s": round(deps.now() - float(beat.get("ts") or deps.now())),
            "engine": {"up": getattr(signals, "engine_up", None), "restarts": restarts_of(book, n) if n else 0},
            "series": {"book": codex, "first": series["first"], "last": series["last"], "published": public,
                       "parked": [{"episode": r["episode"], "reason": r["reason"], "ts": r["ts"]} for r in parked],
                       "next": n, "state": "paused" if done["state"] == "PAUSED" else
                       ("complete" if n is None else "running")},
            "episode": episode_doc(n, derived, signals, done),
            "last_events": rows_of(paths_of(book).events)[-5:]}


def episode_doc(n: int | None, derived, signals, done: dict) -> dict:
    """The episode block of status.json; `done` is what `act` left behind."""
    if n is None:
        return {"n": None, "state": "COMPLETE"}
    lock = getattr(signals, "lock", None) or {}
    return {"n": n, "state": done["state"], "action": done["action"], "reason": scrub(str(derived.reason or "")),
            "drive_pid": done.get("drive_pid") or lock.get("drive_pid"), "sha": signals.head_sha[:8],
            "run": sum(1 for r in signals.drive_rows if r.get("event") == "run"),
            "clock_spent_s": round(signals.clock_spent_s), "media_spent_usd": signals.media_spent_usd,
            "brain_attempts": done["brain_attempts"]}


def tick(book: Path, codex: str, deps: Deps, tick_no: int = 0) -> dict:
    """One pass: gather -> derive -> ONE action -> status.json + heartbeat."""
    series, p = load_series(book, codex, deps.chapters), paths_of(book)
    uploads, parked = rows_of(Path(book) / "uploads.jsonl"), rows_of(p.parked)
    n = deps.next_unit(deps.chapters(book), uploads, parked, series["last"])
    if n is None:
        derived, signals = SimpleNamespace(state="COMPLETE", reason="", order=None, packet={}), SimpleNamespace(engine_up=None)
        done = complete(book, series, parked, uploads, deps)
    else:
        signals = gather(book, codex, n, deps, series)
        derived = deps.derive(signals, n)
        if signals.paused:
            derived = SimpleNamespace(state="PAUSED", reason="paused", order=None, packet={})
        done = act(book, codex, n, derived, signals, deps)
        done["brain_attempts"] = len(brain_attempts_of(home_of(book, n)))
    doc = status_doc(book, codex, n, derived, signals, series, done, deps)
    write_atomic(p.status, doc)
    heartbeat(deps, tick_no, doc["episode"]["state"], n)
    return doc


def run_loop(book: Path, codex: str, deps: Deps, every: float = 30.0, ticks: int | None = None) -> int:
    """The long-lived loop; a second instance exits 0 silently; a tick that
    raises is an event, never a stop (the one rule: silence is not a state)."""
    if not claim_supervisor(deps):
        return 0
    adopt(book, deps)
    i = 0
    while ticks is None or i < ticks:
        i += 1
        try:
            tick(book, codex, deps, i)
        except Exception as why:                               # noqa: BLE001 -- the supervisor outlives any fault
            log.exception("tick %d failed", i)
            event(book, {"event": "tick_error", "error": scrub(repr(why))})
        deps.sleep(every)
    return 0


# ---- the scheduler ---------------------------------------------------------------

def install(repo: Path, every: int, book: str | None, run: Callable[[str], int] = None,
            which: Callable[[str], str | None] = shutil.which) -> int:
    """Register the task: S4U first; refused (0x80070005 needs elevation this
    shell lacks, 2026-10-06), the same task on an Interactive logon.  uv.exe
    goes in by full path: the scheduler has no user PATH (0x80070002)."""
    run, uv = run or powershell, Path(which("uv") or "uv").as_posix()
    for logon, startup in (("S4U", True), ("Interactive", False)):
        if run(install_command(repo, every, book, logon=logon, startup=startup, uv=uv)) == 0:
            print(f"task {TASK} registered with a {logon} logon, every {every} min"
                  + ("" if startup else " (AtLogOn only: AtStartup needs elevation)"))
            return 0
    return 1


def install_command(repo: Path, every: int, book: str | None = None, logon: str = "S4U",
                    startup: bool = True, uv: str = "uv") -> str:
    """The Register-ScheduledTask line (ops §2): AtStartup + AtLogOn + every N
    min, IgnoreNew, no time limit, restart x3, wake, S4U limited.  Pure.  A
    refusal exits 5: a cmdlet error alone leaves PowerShell at 0 (2026-10-06)."""
    work = Path(repo).as_posix()
    arg = "run --no-sync python scripts/episode/autopilot.py run" + (f" --book {book}" if book else "")
    boot = "(New-ScheduledTaskTrigger -AtStartup), " if startup else ""
    return (f"$a = New-ScheduledTaskAction -Execute '{uv}' -Argument '{arg}' -WorkingDirectory '{work}'; "
            f"$rep = New-ScheduledTaskTrigger -Once -At 00:00 -RepetitionInterval "
            f"([System.Xml.XmlConvert]::ToTimeSpan('PT{every}M')); "
            f"$t = @({boot}(New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME), $rep); "
            f"$s = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew "
            f"-ExecutionTimeLimit ([System.Xml.XmlConvert]::ToTimeSpan('PT0S')) -StartWhenAvailable "
            f"-RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -WakeToRun; "
            f"$p = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType {logon} -RunLevel Limited; "
            f"try {{ Register-ScheduledTask -TaskName '{TASK}' -Action $a -Trigger $t -Settings $s -Principal $p "
            f"-Force -ErrorAction Stop | Out-Null }} catch {{ Write-Error $_; exit 5 }}; "
            f"powercfg /change standby-timeout-ac 0")


def uninstall_command() -> str:
    return f"Unregister-ScheduledTask -TaskName '{TASK}' -Confirm:$false"


def powershell(command: str) -> int:
    return subprocess.run(["powershell", "-NoProfile", "-Command", command], cwd=ROOT, check=False).returncode


# ---- the owner's acts ------------------------------------------------------------

def retry(book: Path, n: int) -> int:
    """The parked row for N is removed; the next tick picks N up (resume is idempotent)."""
    path = paths_of(book).parked
    rows = rows_of(path)
    kept = [r for r in rows if r.get("episode") != n]
    if len(kept) == len(rows):
        return 0
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept), encoding="utf-8")
    retire_brain(home_of(book, n))
    event(book, {"event": "retry", "episode": n})
    return len(rows) - len(kept)


def retire_brain(home: Path) -> Path | None:
    """A retry starts the brain's count over: the old attempts move aside, so an
    old `park` verdict is never read as today's (ep20, 2026-10-06)."""
    folder = Path(home) / "brain"
    if not folder.exists():
        return None
    n = 1 + len([p for p in Path(home).glob("brain_retired_*") if p.is_dir()])
    retired = Path(home) / f"brain_retired_{n:02d}"
    folder.rename(retired)
    return retired


def book_of(codex: str | None) -> Path | None:
    """The book folder for a codex; with none given, the one book that has a series."""
    if codex:
        hits = sorted(p for p in LIBRARY.iterdir() if p.name.startswith(codex) or p.name == codex)
        return hits[0] if hits else None
    env = os.environ.get("AUTOPILOT_BOOK")
    if env:
        return book_of(env)
    hits = sorted(p for p in LIBRARY.glob("*/autopilot/series.json"))
    return hits[0].parents[1] if len(hits) == 1 else None


def setup_logging(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if not any(isinstance(h, RotatingFileHandler) for h in log.handlers):
        handler = RotatingFileHandler(root / "autopilot.log", maxBytes=5 * 2**20, backupCount=5, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(handler)
        log.setLevel(logging.INFO)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="autopilot.py", description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("run", "tick", "status", "install", "uninstall", "pause", "resume", "retry", "park"):
        s = sub.add_parser(name)
        s.add_argument("--book", default=None)
        if name in ("retry", "park"):
            s.add_argument("n", type=int)
        if name == "park":
            s.add_argument("--why", required=True)
        if name in ("run", "install"):
            s.add_argument("--every", type=int, default=30 if name == "run" else 5)
    return p


def main(argv: list[str]) -> int:
    args = parser().parse_args(argv)
    if args.cmd == "install":
        return install(ROOT, args.every, args.book)
    if args.cmd == "uninstall":
        return powershell(uninstall_command())
    book = book_of(args.book)
    if book is None:
        raise SystemExit("say which book: --book <codex> (or AUTOPILOT_BOOK)")
    codex = book.name.split("_", 1)[0]
    deps = default_deps()
    setup_logging(deps.root)
    return dispatch(args, book, codex, deps)


def dispatch(args: argparse.Namespace, book: Path, codex: str, deps: Deps) -> int:
    if args.cmd == "run":
        return run_loop(book, codex, deps, every=float(args.every))
    if args.cmd == "tick":
        print(json.dumps(tick(book, codex, deps, 1), indent=1, ensure_ascii=False))
    elif args.cmd == "status":
        print(json.dumps(read_json(paths_of(book).status, {}), indent=1, ensure_ascii=False))
    elif args.cmd in ("pause", "resume"):
        set_paused(book, codex, args.cmd == "pause")
    elif args.cmd == "retry":
        print(f"ep{args.n:02d}: {retry(book, args.n)} parked row(s) cleared")
    elif args.cmd == "park":
        park(book, codex, args.n, f"owner: {args.why}", {}, deps)
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
