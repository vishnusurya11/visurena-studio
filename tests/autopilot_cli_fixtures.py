"""Fakes for the autopilot CLI tests (decision 2026-10-06, lane D).  Nothing
here spends, spawns a real drive, or reads this machine's process table: the
CLI takes every outward call as a `Deps` field, and these are the stand-ins.

    load()        the CLI module, by file (scripts/episode has no package)
    book(tmp)     a book folder with three chapters and no episode yet
    deps(tmp, ..) a Deps whose popen, procs, engine, notify, derive, brain and
                  next_unit are all recorded fakes
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
CODEX = "20990101000000"


def load():
    """The CLI module under test, loaded once by path."""
    if "autopilot_cli" in sys.modules:
        return sys.modules["autopilot_cli"]
    spec = importlib.util.spec_from_file_location("autopilot_cli", ROOT / "scripts" / "episode" / "autopilot.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["autopilot_cli"] = mod
    spec.loader.exec_module(mod)
    return mod


def book(tmp: Path, chapters: int = 3) -> Path:
    """A book under a fake library: `source/chapters/ch_NN.json` for 1..chapters."""
    root = tmp / "library" / f"{CODEX}_a-fake-book"
    for n in range(0, chapters + 1):
        path = root / "source" / "chapters" / f"ch_{n:02d}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"n": n}), encoding="utf-8")
    return root


def derived(state: str, reason: str = "", order=None, packet=None):
    return SimpleNamespace(state=state, reason=reason, order=order, packet=packet or {})


class FakeProc:
    """What a fake Popen returns: a pid and nothing else the CLI reads."""

    def __init__(self, pid: int = 777):
        self.pid = pid


class FakeEngine:
    """engine_ops as the CLI sees it; every call is counted."""

    def __init__(self, up: bool = True, prompt: str | None = None):
        self.up, self.prompt, self.calls = up, prompt, []

    def alive(self, base_url: str) -> bool:
        self.calls.append("alive")
        return self.up

    def queue(self, base_url: str) -> dict:
        self.calls.append("queue")
        return {"queue_running": [[1, self.prompt]] if self.prompt else []}

    def drive_alive(self, rows, codex, n):
        from studio import engine_ops
        return engine_ops.drive_alive(rows, codex, n)      # pure; the real rule, counted nowhere

    def kill_run_tree(self, rows, codex, n):
        self.calls.append("kill_run_tree")
        return []

    def kill_engine(self, rows):
        self.calls.append("kill_engine")
        return []

    def restart(self):
        self.calls.append("restart")
        return True


def deps(tmp: Path, state: str = "IDLE", *, reason: str = "", order=None, procs=(), engine=None,
         brain=None, now=None, chapters=(1, 2, 3)):
    """A Deps with every outward call faked and recorded on `.calls`."""
    cli = load()
    calls = {"popen": [], "notify": [], "orders": []}

    def popen(argv, **kw):
        calls["popen"].append((argv, kw))
        return FakeProc()

    def next_unit(chaps, uploads, parked, last):
        done = {r["episode"] for r in uploads if r.get("privacy") == "public"} | {r["episode"] for r in parked}
        return next((n for n in chaps if n not in done and n <= last), None)

    d = cli.Deps(popen=popen, drive_argv=lambda codex, n: ["fake-drive", codex, str(n)],
                 procs=lambda: list(procs), git=lambda *a: "" if a[0] == "status" else "abc123def\n",
                 engine=engine or FakeEngine(), notify=lambda text: calls["notify"].append(text),
                 derive=lambda signals, n: derived(state, reason, order),
                 next_unit=next_unit, chapters=lambda book: list(chapters),
                 brain=brain or (lambda book, codex, n, packet, path: {"verdict": "park", "why": "fake"}),
                 order=lambda codex, n, order: calls["orders"].append((codex, n, order)) or 1,
                 spent_usd=lambda codex, n: 0.0, now=now or (lambda: 1_000_000.0), sleep=lambda s: None,
                 pid=4242, root=tmp / "library" / ".autopilot")
    d.calls = calls
    return d
