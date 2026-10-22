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
STAND_INS = ("canned", "substituted", "worker_canned", "sdk_canned", "sdk_substituted", "sdk_scripted")
"""Answer classes that are NOT the real component answering this ask (AUDIT A2, A4): the engine's
canned grey and its substituted recording of ANOTHER graph (ep01's kept takes served to ep02), a
fake worker's memo miss (an empty detection, a silent transcript), a fake SDK's canned refusal, its
writer parts folded from a target plan (`writer_plan`: S0a's and F5's plan is ep01's own, not the
writer answering this brief) and the brain script's scripted verdict.  A quality row resting on
any of them is mechanism."""
CONTENT_PARKS = ("EYE_PANELS", "EYE_TAKES", "MASTER", "LOOK_STATE", "CONTENT", "CROWD", "speech_gap",
                 "split_voice", "speaker", "voice")
"""Words a park's reason carries when a content or voice gate parked it (gates.yaml's picture
judges, the content checks, the voice gates): S0b's pre-registered park (DESIGN 3.2, AUDIT A4)."""


def row(check: str, passed: bool, evidence: Iterable, *, question: str | None = None, detail: str = "",
        kind: str = "mechanism", n_points: int = 1, n_distinct: int | None = None, match_classes: Mapping | None = None,
        instrument: str = "files", instrument_state: str = "n/a") -> dict:
    """One counted row; any stand-in answer under it makes it `mechanism` (5.1, AUDIT A2/A4)."""
    classes = dict(match_classes or {})
    kind = "mechanism" if stands_in(classes) and kind == "quality" else kind
    return {"check": check, "question": question or QUESTIONS.get(check, "Q6"), "passed": bool(passed),
            "n_points": n_points, "n_distinct": n_points if n_distinct is None else n_distinct,
            "evidence": [str(e) for e in evidence], "match_classes": classes, "instrument": instrument,
            "instrument_state": instrument_state, "kind": kind, "detail": detail}


def stands_in(classes: Mapping | Iterable | None) -> bool:
    """Whether any answer under a row was a stand-in (STAND_INS): a count above 0, or a listed class."""
    if isinstance(classes, Mapping):
        return any(classes.get(k) for k in STAND_INS)
    return any(k in STAND_INS for k in classes or ())


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


def when(r: Mapping) -> float:
    """A row's epoch: a number as is, an ISO stamp parsed, 0 when it has none."""
    ts = r.get("ts")
    if isinstance(ts, (int, float)):
        return float(ts)
    try:
        return epoch(str(ts))
    except ValueError:
        return 0.0


def resubmitted_unordered(engine_rows: Iterable[Mapping], cuts: list[float], named: set, in_flight: int | None) -> list[str]:
    """Takes submitted twice between two cuts (a drive's end or death), unless named or in flight."""
    from studio.rehearsal import sweep
    seen: Counter = Counter()
    for r in engine_rows:
        if sweep.is_take_submit(r) and (i := take_index(r)) is not None:
            seen[(i, sum(1 for d in cuts if d < when(r)))] += 1
    return [f"T{i:02d} x{c}" for (i, _), c in sorted(seen.items())
            if c > 1 and i not in named and not (i == in_flight and c == 2)]


def resaved(collected: Iterable[Mapping], named: set) -> list[str]:
    """Takes SAVED twice in the run (phases.jsonl rows: one per take the client collected): finished
    work rendered again, which no cut excuses, unless a gate's retake named it."""
    saved = Counter(int(r["take"]) for r in collected if r.get("take") is not None)
    return [f"T{i:02d} saved x{c}" for i, c in sorted(saved.items()) if c > 1 and i not in named]


def a_norerender(engine_rows: Iterable[Mapping], ladder: Mapping, fault_at: float, in_flight: int | None,
                 deaths: Iterable[float] = (), collected: Iterable[Mapping] = ()) -> dict:
    """No take rendered again unordered.  The take in flight at an engine fault, and a take a cut
    lost (submitted before a drive ended or was killed, never saved), may be submitted once more
    after it; a take saved before the cut and saved again after is a re-render (`collected`: the
    run's new phases.jsonl rows)."""
    cuts, named = sorted(deaths), ordered_retakes(ladder, fault_at)
    extra = resubmitted_unordered(engine_rows, cuts, named, in_flight) + resaved(collected, named)
    return row("A-norerender", not extra, ["engine_log.jsonl", "takes/r2v/ladder.json", "takes/r2v/phases.jsonl"],
               detail="; ".join(extra) or f"{len(cuts)} cut(s), no take re-rendered unordered")


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


UNNAMED = "unclassified"
"""The autopilot's classifier's 'no pattern matched' (`unclassified: <last line>`): a traceback it
could not name.  S0a's `unclassified: FileNotFoundError ... plan.json` is a crash, never A-named's pass."""


def a_named(book: Path, n: int, notify: Iterable[str]) -> dict:
    """The terminal state is in the enum with a reason; each park reason is in the vocabulary;
    a notify line names the episode's terminal."""
    from studio.autopilot import State
    path = Path(book) / "autopilot" / "status.json"
    if not path.is_file():
        return row("A-named", False, ["autopilot/status.json"], detail="no status doc: the run ended without autopilot/status.json")
    status = json.loads(path.read_text(encoding="utf-8"))
    ep = status.get("episode") or {}
    reasons = [r.get("reason", "") for r in jsonl(Path(book) / "autopilot" / "parked.jsonl") if r.get("episode") == n]
    words, said = vocabulary(), [line for line in notify if f"ep{n:02d}" in line]
    faults = [] if ep.get("state") in State.__members__ and str(ep.get("reason") or "").strip() else [f"state {ep}"]
    faults += [f"a crash, not a named stop: {ep.get('reason')}"] * (stem(ep.get("reason") or "") == UNNAMED)
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


def labels_of(rows: Iterable[Mapping], prefix: str) -> Counter:
    """`<prefix>_<label>` counts of a fake's answer rows (a death or an exit row has no label)."""
    return Counter(f"{prefix}_{r['label']}" for r in rows if r.get("label") and r.get("event", "answer") == "answer")


def run_classes(box: Path) -> dict[str, int]:
    """Every answer of a run by class: the engine's (engine_log.jsonl), the fake workers'
    (workers.jsonl, worker_*) and the fake SDK's and brain script's (sdk_log.jsonl, sdk_*)."""
    engine = Counter(classes_of(jsonl(Path(box) / "engine_log.jsonl")))
    workers = labels_of(jsonl(Path(box) / "workers.jsonl"), "worker")
    return dict(engine + workers + labels_of(jsonl(Path(box) / "sdk_log.jsonl"), "sdk"))


def canned_ids(engine_rows: Iterable[Mapping]) -> set[str]:
    return {str(r.get("prompt_id")) for r in engine_rows if r.get("class") == "canned"}


def a_honest(engine_rows: list[Mapping], consumers: list[Mapping], shape: str) -> dict:
    """The engine's answers by match class, the gate that consumed each canned one, the fake's shape."""
    canned = canned_ids(engine_rows)
    who = sorted({str(c.get("caller")) for c in consumers if str(c.get("prompt_id")) in canned})
    return row("A-honest", True, ["engine_log.jsonl", "vl_consumers.jsonl"], match_classes=classes_of(engine_rows),
               instrument="fake_comfy", instrument_state=f"shape: {shape}",
               detail=f"canned consumed by: {', '.join(who) or 'none'}")


FAILED = "failed"
"""instrument_state of a row whose instrument could not measure: the report counts it INSTRUMENT
FAILED (scripts/proof/confidence.instrument_failed), never as a pass or a pipeline failure."""
UNJOINED = ("INSTRUMENT FAILED: no gate outcome joins canned {ids}: vl_consumers rows carry no `passed`, "
            "and a canned take or picture a non-VL gate read has no consumer row at all")


def instrument_failed(r: Mapping) -> bool:
    return str(r.get("instrument_state", "")).strip().lower() in (FAILED, "instrument failed")


def a_canned(engine_rows: list[Mapping], consumers: list[Mapping]) -> dict:
    """No gate PASSED on a canned reply (R3): such a pass is a FAILING Q6 row, named.  A canned
    reply no gate outcome joins is a hole in the measuring tool, so the row is INSTRUMENT FAILED
    (it counts nothing either way), never a failed pipeline row."""
    canned = canned_ids(engine_rows)
    used = [c for c in consumers if str(c.get("prompt_id")) in canned]
    passed = [f"{c.get('ask')} ({c.get('caller')}) passed on canned {c.get('prompt_id')}" for c in used if c.get("passed") is True]
    unjoined = sorted(canned - {str(c.get("prompt_id")) for c in used if "passed" in c})
    hole = UNJOINED.format(ids=", ".join(unjoined)) if unjoined else ""
    state = FAILED if unjoined and not passed else "joined"
    detail = "; ".join(passed + [hole] * bool(hole)) or "no gate passed on a canned reply"
    return row("A-canned", not passed and not unjoined, ["engine_log.jsonl", "vl_consumers.jsonl"],
               match_classes=classes_of(engine_rows), instrument="vl_consumers", instrument_state=state, detail=detail)


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


def content_park(reason: str) -> tuple[bool, str]:
    """S0b's park counts only when a content or voice gate parked it, its reason named (AUDIT A4)."""
    said = str(reason or "").strip()
    if not said:
        return False, "park with no reason"
    if not any(w.lower() in said.lower() for w in CONTENT_PARKS):
        return False, f"park {said!r} is not a content or voice gate's (a harness fault or a memo miss parks so)"
    return True, f"named park: {said}"


def s0b_outcome(state: str, reason: str, refusals: list[str], card: str, auto_clearable: bool,
                classes: Mapping | None = None) -> dict:
    """The one pre-registered correct outcome (R2), judged before the run."""
    gates = [r.split(" ", 1)[0] for r in refusals]
    if state == "PARKED":
        ok, said = content_park(reason)
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
    return row("S0b", ok, ["autopilot/status.json", "learnings.jsonl"], question="Q6", kind="quality", detail=said,
               match_classes=classes)


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


def s0a_rows(book: Path, recorded: Path | None = None, git=None, classes: Mapping | None = None) -> list[dict]:
    """Section 0's brick test: the unexplained differences over n takes, each listed; then each
    deterministic step output against the recording's.  `classes` (the run's engine answers by
    match class) rides on every row, so a graph built on a canned answer is mechanism (5.1)."""
    from studio.rehearsal import graph_diff as gd
    rec, git = Path(recorded or ep01_home()), git or gd.repo_git()
    since, mine = recorded_since(rec), home_of(book, 1)
    total = gd.summary(gd.room_report(rec / "takes" / "r2v", built_takes(mine / "takes" / "r2v"), since, git))
    rows = [row("S0a", total["n"] > 0 and total["unexplained"] == 0, [rec / "takes" / "r2v"], kind="quality",
                n_points=total["n"], instrument="graph_diff", match_classes=classes,
                detail=f"{total['unexplained']} unexplained over n={total['n']}: {total['listed'][:8]}")]
    return rows + [doc_row(rel, rec, mine, since, git, classes) for rel in DETERMINISTIC
                   if (mine / rel).is_file() and (rec / rel).is_file()]


def doc_row(rel: str, rec: Path, mine: Path, since: str, git, classes: Mapping | None) -> dict:
    """One deterministic step output against the recording's, diffed the way the take graphs are."""
    from studio.rehearsal import graph_diff as gd
    rep = gd.doc_report(rel, json.loads((rec / rel).read_text(encoding="utf-8")),
                        json.loads((mine / rel).read_text(encoding="utf-8")), since, git)
    return row("S0a", not rep["unexplained"], [rec / rel], kind="quality", instrument="graph_diff", match_classes=classes,
               detail=f"{rel}: {len(rep['unexplained'])} unexplained {rep['unexplained'][:6]}")


def s0b_rows(book: Path, box: Path) -> list[dict]:
    """S0b's one pre-registered outcome, the refusals and the lock read by the real publish lock;
    the publish card is the status reason, the held_publish events and the notify lines.  The
    run's engine answers by class ride on the row: gates judged on canned replies are mechanism."""
    ep = json.loads((Path(book) / "autopilot" / "status.json").read_text(encoding="utf-8")).get("episode") or {}
    refusals, clearable = publish_refusals(home_of(book, 2))
    held = [str(r.get("reason", "")) for r in jsonl(Path(book) / "autopilot" / "events.jsonl") if r.get("event") == "held_publish"]
    said = [str(r.get("text", "")) for r in jsonl(Path(box) / "notify.jsonl")]
    card = " ".join([str(ep.get("reason") or ""), *held, *said])
    return [s0b_outcome(str(ep.get("state")), str(ep.get("reason") or ""), refusals, card, clearable,
                        run_classes(box))]


def resubmits(engine_rows: list[Mapping]) -> int:
    """Submits of the faulted take (its workflow and index) after the faulted one; -1 unfaulted."""
    hit = next((i for i, r in enumerate(engine_rows) if r.get("fault")), None)
    if hit is None:
        return -1
    w, idx = engine_rows[hit].get("workflow"), engine_rows[hit].get("index")
    return sum(1 for r in engine_rows[hit + 1:] if r.get("call") == "prompt" and r.get("workflow") == w
               and r.get("index") == idx)


# ---- A-served: the planted fault reached its fake ------------------------------------------

from studio.rehearsal.faults import ENGINE as ENGINE_KINDS  # noqa: E402 -- the one list of engine kinds

SERVED_IN = {**{k: ("engine_log.jsonl", lambda r: bool(r.get("fault"))) for k in ENGINE_KINDS},
             "rate_limit": ("sdk_log.jsonl", lambda r: r.get("label") == "fault"),
             "brain_failed": ("sdk_log.jsonl", lambda r: r.get("label") == "fault"),
             "worker_death": ("workers.jsonl", lambda r: r.get("event") == "died"),
             "oauth": ("youtube.jsonl", lambda r: r.get("event") == "invalid_grant")}
"""Where each planted fault shows that its fake SERVED it: the fake's own log row."""


def served(kind: str, box: Path, sup: Mapping, planted: Mapping | None) -> tuple[bool, list[str]] | None:
    """(the fault fired, its evidence); None for a fault with no channel (a planted file, none)."""
    if kind in SERVED_IN:
        name, hit = SERVED_IN[kind]
        return any(hit(r) for r in jsonl(Path(box) / name)), [name]
    if kind == "kill":
        return any((Path(box) / f).exists() for f in ("kill.done", "kill.request")), ["kill.done"]
    if kind == "commit":
        return bool(sup.get("commits")), ["supervisor.json"]
    if kind == "tear":
        return bool((planted or {}).get("torn")), ["planted"]
    return None


def a_served(fault: Mapping, box: Path, sup: Mapping, planted: Mapping | None = None) -> dict | None:
    """A planted fault its fake never served leaves an UNFAULTED run: that point fails, named."""
    got = served(str(fault.get("kind")), box, sup, planted)
    if got is None:
        return None
    ok, evidence = got
    return row("A-served", ok, evidence, detail=f"{fault.get('kind')} " + ("served" if ok else
               "planted but never served: the point ran unfaulted"))


# ---- the specific checks, one per scenario --------------------------------------------------

def state_of(book: Path) -> tuple[str, str]:
    """(state, reason) of the unit in status.json; ("", "") when there is none."""
    path = Path(book) / "autopilot" / "status.json"
    ep = (json.loads(path.read_text(encoding="utf-8")).get("episode") or {}) if path.is_file() else {}
    return str(ep.get("state") or ""), str(ep.get("reason") or "")


def take_submits(engine_rows: list[Mapping]) -> list[Mapping]:
    from studio.rehearsal import sweep
    return [r for r in engine_rows if sweep.is_take_submit(r)]


def resubmitted(ok, said: str):
    """A check on how often the faulted take was submitted again."""
    def check(sid: str, box: Path, book: Path, engine: list[Mapping], sup: Mapping) -> dict:
        got = resubmits(engine)
        return row(sid, bool(ok(got)), ["engine_log.jsonl"], detail=f"the faulted take resubmitted {got}; pre-registered {said}")
    return check


def f_drives(sid: str, box: Path, book: Path, engine: list[Mapping], sup: Mapping) -> dict:
    """F2: at most one drive alive at every tick."""
    most = max(sup.get("drives_alive") or [0])
    return row(sid, most <= 1, ["supervisor.json"], detail=f"at most {most} drive(s) alive at any tick")


def f_reboot(sid: str, box: Path, book: Path, engine: list[Mapping], sup: Mapping) -> dict:
    """F4: adopt() and clear_stale_lock act."""
    events = [r.get("event") for r in jsonl(Path(book) / "autopilot" / "events.jsonl")]
    ok = "stale_lock" in events and "supervisor_died_at" in events
    return row(sid, ok, ["autopilot/events.jsonl"], detail=f"stale_lock + supervisor_died_at: {ok}")


def f_engine_park(sid: str, box: Path, book: Path, engine: list[Mapping], sup: Mapping) -> dict:
    """F1b: restarts <= 2 (A-caps), then PARK(engine) named."""
    state, reason = state_of(book)
    ok = state == "PARKED" and "engine" in reason.lower()
    return row(sid, ok, ["autopilot/status.json"], detail=f"{state or 'no state'}: {reason}; pre-registered PARK(engine)")


def f_corrupt(sid: str, box: Path, book: Path, engine: list[Mapping], sup: Mapping) -> dict:
    """F13: the corrupt take is retaken (within caps: A-caps), or the episode parks named."""
    state, reason = state_of(book)
    got = resubmits(engine)
    ok = got >= 1 or (state == "PARKED" and bool(reason.strip()))
    return row(sid, ok, ["engine_log.jsonl", "autopilot/status.json"], detail=f"retaken {got}; {state}: {reason}")


def f_no_take(sid: str, box: Path, book: Path, engine: list[Mapping], sup: Mapping) -> dict:
    """F3: the resume of step 10 submits no take."""
    takes = take_submits(engine)
    return row(sid, not takes, ["engine_log.jsonl"], detail=f"{len(takes)} take submit(s); pre-registered 0")


def f_oauth(sid: str, box: Path, book: Path, engine: list[Mapping], sup: Mapping) -> dict:
    """F6: no upload; the consent pending in the SANDBOX library; a park named for the token; the
    notify line carries the consent text."""
    from studio import settings
    state, reason = state_of(book)
    said = [str(r.get("text", "")) for r in jsonl(Path(box) / "notify.jsonl")]
    faults = [f"uploaded {n}" for n in [sum(r.get("event") == "would_upload" for r in jsonl(Path(box) / "youtube.jsonl"))] if n]
    faults += [] if (Path(box) / settings.LIBRARY_DIR / ".youtube_consent.json").is_file() else ["no sandbox consent file"]
    faults += [] if state == "PARKED" and re.search(r"youtube|oauth", reason, re.I) else [f"{state}: {reason}"]
    faults += [] if any(re.search(r"youtube_auth|approve|consent", t, re.I) for t in said) else ["no consent line"]
    return row(sid, not faults, ["youtube.jsonl", "notify.jsonl"], detail="; ".join(faults) or "parked on the token")


def drive_logs(book: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8", errors="replace")
                     for p in sorted(Path(book).glob("episodes/ep*/drive_run*.log")))


def f_commit(sid: str, box: Path, book: Path, engine: list[Mapping], sup: Mapping) -> dict:
    """F7: code_moved hands over and the resume names the moved code; F7b: said at most once."""
    moved = [r for r in jsonl(Path(book) / "autopilot" / "events.jsonl") if r.get("event") == "code_moved_during_run"]
    named = "code moved mid-episode" in drive_logs(book) or bool(moved)
    ok = bool(sup.get("handovers")) and (named if sid == "F7" else len(moved) <= 1)
    return row(sid, ok, ["supervisor.json", "autopilot/events.jsonl"],
               detail=f"handovers {len(sup.get('handovers') or [])}; resume named it {named}; said {len(moved)}")


def f_repair(sid: str, box: Path, book: Path, engine: list[Mapping], sup: Mapping) -> dict:
    """F8: leftover_window closes the window; the dry check refuses (exit 2); zero take submits; named."""
    from studio import repair_clock
    homes = [p for p in Path(book).glob("episodes/ep*") if p.is_dir()]
    faults = [f"{h.name}: window still open" for h in homes if (h / repair_clock.WINDOW).is_file()]
    closed = [r for h in homes for r in jsonl(h / repair_clock.LOG) if r.get("closed_by") == repair_clock.UNBACKED]
    refused = [r for h in homes for r in jsonl(h / "drive.jsonl") if r.get("event") == "end" and r.get("code") == 2]
    faults += [] if closed else ["no window closed as unbacked"]
    faults += [] if refused else ["no drive end refused with exit 2"]
    faults += [f"{n} take submit(s)" for n in [len(take_submits(engine))] if n]
    faults += [] if state_of(book)[0] in ("PARKED", "HELD_PUBLISH") else [f"state {state_of(book)[0] or 'none'}"]
    return row(sid, not faults, ["repair.jsonl", "drive.jsonl", "engine_log.jsonl"], detail="; ".join(faults) or "closed and refused")


def ask_cap() -> int:
    """The most asks llm.structured makes of one prompt: its own defaults (re-asks x transient tries)."""
    from studio import llm
    params = inspect.signature(llm.structured).parameters
    return int(params["retries"].default) * (int(params["transient_retries"].default) + 1)


def f_brain(sid: str, box: Path, book: Path, engine: list[Mapping], sup: Mapping) -> dict:
    """F15: the faulted ask is never asked again past llm's cap, and the run ends named."""
    rows = jsonl(Path(box) / "sdk_log.jsonl")
    hit = next((i for i, r in enumerate(rows) if r.get("label") == "fault"), None)
    again = 0 if hit is None else sum(r.get("prompt_sha") == rows[hit].get("prompt_sha") for r in rows[hit + 1:])
    state, reason = state_of(book)
    ok = hit is not None and again <= ask_cap() and bool(state)
    return row(sid, ok, ["sdk_log.jsonl", "autopilot/status.json"],
               detail=f"asked again {again} (cap {ask_cap()}); {state or 'no state'}: {reason}")


def f_worker(sid: str, box: Path, book: Path, engine: list[Mapping], sup: Mapping) -> dict:
    """F17: the dead worker is started again within the real SPAWNS; never a third start."""
    from studio import routed_whisper
    rows = jsonl(Path(box) / "workers.jsonl")
    died = {r.get("worker") for r in rows if r.get("event") == "died"}
    starts = {w: len({r.get("pid") for r in rows if r.get("worker") == w}) for w in died}
    over = [f"{w} started {n} > {routed_whisper.SPAWNS}" for w, n in starts.items() if n > routed_whisper.SPAWNS]
    return row(sid, bool(died) and not over, ["workers.jsonl"], detail="; ".join(over) or f"starts {starts}")


STEP_RAN = re.compile(r"^--- step (\d{2}) \([^)]*\) \|", re.MULTILINE)
"""The runner's line for a step it STARTED (`--- step 02 (plan) | <label> ---`); a skipped step's
`--- step 01 (bind) skipped: output exists` is not one."""


def stop_said(book: Path) -> str:
    """The unit's stop in words: status.json's state and reason, and every parked.jsonl row."""
    state, reason = state_of(book)
    return " ".join([state, reason] + [json.dumps(r) for r in jsonl(Path(book) / "autopilot" / "parked.jsonl")])


def f_plan_refused(sid: str, box: Path, book: Path, engine: list[Mapping], sup: Mapping) -> dict:
    """F5: step 02 ran and nothing after it started (no engine call from 03 on); the draft set aside
    as plan.deferred.json; the stop named `plan`.  A run that died before step 02 never met its fault."""
    from studio.plan_ladder import DEFERRED
    ran, said = set(STEP_RAN.findall(drive_logs(book))), stop_said(book)
    faults = [] if "02" in ran else ["step 02 never ran: the planted refusal was never met"]
    faults += [f"step {s} started past the refused plan" for s in sorted(ran) if s > "02"]
    faults += [] if any(Path(book).glob(f"episodes/ep*/{DEFERRED}")) else [f"no {DEFERRED}"]
    faults += [] if re.search(r"plan", said, re.I) else ["the stop is not named plan"]
    state, reason = state_of(book)
    return row(sid, not faults, ["episodes", "autopilot/status.json", "autopilot/parked.jsonl"],
               detail="; ".join(faults + [f"ended {state or 'no state'}: {reason}"]))


GAPS = "gaps.json"
"""F14's planted gaps (faults.plant_all's rows), left in the sandbox by the harness when it plants them."""


def gap_met(book: Path, gap: Mapping, said: str) -> bool:
    """A planted gap was met: the stop names it, or its just-in-time step put it back on disk."""
    from studio.rehearsal.faults import gap_target
    target = gap_target(gap)
    if str(gap.get("what") or "\0") in said or str(target.get("path") or "\0") in said:
        return True
    if target.get("path"):
        return (Path(book) / target["path"]).is_file()
    record = Path(book) / target["record"]
    doc = json.loads(record.read_text(encoding="utf-8")) if record.is_file() else {}
    return (target.get("field") or target.get("key")) in doc


def f_gaps(sid: str, box: Path, book: Path, engine: list[Mapping], sup: Mapping) -> dict:
    """F14: each planted gap ends in its just-in-time step or a stop NAMED with it; a run that stopped
    before a gap's step never met it (the first window: every gap unmet behind a step-01 park)."""
    path = Path(box) / GAPS
    gaps = [g for g in json.loads(path.read_text(encoding="utf-8")) if g.get("present")] if path.is_file() else []
    said, (state, reason) = stop_said(book), state_of(book)
    missed = [f"{g.get('kind')} {g.get('what')}" for g in gaps if not gap_met(book, g, said)]
    faults = (["no gap planted"] if not gaps else []) + [f"never met: {', '.join(missed[:6])}"] * bool(missed)
    return row(sid, not faults, [GAPS, "autopilot/status.json"],
               detail="; ".join(faults + [f"{len(gaps)} gap(s); ended {state or 'no state'}: {reason}"]))


CHECKS = {"F1": resubmitted(lambda n: n == 1, "1"), "F1b": f_engine_park, "F2": f_drives, "F3": f_no_take,
          "F4": f_reboot, "F5": f_plan_refused, "F6": f_oauth, "F7": f_commit, "F7b": f_commit, "F8": f_repair,
          "F9": resubmitted(lambda n: n <= 1, "<= 1"), "F10": resubmitted(lambda n: n == 1, "1"), "F13": f_corrupt,
          "F14": f_gaps, "F15": f_brain, "F16": resubmitted(lambda n: n == 0, "0"), "F17": f_worker}
"""Each scenario's pre-registered specific check (3.2).  F1: the take in flight rendered again exactly
once; F9: the hung take at most once; F10: one resubmission; F16: none.  F11 and F18 have none yet:
their common rows (A-caps, A-named, A-canned, A-torn) are all that scores them."""


def specific(sid: str, box: Path, book: Path, sup: Mapping) -> list[dict]:
    """The pre-registered specific asserts of 3.2 that the files answer; [] for the others."""
    if sid in ("S0a", "S0b"):
        return s0a_rows(book, classes=run_classes(box)) if sid == "S0a" else s0b_rows(book, box)
    if sid not in CHECKS:
        return []
    return [CHECKS[sid](sid, box, book, jsonl(Path(box) / "engine_log.jsonl"), sup)]
