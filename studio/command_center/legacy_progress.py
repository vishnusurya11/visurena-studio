"""v1's progress source (progress tracker spec, read side, before W1-W7):
the progress events a run WOULD write to progress.jsonl, derived from what it
already writes, so `studio.progress.fold()` draws the card either way.

- steps: the run's rows in the `events` table (UTC stamps), named by the
  drive log's `--- step NN (name)` banners;
- the shoot: the drive log's `queueing N takes in one go: ...` line is the
  plan (every take card in prompts.json, the rest kept), each
  `  T05 shots [5] 192f 8.00s in 182s` line is a landing, timed by its mp4;
- the board and panels: a panel file written after the step started is a landing;
- ladder rungs: the runner log's `GATE: measured X vs Y -> action` lines;
- the end: drive.jsonl's `run` row for this log, or `=== EPISODE completed`.

Reads only; every file is under the episode's own folder or the run's log."""
from __future__ import annotations

import json
import re
from pathlib import Path

from studio import registry
from studio.eta import to_epoch

READ_BYTES = 512 * 1024
BANNER_RUN = re.compile(r"^=== EPISODE start \| .* \| run (?P<run>\S+) ===", re.M)
STEP = re.compile(r"^--- step (?P<id>\d+) \((?P<name>[^)]+)\)(?: \||\s+skipped)", re.M)
QUEUE = re.compile(r"queueing \d+ takes in one go: (?P<ids>[T\d, ]+)$")
TAKE = re.compile(r"^\s+(?P<id>T\d+) shots \[[^\]]*\]\s+(?P<f>\d+)f\s+[\d.]+s in (?P<s>\d+)s")
RUNG = re.compile(r"^(?P<gate>[A-Z][A-Z_]*): measured (?P<m>\S+) vs (?P<th>\S+) -> (?P<action>[a-z_]+)"
                  r"(?P<term> \(terminal\))?")
STATES = {"started": "start", "completed": "done", "skipped": "skip", "failed": "fail",
          "deferred": "deferred", "escalated": "escalated"}
_JSON_CACHE: dict[tuple[str, int], object] = {}


# --- reads ---


def read_tail(path: Path | None, limit: int = READ_BYTES) -> str:
    """The last `limit` bytes of a text file; empty when it is not there."""
    try:
        with Path(path).open("rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - limit))
            return f.read().decode("utf-8", errors="replace")
    except (OSError, TypeError):
        return ""


def cached_json(path: Path):
    """A JSON file's content, parsed once per mtime; None when missing or not JSON."""
    try:
        key = (str(path), path.stat().st_mtime_ns)
    except OSError:
        return None
    if key not in _JSON_CACHE:
        try:
            _JSON_CACHE[key] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _JSON_CACHE[key] = None
    return _JSON_CACHE[key]


def jsonl_rows(text: str) -> list[dict]:
    """The JSON object lines of a text; anything else is skipped."""
    out = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def newest_log(home: Path) -> tuple[Path | None, int]:
    """The drive log this launch wrote last (drive.py restarts the count per launch) and its run number."""
    logs = sorted(home.glob("drive_run*.log"), key=lambda p: p.stat().st_mtime)
    if not logs:
        return None, 0
    digits = re.findall(r"\d+", logs[-1].stem)
    return logs[-1], int(digits[-1]) if digits else 0


def mtimes(paths) -> dict[str, float]:
    """{stem: mtime} for files that exist."""
    out = {}
    for p in paths:
        try:
            out[p.stem] = p.stat().st_mtime
        except OSError:
            continue
    return out


# --- the drive log ---


def banner_run(text: str) -> str | None:
    """The run id the log's `=== EPISODE start` banner names (the last one)."""
    found = BANNER_RUN.findall(text)
    return found[-1] if found else None


def step_names(text: str) -> dict[str, str]:
    """{step id: name} from the log's step banners."""
    return {m.group("id"): m.group("name") for m in STEP.finditer(text)}


def registry_names(stage: str = "episode") -> dict[str, str]:
    """{step id: name} from stages.yaml; empty when the registry cannot be read."""
    try:
        return {str(s["id"]): s["name"] for s in registry.steps(stage)}
    except (KeyError, OSError, ValueError, TypeError):
        return {}


def after_banner(text: str, step: str) -> list[str]:
    """The log's lines after the step's last `--- step NN (name) |` banner; none without it."""
    marks = [m for m in STEP.finditer(text) if m.group("id") == step and "skipped" not in m.group(0)]
    return text[marks[-1].end():].splitlines() if marks else []


def _plan_event(frames: dict[str, int], jobs: list[str], t: float | None) -> dict:
    items = [[i, frames[i]] for i in sorted(frames)]
    return {"t": t, "ev": "plan", "step": "09", "items": items, "kept": [i for i, _ in items if i not in jobs]}


def take_events(text: str, frames: dict[str, int], times: dict[str, float], step_t: float) -> list[dict]:
    """The shoot's plan and landings from the drive log; with no queue line yet,
    the takes on disk from before the step are the kept ones."""
    lines = after_banner(text, "09")
    if not lines:
        return []
    old = [i for i in frames if times.get(i, step_t) < step_t]
    evs = [_plan_event(frames, [i for i in frames if i not in old], step_t)]
    for line in lines:
        if q := QUEUE.search(line):
            evs.append(_plan_event(frames, [x.strip() for x in q.group("ids").split(",")], step_t))
        elif m := TAKE.match(line):
            t = times.get(m.group("id"))
            evs.append({"t": t if t is not None and t >= step_t else None, "ev": "item", "item": m.group("id"),
                        "weight": int(m.group("f")), "secs": float(m.group("s")), "state": "done"})
    return evs


def panel_events(ids: list[str], times: dict[str, float], step_t: float) -> list[dict]:
    """The board/panels steps: every shot's panel, landed when written after the step began."""
    evs = [{"t": step_t, "ev": "plan", "items": [[i, 1] for i in ids],
            "kept": [i for i in ids if times.get(i, step_t) < step_t]}]
    for i in sorted((i for i in ids if times.get(i, 0) >= step_t), key=lambda i: times[i]):
        evs.append({"t": times[i], "ev": "item", "item": i, "weight": 1, "secs": None, "state": "done"})
    return evs


def log_outcome(text: str) -> str | None:
    """`completed` once the log says so; None while it runs or ended otherwise."""
    return "completed" if "=== EPISODE completed" in text else None


def last_line(text: str) -> str:
    """The log's last line with words in it."""
    for line in reversed(text.splitlines()):
        if line.strip() and not line.startswith(("W0000", "INFO:", "WARNING: Logging")):
            return line.strip()[:240]
    return ""


# --- the events table, the runner log, drive.jsonl ---


def db_step_events(rows: list[dict], run_id: str | None, names: dict[str, str]) -> list[dict]:
    """The run's step rows as step events, in the order written."""
    out = []
    for r in rows:
        if r.get("run_id") == run_id and r.get("event") in STATES:
            sid = str(r.get("step_id"))
            out.append({"t": to_epoch(r.get("event_ts")), "ev": "step", "step": sid,
                        "name": names.get(sid, ""), "state": STATES[r["event"]], "run": run_id})
    return out


def _measured(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def runner_rounds(rows: list[dict]) -> list[dict]:
    """Every ladder rung the runner log carries, as round events."""
    out = []
    for r in rows:
        m = RUNG.match(str(r.get("msg") or ""))
        if m:
            out.append({"t": to_epoch(r.get("ts")), "ev": "round", "gate": m.group("gate"),
                        "measured": _measured(m.group("m")), "threshold": _measured(m.group("th")),
                        "action": m.group("action"), "terminal": bool(m.group("term"))})
    return out


def refusal(rows: list[dict]) -> str:
    """The runner log's last refusal, as one sentence (its first line with a fault)."""
    for r in reversed(rows):
        msg = str(r.get("msg") or "")
        if "refused" in msg.lower():
            lines = [l.strip() for l in msg.splitlines() if l.strip()]
            fault = next((l for l in lines[1:] if not l.startswith("CONTRACT OK") and "clean" not in l), "")
            return f"{lines[0].rstrip(':')}: {fault}"[:240] if fault else lines[0][:240]
    return ""


def ledger_outcome(rows: list[dict], n: int) -> str | None:
    """The outcome drive.jsonl wrote for run n of the latest launch, or None while it runs."""
    starts = [i for i, r in enumerate(rows) if r.get("event") == "start"]
    for r in rows[starts[-1] + 1 if starts else 0:]:
        if r.get("event") == "run" and r.get("n") == n:
            return r.get("outcome")
    return None


def drive_ended(rows: list[dict]) -> bool:
    """True when drive.jsonl's last launch wrote its `end` row."""
    events = [r.get("event") for r in rows]
    return "end" in events and (events[::-1].index("end") < events[::-1].index("start")
                                if "start" in events else True)


# --- one episode folder ---


def take_frames(home: Path) -> dict[str, int]:
    """{Tnn: frames} for every take card step 06 wrote (takes/r2v/prompts.json)."""
    cards = cached_json(home / "takes" / "r2v" / "prompts.json")
    return {f"T{int(c['index']):02d}": int(c.get("frames") or 0) for c in cards or []
            if isinstance(c, dict) and "index" in c}


def shot_ids(home: Path) -> list[str]:
    """The plan's shot numbers as two digits."""
    plan = cached_json(home / "plan.json")
    shots = plan.get("shots") if isinstance(plan, dict) else None
    return [f"{i:02d}" for i in range(len(shots or []))]


def panel_times(home: Path) -> dict[str, float]:
    """{NN: newest mtime of storyboard/shot_NN.png or storyboard/h3/shot_NN.png}."""
    out: dict[str, float] = {}
    for folder in (home / "storyboard", home / "storyboard" / "h3"):
        for stem, t in mtimes(folder.glob("shot_*.png")).items():
            key = stem.split("_")[-1]
            out[key] = max(t, out.get(key, 0.0))
    return out


def _counted(home: Path, text: str, steps: list[dict]) -> list[dict]:
    """The count events of the last counted step this run started (07, 08 or 09)."""
    started = [e for e in steps if e["state"] == "start" and e["step"] in ("07", "08", "09")]
    if not started:
        return []
    last = started[-1]
    if last["step"] == "09":
        return take_events(text, take_frames(home), mtimes((home / "takes" / "r2v").glob("T*.mp4")), last["t"])
    return panel_events(shot_ids(home), panel_times(home), last["t"])


def _insert_after_start(steps: list[dict], extra: list[dict]) -> list[dict]:
    """The count events right after their step's start, so later steps fold after them."""
    if not extra:
        return steps
    at = max(i for i, e in enumerate(steps) if e["state"] == "start" and e["step"] in ("07", "08", "09"))
    return steps[:at + 1] + extra + steps[at + 1:]


def derive(home: Path, db_rows: list[dict], runner_rows: list[dict], run_id: str | None = None) -> dict:
    """The run's progress events plus what the vitals need: the runner
    signals (epoch stamps), the last words and the refusal sentence."""
    log, n = newest_log(home)
    text, ledger = read_tail(log), jsonl_rows(read_tail(home / "drive.jsonl"))
    run_id = banner_run(text) or run_id
    steps = db_step_events(db_rows, run_id, {**registry_names(), **step_names(text)})
    evs = _insert_after_start(steps, _counted(home, text, steps)) + runner_rounds(runner_rows)
    if outcome := ledger_outcome(ledger, n) or log_outcome(text):
        evs.append({"t": None, "ev": "end", "outcome": outcome})
    signals = [to_epoch(r.get("ts")) for r in runner_rows] + [e["t"] for e in evs if e["ev"] == "item"]
    signals += list(mtimes([log]).values()) if log else []
    return {"events": evs, "run_id": run_id, "signals": sorted(s for s in signals if s is not None),
            "last_words": last_line(text) or str((runner_rows[-1:] or [{}])[0].get("msg", ""))[:240],
            "refusal": refusal(runner_rows), "drive_ended": drive_ended(ledger), "log_n": n}
