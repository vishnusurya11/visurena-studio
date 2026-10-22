"""The rehearsal supervisor (2026-10-21_ep02_proof DESIGN 3): the REAL scripts.episode.autopilot.tick,
called in-process in a loop, against the sandbox only.

Run as `python -m studio.rehearsal.supervisor --box <sandbox> --episode N --expected K` with
VISURENA_LIBRARY=<sandbox>/library, so `import studio` arms the fence, the fakes and the trace
first.  Deps, per DESIGN 3: `popen` launches the REAL drive.py with the sandbox env and a
`--rehearsal=<run_id>` argv tail; `procs` is only this supervisor's process tree (pid ancestry,
remembering every pid it ever held so an orphan of a killed drive stays visible); `git` the
sandbox repo (autopilot.git already answers from settings.git_root()); `brain` the real brain
code over P4's ReplayTransport, with the manifest's `brain_stream` scripted in front of it
(brain_script.py); `notify` a capture to <sandbox>/notify.jsonl; `root` <sandbox>/library/.autopilot;
`ledger` None; `token_note` the fake (the manifest's `youtube`); `chapters` the rehearsed unit.
The loop stops at a terminal of the unit (HELD_PUBLISH, PARKED, COMPLETE), or FAILS at twice the
expected ACTING ticks (a wait while the drive runs is not an act) or at the wall.  A moved HEAD
is handed over in process: the supervisor is its own successor, it never spawns one."""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Callable, Iterable, Mapping

from studio import settings

ROOT = Path(__file__).resolve().parents[2]
TERMINALS = ("HELD_PUBLISH", "PARKED", "COMPLETE")
WAIT = "wait"
WALL_S = 3600.0
RESULT = "supervisor.json"


# ---- the process tree ----------------------------------------------------------------

def parent_map() -> dict[int, int]:
    """{pid: parent pid} for every process (Toolhelp32 snapshot); {} off Windows."""
    if sys.platform != "win32":
        return {}
    import ctypes
    from ctypes import wintypes

    class Entry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD),
                    ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD),
                    ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]
    return _walk_snapshot(ctypes, Entry)


def _walk_snapshot(ctypes, Entry) -> dict[int, int]:
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)                       # TH32CS_SNAPPROCESS
    if not snap or snap == ctypes.c_void_p(-1).value:
        return {}
    entry, out = Entry(), {}
    entry.dwSize = ctypes.sizeof(Entry)
    ok = k32.Process32FirstW(ctypes.c_void_p(snap), ctypes.byref(entry))
    while ok:
        out[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
        ok = k32.Process32NextW(ctypes.c_void_p(snap), ctypes.byref(entry))
    k32.CloseHandle(ctypes.c_void_p(snap))
    return out


def descendants(parents: Mapping[int, int], roots: Iterable[int]) -> set[int]:
    """Every pid under `roots` (the roots included)."""
    found, frontier = set(roots), list(roots)
    children: dict[int, list[int]] = {}
    for pid, parent in parents.items():
        children.setdefault(parent, []).append(pid)
    while frontier:
        for child in children.get(frontier.pop(), ()):
            if child not in found:
                found.add(child)
                frontier.append(child)
    return found


def tree_procs(root: int, known: set, table: Callable | None = None, parents: Callable = parent_map) -> list:
    """The process-table rows under `root` or any pid this tree held before (kept in `known`)."""
    if table is None:
        from studio.command_center import procs
        table = procs.list_processes
    mine = descendants(parents(), {root, *known}) - {root}
    rows = [p for p in table() if p.pid in mine]
    known.update(p.pid for p in rows)
    return rows


# ---- Deps -------------------------------------------------------------------------------

def drive_argv_for(run_id: str, box: Path | None = None) -> Callable[[str, int], list[str]]:
    """The autopilot's own drive argv plus `--rehearsal=<run_id>` (drive.py reads argv[1:3] only).
    The autopilot asks for it only to launch, while no drive runs: a checkpoint still pending is
    copied first, so no relaunch ever runs past an uncopied one."""
    from scripts.episode import autopilot
    from studio.rehearsal import checkpoint_stop

    def argv(codex: str, n: int) -> list[str]:
        if box is not None:
            checkpoint_stop.take(box, launching=True)
        return [*autopilot.drive_argv(codex, n), f"--rehearsal={run_id}"]
    return argv


def notify_to(box: Path) -> Callable[[str], None]:
    """Deps.notify: every message the autopilot would send, one row in <sandbox>/notify.jsonl."""
    def say(text: str) -> None:
        row = {"ts": time.time(), "source": "autopilot", "text": str(text)}
        with open(Path(box) / "notify.jsonl", "a", encoding="utf-8") as out:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    return say


def make_deps(box: Path, manifest: Mapping, n: int):
    """autopilot.Deps per DESIGN 3, scoped to this sandbox and this unit."""
    from scripts.episode import autopilot
    from studio import engine_ops
    from studio.rehearsal import faults
    known: set = set()
    return autopilot.Deps(drive_argv=drive_argv_for(str(manifest["run_id"]), box),
                          procs=lambda: tree_procs(os.getpid(), known), notify=notify_to(box),
                          chapters=lambda book: [n], root=Path(box) / settings.LIBRARY_DIR / ".autopilot",
                          cpu_s=engine_ops.tree_cpu_s, outputs_at=autopilot.newest_output, ledger=None,
                          token_note=faults.token_note(manifest))


# ---- the loop -----------------------------------------------------------------------------

def terminal_of(doc: Mapping | None, n: int) -> str | None:
    """The unit's terminal state in a status doc; COMPLETE once the series has no unit left."""
    ep = (doc or {}).get("episode") or {}
    state = ep.get("state")
    if state == "COMPLETE" and ep.get("n") is None:
        return state
    return state if state in TERMINALS and ep.get("n") == n else None


def kill_on_request(box: Path, deps, codex: str, n: int) -> list[int]:
    """A child's kill-at-write fired: kill the rest of its drive tree, once per request."""
    from studio.rehearsal import faults
    asked = faults.kill_requested(box)
    if asked is None:
        return []
    os.replace(Path(box) / faults.KILL_REQUEST, Path(box) / "kill.done")
    return list(deps.engine.kill_run_tree(deps.procs(), codex, n) or [])


def sample(box: Path, book: Path, n: int, deps, out: dict) -> None:
    """Before each tick: a kill request answered, then the drives alive in the tree and spent_before."""
    from studio import run_budget
    out["killed"] += kill_on_request(box, deps, Path(book).name.split("_", 1)[0], n)
    rows = deps.procs()
    out["drives_alive"].append(sum(1 for p in rows if "drive.py" in p.cmdline.replace("\\", "/")))
    out["spent"].append(round(float(run_budget.spent_before(Path(book) / "episodes" / f"ep{n:02d}")), 3))


def one_tick(ap, book: Path, codex: str, deps, i: int, out: dict) -> dict | None:
    """One real tick; a raise is an event and a count (the real run_loop's rule), never a stop."""
    try:
        doc = ap.tick(book, codex, deps, i)
    except Exception as why:                                    # noqa: BLE001 -- counted, then the loop goes on
        out["tick_errors"] += 1
        ap.event(book, {"event": "tick_error", "error": repr(why)[:400]})
        return None
    out["states"].append(((doc.get("episode") or {}).get("state"), (doc.get("episode") or {}).get("action")))
    return doc


def hand_over(ap, book: Path, codex: str, deps, out: dict) -> None:
    """A moved HEAD (F7): the autopilot's own hand_over decides; this supervisor is the successor."""
    head = ap.hand_over(book, codex, deps, out["born"])
    if head is not None:
        out["handovers"].append(head)
        out["born"] = head
        ap.claim_supervisor(deps)


def fresh(deps) -> dict:
    return {"terminal": None, "ticks": 0, "acting": 0, "capped": None, "tick_errors": 0, "states": [],
            "handovers": [], "drives_alive": [], "spent": [], "killed": [], "started": time.time(),
            "born": deps.git("rev-parse", "HEAD").strip()}


def loop(ap, book: Path, codex: str, n: int, deps, expected: int, every: float, wall_s: float,
         before: Callable[[dict], str | None] | None = None) -> dict:
    """Tick until the unit's terminal; FAIL at 2 x the expected acting ticks or at the wall.
    `before(out)` runs ahead of every tick, while no tick is acting (a kill answered, a checkpoint
    copied between drives); a word it returns ends the run (BOUNDED)."""
    if not ap.claim_supervisor(deps):
        return {**fresh(deps), "capped": "supervisor lock held"}
    ap.adopt(book, deps)
    out, deadline = fresh(deps), time.monotonic() + wall_s
    while out["terminal"] is None and out["capped"] is None:
        go_round(ap, book, codex, n, deps, out, before)
        if out["terminal"] is None:
            out["capped"] = "ticks" if out["acting"] > 2 * expected else ("wall" if time.monotonic() > deadline else None)
        if out["terminal"] is None and out["capped"] is None:
            deps.sleep(every)
    return {**out, "ended": time.time()}


def go_round(ap, book: Path, codex: str, n: int, deps, out: dict, before: Callable[[dict], str | None] | None) -> None:
    """One round: the pre-tick hook, a moved HEAD handed over, one real tick.  The hook's word ends
    the run AFTER the hand-over: the round a bounded drive ends in is the round a commit made under
    it is handed over (autopilot.hand_over waits for the drive; F7, window 3)."""
    out["ticks"] += 1
    word = before(out) if before is not None else None
    hand_over(ap, book, codex, deps, out)
    if word:
        out["terminal"] = word
        return
    doc = one_tick(ap, book, codex, deps, out["ticks"], out)
    out["terminal"] = terminal_of(doc, n)
    out["acting"] += bool(doc) and (doc.get("episode") or {}).get("action") != WAIT


# ---- boundaries: checkpoints, bounded runs, a commit mid-run ----------------------------------

STEP_LINE = re.compile(r"^--- step (\d{2}) ", re.MULTILINE)
BEFORE_STEP = re.compile(r"PAUSED AT BOUNDARY \| .* \| before step (\d{2})")
"""The real runner's line for a unit stopped in front of a step (step_runner._paused)."""


def last_log(home: Path) -> str:
    logs = sorted(Path(home).glob("drive_run*.log"))
    return logs[-1].read_text(encoding="utf-8", errors="replace") if logs else ""


def latest_step(home: Path) -> int:
    """The highest step the last run started (0 before any)."""
    return max((int(s) for s in STEP_LINE.findall(last_log(home))), default=0)


def checkpoint_tick(box: Path, alive: bool, state: dict) -> None:
    """S0a's checkpoint maker: the runner stopped a drive in front of a due checkpoint
    (checkpoint_stop, between steps only); once that drive is down it is copied, once."""
    from studio.rehearsal import checkpoint_stop
    if not alive and (name := checkpoint_stop.take(box)):
        state["made"].append(name)


def bounded_tick(home: Path, alive: bool, bound: str) -> str | None:
    """A bounded run (3): past the faulted step the drive is asked to stop at the next boundary; a
    stopped drive past it ends the run BOUNDED."""
    from studio import boundary
    past = latest_step(home) > int(bound)
    if past and alive and not boundary.requested(home):
        boundary.request(home, f"rehearsal bound: step {bound} and one boundary")
    return "BOUNDED" if past and not alive and "PAUSED AT BOUNDARY" in last_log(home) else None


def commit_tick(box: Path, manifest: Mapping, tick: int) -> list[str]:
    """F7/F7b: a planted `commit` row lands in <sandbox>/git at its tick."""
    from studio.rehearsal import faults
    rows = [r for r in manifest.get("harness_faults") or () if r.get("kind") == "commit" and int(r.get("tick", 0)) == tick]
    return [faults.sandbox_commit(box, r.get("path")) for r in rows]


def before_tick(box: Path, book: Path, n: int, deps, manifest: Mapping, state: dict) -> Callable[[dict], str | None]:
    """The child's pre-tick hook: sample, answer a kill, plant a commit, make checkpoints, bound."""
    home = Path(book) / "episodes" / f"ep{n:02d}"

    def hook(out: dict) -> str | None:
        sample(box, book, n, deps, out)
        out.setdefault("commits", []).extend(commit_tick(box, manifest, out["ticks"]))
        alive = bool(out["drives_alive"][-1])
        if manifest.get("checkpoints"):
            checkpoint_tick(box, alive, state)
            out["checkpoints"] = state["made"]
        return bounded_tick(home, alive, str(manifest["bound"])) if manifest.get("bound") else None
    return hook


# ---- the child entry ------------------------------------------------------------------------

def start_engine(box: Path, manifest: Mapping):
    """The fake ComfyUI in this process, when the manifest wants one and P3's module is on disk."""
    if manifest.get("engine") is False or importlib.util.find_spec("studio.rehearsal.fake_comfy") is None:
        return None
    from studio.rehearsal import fake_comfy
    return fake_comfy.FakeComfy.from_manifest(box).start()


def book_dir(box: Path, manifest: Mapping) -> Path:
    from studio.rehearsal import sandbox
    return Path(box) / settings.LIBRARY_DIR / sandbox.book_name(str(manifest.get("codex") or sandbox.SANDBOX_CODEX))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="run the real autopilot tick on a rehearsal sandbox")
    p.add_argument("--box", required=True)
    p.add_argument("--episode", type=int, required=True)
    p.add_argument("--expected", type=int, required=True)
    p.add_argument("--every", type=float, default=1.0)
    p.add_argument("--wall", type=float, default=WALL_S)
    return p


def main(argv: list[str]) -> int:
    """Arm (import studio), start the fake engine, loop, write <sandbox>/supervisor.json."""
    args = parser().parse_args(argv)
    sys.path.insert(0, str(ROOT))
    from scripts.episode import autopilot                      # `import studio` (above) armed this process
    box, manifest = Path(args.box), settings.rehearsal()
    if manifest is None or Path(settings.sandbox()).resolve() != box.resolve():
        raise SystemExit(f"refused: {box} is not this process's rehearsal sandbox")
    from studio.rehearsal import brain_script, faults
    os.environ[faults.SUPERVISOR_ENV] = str(os.getpid())       # a drive tree's kill stops below this process
    brain_script.install(manifest, box)                        # the brain runs in THIS process
    engine, deps = start_engine(box, manifest), make_deps(box, manifest, args.episode)
    book = book_dir(box, manifest)
    hook = before_tick(box, book, args.episode, deps, manifest, {"made": []})
    out = loop(autopilot, book, str(manifest.get("codex")), args.episode, deps, args.expected, args.every,
               args.wall, before=hook)
    (box / RESULT).write_text(json.dumps(out, indent=1), encoding="utf-8")
    if engine is not None:
        engine.stop()
    return 0 if out["terminal"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
