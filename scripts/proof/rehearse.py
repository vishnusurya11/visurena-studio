"""Run a rehearsal scenario (2026-10-21_ep02_proof DESIGN 3) and write its counted rows.

    uv run --no-sync python scripts/proof/rehearse.py <scenario|all|checkpoints> [--run-id ID] [--results DIR]

This process is the HARNESS: it never sets VISURENA_LIBRARY on itself, so it is unfenced and
reads only (the real repo's git log for the graph diff, the stat guard, the sandbox's files).
Each point runs in a CHILD: `python -m studio.rehearsal.supervisor` with the sandbox env, which
arms the fence, the fakes and the trace, and calls the REAL autopilot tick.  Per point: restore
the checkpoint, plant ONE fault, run, assert (3.1), trace; per scenario: points tried, distinct
recovery traces, passes over distinct traces (3.3).  A sweep runs in shards of `--budget-hours`
(4 h) at the measured cost of its unfaulted baseline; the next run on the same sandbox resumes
the untried points, and a scenario with untried points is never a pass.  A scenario whose packages, checkpoint or
fixture are missing writes one row that says so (passed: false, `blocked: ...`): never a pass,
never extrapolated.  Before any real-book rehearsal the harness refuses while the real
Task Scheduler entry is enabled or a real series is unpaused (activate's own rule).
Rows land in docs/audit/2026-10-21_ep02_proof/results/<id>.json (git-ignored)."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import settings  # noqa: E402
from studio.rehearsal import activate, asserts, faults, guard, sandbox, sweep, trace  # noqa: E402

SCENARIOS = ROOT / "tests" / "fixtures" / "proof" / "scenarios"
PROOF = ROOT / "docs" / "audit" / "2026-10-21_ep02_proof"
RESULTS = PROOF / "results"
ROW_KEYS = asserts.ROW_KEYS
PACKAGES = {"engine": "studio.rehearsal.fake_comfy", "fakes": "studio.rehearsal.fakes",
            "sdk": "studio.rehearsal.fake_sdk", "recordings": "studio.rehearsal.recordings"}
FILES = {"preconditions": RESULTS / "preconditions_ch2.json", "writer": SCENARIOS / "S0b" / "writer_stream.json"}
"""Inputs a scenario stands on that are files: P2's ch2 audit, SR-2's recorded writer session."""
REAL = ("engine", "fakes", "sdk", "recordings")


@dataclass(frozen=True)
class Scenario:
    id: str
    episode: int
    checkpoint: str
    expected: int
    needs: tuple[str, ...] = REAL
    sweep: str | None = None            # take | write | record
    fault: Mapping = field(default_factory=dict)
    bound: str | None = None            # the faulted step: run to its end plus one boundary
    why: str = ""


def take(sid: str, kind: str, why: str, detail: str | None = None) -> Scenario:
    return Scenario(sid, 1, "after_08", 12, sweep="take", fault={"kind": kind, "detail": detail}, bound="09", why=why)


TABLE: dict[str, Scenario] = {s.id: s for s in (
    Scenario("smoke", 2, "after_12", 1, needs=(), fault={"kind": "tear", "record": ".autopilot/heartbeat.json"},
             why="one checkpoint, one take, one fault: the supervisor's torn heartbeat read by the real tick"),
    Scenario("S0a", 1, "fresh", 60, fault={"kind": "none", "checkpoints": True}, why="ep01 replayed fresh"),
    Scenario("S0b", 2, "fresh", 60, needs=(*REAL, "writer"), fault={"kind": "none"}, why="ep02 on SR-2's plan"),
    take("F1", "crash", "engine crash mid-09"), take("F1b", "lost", "engine never returns"),
    take("F9", "hang", "ComfyUI hang"), take("F10", "exec_error", "transient exec error"),
    take("F13", "corrupt", "corrupt output", "zero_byte"), take("F16", "exec_fatal", "non-transient exec error"),
    Scenario("F2", 1, "after_08", 12, sweep="write", fault={"kind": "kill", "step": "09"}, bound="09", why="drive killed mid-09"),
    Scenario("F3", 1, "after_09", 8, sweep="write", fault={"kind": "kill", "step": "10"}, bound="10", why="drive killed mid-10"),
    Scenario("F4", 1, "after_08", 12, fault={"kind": "reboot"}, bound="09", why="reboot: stale gpu.lock, dead supervisor"),
    Scenario("F5", 2, "fresh", 12, needs=(*REAL,), fault={"kind": "none", "writer_plan": "ep01"}, bound="02",
             why="the renumbered ep01 plan refused by the plan gate"),
    Scenario("F6", 1, "after_12", 6, fault={"kind": "oauth"}, why="OAuth expired at 13 (a sandbox standing.json lists ep01)"),
    Scenario("F7", 1, "after_05", 12, fault={"kind": "commit", "tick": 2}, bound="06", why="a commit mid-run"),
    Scenario("F7b", 1, "after_05", 12, fault={"kind": "commit", "tick": 2, "path": "scripts/episode/takes_r2v.py"},
             bound="06", why="a guarded-path commit mid-run"),
    Scenario("F8", 1, "after_12", 6, fault={"kind": "repair_window"},
             why="a stale repair window on the delivered ep01, no owner order behind it"),
    Scenario("F11", 1, "after_07", 10, fault={"kind": "unreadable", "first": 3}, bound="08", why="unreadable VL"),
    Scenario("F14", 2, "fresh", 20, needs=(*REAL, "preconditions"), fault={"kind": "gaps"}, bound="04",
             why="the ch2 precondition gaps planted"),
    Scenario("F15", 1, "after_09", 10, fault={"kind": "rate_limit", "call": 1}, bound="10", why="rate limit"),
    Scenario("F17", 1, "after_09", 10, fault={"kind": "worker_death", "worker": "whisper", "line": 2}, bound="10",
             why="the whisper worker dies"),
    Scenario("F18", 1, "after_08", 12, sweep="record", fault={"kind": "tear"}, bound="09", why="torn records"),
)}
CHECKPOINTS = ("after_02", "after_05", "after_07", "after_08", "after_09", "after_12")


# ---- what a scenario stands on -------------------------------------------------------------

def module_present(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def missing_packages(sid: str, present: Callable[[str], bool] = module_present) -> list[str]:
    """The modules and input files the scenario stands on that are not on disk."""
    sc = TABLE[sid]
    mods = [PACKAGES[k] for k in sc.needs if k in PACKAGES and not present(PACKAGES[k])]
    return mods + [str(FILES[k]) for k in sc.needs if k in FILES and not Path(FILES[k]).is_file()]


SKIPPABLE = ("refused:", "absent:")
"""The only blocks a test may skip: the real scheduler refused, or an input is not on disk yet.  Any
other block (a checkpoint absent, prepare() failing) is a FAILURE, never a skip."""


def skippable(out: Mapping) -> bool:
    return bool(out.get("blocked")) and all(str(b).startswith(SKIPPABLE) for b in out["blocked"])


def blocked_row(sid: str, why: str) -> dict:
    return asserts.row(sid, False, [], question="Q6", instrument_state=f"blocked: {why}", n_points=0,
                       detail=f"not run: {why}")


# ---- the sandbox ----------------------------------------------------------------------------

def stage(box: Path, fixture: Path) -> Path:
    """A scenario fixture into the sandbox: book/ -> the sandbox book, autopilot_root/ -> library/.autopilot."""
    book = Path(box) / settings.LIBRARY_DIR / sandbox.book_name()
    for src, dest in ((fixture / "book", book), (fixture / "autopilot_root", Path(box) / settings.LIBRARY_DIR / ".autopilot")):
        if src.is_dir():
            shutil.copytree(src, dest, dirs_exist_ok=True)
    return book


def real_box(run_id: str, sc: Scenario) -> Path:
    """A sandbox of the real Jekyll book (named records, read once into the golden copy)."""
    real = settings.REAL_LIBRARY / f"{sandbox.REAL_CODEX}_{sandbox.SLUG}"
    port = f"http://127.0.0.1:{free_port()}"
    return sandbox.build(run_id, source_book=real, real_db=settings.REPO / settings.db_path(env={}), episode=sc.episode,
                         manifest={"fakes": True, "comfy_host": port})


def free_port() -> int:
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def refuse_if_live() -> None:
    """The real autopilot could run: no rehearsal of the real book starts (activate's rule, asked here first)."""
    from studio.rehearsal import activate
    series = lambda: [p for lib in settings.real_libraries(env={}) for p in activate.unpaused_series(lib)]
    activate.refuse_live_autopilot(activate.schtasks_query, series)


def set_manifest(box: Path, fields: Mapping) -> dict:
    doc = {**faults.read_manifest(box), **fields}
    (Path(box) / "rehearsal.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return doc


# ---- one point ------------------------------------------------------------------------------

def child_env(box: Path, cleared: bool) -> dict:
    """The child's env: the one variable, and (tests on a tmp sandbox only) the parent's scheduler verdict."""
    from studio.rehearsal import activate
    env = {k: v for k, v in os.environ.items() if k not in (settings.ENV, activate.CLEARED)}
    env[settings.ENV] = str(Path(box) / settings.LIBRARY_DIR)
    if cleared:
        env[activate.CLEARED] = f"{int(time.time())}|{box}"
    return env


def launch_supervisor(box: Path, sc: Scenario, cleared: bool, every: float, wall: float) -> dict:
    """The child supervisor to its end; its supervisor.json (or the failure that stopped it)."""
    argv = [sys.executable, "-m", "studio.rehearsal.supervisor", "--box", str(box), "--episode", str(sc.episode),
            "--expected", str(sc.expected), "--every", str(every), "--wall", str(wall)]
    done = subprocess.run(argv, cwd=ROOT, env=child_env(box, cleared), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=wall + 120)
    (Path(box) / "supervisor.log").write_text(done.stdout + done.stderr, encoding="utf-8")
    result = Path(box) / "supervisor.json"
    if result.is_file():
        return json.loads(result.read_text(encoding="utf-8"))
    return {"terminal": None, "capped": f"supervisor exit {done.returncode}", "tick_errors": 0,
            "error": (done.stderr or done.stdout)[-800:], "spent": [], "drives_alive": []}


def clear_run(box: Path) -> None:
    """A point's own traces, writes and logs start empty (they are not in a checkpoint)."""
    for name in (trace.TRACES, trace.WRITES):
        shutil.rmtree(Path(box) / name, ignore_errors=True)
    for name in ("supervisor.json", "tripwire.jsonl", "notify.jsonl", "engine_log.jsonl", "vl_consumers.jsonl",
                 faults.KILL_REQUEST, "kill.done"):
        (Path(box) / name).unlink(missing_ok=True)


def plant(box: Path, book: Path, sc: Scenario, point: sweep.Point) -> dict:
    """The point's ONE fault, into the restored sandbox; what was planted."""
    kind, w = sc.fault.get("kind"), point.where
    if sc.sweep == "take":
        return faults.add(box, faults.engine(sc.fault["kind"], w["k"], w["workflow"], sc.fault.get("detail")))
    if sc.sweep == "write":
        return faults.add(box, faults.kill_at_write(w["kind"], w["site"], w["occurrence"], w["step"]))
    if kind == "tear":
        path = faults.record_path(book, sc.episode, w.get("record") or sc.fault["record"])
        return {"torn": str(path), "kept": faults.tear(path)} if path.is_file() else {"torn": None, "absent": str(path)}
    return plant_other(box, book, sc)


def plant_other(box: Path, book: Path, sc: Scenario) -> dict:
    kind = sc.fault.get("kind")
    if kind == "reboot":
        faults.drop_supervisor(box, faults.dead_pid(), sc.episode, time.time())
        return {"reboot": True}
    if kind == "commit":
        return faults.add(box, {"kind": "commit", "tick": sc.fault["tick"], "path": sc.fault.get("path")})
    if kind == "oauth":
        standing(book, sc.episode)
        return faults.add(box, faults.oauth_expired())
    if kind == "repair_window":
        return {"window": stale_window(asserts.home_of(book, sc.episode))}
    if kind == "unreadable":
        return [faults.add(box, faults.engine("unreadable", k)) for k in range(1, sc.fault["first"] + 1)][-1]
    if kind == "rate_limit":
        return faults.add(box, faults.rate_limit(sc.fault["call"]))
    if kind == "worker_death":
        return faults.add(box, faults.worker_death(sc.fault["worker"], sc.fault["line"]))
    if kind == "gaps":
        return {"gaps": faults.plant_all(book, json.loads(FILES["preconditions"].read_text(encoding="utf-8")))}
    return {"none": True}


UNOWNED_ORDER = 999_999
"""A work-order id no owner receipt carries: the window it backs is unbacked (F8)."""


def stale_window(home: Path) -> dict:
    """F8: an open repair window an hour old whose order no owner receipt backs (repair_clock's own writer)."""
    from studio import repair_clock
    return repair_clock.open_window(home, {"09": UNOWNED_ORDER}, started=time.time() - 3600.0)


def standing(book: Path, n: int) -> Path:
    """F6's setup: the SANDBOX book's standing approval lists the episode, so step 13 reaches the send."""
    from studio import standing_approval
    path = standing_approval.path(book)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"kind": "publish", "decision": standing_approval.DECISION, "by": "rehearsal (sandbox)",
                                "at": time.strftime("%Y-%m-%d"), "episodes": [n]}), encoding="utf-8")
    return path


def assert_point(box: Path, book: Path, sc: Scenario, sup: Mapping, before: list[dict], expect_trip: bool) -> list[dict]:
    """The common asserts of 3.1 for one point."""
    home, engine = asserts.home_of(book, sc.episode), asserts.jsonl(Path(box) / "engine_log.jsonl")
    notify = [r.get("text") or r.get("message") or json.dumps(r) for r in asserts.jsonl(Path(box) / "notify.jsonl")]
    trips = asserts.jsonl(Path(box) / "tripwire.jsonl")
    resume = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in sorted(home.glob("drive_run*.log")))
    records = [faults.record_path(book, sc.episode, r) for r in faults.RECORDS]
    rows = [asserts.a_caps(book, sc.episode), asserts.a_noupload(book, before, trips),
            asserts.a_real(trips, [], expect_trip=expect_trip),
            asserts.a_torn(records, resume + json.dumps(asserts.jsonl(book / "autopilot" / "events.jsonl"))),
            asserts.a_ledger(home, steps_since(home, sup.get("started", 0.0)), list(sup.get("spent") or []))]
    rows += [asserts.a_named(book, sc.episode, notify)]                 # a missing status doc FAILS it
    if engine:
        consumers, ladder = asserts.jsonl(Path(box) / "vl_consumers.jsonl"), home / "takes" / "r2v" / "ladder.json"
        at, flight = fault_moment(engine)
        rows += [asserts.a_honest(engine, consumers, shape_of(engine)), asserts.a_canned(engine, consumers),
                 asserts.a_norerender(engine, json.loads(ladder.read_text(encoding="utf-8")) if ladder.is_file() else {},
                                      at, flight)]
    return rows


def anchored(rows: list[dict], box: Path, book: Path) -> list[dict]:
    """Every relative evidence path made absolute: sandbox files under <sandbox>, book records under
    the sandbox book, so the report can see a sandbox clock and refuse it for Q5/Q7 (R15)."""
    def where(e: str) -> str:
        if Path(e).is_absolute():
            return e
        return str((Path(book) if e.split("/")[0] in ("autopilot", "episodes", "uploads.jsonl") else Path(box)) / e)
    return [{**r, "evidence": [where(e) for e in r["evidence"]]} for r in rows]


def fault_moment(engine_rows: list[Mapping]) -> tuple[float, int | None]:
    """(epoch of the first faulted answer, the take index it hit); (0.0, None) when unfaulted."""
    hit = next((r for r in engine_rows if r.get("fault")), None)
    if hit is None:
        return 0.0, None
    try:
        at = datetime.fromisoformat(str(hit.get("ts"))).timestamp()
    except ValueError:
        at = 0.0
    return at, asserts.take_index(hit)


def steps_since(home: Path, since: float) -> list[str]:
    """Steps whose `--- step NN` line a drive run logged after `since` (the steps that ran)."""
    from studio.rehearsal import supervisor
    logs = [p for p in Path(home).glob("drive_run*.log") if p.stat().st_mtime >= since]
    return sorted({s for p in logs for s in supervisor.STEP_LINE.findall(p.read_text(encoding="utf-8", errors="replace"))})


def shape_of(engine_rows: list[Mapping]) -> str:
    return next((str(r.get("shape")) for r in engine_rows if r.get("header")), "unknown")


def run_point(box: Path, book: Path, sc: Scenario, point: sweep.Point, cleared: bool, every: float, wall: float) -> dict:
    """Restore, plant, run the child supervisor, assert, trace: one point's result."""
    if sc.checkpoint != "fresh":
        sandbox.restore(box, sc.checkpoint)
    clear_run(box)
    set_manifest(box, {**faults.CLEAN, "bound": sc.bound, "checkpoints": bool(sc.fault.get("checkpoints"))})
    planted, before, began = plant(box, book, sc, point), asserts.jsonl(book / "uploads.jsonl"), time.monotonic()
    sup = launch_supervisor(box, sc, cleared, every, wall)
    served = asserts.a_served({**sc.fault, "kind": "kill" if sc.sweep == "write" else sc.fault.get("kind")}, box, sup,
                              planted if isinstance(planted, dict) else None)
    rows = anchored(assert_point(box, book, sc, sup, before, expect_trip=False) + asserts.specific(sc.id, box, book, sup)
                    + ([served] if served else []), box, book)
    lines = trace.read_all(Path(box) / trace.TRACES)
    passed = bool(sup.get("terminal")) and not sup.get("tick_errors") and all(r["passed"] for r in rows)
    return {"id": point.id, "passed": passed, "trace": trace.signature(lines) if lines else None, "rows": rows,
            "match_classes": point_classes(rows),
            "supervisor": sup, "planted": planted, "seconds": round(time.monotonic() - began, 1),
            "trace_lines": sorted(lines)}


def baseline(box: Path, book: Path, sc: Scenario, cleared: bool, every: float, wall: float) -> Path:
    """A sweep's UNFAULTED run from its checkpoint, write sites recorded: its engine_log.jsonl and
    writes/ are the point list's source (3.3), kept in <sandbox>/baseline."""
    if sc.checkpoint != "fresh":
        sandbox.restore(box, sc.checkpoint)
    clear_run(box)
    set_manifest(box, {**faults.CLEAN, "bound": sc.bound, "record_writes": True, "checkpoints": False})
    began = time.monotonic()
    launch_supervisor(box, sc, cleared, every, wall)
    seconds = round(time.monotonic() - began, 1)
    dest = Path(box) / "baseline"
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir()
    for name in ("engine_log.jsonl", trace.WRITES, "supervisor.json"):
        src = Path(box) / name
        if src.is_dir():
            shutil.copytree(src, dest / name)
        elif src.is_file():
            shutil.copy2(src, dest / name)
    set_manifest(box, {"record_writes": False})
    (dest / "seconds.json").write_text(json.dumps({"seconds": seconds}), encoding="utf-8")
    return dest


# ---- the points of a scenario -----------------------------------------------------------------

def points_of(box: Path, sc: Scenario) -> list[sweep.Point]:
    """The sweep's point list from the unfaulted run's records, or the scenario's one point."""
    if sc.sweep == "take":
        return sweep.take_points(sc.id, asserts.jsonl(Path(box) / "baseline" / "engine_log.jsonl"))
    if sc.sweep == "write":
        rows = [r for p in sorted((Path(box) / "baseline" / trace.WRITES).glob("*.jsonl")) for r in asserts.jsonl(p)]
        return sweep.write_points(sc.id, rows, sc.fault["step"])
    if sc.sweep == "record":
        return sweep.record_points(faults.RECORDS, [sc.checkpoint], sc.id)
    return [sweep.Point(sc.id, {"checkpoint": sc.checkpoint})]


LIVE_WRITERS = {"gpu_ledger.py": (r"library[\\/]\.device[\\/]gpu_util\.jsonl$",),
                "autopilot.py": (r"library[\\/]\.autopilot([\\/][^\\/]+)?$", r"library[\\/][^\\/]+[\\/]autopilot([\\/][^\\/]+)?$")}
"""A real process this machine runs outside any rehearsal (the GPU ledger, the scheduled autopilot
loop, which ticks even while every series is paused or complete) and the real paths it rewrites."""


def live_writers(table: Callable | None = None) -> dict[str, int]:
    """{process mark: pid} for each live writer running OUTSIDE this harness's process tree."""
    from studio.command_center import procs
    from studio.rehearsal import supervisor
    mine = supervisor.descendants(supervisor.parent_map(), {os.getpid()})
    rows = (table or procs.list_processes)()
    return {mark: p.pid for mark in LIVE_WRITERS for p in rows if mark in p.cmdline and p.pid not in mine}


def excused_by(line: str, live: Mapping[str, int]) -> str | None:
    """The live writer whose own paths a touched line names, or None."""
    path = line.split(": ", 1)[-1]
    return next((m for m in live if any(re.search(rx, path) for rx in LIVE_WRITERS.get(m, ()))), None)


def guard_row(snap: Mapping, writers: Callable[[], dict] = live_writers) -> dict:
    """A-real's stat guard over the scenario.  A path a live writer OUTSIDE the rehearsal rewrites is
    excused BY NAME with its pid (the fence's empty tripwire, not this guard, proves no rehearsal
    process wrote it); every other moved path fails the row."""
    lines, live = guard.touched(dict(snap), guard.snapshot(guard.named_paths())), writers()
    by = {ln: excused_by(ln, live) for ln in lines}
    r = asserts.a_real([], [ln for ln, who in by.items() if who is None], instrument="guard")
    note = "; ".join(f"excused {ln.split(': ', 1)[-1]}: {who} pid {live[who]} outside the rehearsal"
                     for ln, who in by.items() if who)
    return {**r, "detail": "; ".join(x for x in (r["detail"], note) if x)}


def point_classes(rows) -> dict:
    """A point's engine answers by match class, summed over its rows."""
    out: dict = {}
    for row in rows:
        for k, v in (row.get("match_classes") or {}).items():
            out[k] = out.get(k, 0) + v
    return out


def summary_row(sc: Scenario, results: list[dict], planned: int) -> dict:
    """Passes over DISTINCT recovery traces (3.3): the scenario's own counted row."""
    t = sweep.tally(results, planned)
    classes: dict = {}
    for r in results:
        for k, v in (r.get("match_classes") or point_classes(r.get("rows") or ())).items():
            classes[k] = classes.get(k, 0) + v
    ok = t["n_distinct"] > 0 and t["passed_distinct"] == t["n_distinct"] and not t["failing"] and not t["untried"]
    rest = f"; {t['untried']} untried: run again to continue the sweep" if t["untried"] else ""
    return asserts.row(sc.id, ok, [f"results/{sc.id}.json"], n_points=t["tried"], n_distinct=t["n_distinct"],
                       match_classes=classes, instrument="trace", instrument_state=f"untried {t['untried']}",
                       detail=f"{t['passed_distinct']}/{t['n_distinct']} distinct traces passed; failing {t['failing'][:5]}{rest}")


def write_results(results: Path, sid: str, rows: list[dict], extra: Mapping) -> Path:
    results.mkdir(parents=True, exist_ok=True)
    path = results / f"{sid}.json"
    path.write_text(json.dumps({"scenario": sid, "written": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "rows": rows,
                                **extra}, indent=1, default=str), encoding="utf-8")
    return path


CHECKPOINT_RUN = "ckpt_ep{n:02d}"
"""S0a's sandboxes are named so: the fault scenarios restore their checkpoints from the newest one."""


def checkpoint_box(n: int, name: str, base: Path | None = None) -> Path | None:
    """The newest S0a sandbox of episode n that holds checkpoint `name`, or None."""
    base = Path(base or sandbox.default_base())
    boxes = sorted(base.glob(CHECKPOINT_RUN.format(n=n) + "_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return next((b for b in boxes if (b / "checkpoints" / name).is_dir()), None)


def prepare(sid: str, sc: Scenario, box: Path | None, run_id: str | None) -> tuple[Path | None, Path | None, str | None]:
    """(sandbox, book, why it cannot run): a staged fixture, a fresh sandbox of the real book (S0a
    names it for its checkpoints), or the S0a sandbox holding the scenario's checkpoint."""
    fixture = SCENARIOS / sid
    if box is not None and (fixture / "book").is_dir():
        book = stage(box, fixture)
        set_manifest(box, {"comfy_host": f"http://127.0.0.1:{free_port()}"})
        sandbox.checkpoint(box, sc.checkpoint)
        return box, book, None
    refuse_if_live()
    if sc.checkpoint == "fresh":
        name = CHECKPOINT_RUN.format(n=sc.episode) if sid == "S0a" else sid
        box = real_box(run_id or f"{name}_{uuid.uuid4().hex[:8]}", sc)
    else:
        box = checkpoint_box(sc.episode, sc.checkpoint)
    if box is None:
        return None, None, f"checkpoint {sc.checkpoint} absent: run `rehearse.py checkpoints` (S0a) first"
    return box, Path(box) / settings.LIBRARY_DIR / sandbox.book_name(), None


def blocked(results: Path, sid: str, why: str, extra: Mapping | None = None) -> dict:
    """The one row a scenario that cannot run writes: passed false, the reason named."""
    path = write_results(Path(results), sid, [blocked_row(sid, why)], dict(extra or {}))
    return {"scenario": sid, "blocked": [why], "path": str(path)}


def shard_of(points: list[sweep.Point], done: set[str], cost_s: float | None, budget_s: float) -> list[sweep.Point]:
    """The points this run tries: the next shard at the MEASURED cost of one point, or every untried
    point when no cost has been measured (a one-point scenario)."""
    if cost_s:
        return sweep.next_shard(points, done, cost_s, budget_s)["run"]
    return [p for p in points if p.id not in done]


def run_budgeted(todo: list[sweep.Point], run: Callable, budget_s: float, clock: Callable[[], float] = time.monotonic) -> list[dict]:
    """Each point in turn; the shard stops when the clock says the next one (at the mean so far) overruns."""
    out, t0 = [], clock()
    for point in todo:
        spent = clock() - t0
        if out and spent + spent / len(out) > budget_s:
            break
        out.append(run(point))
    return out


def prior_shard(results: Path, sid: str, box: Path) -> tuple[list[dict], list[dict]]:
    """(the points, their rows) an earlier shard of this scenario left for THIS sandbox; ([], []) else.
    The summary and guard rows are the run's own, never carried."""
    try:
        doc = json.loads((Path(results) / f"{sid}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [], []
    if doc.get("box") != str(box):
        return [], []
    return list(doc.get("points") or []), [r for r in doc.get("rows") or () if r.get("instrument") not in ("trace", "guard")]


def baseline_cost(box: Path) -> float | None:
    try:
        return float(json.loads((Path(box) / "baseline" / "seconds.json").read_text(encoding="utf-8"))["seconds"])
    except (OSError, ValueError, KeyError):
        return None


def run_points(box: Path, book: Path, sc: Scenario, cleared: bool, every: float, wall: float,
               done: set[str], budget_s: float) -> tuple[list[dict], int]:
    """A sweep's baseline first (it measures a point's cost), then the next shard: (results, planned)."""
    if sc.sweep in ("take", "write"):
        baseline(box, book, sc, cleared, every, wall)
    points = points_of(box, sc)
    todo = shard_of(points, done, baseline_cost(box), budget_s)
    run = lambda p: run_point(box, book, sc, p, cleared, every, wall)  # noqa: E731
    return run_budgeted(todo, run, budget_s), len(points)


def run_scenario(sid: str, results: Path = RESULTS, box: Path | None = None, cleared: bool = False,
                 run_id: str | None = None, every: float = 0.5, wall: float = 45.0,
                 budget_s: float = sweep.BUDGET_S) -> dict:
    """Every point of the scenario, its rows, and its summary row, written to results/<sid>.json."""
    sc = TABLE[sid]
    if missing := missing_packages(sid):
        return blocked(results, sid, "absent: " + ", ".join(missing), {"absent": missing})
    snap = guard.snapshot(guard.named_paths())
    try:
        box, book, why = prepare(sid, sc, box, run_id)
    except activate.RehearsalRefused as refused:          # the real autopilot could run: never a crash
        return blocked(results, sid, f"refused: {refused}")
    if why:
        return blocked(results, sid, why)
    before, carried = prior_shard(Path(results), sid, box)
    done, planned = run_points(box, book, sc, cleared, every, wall, {p["id"] for p in before}, budget_s)
    kept = before + [{k: v for k, v in d.items() if k != "rows"} for d in done]
    rows = carried + [r for d in done for r in d["rows"]] + [guard_row(snap), summary_row(sc, kept, planned)]
    path = write_results(Path(results), sid, rows, {"box": str(box), "points": kept, "planned": planned})
    last = done[-1] if done else {}
    return {"scenario": sid, "path": str(path), "supervisor": last.get("supervisor"), "trace": last.get("trace"),
            "trace_lines": last.get("trace_lines", []), "points": len(done), "untried": planned - len(kept)}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("scenario", choices=[*TABLE, "all", "checkpoints"])
    p.add_argument("--run-id")
    p.add_argument("--results", default=str(RESULTS))
    p.add_argument("--wall", type=float, default=3600.0)
    p.add_argument("--budget-hours", type=float, default=sweep.BUDGET_S / 3600.0, help="one shard's machine time")
    args = p.parse_args(argv)
    sid = "S0a" if args.scenario == "checkpoints" else args.scenario
    ids = [k for k in TABLE if k != "smoke"] if sid == "all" else [sid]
    for one in ids:
        out = run_scenario(one, Path(args.results), run_id=args.run_id, every=5.0, wall=args.wall,
                           budget_s=args.budget_hours * 3600.0)
        print(json.dumps({k: out.get(k) for k in ("scenario", "path", "blocked", "points", "untried")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
