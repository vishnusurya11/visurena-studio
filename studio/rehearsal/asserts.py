"""The common asserts (2026-10-21_ep02_proof DESIGN 3.1) and S0b's pre-registered outcome (R2).

Each assert reads what a rehearsal left in its sandbox and returns ONE row of the section-5 schema
{check, question, passed, n_points, n_distinct, evidence, match_classes, instrument,
instrument_state, kind} plus a `detail` line naming what failed.  A row whose evidence rests on a
canned answer is `mechanism`, never `quality` (5.1).  The real code answers wherever it can: the
cap table is studio.step_caps', the relaunch rule autopilot's, the park vocabulary is read out of
the autopilot's own source, and the publish refusals come from studio.publish_lock."""
from __future__ import annotations

import inspect
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping

ROW_KEYS = ("check", "question", "passed", "n_points", "n_distinct", "evidence", "match_classes", "instrument",
            "instrument_state", "kind")
LEDGER_QUESTION = "Q6"
"""A-ledger proves the ledger is KEPT, never a duration (R15): it is a Q6 mechanism row, never Q5."""
QUESTIONS = {"A-caps": "Q5", "A-canned": "Q6"}
ENGINE_RESTARTS = 2
BRAIN_SESSIONS = 3
UNCAPPED = ("wall", "takes", "tiny_face")
"""attempts.json keys that count time or first renders, not retry rounds (no cap-table row)."""
YOUTUBE = ("googleapis", "youtube", "accounts.google")


def row(check: str, passed: bool, evidence: Iterable, *, question: str | None = None, detail: str = "",
        kind: str = "mechanism", n_points: int = 1, n_distinct: int | None = None, match_classes: Mapping | None = None,
        instrument: str = "files", instrument_state: str = "n/a") -> dict:
    """One counted row; any canned dependency makes it `mechanism` (5.1)."""
    classes = dict(match_classes or {})
    kind = "mechanism" if classes.get("canned") and kind == "quality" else kind
    return {"check": check, "question": question or QUESTIONS.get(check, "Q6"), "passed": bool(passed),
            "n_points": n_points, "n_distinct": n_points if n_distinct is None else n_distinct,
            "evidence": [str(e) for e in evidence], "match_classes": classes, "instrument": instrument,
            "instrument_state": instrument_state, "kind": kind, "detail": detail}


def jsonl(path: Path) -> list[dict]:
    """A JSONL file's parseable rows ([] when absent)."""
    if not Path(path).is_file():
        return []
    out = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            out.append(json.loads(line)) if line.strip() else None
        except ValueError:
            continue
    return out


def home_of(book: Path, n: int) -> Path:
    return Path(book) / "episodes" / f"ep{n:02d}"


# ---- A-caps -----------------------------------------------------------------------------

def allowed_rounds(key: str, table: Mapping) -> int | None:
    """The cap a counter answers to: relaunch.NN by autopilot's rule, plan.climbs by the plan row's
    climbs, a phase (or `phase.thing`) by its rows x climbs; None for a time or first-render key."""
    base, _, rest = key.partition(".")
    if base in UNCAPPED or rest == "order":
        return None
    if base == "relaunch":
        return sum(c.rounds for c in table.values() if c.step == rest) + 1
    if key == "plan.climbs":
        return table["plan"].climbs
    cap = table.get(base)
    return None if cap is None else cap.rounds * (cap.climbs if cap.per == "climb" else 1)


def counter_faults(attempts: Mapping, table: Mapping) -> list[str]:
    out = []
    for key, value in sorted(attempts.items()):
        cap = allowed_rounds(key, table)
        taken = int((value or {}).get("rounds", 0)) if isinstance(value, dict) else 0
        if cap is not None and taken > cap:
            out.append(f"{key} {taken} > {cap}")
    return out


def a_caps(book: Path, n: int, table: Mapping | None = None) -> dict:
    """Every phase within its cap-table rounds; engine restarts <= 2; brain sessions <= 3."""
    from studio import step_caps
    home = home_of(book, n)
    attempts_path = home / "attempts.json"
    attempts = json.loads(attempts_path.read_text(encoding="utf-8")) if attempts_path.is_file() else {}
    faults = counter_faults(attempts, table or step_caps.table())
    events = Path(book) / "autopilot" / "events.jsonl"
    restarts = sum(1 for r in jsonl(events) if r.get("event") == "engine_restart" and r.get("episode") == n)
    brains = len(list((home / "brain").glob("attempt_*.json"))) if (home / "brain").is_dir() else 0
    faults += [f"engine restarts {restarts} > {ENGINE_RESTARTS}"] * (restarts > ENGINE_RESTARTS)
    faults += [f"brain sessions {brains} > {BRAIN_SESSIONS}"] * (brains > BRAIN_SESSIONS)
    return row("A-caps", not faults, [attempts_path, events], detail="; ".join(faults) or "every counter in its cap")


# ---- A-norerender -----------------------------------------------------------------------

def take_index(r: Mapping) -> int | None:
    value = r.get("index", (r.get("key") or {}).get("index") if isinstance(r.get("key"), dict) else None)
    return int(value) if value is not None else None


def ordered_retakes(ladder: Mapping, after: float) -> set[int]:
    """Take indices a gate's retake round named after the fault."""
    return {int(i) for r in ladder.get("rounds") or () if float(r.get("at") or 0) >= after for i in (r.get("faults") or {})}


def a_norerender(engine_rows: Iterable[Mapping], ladder: Mapping, fault_at: float, in_flight: int | None) -> dict:
    """No take submitted twice unless a gate's retake named it after the fault (the take in flight
    at the fault may render once more)."""
    from studio.rehearsal import sweep
    seen: Counter = Counter()
    for r in engine_rows:
        if sweep.is_take_submit(r) and (i := take_index(r)) is not None:
            seen[i] += 1
    named = ordered_retakes(ladder, fault_at)
    extra = [f"T{i:02d} x{c}" for i, c in sorted(seen.items())
             if c > 1 and i not in named and not (i == in_flight and c == 2)]
    return row("A-norerender", not extra, ["engine_log.jsonl", "takes/r2v/ladder.json"],
               detail="; ".join(extra) or f"{len(seen)} takes, none re-rendered unordered")


# ---- A-noupload ---------------------------------------------------------------------------

def a_noupload(book: Path, before: list[dict], tripwire: Iterable[Mapping]) -> dict:
    """uploads.jsonl unchanged and no connection toward YouTube was even tried."""
    now = jsonl(Path(book) / "uploads.jsonl")
    trips = [t for t in tripwire if any(w in json.dumps(t).lower() for w in YOUTUBE)]
    faults = (["uploads.jsonl changed"] if now != list(before) else []) + [f"youtube trip: {t}" for t in trips][:3]
    return row("A-noupload", not faults, [Path(book) / "uploads.jsonl", "tripwire.jsonl"],
               detail="; ".join(faults) or "no upload")


# ---- A-ledger ---------------------------------------------------------------------------

def epoch(stamp: str) -> float:
    return datetime.fromisoformat(stamp).timestamp()


def drive_spans(home: Path) -> list[tuple[float, float]]:
    """(start, end) of every drive that ran to an end row."""
    spans, start = [], None
    for r in jsonl(home / "drive.jsonl"):
        if r.get("event") == "start":
            start = epoch(r["ts"])
        elif r.get("event") == "end" and start is not None:
            spans.append((start, epoch(r["ts"])))
            start = None
    return spans


def uncovered(drives: list[tuple[float, float]], clocks: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Drives that lasted and that no clock span overlaps."""
    return [d for d in drives if d[1] > d[0] and not any(c[0] < d[1] and c[1] > d[0] for c in clocks)]


def a_ledger(home: Path, steps_ran: Iterable[str], spent: list[float]) -> dict:
    """The LEDGER is kept (R15): every drive has a clock span, every step that ran a timing row,
    and run_budget.spent_before never went back.  Never a duration."""
    clocks = [(float(r["started"]), float(r.get("ended") or r["started"])) for r in jsonl(home / "clock.jsonl")]
    stages = {str(r.get("stage")) for r in jsonl(home / "timing.jsonl")}
    faults = [f"drive {d[0]:.0f}-{d[1]:.0f} has no clock span" for d in uncovered(drive_spans(home), clocks)]
    faults += [f"step {s} has no timing row" for s in steps_ran if f"step_{s}" not in stages]
    faults += [f"spent went back at sample {i}" for i in range(1, len(spent)) if spent[i] < spent[i - 1]]
    return row("A-ledger", not faults, [home / "clock.jsonl", home / "timing.jsonl"], question=LEDGER_QUESTION,
               detail="; ".join(faults) or "ledger kept")


# ---- A-named --------------------------------------------------------------------------------

def vocabulary() -> set[str]:
    """Every park reason the code can write: the stop table's park rows, the derive states'
    PARKED reasons and autopilot.park's literal reasons, each by its first word."""
    from scripts.episode import autopilot as ap
    from studio import autopilot as core
    words = {a[1] for _, a in core.TABLE if isinstance(a, tuple) and a[0] == "park"}
    words |= set(re.findall(r"State\.PARKED, \"([^\"]+)\"", inspect.getsource(core)))
    words |= set(re.findall(r"park\(book, codex, n, \"([^\"]+)\"", inspect.getsource(ap)))
    return {stem(w) for w in words} | {"brain", "parked"}


def stem(reason: str) -> str:
    return re.split(r"[:\s{]", str(reason).strip(), maxsplit=1)[0]


def a_named(book: Path, n: int, notify: Iterable[str]) -> dict:
    """The terminal state is in the enum with a reason; each park reason is in the vocabulary;
    a notify line names the episode's terminal."""
    from studio.autopilot import State
    status = json.loads((Path(book) / "autopilot" / "status.json").read_text(encoding="utf-8"))
    ep = status.get("episode") or {}
    reasons = [r.get("reason", "") for r in jsonl(Path(book) / "autopilot" / "parked.jsonl") if r.get("episode") == n]
    words, said = vocabulary(), [line for line in notify if f"ep{n:02d}" in line]
    faults = [] if ep.get("state") in State.__members__ and str(ep.get("reason") or "").strip() else [f"state {ep}"]
    faults += [f"park reason not in the vocabulary: {r}" for r in reasons if stem(r) not in words]
    faults += [] if said else [f"no notify line names ep{n:02d}"]
    return row("A-named", not faults, ["autopilot/status.json", "autopilot/parked.jsonl", "notify.jsonl"],
               detail="; ".join(faults) or f"{ep.get('state')}: {ep.get('reason')}")


# ---- A-real, A-honest, A-canned ------------------------------------------------------------

def a_real(tripwire: list[Mapping], guard_lines: list[str], expect_trip: bool = False, instrument: str = "fence") -> dict:
    """No refused reach outside the sandbox (unless the trip is the point) and a clean stat guard."""
    faults = ([] if expect_trip or not tripwire else [f"{len(tripwire)} tripwire rows"]) + list(guard_lines)
    return row("A-real", not faults, ["tripwire.jsonl", "guard"], instrument=instrument,
               detail="; ".join(faults) or "fenced and untouched")


def classes_of(engine_rows: Iterable[Mapping]) -> dict[str, int]:
    return dict(Counter(str(r["class"]) for r in engine_rows if r.get("class")))


def canned_ids(engine_rows: Iterable[Mapping]) -> set[str]:
    return {str(r.get("prompt_id")) for r in engine_rows if r.get("class") == "canned"}


def a_honest(engine_rows: list[Mapping], consumers: list[Mapping], shape: str) -> dict:
    """The engine's answers by match class, the gate that consumed each canned one, the fake's shape."""
    canned = canned_ids(engine_rows)
    who = sorted({str(c.get("caller")) for c in consumers if str(c.get("prompt_id")) in canned})
    return row("A-honest", True, ["engine_log.jsonl", "vl_consumers.jsonl"], match_classes=classes_of(engine_rows),
               instrument="fake_comfy", instrument_state=f"shape: {shape}",
               detail=f"canned consumed by: {', '.join(who) or 'none'}")


def a_canned(engine_rows: list[Mapping], consumers: list[Mapping]) -> dict:
    """No gate PASSED on a canned reply (R3): such a pass is a FAILING Q6 row, named; a canned
    reply no consumer row judged cannot be proven clean, so it fails as `unjoined`."""
    canned = canned_ids(engine_rows)
    used = [c for c in consumers if str(c.get("prompt_id")) in canned]
    passed = [f"{c.get('ask')} ({c.get('caller')}) passed on canned {c.get('prompt_id')}" for c in used if c.get("passed") is True]
    unjoined = sorted(canned - {str(c.get("prompt_id")) for c in used if "passed" in c})
    state = "unjoined" if unjoined and not passed else "joined"
    detail = "; ".join(passed + [f"canned {p} has no judged consumer" for p in unjoined]) or "no gate passed on a canned reply"
    return row("A-canned", not passed and not unjoined, ["engine_log.jsonl", "vl_consumers.jsonl"],
               match_classes=classes_of(engine_rows), instrument_state=state, detail=detail)


# ---- A-torn ---------------------------------------------------------------------------------

def parses(path: Path) -> bool:
    """A JSON file parses whole; a JSONL file parses line by line."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    try:
        if Path(path).suffix == ".jsonl":
            [json.loads(line) for line in text.splitlines() if line.strip()]
        else:
            json.loads(text)
        return True
    except ValueError:
        return False


def a_torn(records: Iterable[Path], resume_log: str) -> dict:
    """After a resume every record it read parses, or the resume named the torn file."""
    bad = [Path(p) for p in records if Path(p).is_file() and not parses(p)]
    silent = [p.name for p in bad if p.name not in (resume_log or "")]
    return row("A-torn", not silent, list(records), detail="; ".join(f"{s} torn and never named" for s in silent)
               or f"{len(bad)} torn, each named")


# ---- S0b ------------------------------------------------------------------------------------

def publish_refusals(home: Path) -> tuple[list[str], bool]:
    """(the open content refusals, whether the lock would auto-clear them), by the REAL publish lock."""
    from studio import publish_lock
    refusals = publish_lock.open_terminals(home)
    waived = {**publish_lock.judge_waivers(home), **publish_lock.waivers(home)}
    held = [t for t in refusals if t.split(" ", 1)[0] not in waived] + publish_lock.speaker_stops(home)
    return refusals, not held


def s0b_outcome(state: str, reason: str, refusals: list[str], card: str, auto_clearable: bool) -> dict:
    """The one pre-registered correct outcome (R2), judged before the run."""
    gates = [r.split(" ", 1)[0] for r in refusals]
    if state == "PARKED":
        ok, said = bool(str(reason).strip()), f"named park: {reason}" if reason else "park with no reason"
    elif state != "HELD_PUBLISH":
        ok, said = False, f"no terminal: {state}"
    elif not refusals:
        ok, said = False, "unregistered: HELD_PUBLISH with no content refusal on substituted pictures"
    elif auto_clearable:
        ok, said = False, f"FAILING: upload-ready with {len(refusals)} unresolved refusals and an auto-clearable lock"
    elif missing := [g for g in gates if g not in card]:
        ok, said = False, f"refusal not carried onto the publish card: {', '.join(missing)}"
    else:
        ok, said = True, f"held, {len(refusals)} refusals carried, lock held"
    return row("S0b", ok, ["autopilot/status.json", "learnings.jsonl"], question="Q6", kind="quality", detail=said)


# ---- the scenarios' own pre-registered checks (3.2) ---------------------------------------

def ep01_home() -> Path:
    """The recorded episode S0a replays (opened for READ only, by name)."""
    from studio import settings
    return settings.REAL_LIBRARY / "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde" / "episodes" / "ep01"


DETERMINISTIC = ("takes/r2v/prompts.json", "takes/r2v/shots.json", "timeline/placed.json")
"""S0a's deterministic step outputs, diffed against ep01's the same way as the take graphs."""


def built_takes(room: Path) -> dict[int, tuple[dict, int]]:
    """{index: (the graph the sandbox rendered with, its try count)} from a take room."""
    from studio.rehearsal import graph_diff
    tries = graph_diff.kept_tries(room)
    found = sorted(Path(room).glob("T[0-9][0-9].graph.json")) if Path(room).is_dir() else []
    return {int(p.name[1:3]): (json.loads(p.read_text(encoding="utf-8")), tries.get(int(p.name[1:3]), 0)) for p in found}


def recorded_since(home: Path) -> str:
    """The recording's date: its oldest drive start (the diff's `--since`)."""
    stamps = [r["ts"] for r in jsonl(Path(home) / "drive.jsonl") if r.get("event") == "start" and r.get("ts")]
    return min(stamps)[:10] if stamps else "2026-10-13"


def s0a_rows(book: Path, recorded: Path | None = None, git=None) -> list[dict]:
    """Section 0's brick test: the unexplained differences over n takes, each listed; then each
    deterministic step output against the recording's."""
    from studio.rehearsal import graph_diff as gd
    rec, git = Path(recorded or ep01_home()), git or gd.repo_git()
    since, mine = recorded_since(rec), home_of(book, 1)
    total = gd.summary(gd.room_report(rec / "takes" / "r2v", built_takes(mine / "takes" / "r2v"), since, git))
    rows = [row("S0a", total["n"] > 0 and total["unexplained"] == 0, [rec / "takes" / "r2v"], kind="quality",
                n_points=total["n"], instrument="graph_diff",
                detail=f"{total['unexplained']} unexplained over n={total['n']}: {total['listed'][:8]}")]
    for rel in DETERMINISTIC:
        if (mine / rel).is_file() and (rec / rel).is_file():
            rep = gd.doc_report(rel, json.loads((rec / rel).read_text(encoding="utf-8")),
                                json.loads((mine / rel).read_text(encoding="utf-8")), since, git)
            rows.append(row("S0a", not rep["unexplained"], [rec / rel], kind="quality", instrument="graph_diff",
                            detail=f"{rel}: {len(rep['unexplained'])} unexplained {rep['unexplained'][:6]}"))
    return rows


def s0b_rows(book: Path, box: Path) -> list[dict]:
    """S0b's one pre-registered outcome, the refusals and the lock read by the real publish lock;
    the publish card is the status reason, the held_publish events and the notify lines."""
    ep = json.loads((Path(book) / "autopilot" / "status.json").read_text(encoding="utf-8")).get("episode") or {}
    refusals, clearable = publish_refusals(home_of(book, 2))
    held = [str(r.get("reason", "")) for r in jsonl(Path(book) / "autopilot" / "events.jsonl") if r.get("event") == "held_publish"]
    said = [str(r.get("text", "")) for r in jsonl(Path(box) / "notify.jsonl")]
    card = " ".join([str(ep.get("reason") or ""), *held, *said])
    return [s0b_outcome(str(ep.get("state")), str(ep.get("reason") or ""), refusals, card, clearable)]


def resubmits(engine_rows: list[Mapping]) -> int:
    """Submits of the faulted take (its workflow and index) after the faulted one; -1 unfaulted."""
    hit = next((i for i, r in enumerate(engine_rows) if r.get("fault")), None)
    if hit is None:
        return -1
    w, idx = engine_rows[hit].get("workflow"), engine_rows[hit].get("index")
    return sum(1 for r in engine_rows[hit + 1:] if r.get("call") == "prompt" and r.get("workflow") == w
               and r.get("index") == idx)


def specific(sid: str, box: Path, book: Path, sup: Mapping) -> list[dict]:
    """The pre-registered specific asserts of 3.2 that one file answers; [] for the others."""
    engine = jsonl(Path(box) / "engine_log.jsonl")
    if sid == "S0a":
        return s0a_rows(book)
    if sid == "S0b":
        return s0b_rows(book, box)
    if sid in ("F10", "F16"):
        want, got = (1 if sid == "F10" else 0), resubmits(engine)
        return [row(sid, got == want, ["engine_log.jsonl"], detail=f"resubmitted {got}, pre-registered {want}")]
    if sid == "F2":
        most = max(sup.get("drives_alive") or [0])
        return [row(sid, most <= 1, ["supervisor.json"], detail=f"at most {most} drive(s) alive at any tick")]
    if sid == "F4":
        events = [r.get("event") for r in jsonl(Path(book) / "autopilot" / "events.jsonl")]
        ok = "stale_lock" in events and "supervisor_died_at" in events
        return [row(sid, ok, ["autopilot/events.jsonl"], detail=f"stale_lock + supervisor_died_at: {ok}")]
    return []
