"""The fault injectors F1-F18 (2026-10-21_ep02_proof DESIGN 3.2): each plants ONE fault at ONE point.

Three kinds of injector:
- a manifest row the fakes read: engine faults for the fake ComfyUI (P3: `{kind, on: submit#k,
  workflow, detail}`), and worker deaths, rate limits, brain failures, the OAuth expiry and the
  brain's scripted stream for P4's fakes;
- a hook in a child: `kill_at_write` stops the process BEFORE its k-th write at a named site
  (file kind x code location, trace.py's names), writes `<sandbox>/kill.request`, and exits
  KILLED; the supervisor then kills the rest of the drive tree;
- a file planted in the sandbox before the run: a dropped supervisor with a stale gpu.lock, a
  commit in <sandbox>/git, a precondition gap (preconditions_ch2.json rows), a torn record.
Nothing here touches anything outside the sandbox it is given."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
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


def add(box: Path, row: Mapping) -> dict:
    """Append one fault row to the sandbox manifest; the manifest as written."""
    doc = read_manifest(box)
    doc["faults"] = [*(doc.get("faults") or []), dict(row)]
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
    """The fake for Deps.token_note: the expired token's message when F6 is planted, else None."""
    said = next((r.get("error") for r in manifest.get("faults") or () if r.get("kind") == "oauth"), None)
    return lambda: said


# ---- a kill at write k (a child's hook) ----------------------------------------------

def kill_at_write(kind: str, site: str, occurrence: int, step: str | None) -> dict:
    return {"kind": "kill_at_write", "file_kind": kind, "site": site, "occurrence": int(occurrence), "step": step}


def kill_rows(manifest: Mapping, step: str) -> list[dict]:
    rows = [r for r in manifest.get("faults") or () if r.get("kind") == "kill_at_write"]
    return [r for r in rows if r.get("step") in (None, step)]


def request_kill(box: Path, row: Mapping) -> None:
    """Tell the supervisor which fault fired, from which pid, before this process dies."""
    body = {"fault": dict(row), "pid": os.getpid(), "argv": sys.argv[:4]}
    (Path(box) / KILL_REQUEST).write_text(json.dumps(body), encoding="utf-8")


def kill_hook(row: Mapping, box: Path, exit: Callable[[int], None] = os._exit):
    """An audit hook counting writes at the row's site; at the k-th it dies before the write."""
    from studio.rehearsal import fence, trace
    seen = {"n": 0}

    def hook(event: str, args: tuple) -> None:
        if event != "open" or getattr(_BUSY, "on", False) or not fence.writes(args[1], args[2]):
            return
        if trace.kind_of(args[0], box) != row["file_kind"] or trace.site_of(sys._getframe(1)) != row["site"]:
            return
        seen["n"] += 1
        if seen["n"] == row["occurrence"]:
            _BUSY.on = True
            request_kill(box, row)
            exit(KILLED)
    return hook


def arm(manifest: Mapping, box: Path) -> int:
    """Install this process's kill hooks (its step's rows); how many were armed."""
    from studio.rehearsal import trace
    rows = kill_rows(manifest, trace.step_of(sys.argv))
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
