"""The fault injectors F1-F18 (2026-10-21_ep02_proof DESIGN 3.2): each plants ONE fault at ONE point.

Three kinds of injector:
- a manifest row at the key its fake reads (`route`): engine faults for the fake ComfyUI (P3's
  `faults`: `{kind, on: submit#k, workflow, detail}`, its seven kinds only), and for P4's fakes
  `sdk_faults` (rate limit, brain failure), `worker_die_at`, `youtube: invalid_grant`, plus the
  brain's scripted stream (`brain_stream`, brain_script.py);
- a hook in a child: `kill_at_write` stops the process BEFORE its k-th write at a named site
  (file kind x code location, trace.py's names) while the runner is in the row's step; it kills
  its whole drive tree at once, the drive first (so drive.py never handles a child's exit), writes
  `<sandbox>/kill.request` and exits KILLED; the supervisor then sweeps any orphan left;
- a file planted in the sandbox before the run: a dropped supervisor with a stale gpu.lock, a
  commit in <sandbox>/git, a precondition gap (preconditions_ch2.json rows), a torn record.
Nothing here touches anything outside the sandbox it is given."""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Mapping

from studio import settings

ENGINE = ("crash", "hang", "lost", "exec_error", "exec_fatal", "unreadable", "corrupt")
CORRUPT = ("zero_byte", "truncated", "no_audio", "wrong_frames")
KILLED = 137
KILL_REQUEST = "kill.request"
INVALID_GRANT = "invalid_grant: Token has been expired or revoked."
"""The recorded reply of Google's token endpoint (memory: youtube-oauth weekly expiry)."""
GIT_IDENT = ["-c", "user.name=rehearsal", "-c", "user.email=rehearsal@localhost", "-c", "commit.gpgsign=false"]
_BUSY = threading.local()


# ---- manifest rows ------------------------------------------------------------------

def read_manifest(box: Path) -> dict:
    return json.loads((Path(box) / "rehearsal.json").read_text(encoding="utf-8"))


HARNESS = ("kill_at_write", "commit")
"""Faults the harness plants itself (a child's kill hook, a supervisor's commit): `harness_faults`."""
CLEAN = {"faults": [], "harness_faults": [], "sdk_faults": [], "worker_die_at": {}, "youtube": "refuse",
         "brain_stream": []}
"""A point's manifest before its ONE fault: no fault at any key a fake reads."""


def call_k(row: Mapping) -> int:
    return int(str(row["on"]).rpartition("#")[2])


def _append(doc: Mapping, key: str, item: Mapping) -> dict:
    return {key: [*(doc.get(key) or []), dict(item)]}


ROUTES: dict[str, Callable[[Mapping, Mapping], dict]] = {
    **{k: (lambda d, r: _append(d, "faults", r)) for k in ENGINE},
    "rate_limit": lambda d, r: _append(d, "sdk_faults", {"on": call_k(r), "kind": "rate_limit"}),
    "brain_failed": lambda d, r: _append(d, "sdk_faults", {"on": call_k(r), "kind": "error"}),
    "worker_death": lambda d, r: {"worker_die_at": {**(d.get("worker_die_at") or {}), r["worker"]: int(r["line"])}},
    "oauth": lambda d, r: {"youtube": "invalid_grant"},
    "brain_stream": lambda d, r: {"brain_stream": list(r["stream"])},
    **{k: (lambda d, r: _append(d, "harness_faults", r)) for k in HARNESS}}
"""Each fault kind -> the manifest keys ITS fake reads: P3's engine `faults` (its seven kinds only);
P4's `sdk_faults` [{on: k, kind: rate_limit|error}], `worker_die_at` {worker: line} and
`youtube: invalid_grant`; brain_script's `brain_stream`; the harness's own `harness_faults`."""


def route(doc: Mapping, row: Mapping) -> dict:
    """The manifest with `row` at the key its fake reads; a kind no fake reads raises."""
    kind = row.get("kind")
    if kind not in ROUTES:
        raise ValueError(f"no fake reads a fault of kind {kind!r}; known: {', '.join(ROUTES)}")
    return {**doc, **ROUTES[kind](doc, row)}


def add(box: Path, row: Mapping) -> dict:
    """Plant one fault row in the sandbox manifest, at the key its fake reads; the manifest as written."""
    doc = route(read_manifest(box), row)
    (Path(box) / "rehearsal.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return doc


def engine(kind: str, k: int, workflow: str | None = None, detail: str | None = None) -> dict:
    """A fake-engine fault at the k-th submit of `workflow` (every workflow when None)."""
    if kind not in ENGINE:
        raise ValueError(f"no engine fault {kind!r}; known: {', '.join(ENGINE)}")
    if kind == "corrupt" and detail not in CORRUPT:
        raise ValueError(f"a corrupt output names one of {', '.join(CORRUPT)}, not {detail!r}")
    row = {"kind": kind, "on": f"submit#{int(k)}"}
    return {**row, **({"workflow": workflow} if workflow else {}), **({"detail": detail} if detail else {})}


def worker_death(worker: str, line: int) -> dict:
    """F17: the fake worker (detect, anime_id, whisper) exits on its line-th request."""
    return {"kind": "worker_death", "worker": worker, "line": int(line)}


def rate_limit(call: int) -> dict:
    """F15: the k-th structured call's stream carries a RateLimitEvent."""
    return {"kind": "rate_limit", "on": f"call#{int(call)}"}


def brain_failed(call: int) -> dict:
    return {"kind": "brain_failed", "on": f"call#{int(call)}"}


def oauth_expired() -> dict:
    """F6: the YouTube send raises the recorded invalid_grant."""
    return {"kind": "oauth", "error": INVALID_GRANT}


def brain_stream(verdicts: list[str]) -> dict:
    """The brain's scripted answers, one per session: relaunch, redo:<step>, park."""
    return {"kind": "brain_stream", "stream": list(verdicts)}


def token_note(manifest: Mapping) -> Callable[[], str | None]:
    """The fake for Deps.token_note: the expired token's message when F6 set `youtube: invalid_grant`
    (the drive's step-13 send then raises P4's recorded RefreshError), else None."""
    said = INVALID_GRANT if manifest.get("youtube") == "invalid_grant" else None
    return lambda: said


# ---- a kill at write k (a child's hook) ----------------------------------------------

def kill_at_write(kind: str, site: str, occurrence: int, step: str | None) -> dict:
    return {"kind": "kill_at_write", "file_kind": kind, "site": site, "occurrence": int(occurrence), "step": step}


def kill_rows(manifest: Mapping, step: str | None = None) -> list[dict]:
    """The kill-at-write rows; with `step`, only those for that step (or for any step)."""
    rows = [r for r in manifest.get("harness_faults") or () if r.get("kind") == "kill_at_write"]
    return [r for r in rows if step is None or r.get("step") in (None, step)]


def request_kill(box: Path, row: Mapping, step: str, killed: list[int]) -> None:
    """Tell the supervisor which fault fired, from which pid and step, when, and which pids of the
    drive tree went with it, before this process dies."""
    body = {"fault": dict(row), "pid": os.getpid(), "step": step, "ts": time.time(), "killed": killed,
            "argv": sys.argv[:4]}
    (Path(box) / KILL_REQUEST).write_text(json.dumps(body), encoding="utf-8")


SUPERVISOR_ENV = "VISURENA_REHEARSAL_SUPERVISOR"
"""The rehearsal supervisor's pid, put in its env so every drive tree it launches knows where it ends."""


def supervisor_pid() -> int | None:
    try:
        return int(os.environ[SUPERVISOR_ENV])
    except (KeyError, ValueError):
        return None


def drive_root(parents: Mapping[int, int], me: int, supervisor: int | None) -> int:
    """The drive the autopilot launched: `me`'s topmost ancestor below the supervisor; `me` itself
    when the supervisor is unknown or not among its ancestors."""
    chain, pid = [me], me
    while (parent := parents.get(pid)) is not None and parent not in chain:
        if parent == supervisor:
            return pid
        chain.append(parent)
        pid = parent
    return me


def terminate(pid: int) -> None:
    os.kill(pid, signal.SIGTERM)                       # TerminateProcess on Windows: no handler runs


def kill_tree(me: int, supervisor: int | None, parents: Callable[[], Mapping[int, int]] | None = None,
              kill: Callable[[int], None] = terminate) -> list[int]:
    """DESIGN 3.2's tree kill, from inside the dying process: the drive first, so it never sees a
    child's exit and handles it, then every other process under it; never `me` (it exits after)."""
    from studio.rehearsal import supervisor as sup
    table = (parents or sup.parent_map)()
    root = drive_root(table, me, supervisor)
    pids = [p for p in [root, *sorted(sup.descendants(table, {root}) - {root})] if p != me]
    for pid in pids:
        try:
            kill(pid)
        except OSError:                                # already gone: what a kill wants
            pass
    return pids


def kill_hook(row: Mapping, box: Path, exit: Callable[[int], None] = os._exit):
    """An audit hook counting the row's step's writes at the row's site; at the k-th it dies
    before the write.  The step is the runner's at that write (trace.current_step), so a step
    imported into episode.py is killed in episode.py."""
    from studio.rehearsal import fence
    seen = {"n": 0}

    def hook(event: str, args: tuple) -> None:
        if event != "open" or getattr(_BUSY, "on", False) or not fence.writes(args[1], args[2]):
            return
        step = at_site(row, box, args[0], sys._getframe(1))
        if step is None:
            return
        seen["n"] += 1
        if seen["n"] == row["occurrence"]:
            _BUSY.on = True
            request_kill(box, row, step, kill_tree(os.getpid(), supervisor_pid()))
            exit(KILLED)
    return hook


def at_site(row: Mapping, box: Path, path, frame) -> str | None:
    """The runner's step when this write is the row's (its file kind, code site and step); else None."""
    from studio.rehearsal import trace
    if trace.kind_of(path, box) != row["file_kind"] or trace.site_of(frame) != row["site"]:
        return None
    step = trace.current_step(frame)
    return step if row.get("step") in (None, step) else None


def arm(manifest: Mapping, box: Path) -> int:
    """Install this process's kill hooks, one per row (each filters on the runner's step at the
    write); how many were armed."""
    rows = kill_rows(manifest)
    for row in rows:
        sys.addaudithook(kill_hook(row, Path(box)))
    return len(rows)


def kill_requested(box: Path) -> dict | None:
    path = Path(box) / KILL_REQUEST
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# ---- planted files -------------------------------------------------------------------

def dead_pid() -> int:
    """A pid that ran and is gone: what a reboot leaves in gpu.lock."""
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


def drop_supervisor(box: Path, pid: int, episode: int, now: float, age_s: float = 3600.0) -> None:
    """F4: a gpu.lock naming a dead drive and a heartbeat `age_s` old, as a reboot leaves them."""
    root = Path(box) / settings.LIBRARY_DIR / ".autopilot"
    root.mkdir(parents=True, exist_ok=True)
    lock = {"drive_pid": pid, "started": "2026-10-21T00:00:00+00:00", "episode": episode, "sha": "0" * 40}
    (root / "gpu.lock").write_text(json.dumps(lock), encoding="utf-8")
    (root / "heartbeat.json").write_text(json.dumps({"ts": now - age_s, "tick": 7, "state": "RUNNING",
                                                     "episode": episode, "engine_down_ticks": 0}), encoding="utf-8")


def sandbox_commit(box: Path, path: str | None = None) -> str:
    """F7: an empty commit in <sandbox>/git; F7b: one that touches `path` (a guarded take file)."""
    repo = Path(box) / "git"
    if path:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# rehearsal edit {os.getpid()}\n" + (target.read_text() if target.exists() else ""))
        subprocess.run(["git", "-C", str(repo), "add", path], check=True, capture_output=True)
    argv = ["commit", "-q", "-m", f"rehearsal commit {path or '(empty)'}"] + ([] if path else ["--allow-empty"])
    subprocess.run(["git", "-C", str(repo), *GIT_IDENT, *argv], check=True, capture_output=True)
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True,
                          text=True).stdout.strip()


def drop_key(doc, key: str):
    """A dict without `key`, or a list without the rows that name it."""
    if isinstance(doc, dict):
        return {k: v for k, v in doc.items() if k != key}
    return [r for r in doc if not (isinstance(r, dict) and key in map(str, r.values()))]


def gap_target(gap: Mapping) -> dict:
    """A gap as {path} or {record, field|key}: the shapes above, or a preconditions_ch2.json row
    (a base sheet the note names, a place master refs/locations/<what>.png, a book field)."""
    if gap.get("path") or gap.get("record"):
        return dict(gap)
    kind, what = gap.get("kind"), str(gap.get("what") or "")
    if kind == "base_sheet" and (hit := re.search(r"names (\S+?);", str(gap.get("note") or ""))):
        return {"path": hit.group(1)}
    if kind == "place_picture":
        return {"path": f"refs/locations/{what}.png"}
    if kind == "book_field":
        return {"record": "source/book.json", "field": what}
    return {}


def plant(book: Path, gap: Mapping) -> dict:
    """F14: one precondition gap made true in the sandbox book: a `path` removed, or a record's
    `field` / `key` removed.  `planted`: this call changed the book; `present`: the gap now holds
    (a sheet the real book already lacks is present without a plant)."""
    target = gap_target(gap)
    if not target:
        return {**gap, "planted": False, "present": False}
    path = Path(book) / (target.get("path") or target["record"])
    if target.get("path"):
        planted = path.is_file()
        path.unlink(missing_ok=True)
        return {**gap, "planted": planted, "present": True}
    if not path.is_file():
        return {**gap, "planted": False, "present": True}
    doc = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(drop_key(doc, target.get("field") or target.get("key")), indent=1), encoding="utf-8")
    return {**gap, "planted": True, "present": True}


def plant_all(book: Path, doc: Mapping) -> list[dict]:
    """Every gap of a preconditions report (`results/preconditions_ch2.json` rows under `gaps`)."""
    return [plant(book, gap) for gap in doc.get("gaps") or ()]


RECORDS = ("attempts.json", "drive.jsonl", "clock.jsonl", "timing.jsonl", "takes/r2v/ladder.json",
           "takes/r2v/shots.json", "takes/r2v/phases.jsonl", "autopilot/status.json", "autopilot/parked.jsonl",
           "autopilot/events.jsonl", ".autopilot/heartbeat.json", ".autopilot/gpu.lock")
"""F18's record kinds: what a resume reads, under the episode home, the book or the library."""


def record_path(book: Path, n: int, record: str) -> Path:
    """Where a record kind lives: `.autopilot/` under the library, `autopilot/` under the book,
    everything else under the episode home."""
    if record.startswith(".autopilot/"):
        return Path(book).parent / record
    if record.startswith("autopilot/"):
        return Path(book) / record
    return Path(book) / "episodes" / f"ep{n:02d}" / record


def tear(path: Path, keep: float = 0.5) -> int:
    """F18: cut a record to a strict prefix of its bytes (a write killed mid-way); bytes kept."""
    data = Path(path).read_bytes()
    kept = min(max(int(len(data) * keep), 1), len(data) - 1)
    Path(path).write_bytes(data[:kept])
    return kept
