#!/usr/bin/env python
"""The autopilot: the supervisor that launches, watches, and never stops silently.

    uv run --no-sync python scripts/episode/autopilot.py run  [--book <codex>] [--every 30]
    uv run --no-sync python scripts/episode/autopilot.py tick  --book <codex>      one pass, prints status
    uv run --no-sync python scripts/episode/autopilot.py status [--book <codex>]
    uv run --no-sync python scripts/episode/autopilot.py install [--every 5] [--book <codex>]
    uv run --no-sync python scripts/episode/autopilot.py uninstall | resume
    uv run --no-sync python scripts/episode/autopilot.py pause [--at-boundary] [--by owner|retro] [--why ".."] [--hours H]
    uv run --no-sync python scripts/episode/autopilot.py retry N | park N --why "..."
    uv run --no-sync python scripts/episode/autopilot.py watchdog       the second task's heartbeat look
    uv run --no-sync python scripts/episode/autopilot.py may-commit     exit 3 while a drive runs on staged runtime code

Decision 2026-10-06 (architecture/decisions/2026-10-06_autopilot_and_brain.md):
the interactive session that watched a run, read a deferral and relaunched was
the one thing that ended; so the lifetime lives here, in Python, re-armed by
Task Scheduler (`install`), and every tick is a function of disk: `gather`
reads the ledgers, `studio.autopilot.derive` names the state, `act` takes ONE
action -- launch, cure, wait, restart the engine, call the brain, park, note a
publish, or say the series is complete.  PARKED is a record, never a wait; the
series moves to N+1 on the same tick.  Telegram speaks only on PUBLISHED,
PARKED, HELD_PUBLISH, SERIES_COMPLETE, a tree dirty past six hours, a pause past
its lease, a silent supervisor (the watchdog task) and an old YouTube token.

Retro 2026-10-20 (architecture/decisions/2026-10-20_ops_leases_and_watchdog.md):
a pause is a lease {by, why, expires}; a G-STANDING hold is HELD_PUBLISH, never a
park; HEAD moving under a live drive keeps this loop on its code until the drive
ends; a relaunch on moved code names the checks the new judge code invalidates.

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
ENGINE_DOWN_TICKS = 2
"""Consecutive ticks /system_stats must fail before a non-idle engine is restarted."""
COMMIT_LOW_GB = 8.0
COMMIT_HARD_GB = 3.0
"""Host commit headroom: below LOW with an empty queue the engine is told to /free;
below HARD after that, and with no drive alive, it is recycled."""
UNPARK_CAP = 2
LIVENESS_QUIET_S = 600
"""CPU flat and outputs still for this long, past 1.5x the step's cap wall: stuck."""
OVERRUN_FACTOR = 1.5
OVERRUN_FLOOR_S = 20 * 60
OVERRUNS_BEFORE_PARK = 2
OUTPUT_IGNORED = re.compile(r"(\.log|\.jsonl|\.tmp|\.lock|attempts\.json|heartbeat\.json)$")
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


def core_failed_sha(drive_rows: list[dict]) -> str | None:
    return importlib.import_module("studio.autopilot").failed_sha(drive_rows)


def episode_drive_dirty(porcelain: str) -> bool:
    return importlib.import_module("studio.episode_drive").dirty(porcelain)


def uploads_of(book: Path) -> list[dict]:
    """uploads.jsonl's chapter rows; the book video's rows are another unit."""
    return importlib.import_module("studio.autopilot").episode_rows(rows_of(Path(book) / "uploads.jsonl"))


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
    tail = "\n".join([tail, *evidence_lines(packet)])
    return core.brief(packet.get("home", f"episodes/ep{n:02d}"), tail, faults, learnings,
                      float(packet.get("media_spent_usd") or 0.0), allowed_orders())


REFUSAL = re.compile(r"REFUSED|CAP |FLAGGED|G-[A-Z]+|Traceback")
REFUSALS = 12


def evidence_lines(packet: dict) -> list[str]:
    """The brief's facts beyond the last line: which commit failed, where HEAD is
    now, the commits between, the refusals and the log's tail (P13: the brain saw
    only the wrapper's REFUSED line and parked three episodes on it)."""
    lines = [f"failed_sha={packet.get('failed_sha')} head={packet.get('head')}"]
    lines += [f"commit since: {c}" for c in packet.get("commits_since") or []]
    lines += [f"refusal: {r}" for r in packet.get("refusals") or []]
    if packet.get("log_tail"):
        lines += ["log tail:", str(packet["log_tail"])]
    return lines


def run_logs(home: Path) -> list[Path]:
    """Every launch's drive log, oldest first (drive.py numbers them, so the name sorts)."""
    return sorted(Path(home).glob("drive_run*.log"))


def refusal_lines(home: Path) -> list[str]:
    """The last REFUSALS lines of any launch log that look like a refusal, newest last."""
    found: list[str] = []
    for path in reversed(run_logs(home)):
        text = path.read_text(encoding="utf-8", errors="replace").splitlines()
        found = [scrub(ln.strip()) for ln in text if REFUSAL.search(ln)] + found
        if len(found) >= REFUSALS:
            break
    return found[-REFUSALS:]


def packet_extras(home: Path, n: int) -> dict:
    """What the brain is told on top of the derived packet: the log's tail and
    the refusal lines, read from this episode's logs."""
    return {"log_tail": log_tail_of(home), "refusals": refusal_lines(home)}


def commits_since(deps: "Deps", failed: str | None, head: str) -> list[str]:
    """`git log --oneline failed..HEAD`, newest first, at most ten."""
    if not failed or failed == head:
        return []
    try:
        return deps.git("log", "--oneline", f"{failed}..{head}").strip().splitlines()[:10]
    except Exception:                                          # noqa: BLE001 -- a stale sha must not lose the brief
        return []


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
        core.ledger(conn, codex, f"ep{n:02d}", "triage", getattr(core, "TRIAGE_MODEL", "claude-sonnet-5"), 0.0, meta)
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
    cpu_s: Callable | None = None                # (rows, codex, n) -> run-tree CPU seconds; None = no watchdog
    outputs_at: Callable[[Path], float] | None = None   # the newest artifact mtime under an episode home
    ledger: Callable[[], None] | None = None     # starts the GPU ledger beside a drive
    token_note: Callable[[], str | None] | None = None  # the YouTube token's message, None = good; None = no check


def youtube_token_note() -> str | None:
    """youtube_auth.token_note for this repo's .env and OAuth client file (retro 2026-10-20 item 8)."""
    from scripts.publish import youtube_auth
    return youtube_auth.token_note(ROOT / ".env", youtube_auth.default_blob(ROOT), time.time())


def pure():
    """The pure core, `studio.autopilot`, imported when first needed."""
    return importlib.import_module("studio.autopilot")


def newest_output(home: Path) -> float:
    """Newest mtime of any artifact under an episode home: logs, ledgers and the
    attempt heartbeat are written by a stuck step too, so they are not growth."""
    newest = 0.0
    for path in Path(home).rglob("*"):
        if path.is_file() and not OUTPUT_IGNORED.search(path.name):
            newest = max(newest, path.stat().st_mtime)
    return newest


def start_ledger() -> None:
    """One detached gpu_ledger.py, unless one already runs."""
    if any("gpu_ledger.py" in r.cmdline for r in procs.list_processes()):
        return
    flags = (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS) if sys.platform == "win32" else 0
    subprocess.Popen(["uv", "run", "--no-sync", "python", "scripts/episode/gpu_ledger.py"], cwd=ROOT,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)


def default_deps() -> Deps:
    from studio import engine_ops
    return Deps(cpu_s=engine_ops.tree_cpu_s, outputs_at=newest_output, ledger=start_ledger,
                token_note=youtube_token_note)


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


def is_paused(book: Path, series: dict | None = None) -> bool:
    """Paused is series.json `paused` OR the STOP file; either one holds the series."""
    doc = series if series is not None else read_json(paths_of(book).series, {})
    return bool(doc.get("paused")) or paths_of(book).stop.exists()


def patch_status(book: Path, paused: bool) -> dict:
    """The status file with the live pause flag laid over it (no tick needed)."""
    doc = read_json(paths_of(book).status, {})
    series = doc.setdefault("series", {})
    series["paused"] = paused
    if paused:
        series["state"] = "paused"
    elif series.get("state") == "paused":
        series["state"] = "complete" if series.get("next") is None else "running"
    return doc


def status_now(book: Path) -> dict:
    """What `status` prints: the tick's file, its pause flag read live."""
    return patch_status(book, is_paused(book))


def set_paused(book: Path, codex: str, paused: bool, by: str = "owner", why: str = "",
               hours: float | None = None, now: float | None = None, sha: str | None = None) -> dict:
    """Pause sets the flag and its lease {by, why, since, expires, sha} (retro 2026-10-20
    V7); resume clears the flag, the lease, paused_why and the STOP file.  status.json
    is rewritten at once, the next tick launches nothing while paused."""
    doc = load_series(book, codex, lambda b: chapters_of(b))
    doc["paused"] = paused
    if paused:
        doc["pause"] = pure().lease(by, why, time.time() if now is None else now, hours, sha)
        if why:
            doc["paused_why"] = why
    else:
        for key in ("paused_why", "pause"):
            doc.pop(key, None)
        paths_of(book).stop.unlink(missing_ok=True)
    write_atomic(paths_of(book).series, doc)
    event(book, {"event": "pause" if paused else "resume", "by": by, **({"why": why} if why else {})})
    if paths_of(book).status.exists():
        write_atomic(paths_of(book).status, patch_status(book, is_paused(book, doc)))
    return doc


def lease_check(book: Path, codex: str, series: dict, deps: "Deps") -> dict:
    """A pause past its lease: the autopilot's own resumes once a fix landed; any other
    is said once and stays paused (V7: an owner's pause is never lifted by code)."""
    held = series.get("pause") if series.get("paused") else None
    if not pure().lease_expired(held, deps.now()):
        return series
    if pure().may_resume(held, deps.now(), deps.git("rev-parse", "HEAD").strip()):
        return set_paused(book, codex, False, by="autopilot")
    if not any(r.get("event") == "pause_expired" and r.get("since") == held.get("since")
               for r in rows_of(paths_of(book).events)):
        event(book, {"event": "pause_expired", "by": held.get("by"), "why": held.get("why"), "since": held.get("since")})
        deps.notify(f"the series pause set by {held.get('by')} ({held.get('why') or 'no reason given'}) passed its "
                    f"lease and is still holding the GPU: `autopilot.py resume` to go on, or pause again with --hours")
    return series


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


def other_unit_running(deps: Deps, codex: str, n: int, rows: list) -> int | None:
    """The episode whose drive holds gpu.lock and is alive, when it is not N
    (2026-10-08: ep19 un-parked under ep20's run, launched beside it, and its
    bind rewrote the shared refs.json to chapter 19 under ep20's take check)."""
    body = read_json(deps.root / "gpu.lock", {})
    other = body.get("episode")
    if other is None or int(other) == n:
        return None
    return int(other) if procs.find_drive(rows, codex, int(other)) is not None else None


def clear_stale_lock(book: Path, codex: str, n: int, deps: Deps, rows: list) -> bool:
    """A gpu.lock whose drive is not in the process table is removed and logged;
    one held by another unit's LIVE drive is not stale (one unit at a time)."""
    lock = deps.root / "gpu.lock"
    if not lock.exists() or procs.find_drive(rows, codex, n) is not None:
        return False
    if other_unit_running(deps, codex, n, rows) is not None:
        return False
    body = read_json(lock, {})
    lock.unlink()
    event(book, {"event": "stale_lock", "episode": n, "drive_pid": body.get("drive_pid")})
    return True


def release_supervisor(deps: Deps) -> None:
    """Our supervisor.lock goes, so the next instance claims it at once."""
    lock = deps.root / "supervisor.lock"
    if read_json(lock, {}).get("pid") == deps.pid:
        lock.unlink(missing_ok=True)


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


def heartbeat(deps: Deps, tick_no: int, state: str, n: int | None, engine_down_ticks: int | None = None) -> None:
    """The beat, with the engine's missed-poll count carried from the last one."""
    kept = engine_down_ticks if engine_down_ticks is not None else read_json(deps.root / "heartbeat.json", {}).get("engine_down_ticks", 0)
    write_atomic(deps.root / "heartbeat.json", {"ts": deps.now(), "tick": tick_no, "state": state, "episode": n,
                                                "engine_down_ticks": kept})


WATCHDOG_TASK = TASK + "-watchdog"
WATCHDOG_EVERY = 5
"""Minutes between the second task's looks at heartbeat.json (retro 2026-10-20 item 7)."""


def told_silent(book: Path, beat: dict) -> bool:
    """This silence (this heartbeat's ts) was already said."""
    return any(r.get("event") == "supervisor_silent" and r.get("beat_ts") == beat.get("ts")
               for r in rows_of(paths_of(book).events))


def watchdog(book: Path, deps: Deps) -> dict:
    """The second task's one look: a heartbeat older than ten minutes is ONE
    `supervisor_silent` row and ONE message per silence.  ep01's 4.68 h gap was a
    Windows Update restart with nobody logged on; only `adopt` said so, afterwards."""
    beat = read_json(deps.root / "heartbeat.json", {}) or {}
    if not beat.get("ts"):
        return {"silent": False, "age_s": None}
    age = deps.now() - float(beat["ts"])
    if age <= DEAD_BEAT_S:
        return {"silent": False, "age_s": round(age)}
    if not told_silent(book, beat):
        event(book, {"event": "supervisor_silent", "heartbeat_age_s": round(age), "tick": beat.get("tick"),
                     "state": beat.get("state"), "beat_ts": beat["ts"]})
        deps.notify(f"autopilot supervisor silent for {age / 60:.0f} min (last tick {beat.get('tick')}, "
                    f"{beat.get('state')}): the PC may have restarted with nobody logged on; log on, "
                    f"or `schtasks /run /tn {TASK}`")
    return {"silent": True, "age_s": round(age)}


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


def current_verdict(attempts: list[Path], ends: list[dict]) -> dict | None:
    """The latest brain verdict, only while it is newer than the drive ledger's
    last end row: once the run it ordered has ended, it is history (ep21)."""
    if not attempts:
        return None
    if ends:
        last_end = when(ends[-1].get("ts", "")).timestamp()
        if attempts[-1].stat().st_mtime <= last_end:
            return None
    return read_json(attempts[-1])


def allowed_orders() -> list[str]:
    """What the brain may order, with the registry's step ids spelled out (ep21:
    it ordered `redo plan` and the clamp parked the episode)."""
    from studio import registry
    steps = [f"redo {s['id']} ({s.get('name', '')})".rstrip(" ()") for s in registry.steps("episode")]
    return steps + ["retry", "requeue"]


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
    verdict = current_verdict(attempts, ends)
    from studio import run_budget
    porcelain = deps.git("status", "--porcelain")
    return signals_of({
        "drive_rows": drive_rows, "exit_code": ends[-1].get("code") if ends else None,
        "lock": read_json(deps.root / "gpu.lock"), "proc_alive": deps.engine.drive_alive(rows, codex, n),
        "uploads_rows": uploads_of(book), "parked_rows": rows_of(paths_of(book).parked),
        "home_files": sorted(p.name for p in home.iterdir()) if home.exists() else [],
        "log_tail": log_tail_of(home), "porcelain": porcelain,
        "engine_up": bool(deps.engine.alive(ENGINE_URL)), "clock_spent_s": run_budget.spent_before(home),
        "brain_attempts": len(attempts), "brain_verdict": verdict,
        "paused": is_paused(book, series),
        "head_sha": deps.git("rev-parse", "HEAD").strip(), "media_spent_usd": deps.spent_usd(codex, n),
        "failed_sha": core_failed_sha(drive_rows), "code_dirty": episode_drive_dirty(porcelain),
        "standing": standing_ok(book, n)})


def standing_ok(book: Path, n: int) -> bool:
    """The owner's standing publish approval lists episode `n` of this book (G-STANDING)."""
    from studio import standing_approval
    return standing_approval.ok(book, n)


def holds_still_owed(book: Path, held: list[dict]) -> list[dict]:
    """The held masters the standing file does not list yet: a signature lifts only its own."""
    return [row for row in held if not standing_ok(book, row["episode"])]


# ---- the actions ---------------------------------------------------------------

STEP_IN_TAIL = re.compile(r"\bstep[ _]?(\d{2})\b", re.IGNORECASE)


def relaunch_allowed(step: str) -> int:
    """Relaunches a step may take: its cap-table rounds, plus the one that started it."""
    from studio import step_caps
    return sum(c.rounds for c in step_caps.table().values() if c.step == step) + 1


UNCOUNTED = ("boundary_resume", "head_moved")
"""Relaunches no step answers for: a boundary stop resumed, and a failure a newer
commit may have fixed (P13)."""


def resumed_by_owner(book: Path) -> bool:
    """The owner's `resume` is newer than the last launch: the relaunch ends a pause, dead time (P13)."""
    names = [r.get("event") for r in rows_of(paths_of(book).events)]
    last = lambda *w: max((i for i, e in enumerate(names) if e in w), default=-1)  # noqa: E731
    return last("resume") > last("launch", "relaunch")


def step_guard(book: Path, n: int, tail: str, deps: Deps, why: str = "relaunch") -> str | None:
    """Count a relaunch against the step the last log names; 'step_cap' once it is past its cap."""
    if why in UNCOUNTED or resumed_by_owner(book):
        return None
    found = STEP_IN_TAIL.findall(tail or "")
    if not found:
        return None
    from studio import step_attempts
    key = f"relaunch.{found[-1]}"
    taken = step_attempts.spend(home_of(book, n), key)
    return "step_cap" if taken > relaunch_allowed(found[-1]) else None


def launch(book: Path, codex: str, n: int, deps: Deps, why: str) -> dict:
    """ONE detached drive.py, its stdout to drive_launchNN.log, and the gpu.lock, both
    naming the sha it launched on (retro 2026-10-20 item 12).  Never while paused."""
    if is_paused(book):
        return {"action": "paused", "state": "PAUSED"}
    home, sha = home_of(book, n), deps.git("rev-parse", "HEAD").strip()
    home.mkdir(parents=True, exist_ok=True)
    k = len(list(home.glob("drive_launch*.log"))) + 1
    out = (home / f"drive_launch{k:02d}.log").open("w", encoding="utf-8")
    if why == "relaunch":
        say_moved_judges(book, n, sha, out, deps)
    flags = (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS) if sys.platform == "win32" else 0
    proc = deps.popen(deps.drive_argv(codex, n), cwd=ROOT, env={**os.environ, "DRIVE_QUIET": "1"},
                      stdout=out, stderr=subprocess.STDOUT, creationflags=flags)
    body = {"drive_pid": proc.pid, "started": utc_now(), "book": codex, "episode": n, "sha": sha}
    if not write_lock(deps.root / "gpu.lock", body):
        event(book, {"event": "lock_held", "episode": n, "drive_pid": proc.pid})
    event(book, {"event": why, "episode": n, "drive_pid": proc.pid, "sha": sha,
                 "log": f"episodes/ep{n:02d}/drive_launch{k:02d}.log"})
    token_watch(book, n, "launch", deps)
    if deps.ledger:
        deps.ledger()                         # the GPU/RAM ledger runs beside every drive (P13)
    return {"action": why, "state": "RUNNING", "drive_pid": proc.pid}


def say_moved_judges(book: Path, n: int, sha: str, out, deps: Deps) -> list[str]:
    """A relaunch on moved code names, atop its launch log and in one event, the checks
    whose judge code changed since the last drive: their verdicts on disk were signed
    by the old code (retro 2026-10-20 item 12)."""
    before = core_failed_sha(rows_of(home_of(book, n) / "drive.jsonl"))
    if not before or not sha or sha.startswith(before) or before.startswith(sha):
        return []
    try:
        checks = pure().invalidated_checks(deps.git("diff", "--name-only", f"{before}..{sha}").splitlines())
    except Exception:                                          # noqa: BLE001 -- an unknown sha names nothing
        return []
    if checks:
        out.write(f"RELAUNCH on moved code {before[:8]}..{sha[:8]}: judge code changed; the verdicts on disk "
                  f"from these checks were signed by the old code: {', '.join(checks)}\n")
        out.flush()
        event(book, {"event": "judge_code_moved", "episode": n, "from": before[:8], "to": sha[:8], "checks": checks})
    return checks


def told_this_drive(book: Path, n: int, at: str) -> bool:
    """A `youtube_token_told` row for N at `at` since N's last launch."""
    rows = rows_of(paths_of(book).events)
    starts = [i for i, r in enumerate(rows) if r.get("event") in ("launch", "relaunch") and r.get("episode") == n]
    since = rows[starts[-1] + 1:] if starts else rows
    return any(r.get("event") == "youtube_token_told" and r.get("episode") == n and r.get("at") == at for r in since)


def token_watch(book: Path, n: int, at: str, deps: Deps) -> None:
    """At launch and at render start, once each per drive: an old or failing YouTube token
    sends the consent paste link while the episode renders (retro 2026-10-20 item 8)."""
    if deps.token_note is None or told_this_drive(book, n, at):
        return
    try:
        note = deps.token_note()
    except Exception as why:                                   # noqa: BLE001 -- a check never stops a launch
        note = f"the YouTube token check failed ({scrub(repr(why))[:160]}); run youtube_auth.py --paste-link"
    if note:
        event(book, {"event": "youtube_token_told", "episode": n, "at": at})
        deps.notify(f"ep{n:02d}: {note}")


def running_id(queue: Any) -> str | None:
    """The prompt /queue says is running, in whichever shape engine_ops hands it."""
    if isinstance(queue, dict):
        queue = queue.get("queue_running") or queue.get("running_ids") or []
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


def open_step(home: Path) -> str | None:
    """The newest step with a `started` row in timing.jsonl and no closing row after it."""
    opened: dict[str, bool] = {}
    for row in rows_of(Path(home) / "timing.jsonl"):
        stage = str(row.get("stage", ""))
        if stage.startswith("step_"):
            opened[stage[5:]] = row.get("event") == "started"
    live = [step for step, is_open in opened.items() if is_open]
    return live[-1] if live else None


def cpu_quiet_s(step: str, cpu: float, deps: Deps) -> float:
    """Seconds the run tree's CPU time has not grown, kept in liveness.json across ticks."""
    path, seen = deps.root / "liveness.json", read_json(deps.root / "liveness.json", {})
    if seen.get("step") != step or cpu > float(seen.get("cpu", 0.0)) + 0.5:
        seen = {"step": step, "cpu": cpu, "changed_at": deps.now()}
        write_atomic(path, seen)
    return deps.now() - float(seen["changed_at"])


def stuck_limit_s(step: str) -> float:
    from studio import step_caps
    return max(OVERRUN_FACTOR * step_caps.step_wall_s(step), OVERRUN_FLOOR_S)


def stuck_step(book: Path, codex: str, n: int, deps: Deps) -> str | None:
    """The open step id when ALL THREE hold: elapsed past 1.5x its cap wall, the run
    tree's CPU flat, its outputs still for LIVENESS_QUIET_S.  A quiet log alone is
    not liveness (Jekyll ep01: the log was quiet through healthy renders)."""
    home = home_of(book, n)
    if deps.cpu_s is None or deps.outputs_at is None or (step := open_step(home)) is None:
        return None
    from studio import step_attempts
    quiet = cpu_quiet_s(step, deps.cpu_s(deps.procs(), codex, n), deps)
    over = step_attempts.elapsed(home, f"wall.{step}") > stuck_limit_s(step)
    still = deps.now() - deps.outputs_at(home) >= LIVENESS_QUIET_S
    return step if over and quiet >= LIVENESS_QUIET_S and still else None


def overran(book: Path, codex: str, n: int, step: str, deps: Deps) -> dict:
    """Kill the stuck step's tree and relaunch; the third overrun of a step parks."""
    before = sum(1 for r in rows_of(paths_of(book).events) if r.get("event") == "step_overran"
                 and r.get("episode") == n and r.get("step") == step)
    from studio import step_attempts
    event(book, {"event": "step_overran", "episode": n, "step": step, "limit_s": stuck_limit_s(step),
                 "elapsed_s": step_attempts.elapsed(home_of(book, n), f"wall.{step}")})
    deps.engine.kill_run_tree(deps.procs(), codex, n)
    (deps.root / "gpu.lock").unlink(missing_ok=True)
    if before >= OVERRUNS_BEFORE_PARK:
        return park(book, codex, n, "step_overran", {"step": step}, deps)
    return launch(book, codex, n, deps, "relaunch")


def note_dirty_during_run(book: Path, n: int, signals, deps: Deps) -> None:
    """A runtime edit while a drive runs: one event per drive, no pause (owner: drive, don't babysit)."""
    if not (signals.proc_alive and signals.code_dirty):
        return
    pid = (signals.lock or {}).get("drive_pid")
    if any(r.get("event") == "code_dirty_during_run" and r.get("drive_pid") == pid for r in rows_of(paths_of(book).events)):
        return
    from studio import episode_drive
    names = [ln[3:].strip() for ln in signals.porcelain.splitlines() if len(ln) > 3 and episode_drive.runtime_path(ln[3:])]
    event(book, {"event": "code_dirty_during_run", "episode": n, "drive_pid": pid, "files": names})


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
    brake_two_parks(book, rows_of(parked), deps)
    return {"action": "park", "state": "PARKED"}


def brake_two_parks(book: Path, parked: list[dict], deps: Deps) -> bool:
    """The design's drift brake: two consecutive chapters parked means the fault
    is the code, not the chapters (ep20, ep21 on one 400, 2026-10-06).  The
    series pauses itself and says so once; `resume` after the fix lifts it."""
    last = [r.get("episode") for r in parked[-2:]]
    if len(last) < 2 or last[1] != last[0] + 1:
        return False
    series, why = paths_of(book).series, f"two parked in a row: ep{last[0]:02d}, ep{last[1]:02d}"
    doc = read_json(series, {}) or {}
    held = pure().lease("autopilot", why, deps.now(), sha=deps.git("rev-parse", "HEAD").strip())
    write_atomic(series, {**doc, "paused": True, "paused_why": why, "pause": held})   # resumes itself once a fix lands
    event(book, {"event": "two_parked_in_a_row", "episodes": last})
    deps.notify(f"two chapters parked in a row (ep{last[0]:02d}, ep{last[1]:02d}): the series is paused until a fix lands; "
                f"autopilot.py retry N + resume to continue")
    return True


def note_published(book: Path, n: int, uploads: list[dict], deps: Deps) -> dict:
    """One event and one Telegram with the youtu.be URL, the first time only."""
    if any(r.get("event") == "published" and r.get("episode") == n for r in rows_of(paths_of(book).events)):
        return {"action": "published_already", "state": "PUBLISHED"}
    rows = [r for r in uploads if r.get("episode") == n and r.get("privacy") == "public"]
    video = rows[-1].get("video_id", "") if rows else ""
    event(book, {"event": "published", "episode": n, "video_id": video})
    deps.notify(f"ep{n:02d} PUBLISHED https://youtu.be/{video}")
    return {"action": "published", "state": "PUBLISHED"}


def held_units(book: Path) -> list[dict]:
    """Episodes at HELD_PUBLISH: a `held_publish` row newer than their last `retry`,
    as rows `next_unit` can skip like parked ones."""
    held, retried = {}, {}
    for i, row in enumerate(rows_of(paths_of(book).events)):
        if row.get("event") == "held_publish":
            held[row.get("episode")] = i
        elif row.get("event") == "retry":
            retried[row.get("episode")] = i
    return [{"episode": n} for n, i in sorted(held.items()) if i > retried.get(n, -1)]


def hold(book: Path, n: int, derived, deps: Deps) -> dict:
    """HELD_PUBLISH: one row and one message per hold, and no parked row, so a hold
    never trips the two-parks brake (retro 2026-10-20 item 7)."""
    if n not in {r["episode"] for r in held_units(book)}:
        event(book, {"event": "held_publish", "episode": n, "reason": str(derived.reason or "")})
        deps.notify(f"ep{n:02d} HELD before upload: the master is finished; the owner's standing approval "
                    f"publish/standing.json lets step 13 upload it. The series moves on.")
    return {"action": "held_publish", "state": "HELD_PUBLISH"}


def pick_unit(book: Path, deps: Deps, series: dict, uploads: list[dict], parked: list[dict]) -> int | None:
    """The next chapter past parked and held ones; with only holds left, the lowest hold
    (never COMPLETE over a held master).  A standing file lifts the holds it lists."""
    chapters, held = deps.chapters(book), holds_still_owed(book, held_units(book))
    n = deps.next_unit(chapters, uploads, parked + held, series["last"])
    return n if n is not None or not held else deps.next_unit(chapters, uploads, parked, series["last"])


def complete(book: Path, series: dict, parked: list[dict], uploads: list[dict], deps: Deps) -> dict:
    """SERIES_COMPLETE: one Telegram, then the loop idles at its ticks."""
    if not any(r.get("event") == "complete" for r in rows_of(paths_of(book).events)):
        public = sorted({r["episode"] for r in uploads if r.get("privacy") == "public"})
        event(book, {"event": "complete", "published": len(public), "parked": [r["episode"] for r in parked]})
        deps.notify(f"SERIES COMPLETE {len(public)}/{series['last']} public; parked: {[r['episode'] for r in parked]}")
    return {"action": "complete", "state": "COMPLETE"}


def brain_packet(book: Path, n: int, derived, signals, deps: Deps) -> dict:
    """The derived packet plus the log's tail, the refusals and the commits since the failure."""
    packet = {**dict(derived.packet or {}), **packet_extras(home_of(book, n), n)}
    packet["commits_since"] = commits_since(deps, getattr(signals, "failed_sha", None), packet.get("head") or "")
    return packet


def brain(book: Path, codex: str, n: int, derived, signals, deps: Deps) -> dict:
    """One brain attempt; the verdict FILE and git are trusted, never the prose."""
    home = home_of(book, n)
    attempt = home / "brain" / f"attempt_{len(brain_attempts_of(home)) + 1:02d}.json"
    heartbeat(deps, -1, "BRAIN_RUNNING", n)
    event(book, {"event": "brain", "episode": n, "attempt": attempt.name, "reason": str(derived.reason)})
    try:
        doc = deps.brain(book, codex, n, brain_packet(book, n, derived, signals, deps), attempt)
    except Exception as why:                                   # the leash: a dead brain is an attempt
        doc = {"verdict": "error", "why": scrub(repr(why))}
    if not attempt.exists():
        write_atomic(attempt, doc)
    return judge_verdict(book, codex, n, read_json(attempt, {}), deps, getattr(signals, "failed_sha", None))


def judge_verdict(book: Path, codex: str, n: int, verdict: dict, deps: Deps, failed_sha: str | None = None) -> dict:
    """relaunch only on a clean tree at the commit the file names; park only on a
    clean tree whose HEAD is the commit that failed (P13: a park on a dirty tree
    or on code a fix has since replaced is a false park)."""
    said, head = str(verdict.get("verdict")), deps.git("rev-parse", "HEAD").strip()
    from studio import episode_drive
    clean = not episode_drive.dirty(deps.git("status", "--porcelain"))
    same_head = not failed_sha or head.startswith(failed_sha) or failed_sha.startswith(head)
    if said == "park" and clean and same_head:
        return park(book, codex, n, f"brain: {verdict.get('why', '')}", verdict, deps)
    if said == "relaunch" and clean and str(verdict.get("commit")) == head:
        event(book, {"event": "brain_relaunch", "episode": n, "commit": head[:8]})
        return {"action": "brain_relaunch", "state": "IDLE"}
    if said in ("retry", "cure") and clean:
        return triage_action(book, codex, n, said, verdict, deps)
    event(book, {"event": "brain_rejected", "episode": n, "verdict": said, "clean": clean, "same_head": same_head})
    return {"action": "brain_rejected", "state": "NEEDS_BRAIN"}


def triage_action(book: Path, codex: str, n: int, said: str, verdict: dict, deps: Deps) -> dict:
    """A triage answer short of a fix: retry relaunches; cure places the desk order first."""
    if said == "cure" and verdict.get("order"):
        deps.order(codex, n, verdict["order"])
    event(book, {"event": f"brain_{said}", "episode": n, "order": verdict.get("order")})
    return {"action": f"brain_{said}", "state": "IDLE"}


def open_wait(book: Path) -> dict | None:
    """The wait_tree row still open (no tree_clear after it), or None."""
    marks = [r for r in rows_of(paths_of(book).events) if r.get("event") in ("wait_tree", "tree_told", "tree_clear")]
    if not marks or marks[-1].get("event") == "tree_clear":
        return None
    opened = [r for r in marks if r.get("event") == "wait_tree"]
    return opened[-1] if opened else None


def told_since(book: Path, wait: dict) -> bool:
    """A tree_told row written at or after this wait opened."""
    told = [r for r in rows_of(paths_of(book).events) if r.get("event") == "tree_told"]
    return any(when(t.get("ts", "")) >= when(wait.get("ts", "")) for t in told)


def wait_tree(book: Path, deps: Deps) -> dict:
    """The one deliberate wait: the owner's own edit; told once after six hours,
    counted from THIS wait (tree_clear closes the last one, P13)."""
    wait, held = open_wait(book), {"action": "wait_tree", "state": "WAIT_TREE"}
    if wait is None:
        event(book, {"event": "wait_tree", "since": deps.now()})
    elif deps.now() - float(wait.get("since", deps.now())) >= TREE_TOLD_S and not told_since(book, wait):
        event(book, {"event": "tree_told"})
        deps.notify("tree dirty for 6 h, autopilot waiting; commit or stash the code")
    return held


def note_tree_clear(book: Path, deps: Deps) -> None:
    """The tree no longer holds the series: close the open wait, with its length."""
    wait = open_wait(book)
    if wait is not None:
        event(book, {"event": "tree_clear", "waited_s": round(deps.now() - float(wait.get("since", deps.now())))})


# ---- ComfyUI health ----------------------------------------------------------------

def probe(engine: Any, name: str, *args: Any) -> Any:
    """An engine call that may not exist on a stand-in; None when it does not."""
    call = getattr(engine, name, None)
    return call(*args) if call else None


def engine_ticks(deps: Deps, signals) -> int:
    """Consecutive ticks the engine failed to answer, carried in heartbeat.json."""
    if getattr(signals, "engine_up", True):
        return 0
    return int(read_json(deps.root / "heartbeat.json", {}).get("engine_down_ticks", 0)) + 1


def watch_engine(book: Path, n: int, derived, signals, deps: Deps, ticks: int) -> None:
    """Restart a dead engine after ENGINE_DOWN_TICKS missed polls in any state but
    paused (IDLE restarts itself in act_idle); free host commit when it runs low."""
    state = getattr(derived.state, "name", str(derived.state))
    if signals.engine_up:
        return commit_check(book, n, signals, deps)
    if ticks < ENGINE_DOWN_TICKS or state == "PAUSED" or is_paused(book):
        return
    event(book, {"event": "engine_down", "episode": n, "ticks": ticks, "log": probe(deps.engine, "log_tail", 3) or [],
                 "commit_free_gb": probe(deps.engine, "commit_free_gb")})
    if state != "IDLE":
        deps.engine.restart()
        event(book, {"event": "engine_restart", "episode": n, "why": "down"})


def queue_busy(deps: Deps) -> bool:
    queue = deps.engine.queue(ENGINE_URL)
    pending = queue.get("pending") or queue.get("queue_pending") if isinstance(queue, dict) else 0
    return running_id(queue) is not None or bool(pending)


def commit_check(book: Path, n: int, signals, deps: Deps) -> None:
    """Commit headroom under COMMIT_LOW_GB with an empty queue: POST /free and read
    again; still under COMMIT_HARD_GB with no drive alive: recycle the engine."""
    before = probe(deps.engine, "commit_free_gb")
    if before is None or before >= COMMIT_LOW_GB or queue_busy(deps):
        return
    deps.engine.free(ENGINE_URL)
    after = probe(deps.engine, "commit_free_gb")
    event(book, {"event": "commit_low", "episode": n, "before_gb": before, "after_gb": after})
    if after is not None and after < COMMIT_HARD_GB and not signals.proc_alive:
        deps.engine.kill_engine(deps.procs())
        deps.engine.restart()
        event(book, {"event": "engine_recycled", "episode": n, "commit_gb": after})


# ---- auto-unpark and the handover ----------------------------------------------------

def runtime_changed(deps: Deps, sha: str) -> bool:
    """`git diff --name-only sha..HEAD` touches a file a run reads."""
    from studio import episode_drive
    if deps.git("rev-parse", "HEAD").strip().startswith(sha):
        return False                                           # nothing has landed since the park
    try:
        names = deps.git("diff", "--name-only", f"{sha}..HEAD").splitlines()
    except Exception:                                          # noqa: BLE001 -- an unknown sha clears nothing
        return False
    return any(episode_drive.runtime_path(name) for name in names if name.strip())


def unparked_count(book: Path, n: int) -> int:
    return sum(1 for r in rows_of(paths_of(book).events) if r.get("event") == "auto_unpark" and r.get("episode") == n)


def auto_unpark(book: Path, deps: Deps) -> list[int]:
    """A `brain:` park clears when a runtime file changed since its sha (at most
    UNPARK_CAP times per episode): Jekyll ep01's three parks were all false and
    each needed the owner.  step_cap, over_budget, SAFETY, the token and clock_loop
    never match `brain:`, so they never clear."""
    cleared = []
    for row in rows_of(paths_of(book).parked):
        n = row.get("episode")
        if not str(row.get("reason", "")).startswith("brain:") or not row.get("sha"):
            continue
        if unparked_count(book, n) >= UNPARK_CAP or not runtime_changed(deps, str(row["sha"])):
            continue
        retry(book, n)
        event(book, {"event": "auto_unpark", "episode": n, "from": str(row["sha"])[:8]})
        cleared.append(n)
    return cleared


def spawn_successor(book: Path, codex: str, deps: Deps, head: str, every: int) -> bool:
    """One detached `autopilot.py run` for a HEAD that has no successor yet."""
    marker = deps.root / "successor.json"
    if read_json(marker, {}).get("head") == head:
        return False
    write_atomic(marker, {"head": head, "ts": utc_now()})
    flags = (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS) if sys.platform == "win32" else 0
    argv = ["uv", "run", "--no-sync", "python", "scripts/episode/autopilot.py", "run", "--book", codex, "--every", str(every)]
    proc = deps.popen(argv, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
    event(book, {"event": "successor", "head": head[:8], "pid": getattr(proc, "pid", None)})
    return True


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
    if (other := other_unit_running(deps, codex, n, deps.procs())) is not None:
        return {"action": "wait", "state": "IDLE", "other": other, "reason": f"ep{other:02d} runs"}
    if signals.drive_rows and step_guard(book, n, signals.log_tail, deps, str(derived.reason)):
        return park(book, codex, n, "step_cap", {"tail": signals.log_tail[-800:]}, deps)
    return launch(book, codex, n, deps, "relaunch" if signals.drive_rows else "launch")


def act_needs_brain(book: Path, codex: str, n: int, derived, signals, deps: Deps) -> dict:
    if derived.order:
        return cure(book, codex, n, derived, deps)
    if signals.brain_attempts >= BRAIN_ATTEMPTS:
        return park(book, codex, n, "brain_exhausted", {"reason": str(derived.reason)}, deps)
    return brain(book, codex, n, derived, signals, deps)


RENDER_STEP = "09"


def act_running(book: Path, codex: str, n: int, deps: Deps) -> dict:
    """RUNNING: a hung engine is rescued, a stuck step killed; at render start the
    YouTube token is checked so the owner's click lands inside the render (item 8)."""
    if hung(book, n, deps):
        return rescue_engine(book, codex, n, deps)
    if (step := stuck_step(book, codex, n, deps)) is not None:
        return overran(book, codex, n, step, deps)
    if open_step(home_of(book, n)) == RENDER_STEP:
        token_watch(book, n, "render", deps)
    return {"action": "wait", "state": "RUNNING"}


def act(book: Path, codex: str, n: int, derived, signals, deps: Deps) -> dict:
    """ONE action per tick, by the derived state; returns the state it leaves."""
    state = getattr(derived.state, "name", str(derived.state))
    if state == "PAUSED":
        return {"action": "wait", "state": "PAUSED"}
    if state == "IDLE":
        return act_idle(book, codex, n, derived, signals, deps)
    if state == "RUNNING":
        return act_running(book, codex, n, deps)
    if state == "HELD_PUBLISH":
        return hold(book, n, derived, deps)
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
    uploads, parked = uploads_of(book), rows_of(paths_of(book).parked)
    beat = read_json(deps.root / "heartbeat.json", {})
    public = sorted({r["episode"] for r in uploads if r.get("privacy") == "public"})
    return {"ts": utc_now(), "supervisor_pid": deps.pid,
            "heartbeat_age_s": round(deps.now() - float(beat.get("ts") or deps.now())),
            "engine": {"up": getattr(signals, "engine_up", None), "restarts": restarts_of(book, n) if n else 0},
            "series": {"book": codex, "first": series["first"], "last": series["last"], "published": public,
                       "parked": [{"episode": r["episode"], "reason": r["reason"], "ts": r["ts"]} for r in parked],
                       "paused": is_paused(book, series), "next": n,
                       "state": "paused" if done["state"] == "PAUSED" or is_paused(book, series) else
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
    series, p, ticks = load_series(book, codex, deps.chapters), paths_of(book), 0
    series = lease_check(book, codex, series, deps)
    uploads, parked = uploads_of(book), rows_of(p.parked)
    if auto_unpark(book, deps):
        parked = rows_of(p.parked)
    n = pick_unit(book, deps, series, uploads, parked)
    if n is None:
        derived, signals = SimpleNamespace(state="COMPLETE", reason="", order=None, packet={}), SimpleNamespace(engine_up=None)
        done = complete(book, series, parked, uploads, deps)
    else:
        signals = gather(book, codex, n, deps, series)
        derived = deps.derive(signals, n)
        if signals.paused:
            derived = SimpleNamespace(state="PAUSED", reason="paused", order=None, packet={})
        ticks = engine_ticks(deps, signals)
        watch_engine(book, n, derived, signals, deps, ticks)
        note_dirty_during_run(book, n, signals, deps)
        done = act(book, codex, n, derived, signals, deps)
        if done["state"] != "WAIT_TREE":
            note_tree_clear(book, deps)
        done["brain_attempts"] = len(brain_attempts_of(home_of(book, n)))
    doc = status_doc(book, codex, n, derived, signals, series, done, deps)
    write_atomic(p.status, doc)
    heartbeat(deps, tick_no, doc["episode"]["state"], n, ticks)
    return doc


def run_loop(book: Path, codex: str, deps: Deps, every: float = 30.0, ticks: int | None = None) -> int:
    """The long-lived loop; a second instance exits 0 silently; a tick that
    raises is an event, never a stop (the one rule: silence is not a state)."""
    if not claim_supervisor(deps):
        return 0
    adopt(book, deps)
    born, i = deps.git("rev-parse", "HEAD").strip(), 0
    while ticks is None or i < ticks:
        i += 1
        if (head := hand_over(book, codex, deps, born)) is not None:
            spawn_successor(book, codex, deps, head, int(every))
            return 0                       # the successor (or, failing it, the scheduler) runs the new code
        try:
            tick(book, codex, deps, i)
        except Exception as why:                               # noqa: BLE001 -- the supervisor outlives any fault
            log.exception("tick %d failed", i)
            event(book, {"event": "tick_error", "error": scrub(repr(why))})
        deps.sleep(every)
    return 0


def code_moved(book: Path, deps: Deps, born: str, head: str | None = None) -> bool:
    """HEAD is not the commit this loop started on: the first live loop ticked
    on stale code through four fixes (2026-10-06) and paid the brain for it."""
    head = head if head is not None else deps.git("rev-parse", "HEAD").strip()
    if head == born:
        return False
    event(book, {"event": "code_moved", "from": born[:8], "to": head[:8]})
    release_supervisor(deps)
    return True


def live_drive(codex: str, deps: Deps) -> int | None:
    """The episode gpu.lock names, while the process table still runs its drive."""
    n = read_json(deps.root / "gpu.lock", {}).get("episode")
    return int(n) if n is not None and deps.engine.drive_alive(deps.procs(), codex, int(n)) else None


def hand_over(book: Path, codex: str, deps: Deps, born: str) -> str | None:
    """The HEAD to hand the loop over to, or None.  Under a live drive the loop keeps
    the code it was born on, says so once per commit, and hands over after the drive
    ends (retro 2026-10-20 item 12: 62 code_moved, 35 successors in ep01's window)."""
    head = deps.git("rev-parse", "HEAD").strip()
    if head == born:
        return None
    if (n := live_drive(codex, deps)) is not None:
        if not any(r.get("event") == "code_moved_during_run" and r.get("to") == head[:8]
                   for r in rows_of(paths_of(book).events)):
            event(book, {"event": "code_moved_during_run", "episode": n, "from": born[:8], "to": head[:8]})
        return None
    return head if code_moved(book, deps, born, head) else None


def commit_hold(book: Path, codex: str, deps: Deps, names: list[str]) -> str | None:
    """A runtime commit waits while a drive runs (retro 2026-10-20 item 12): the message
    naming `pause --at-boundary`, or None when the staged files may land now."""
    from studio import episode_drive
    runtime = [x.strip() for x in names if x.strip() and episode_drive.runtime_path(x)]
    if not runtime or (n := live_drive(codex, deps)) is None:
        return None
    return (f"ep{n:02d}'s drive is RUNNING: committing {', '.join(runtime[:5])} moves its code mid-run. Run "
            f"`autopilot.py pause --at-boundary --by <you> --why \"...\"`, wait for its paused_at_boundary stop, "
            f"commit, then `autopilot.py resume`")


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
            watched = run(watchdog_command(repo, book, logon=logon, uv=uv)) == 0
            print(f"task {WATCHDOG_TASK} " + ("registered" if watched else "REFUSED") + f", every {WATCHDOG_EVERY} min")
            return 0 if watched else 1
    return 1


def watchdog_command(repo: Path, book: str | None = None, logon: str = "S4U", uv: str = "uv") -> str:
    """The second task (retro 2026-10-20 item 7): AtLogOn + every WATCHDOG_EVERY min, one
    `autopilot.py watchdog` look at heartbeat.json, IgnoreNew, a 5 min limit.  Pure."""
    work = Path(repo).as_posix()
    arg = "run --no-sync python scripts/episode/autopilot.py watchdog" + (f" --book {book}" if book else "")
    span = f"([System.Xml.XmlConvert]::ToTimeSpan('PT{WATCHDOG_EVERY}M'))"
    return (f"$a = New-ScheduledTaskAction -Execute '{uv}' -Argument '{arg}' -WorkingDirectory '{work}'; "
            f"$t = @((New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME), "
            f"(New-ScheduledTaskTrigger -Once -At 00:00 -RepetitionInterval {span})); "
            f"$s = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit {span} "
            f"-StartWhenAvailable -AllowStartIfOnBatteries; "
            f"$p = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType {logon} -RunLevel Limited; "
            f"try {{ Register-ScheduledTask -TaskName '{WATCHDOG_TASK}' -Action $a -Trigger $t -Settings $s "
            f"-Principal $p -Force -ErrorAction Stop | Out-Null }} catch {{ Write-Error $_; exit 5 }}")


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
    """Both tasks: the supervisor's refusal is the exit code; a missing watchdog is no fault."""
    return (f"try {{ Unregister-ScheduledTask -TaskName '{TASK}' -Confirm:$false -ErrorAction Stop }} "
            f"catch {{ Write-Error $_; exit 5 }}; "
            f"Unregister-ScheduledTask -TaskName '{WATCHDOG_TASK}' -Confirm:$false -ErrorAction SilentlyContinue; exit 0")


def powershell(command: str) -> int:
    return subprocess.run(["powershell", "-NoProfile", "-Command", command], cwd=ROOT, check=False).returncode


# ---- the owner's acts ------------------------------------------------------------

def retry(book: Path, n: int) -> int:
    """The parked row for N is removed; the next tick picks N up (resume is idempotent)."""
    path = paths_of(book).parked
    rows = rows_of(path)
    kept = [r for r in rows if r.get("episode") != n]
    if len(kept) != len(rows):
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept), encoding="utf-8")
    retire_brain(home_of(book, n))                 # parked or not: a retry is a launch order (ep21)
    from studio import run_budget
    run_budget.stamp_attempt(home_of(book, n))     # an attempt stamp; the ceiling is NOT reset (C3_verdict #4)
    event(book, {"event": "retry", "episode": n})
    return len(rows) - len(kept)


def pause_at_boundary(book: Path, codex: str, deps: Deps, by: str = "owner", why: str = "",
                      hours: float | None = None) -> str:
    """Pause the series AND ask the running episode (gpu.lock's) to stop at its
    next boundary (C3_verdict #7): wait for `paused_at_boundary`, then commit."""
    set_paused(book, codex, True, by=by, why=why, hours=hours, now=deps.now(), sha=deps.git("rev-parse", "HEAD").strip())
    n = read_json(deps.root / "gpu.lock", {}).get("episode")
    if not n:
        return "series paused; no episode is running, nothing to stop"
    from studio import boundary
    boundary.request(home_of(book, int(n)), "autopilot pause --at-boundary")
    event(book, {"event": "pause_at_boundary", "episode": int(n)})
    return f"series paused; ep{int(n):02d} stops at its next boundary"


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
    for name in ("run", "tick", "status", "install", "uninstall", "pause", "resume", "retry", "park",
                 "watchdog", "may-commit"):
        s = sub.add_parser(name)
        s.add_argument("--book", default=None)
        if name in ("retry", "park"):
            s.add_argument("n", type=int)
        if name == "park":
            s.add_argument("--why", required=True)
        if name == "pause":                   # the lease (retro 2026-10-20 V7): who, why, how long
            s.add_argument("--at-boundary", action="store_true")
            s.add_argument("--by", default="owner")
            s.add_argument("--why", default="")
            s.add_argument("--hours", type=float, default=None)
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


def may_commit(book: Path, codex: str, deps: Deps) -> int:
    """`may-commit`: 0 when the staged files may land now, 3 with the reason when a drive runs."""
    said = commit_hold(book, codex, deps, deps.git("diff", "--cached", "--name-only").splitlines())
    print(said or "may commit: no drive is running, or nothing staged is runtime code")
    return 3 if said else 0


def dispatch(args: argparse.Namespace, book: Path, codex: str, deps: Deps) -> int:
    if args.cmd == "run":
        return run_loop(book, codex, deps, every=float(args.every))
    if args.cmd == "tick":
        print(json.dumps(tick(book, codex, deps, 1), indent=1, ensure_ascii=False))
    elif args.cmd == "status":
        print(json.dumps(status_now(book), indent=1, ensure_ascii=False))
    elif args.cmd == "watchdog":
        print(json.dumps(watchdog(book, deps)))
    elif args.cmd == "may-commit":
        return may_commit(book, codex, deps)
    elif args.cmd == "pause" and args.at_boundary:
        print(pause_at_boundary(book, codex, deps, args.by, args.why, args.hours))
    elif args.cmd == "pause":
        set_paused(book, codex, True, by=args.by, why=args.why, hours=args.hours, now=deps.now(),
                   sha=deps.git("rev-parse", "HEAD").strip())
    elif args.cmd == "resume":
        set_paused(book, codex, False)
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
