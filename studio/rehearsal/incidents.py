"""The incident tally (2026-10-21_ep02_proof DESIGN 4.5): every way a recorded run stopped, by class.

Read-only and $0.  For one episode it opens BY NAME: `drive.jsonl`, `drive_run<NN>.log` and
`drive_launch<NN>.log` (probed 01, 02, ... until the first number that is absent, never a
directory walk), and the book's `autopilot/events.jsonl` and `autopilot/parked.jsonl`.  A drive
log's tail is classified by the REAL `studio.autopilot.classify`, the table the supervisor
itself hands a stop to.  Each incident's text is matched against the ordered rules of
`scripts/proof/incidents_map.yaml`: the first rule that hits names the class and the scenario
that reproduces it; a text no rule knows is a class named from its own words, UNCOVERED.
Paths are stored relative to the library root (never absolute)."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import yaml

SCENARIOS = frozenset({"S0a", "S0b", "S0b-naive", "F1", "F1b", "F2", "F3", "F4", "F5", "F6", "F7", "F7b",
                       "F8", "F9", "F10", "F11", "F12", "F13", "F14", "F15", "F16", "F17", "F18",
                       "UNCOVERED", "NOT_A_FAULT"})
LOG_STEMS = ("drive_run", "drive_launch")
TAIL_BYTES = 16_000
"""A drive log's tail: what the supervisor classifies (it reads the last lines of the log)."""
FAULT_EVENTS = frozenset({"brain", "parked", "brain_rejected", "engine_down", "engine_restart",
                          "engine_recycled", "two_parked_in_a_row"})
BOOK_FAULTS = frozenset({"tick_error", "supervisor_died_at"})
"""Supervisor faults that carry no episode: tallied once per book, under episode None."""
STEP_HEADER = re.compile(r"^--- step (\d+) \([^)]*\) \|", re.MULTILINE)
MAX_PROBE = 99
TERMINAL = re.compile(r"^=== EPISODE (?!start\b)\w+", re.MULTILINE)
"""The drive's own last word (`=== EPISODE completed|escalated|failed ...`); a log the real
classifier cannot place and that has no such line was cut off mid-run."""
PAUSED = re.compile(r"episode paused at a boundary|episode completed after \d+ run")
"""drive.py's last line for a pause the supervisor asked for, or a finished episode: no fault."""


def rel(path: Path, root: Path) -> str:
    """A library-relative POSIX path, so no absolute path is ever stored."""
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def read_rows(path: Path) -> list[dict]:
    """A JSONL file's rows; a line that does not parse is kept as {"torn": <line number>}."""
    rows = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"torn": n})
    return rows


def numbered(home: Path, stem: str) -> list[Path]:
    """`<stem>01.log`, `<stem>02.log`, ... up to the first number with no file."""
    found = []
    for n in range(1, MAX_PROBE + 1):
        path = Path(home) / f"{stem}{n:02d}.log"
        if not path.is_file():
            break
        found.append(path)
    return found


def tail_text(path: Path, nbytes: int = TAIL_BYTES) -> str:
    """The last `nbytes` of a log, decoded leniently, CRLF folded."""
    with open(path, "rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - nbytes))
        return f.read().decode("utf-8", errors="replace").replace("\r\n", "\n")


def outcome_key(row: dict) -> str:
    """`outcome|step|error` of a drive `run` row, '-' for an absent part."""
    return "|".join(str(row.get(k) or "-") for k in ("outcome", "step", "error"))


def drive_summary(rows: list[dict]) -> dict:
    """Starts, ends, silent spells and every run outcome by step and error."""
    events = Counter(r.get("event") for r in rows if "torn" not in r)
    outcomes = Counter(outcome_key(r) for r in rows if r.get("event") == "run")
    return {"start": events["start"], "end": events["end"], "silent": events["silent"],
            "torn": sum(1 for r in rows if "torn" in r), "outcomes": dict(sorted(outcomes.items()))}


def incident(kind: str, text: str, source: str, step: str | None = None, episode: int | None = None) -> dict:
    return {"kind": kind, "text": text, "source": source, "step": step, "episode": episode}


def died_runs(rows: list[dict], source: str) -> list[dict]:
    """One incident per `start` that no `end` closed before the next `start` (or the file's end)."""
    out, open_since = [], None
    for row in rows + [{"event": "start", "ts": None, "_sentinel": True}]:
        if row.get("event") == "start":
            if open_since is not None:
                out.append(incident("drive", f"drive_died after start {open_since}", source))
            open_since = None if row.get("_sentinel") else (row.get("ts") or "?")
        elif row.get("event") == "end":
            open_since = None
    return out


def silent_rows(rows: list[dict], source: str) -> list[dict]:
    return [incident("drive", f"drive_silent {r.get('minutes')} min in {r.get('log')}", source)
            for r in rows if r.get("event") == "silent"]


def torn_incidents(rows: list[dict], source: str) -> list[dict]:
    return [incident("torn", f"torn_record {source} line {r['torn']}", source) for r in rows if "torn" in r]


def last_step(text: str) -> str | None:
    """The step the log last started (a `--- step NN (name) |` header, never a skipped one)."""
    found = STEP_HEADER.findall(text)
    return found[-1] if found else None


def log_incident(path: Path, root: Path) -> dict | None:
    """A drive log's stop through the REAL supervisor classifier; None when it completed."""
    from studio import autopilot
    whole = Path(path).read_text(encoding="utf-8", errors="replace")
    tail = tail_text(path)
    kind, reason, _ = autopilot.classify(tail, set())
    if kind == "completed":
        return None
    last = autopilot.last_line(tail)
    if PAUSED.search(last):
        return None
    text = f"{reason}\n{last}"
    if reason.startswith("unclassified") and not TERMINAL.search(tail):
        text = f"log_cut_off: {last}"
    return incident("log", text, rel(path, root), step=last_step(whole))


def event_text(row: dict) -> str:
    detail = next((str(row[k]) for k in ("reason", "error", "verdict", "why") if row.get(k)), "")
    return f"{row.get('event')} {detail}".strip()


def episode_events(rows: list[dict], number: int, source: str) -> list[dict]:
    """The episode's own fault events (launches, resumes and code moves are not faults)."""
    return [incident("event", event_text(r), source, episode=number)
            for r in rows if r.get("episode") == number and r.get("event") in FAULT_EVENTS]


def book_events(rows: list[dict], source: str) -> list[dict]:
    """Supervisor faults with no episode, once per book."""
    return [incident("event", event_text(r), source)
            for r in rows if "episode" not in r and r.get("event") in BOOK_FAULTS]


def parked_incidents(rows: list[dict], number: int, source: str) -> list[dict]:
    return [incident("parked", f"parked {r.get('reason') or ''}".strip(), source, episode=number)
            for r in rows if r.get("episode") == number]


def load_rules(path: Path) -> list[dict]:
    """The ordered class rules of incidents_map.yaml, each regex compiled once."""
    rules = yaml.safe_load(Path(path).read_text(encoding="utf-8"))["rules"]
    for r in rules:
        r["regex"] = re.compile(r["match"], re.MULTILINE)
    return rules


def fallback_class(found: dict) -> str:
    """A class named from the incident's own first line, digits folded to '#'."""
    first = (found["text"].splitlines() or [""])[0]
    return f"{found['kind']}:" + re.sub(r"\d+", "#", first)[:100]


def classify(found: dict, rules: list[dict]) -> tuple[str, str]:
    """(class id, scenario id): the first rule whose regex hits the text, else UNCOVERED."""
    for r in rules:
        if r["regex"].search(found["text"]):
            return r["id"], r["scenario"]
    return fallback_class(found), "UNCOVERED"


def add_to(classes: dict, cid: str, scenario: str, found: dict) -> None:
    row = classes.setdefault(cid, {"scenario": scenario, "count": 0, "steps": Counter(), "kinds": Counter(),
                                   "episodes": set(), "examples": []})
    row["count"] += 1
    row["kinds"][found["kind"]] += 1
    if found.get("step"):
        row["steps"][found["step"]] += 1
    if found.get("episode") is not None:
        row["episodes"].add(found["episode"])
    if len(row["examples"]) < 3 and found["source"] not in row["examples"]:
        row["examples"].append(found["source"])


def plain(row: dict) -> dict:
    """A class row as JSON-ready data."""
    return {**row, "steps": dict(sorted(row["steps"].items())), "kinds": dict(row["kinds"]),
            "episodes": sorted(row["episodes"])}


def tally(found: list[dict], rules: list[dict]) -> dict:
    """Classes recorded, mapped to a scenario, and the UNCOVERED list; park reasons counted."""
    classes: dict[str, dict] = {}
    for item in found:
        add_to(classes, *classify(item, rules), item)
    ranked = sorted(classes.items(), key=lambda kv: -kv[1]["count"])
    out = {cid: plain(row) for cid, row in ranked if row["scenario"] != "NOT_A_FAULT"}
    uncovered = [cid for cid, row in out.items() if row["scenario"] == "UNCOVERED"]
    parks = Counter(i["text"][len("parked "):] for i in found if i["kind"] == "parked")
    return {"recorded": len(out), "mapped": len(out) - len(uncovered), "uncovered": uncovered,
            "classes": out, "not_faults": {cid: plain(row) for cid, row in ranked if cid not in out},
            "park_reasons": dict(parks.most_common())}


def opened(path: Path, root: Path, read: dict) -> list[dict] | None:
    """Rows of a named JSONL, noting it under `sources` or `missing` in `read`."""
    if not Path(path).is_file():
        read["missing"].append(rel(path, root))
        return None
    read["sources"].append(rel(path, root))
    return read_rows(path)


def drive_part(home: Path, root: Path, read: dict) -> dict:
    """The episode's drive ledger: its summary, and its died / silent / torn incidents."""
    rows = opened(home / "drive.jsonl", root, read)
    if rows is None:
        return {}
    source = rel(home / "drive.jsonl", root)
    read["incidents"] += died_runs(rows, source) + silent_rows(rows, source) + torn_incidents(rows, source)
    return drive_summary(rows)


def logs_part(home: Path, root: Path, read: dict) -> None:
    """Every numbered drive log's stop, one file at a time; the first absent number is noted."""
    for stem in LOG_STEMS:
        logs = numbered(home, stem)
        read["missing"].append(rel(home, root) + f"/{stem}{len(logs) + 1:02d}.log")
        for path in logs:
            read["sources"].append(rel(path, root))
            if (found := log_incident(path, root)) is not None:
                read["incidents"].append({**found, "episode": read["episode"]})


def autopilot_part(book: Path, number: int, root: Path, read: dict) -> None:
    """The book's supervisor events and parked rows that name this episode."""
    events = opened(book / "autopilot" / "events.jsonl", root, read)
    if events is not None:
        read["incidents"] += episode_events(events, number, rel(book / "autopilot" / "events.jsonl", root))
    parked = opened(book / "autopilot" / "parked.jsonl", root, read)
    if parked is not None:
        read["incidents"] += parked_incidents(parked, number, rel(book / "autopilot" / "parked.jsonl", root))


def episode_incidents(book: Path, number: int, root: Path) -> dict:
    """One episode's incidents, drive summary, and the files opened and found absent."""
    read = {"episode": number, "sources": [], "missing": [], "incidents": []}
    home = Path(book) / "episodes" / f"ep{number:02d}"
    read["drive"] = drive_part(home, root, read)
    logs_part(home, root, read)
    autopilot_part(Path(book), number, root, read)
    for item in read["incidents"]:
        item["episode"] = number
    return read


def book_incidents(book: Path, root: Path) -> dict:
    """The book's supervisor faults with no episode (tick errors, a dead supervisor), read once."""
    read = {"episode": None, "sources": [], "missing": [], "incidents": []}
    events = opened(Path(book) / "autopilot" / "events.jsonl", root, read)
    if events is not None:
        read["incidents"] += book_events(events, rel(Path(book) / "autopilot" / "events.jsonl", root))
    return read


def episode_numbers(book: Path, last: int | None = None) -> list[int]:
    """The book's episode numbers, probed epNN by name (01..99), the `last` few when asked."""
    found = [n for n in range(1, MAX_PROBE + 1) if (Path(book) / "episodes" / f"ep{n:02d}").is_dir()]
    return found[-last:] if last else found


def episode_entry(read: dict) -> dict:
    """What the report keeps of one episode's read: its ledger summary and its files."""
    return {"drive": read.get("drive", {}), "incidents": len(read["incidents"]),
            "sources": read["sources"], "missing": read["missing"]}


def survey(plan: list[tuple[str, list[int]]], root: Path, rules: list[dict]) -> dict:
    """Every named book's episodes read one file at a time, tallied into one class table."""
    found, episodes, books = [], {}, {}
    for name, numbers in plan:
        book = Path(root) / name
        whole = book_incidents(book, root)
        found += whole["incidents"]
        books[name] = {"numbers": numbers, "book_incidents": len(whole["incidents"])}
        for n in numbers:
            read = episode_incidents(book, n, root)
            found += read["incidents"]
            episodes[f"{name}/ep{n:02d}"] = episode_entry(read)
    return {"books": books, "episodes": episodes, **tally(found, rules)}
