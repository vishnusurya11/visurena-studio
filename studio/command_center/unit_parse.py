"""The unit page's parsers (research G, 2026-09-26).  Every line the page shows
is a Fault `(kind, where, note)` serialised by one of two writers:
`verdict.summary()` (a learning's note, an event's detail) and `plan_check.py`'s
stdout (a refusal body, one battery fault's note).  One parser per writer,
composed: `split_note` -> faults; a `battery` fault -> `battery_item`.

Pure functions over rows already read; no file, no database, no book word.  Every
parser tolerates junk and returns a raw row rather than raising.  Timestamps:
events and learnings are UTC (`Z`), `timing.jsonl` stamps are naive LOCAL time."""
from __future__ import annotations

import ast
import re
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import PurePosixPath

CLIP = 160
TERMINAL = re.compile(r" -> (?P<terminal>[a-z_]+)$")
FAULT_START = re.compile(r"(?:^|; )(?P<kind>[a-z][a-z_-]*) at (?P<where>[^\s:;]+(?::\d+(?:\.\d+)?)?)(?=: |; |$)")
SECTION = re.compile(r"^(?P<name>[A-Z][A-Za-z /-]*?[A-Za-z])\s*:\s?(?P<head>.*)$")
ITEM = re.compile(r"^\s{2,}(?P<code>[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*|L\d+) "
                  r"(?P<where>plan|shots? \d+(?:-\d+)?|setup '[^']+'|lines?[ .]\d+)[: ] ?(?P<text>.*)$")
ADVISORY = re.compile(r"^\s+advisory:? (?:(?P<code>[A-Z][A-Z0-9-]*) )?(?P<where>shot \d+|plan|setup '[^']+')?:? ?"
                      r"(?:(?P<code2>[A-Z]\d+): )?(?P<text>.*)$")
INFO = re.compile(r"^\s{3,}(?P<text>(?:not applicable|the sheet gate).*)$")
CONTRACT = re.compile(r"^CONTRACT (?P<where>(?:shots|lines)\.\d+|OK|:)?:? ?(?P<text>.*)$")
LISTED = re.compile(r"^(?P<code>[A-Z][A-Z0-9-]*): (?:(?P<where>setup '[^']+'|shot \d+|plan): )?(?P<text>.*)$")
TITLE = re.compile(r"^(?P<title>.*?) \| (?P<shots>\d+) shots \| (?P<secs>\d+)s projected")
TITLE_IN_NOTE = re.compile(r"CONTRACT OK: (?P<title>[^|;]+?) \|")
SHOT_WHERE = re.compile(r"^(?:shot_|T)(?P<n>\d+)$")
SHOT_FILE = re.compile(r"^(?:shot_|T)(?P<n>\d+)\.[a-z0-9]+$")
ENDS = ("completed", "failed", "deferred")
REASONS = (("REFUSED", "refused"), ("DEFERRED", "deferred"), ("INVALID VERDICT", "invalid"))
KEEP = ("ts", "step", "gate", "measured", "threshold", "attempt", "seconds", "terminal")


# --- text ---


def clip(text, n: int = CLIP) -> str:
    """The first line of a text, cut to n characters with a trailing `…`."""
    line = (str(text or "").strip().splitlines() or [""])[0]
    return line if len(line) <= n else line[:n - 1] + "…"


def digest(counts: dict[str, int], n: int = 6) -> str:
    """`G-SIZE 12 · G-AIM 4 · +9`: the n biggest codes, then how many more."""
    items = list(counts.items())
    head = " · ".join(f"{code} {k}" for code, k in items[:n])
    return clip(head + (f" · +{len(items) - n}" if len(items) > n else ""))


def count_codes(faults: list[dict]) -> dict[str, int]:
    """{code: n} biggest first; heads, info lines and uncoded rows are not faults."""
    counts = Counter(f.get("code") for f in faults
                     if f.get("code") and not f.get("head") and not f.get("info"))
    return dict(counts.most_common())


# --- verdict.summary() ---


def split_note(note) -> tuple[list[dict], str]:
    """(faults, terminal) from a verdict.summary() string; `; ` inside a note stays in it."""
    note = str(note or "")
    m = TERMINAL.search(note)
    body, terminal = (note[:m.start()], m["terminal"]) if m else (note, "")
    heads = list(FAULT_START.finditer(body))
    if not heads:
        return ([{"kind": "", "where": "", "text": body}] if body else []), terminal
    out = []
    for a, b in zip(heads, heads[1:] + [None]):
        text = body[a.end():b.start() if b else len(body)]
        out.append({"kind": a["kind"], "where": a["where"], "text": text.removeprefix(": ")})
    return out, terminal


# --- plan_check.py ---


def _item(m: re.Match) -> dict:
    return {"code": m["code"], "where": m["where"], "text": m["text"]}


def _advisory(m: re.Match) -> dict:
    return {"code": m["code"] or m["code2"] or "advisory", "where": m["where"] or "plan",
            "text": m["text"], "advisory": True}


def _contract(line: str) -> dict:
    m = CONTRACT.match(line)
    where = (m["where"] or "plan") if m else "plan"
    out = {"code": "CONTRACT", "where": "plan" if where in ("OK", ":") else where,
           "text": m["text"] if m else line}
    return {**out, "ok": True} if line.startswith("CONTRACT OK") else out


def battery_item(line) -> dict | None:
    """One plan_check line: an item, an advisory, an info line, a CONTRACT line or
    a section head (`{section, head}`); None for a line none of them reads."""
    s = str(line or "").rstrip()
    m = ITEM.match(s)
    if m and not s.lstrip().startswith("advisory"):
        return _item(m)
    if (a := ADVISORY.match(s)) and s.lstrip().startswith("advisory"):
        return _advisory(a)
    if i := INFO.match(s):
        return {"code": "info", "where": "plan", "text": i["text"], "info": True}
    if s.startswith("CONTRACT"):
        return _contract(s)
    if sec := SECTION.match(s.strip()):
        return {"section": sec["name"], "head": sec["head"]}
    return None


def expand(fault: dict) -> dict:
    """A split fault as a page row; a battery fault becomes its plan_check item."""
    if fault["kind"] != "battery":
        return {"code": fault["kind"], "kind": fault["kind"], "where": fault["where"], "text": fault["text"]}
    item = battery_item(fault["text"]) if fault["text"] else None
    if item is None:
        return {"code": "", "kind": "battery", "where": "plan", "text": fault["text"]}
    if "section" in item:
        return {"code": item["section"], "kind": "battery", "where": "plan", "text": item["head"], "head": True}
    flags = {k: True for k in ("advisory", "info") if item.get(k)} | ({"head": True} if item.get("ok") else {})
    return {"code": item["code"], "kind": "battery", "where": item["where"], "text": item["text"], **flags}


def learning_row(row: dict) -> dict:
    """The row with `faults` parsed and `note` dropped; the note's ` -> x` suffix
    is how the rung really ended (it can differ from `action`)."""
    faults, ended = split_note(row.get("note") or row.get("raw") or "")
    parsed = [expand(f) for f in faults] if not row.get("raw") else []
    counts = count_codes(parsed)
    first = parsed[0] if parsed else {}
    line = digest(counts) if counts else clip(" ".join(filter(None, (first.get("code"), first.get("text")))))
    return {**{k: row.get(k) for k in KEEP}, "rung": row.get("action"), "faults": parsed, "digest": line,
            "counts": counts, "ended_as": ended or (row.get("action") if row.get("terminal") else "")}


def head_count(head) -> int:
    """A section head's number: the integer, the length of a list repr, else 0."""
    head = str(head or "").strip()
    if head[:1].isdigit():
        return int(re.match(r"\d+", head).group(0))
    if head.startswith("[") and "]" in head:
        try:
            return len(ast.literal_eval(head[:head.rindex("]") + 1]))
        except (ValueError, SyntaxError):
            return 0
    return 0


def list_items(head: str) -> list[dict]:
    """A head that is a list of strings (G-LIGHT's) as its items; [] otherwise."""
    try:
        values = ast.literal_eval(head.strip()) if head.strip().startswith("[") else []
    except (ValueError, SyntaxError):
        return []
    out = []
    for v in values if isinstance(values, list) else []:
        m = LISTED.match(v) if isinstance(v, str) else None
        if m:
            out.append({"code": m["code"], "where": m["where"] or "plan", "text": m["text"]})
    return out


def _opens(raw: str, item: dict | None) -> dict | None:
    """The section an unindented line opens, or None."""
    if raw[:1] == " " or not item:
        return None
    if "section" in item:
        return {"name": item["section"], "head": item["head"], "count": head_count(item["head"]),
                "items": list_items(item["head"])}
    if item.get("code") == "CONTRACT":
        ok = bool(item.get("ok"))
        return {"name": "CONTRACT", "head": item["text"] if ok else "", "ok": ok, "count": 0 if ok else 1,
                "items": [] if ok else [item]}
    return None


def refusal_sections(text) -> list[dict]:
    """plan_check stdout as sections; an unindented line opens one, an indented
    line is its item; a line nothing reads is a raw item."""
    sections: list[dict] = []
    for raw in str(text or "").splitlines():
        if not raw.strip() or raw.startswith("plan_check refused"):
            continue
        item = battery_item(raw)
        opened = _opens(raw, item)
        if opened:
            sections.append(opened)
        elif sections:
            sections[-1]["items"].append(item if item and "code" in item else
                                         {"code": "", "where": "", "text": raw.strip()})
    return sections


def refusal_counts(sections: list[dict]) -> dict[str, int]:
    """{code: n} over every item, biggest first; info lines are not faults."""
    return count_codes([i for s in sections for i in s["items"]])


def refusal_title(sections: list[dict]) -> dict:
    """The CONTRACT OK line's title, shots and projected seconds, and the verdict."""
    out = {"title": "", "shots": 0, "projected_s": 0, "verdict": ""}
    for s in sections:
        m = TITLE.match(s["head"]) if s.get("ok") else None
        if m:
            out.update(title=m["title"], shots=int(m["shots"]), projected_s=int(m["secs"]))
        if s["name"] == "VERDICT":
            out["verdict"] = s["head"].strip()
    return out


# --- time ---


def parse_ts(ts) -> datetime | None:
    """An ISO stamp as an aware UTC datetime; a naive one is taken as UTC; None for junk."""
    try:
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def local_to_utc(ts, tz: tzinfo | None = None) -> datetime | None:
    """A naive LOCAL stamp (timing.jsonl) in UTC; `tz` names the local zone (default: this machine's)."""
    try:
        d = datetime.fromisoformat(str(ts))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=tz) if tz else d.astimezone()
    return d.astimezone(timezone.utc)


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


# --- passes ---


def group_by_run(events: list[dict]) -> OrderedDict:
    """run_id -> its events, in the order written (skipped kept)."""
    runs: OrderedDict = OrderedDict()
    for e in events:
        runs.setdefault(e.get("run_id") or "", []).append(e)
    return runs


def reason_class(event: str, detail) -> str:
    """How a pass ended in one word: refused, deferred, invalid, error, done, running, killed."""
    text = str(detail or "")
    for prefix, word in REASONS:
        if text.startswith(prefix):
            return word
    if event == "deferred":
        return "deferred"
    return {"completed": "done", "failed": "error"}.get(event, event)


def rungs_between(learnings: list[dict], start: datetime, end: datetime) -> list[str]:
    """`GATE:action` for each learning inside the window; `pass` rows are not a climb."""
    out = []
    for r in learnings:
        ts = parse_ts(r.get("ts"))
        if ts and start <= ts <= end and r.get("action") not in (None, "pass"):
            out.append(f"{r.get('gate')}:{r.get('action')}")
    return out


def seconds_between(timing: list[dict], start: datetime, end: datetime, tz: tzinfo | None = None) -> float:
    """Script seconds of the timing rows that started inside the window."""
    total = 0.0
    for t in timing:
        ts = local_to_utc(t.get("started"), tz) if t.get("started") else None
        if ts and start <= ts <= end:
            total += float(t.get("seconds") or 0)
    return total


def _pass(rid: str, es: list[dict], nxt: datetime | None, live_run, now: datetime) -> dict:
    """One run as a pass row, before the learnings and timing joins."""
    acted = [e for e in es if e.get("event") != "skipped"] or es
    last = acted[-1]
    how = last["event"] if last.get("event") in ENDS else ("running" if rid == live_run else "killed")
    start = parse_ts(es[0].get("event_ts")) or now
    end = (parse_ts(es[-1].get("event_ts")) or now) if how in ENDS else (nxt or now)
    return {"run_id": rid, "start": start, "end": end, "ended_on": last.get("step_id") or "", "how": how,
            "reason": how if how in ("running", "killed") else reason_class(how, last.get("detail")),
            "detail": clip(last.get("detail")), "done": [e["step_id"] for e in es if e.get("event") == "completed"]}


def passes(events: list[dict], learnings: list[dict], timing: list[dict], live_run: str | None,
           now: datetime | None = None, tz: tzinfo | None = None) -> list[dict]:
    """One row per run_id, in order; a run with no closing event ends where the next run starts."""
    now = _now(now)
    runs = group_by_run(events)
    starts = [parse_ts(es[0].get("event_ts")) for es in runs.values()][1:] + [None]
    out = []
    for (rid, es), nxt in zip(runs.items(), starts):
        p = _pass(rid, es, nxt, live_run, now)
        start, end = p.pop("start"), p.pop("end")
        out.append({**p, "started": start.isoformat(), "ended": end.isoformat(),
                    "wall_s": (end - start).total_seconds(), "ladder": rungs_between(learnings, start, end),
                    "script_s": seconds_between(timing, start, end, tz)})
    return out


def loop_state(rows: list[dict]) -> dict:
    """LOOPING when 3 of the last 4 finished passes ended on the same (step, reason)
    and that reason is not success; the running pass does not count."""
    finished = [p for p in rows if p.get("how") != "running"][-4:]
    common = Counter((p.get("ended_on"), p.get("reason")) for p in finished).most_common(1)
    if common and common[0][1] >= 3 and common[0][0][1] != "done":
        (step, reason), n = common[0]
        return {"looping": True, "step": step, "reason": reason, "n": n, "of": len(finished)}
    return {"looping": False, "step": "", "reason": "", "n": 0, "of": len(finished)}


def ended_on_counts(rows: list[dict], n: int = 10) -> list[dict]:
    """How the last n passes ended, as `(step, reason) × k`, most first."""
    counts = Counter((p.get("ended_on"), p.get("reason")) for p in rows[-n:])
    return [{"step": s, "reason": r, "n": k} for (s, r), k in counts.most_common()]


def _last_in(rows: list[dict], gate: str, start: datetime, end: datetime):
    hits = [r["measured"] for r in rows if r.get("gate") == gate and r.get("measured") is not None
            and (ts := parse_ts(r.get("ts"))) and start <= ts <= end]
    return hits[-1] if hits else None


def gate_trend(learnings: list[dict], rows: list[dict]) -> list[dict]:
    """Per gate, its last measured value in each pass; `improving` when the last fell."""
    gates = list(dict.fromkeys(r.get("gate") for r in learnings if r.get("gate") and r.get("measured") is not None))
    out = []
    for gate in gates:
        wins = [(parse_ts(p["started"]), parse_ts(p["ended"])) for p in rows]
        series = [v for a, b in wins if a and b and (v := _last_in(learnings, gate, a, b)) is not None]
        direction = "" if len(series) < 2 else ("improving" if series[-1] < series[-2] else "stuck")
        out.append({"gate": gate, "series": [round(v, 2) for v in series], "direction": direction})
    return out


def plan_titles(learnings: list[dict]) -> list[str]:
    """The plan titles the writer drafted (`CONTRACT OK: <title> |`), first seen first."""
    titles = [m["title"].strip() for r in learnings for m in TITLE_IN_NOTE.finditer(str(r.get("note") or ""))]
    return list(dict.fromkeys(titles))


# --- faults per shot ---


def evidence_line(fault: dict) -> str:
    """A note-less fault's evidence as one line: its first four scalar measures and the source."""
    ev = fault.get("evidence") if isinstance(fault.get("evidence"), dict) else {}
    parts = [f"{k} {v}" for k, v in ev.items()
             if k != "source" and isinstance(v, (int, float, str)) and not isinstance(v, bool)][:4]
    src = f" ({ev['source']})" if ev.get("source") else ""
    return (", ".join(parts) + src).strip()


def shot_key(where):
    """`shot_07` / `T07` -> 7; any other where ('master', a character id) stays a string."""
    m = SHOT_WHERE.match(str(where or ""))
    return int(m["n"]) if m else str(where or "")


def collapse(c: Counter) -> list[dict]:
    """(kind, note) counts as one badge per kind with n; three notes at most."""
    by: dict[str, dict] = {}
    for (kind, note), n in c.items():
        b = by.setdefault(kind, {"kind": kind, "notes": [], "n": 0})
        b["n"] += n
        if note and note not in b["notes"]:
            b["notes"].append(note)
    return [{"kind": b["kind"], "text": clip("; ".join(b["notes"][:3]) + ("; …" if len(b["notes"]) > 3 else "")),
             "n": b["n"]} for b in by.values()]


def shot_faults(verdict: dict) -> dict:
    """Faults keyed by shot index; one kind repeated on a shot is one badge with n."""
    by: dict = defaultdict(Counter)
    for f in (verdict or {}).get("faults") or []:
        if isinstance(f, dict):
            by[shot_key(f.get("where"))][(f.get("kind") or "", f.get("note") or evidence_line(f))] += 1
    return {k: collapse(c) for k, c in by.items()}


def fault_kinds(verdict: dict) -> list[dict]:
    """The verdict's faults grouped by kind: count, the shots it names, three notes."""
    by: dict[str, dict] = {}
    for f in (verdict or {}).get("faults") or []:
        if not isinstance(f, dict):
            continue
        k = by.setdefault(f.get("kind") or "", {"kind": f.get("kind") or "", "n": 0, "shots": set(), "notes": []})
        k["n"] += 1
        k["shots"].add(shot_key(f.get("where")))
        note = f.get("note") or evidence_line(f)
        if note and note not in k["notes"] and len(k["notes"]) < 3:
            k["notes"].append(clip(note))
    order = sorted(by.values(), key=lambda k: -k["n"])
    return [{**k, "shots": sorted(k["shots"], key=lambda s: (isinstance(s, str), s))} for k in order]


def panel_shot(path, plan: dict) -> dict | None:
    """storyboard/shot_NN.png or takes/.../TNN.mp4 -> plan shot NN; None when the plan has none."""
    m = SHOT_FILE.match(PurePosixPath(str(path)).name)
    if not m:
        return None
    n = int(m["n"])
    for shot in (plan or {}).get("shots") or []:
        if isinstance(shot, dict) and str(shot.get("index")) == str(n):
            return {**shot, "index": n}
    return None


# --- timing per step ---


def step_windows(events: list[dict], now: datetime | None = None) -> list[tuple]:
    """(step_id, start, end, open) per `started` event; it ends at the run's next event, else now."""
    now, out = _now(now), []
    for es in group_by_run(events).values():
        acted = [e for e in es if e.get("event") != "skipped"]
        for i, e in enumerate(acted):
            start = parse_ts(e.get("event_ts")) if e.get("event") == "started" else None
            if start:
                nxt = parse_ts(acted[i + 1].get("event_ts")) if i + 1 < len(acted) else None
                out.append((e.get("step_id"), start, nxt or now, nxt is None))
    return out


def window_of(wins: list[tuple], ts: datetime | None, pad: float = 1.0) -> str | None:
    """The step whose window (padded ±pad s) holds ts; the latest such window wins."""
    if ts is None:
        return None
    d = timedelta(seconds=pad)
    hits = [w for w in wins if w[1] - d <= ts <= w[2] + d]
    return hits[-1][0] if hits else None


def step_timing(steps: list[dict], events: list[dict], timing: list[dict],
                now: datetime | None = None, tz: tzinfo | None = None) -> list[dict]:
    """Per registry step: runs = its `started` events, last wall seconds, script seconds ≈."""
    wins = step_windows(events, now)
    per: dict = defaultdict(lambda: {"runs": 0, "total_s": 0.0, "last_wall_s": 0.0, "open": False, "scripts": Counter()})
    for sid, a, b, is_open in wins:
        p = per[sid]
        p.update(runs=p["runs"] + 1, last_wall_s=(b - a).total_seconds(), open=is_open)
    for row in timing:
        sid = window_of(wins, local_to_utc(row.get("started"), tz) if row.get("started") else None)
        if sid:
            per[sid]["total_s"] += float(row.get("seconds") or 0)
            per[sid]["scripts"][row.get("stage") or "?"] += 1
    return [{**s, **{k: (dict(v) if k == "scripts" else v) for k, v in per[s["id"]].items()}} for s in steps]


def unplaced(events: list[dict], timing: list[dict], now: datetime | None = None, tz: tzinfo | None = None) -> int:
    """How many timing rows fall in no step window (the join is lossy until the row carries its step)."""
    wins = step_windows(events, now)
    return sum(1 for row in timing
               if not window_of(wins, local_to_utc(row.get("started"), tz) if row.get("started") else None))


def timing_by_stage(timing: list[dict]) -> list[dict]:
    """timing.jsonl folded to one row per script stage: count, total seconds, last ok; biggest first."""
    by: dict[str, dict] = {}
    for row in timing:
        g = by.setdefault(str(row.get("stage") or "?"), {"stage": str(row.get("stage") or "?"),
                                                           "count": 0, "total_s": 0.0, "last_ok": None})
        g["count"] += 1
        g["total_s"] += float(row.get("seconds") or 0)
        g["last_ok"] = row.get("ok")
    return sorted(by.values(), key=lambda g: -g["total_s"])


# --- the log ---


def summary_line(sections: list[dict]) -> str:
    """`REFUSED · <title> · G-SOURCE 6 · G-SIZE 4 · +3` for one refusal."""
    t = refusal_title(sections)
    head = " · ".join(filter(None, (t["verdict"] or "REFUSED", t["title"])))
    return clip(f"{head} · {digest(refusal_counts(sections), n=5)}")


def flat_items(sections: list[dict]) -> list[dict]:
    """Every item of a refusal with its section name; info lines kept, marked."""
    return [{**i, "section": s["name"]} for s in sections for i in s["items"]]


def log_rows(rows: list[dict]) -> list[dict]:
    """Each log row as one line; a plan_check refusal carries its items and counts."""
    out = []
    for r in rows:
        msg = str(r.get("msg") or r.get("raw") or "")
        base = {k: r.get(k) for k in ("ts", "level", "step_id")}
        if msg.startswith("plan_check refused"):
            secs = refusal_sections(msg)
            out.append({**base, "kind": "refusal", "line": summary_line(secs), "items": flat_items(secs)})
        else:
            rest = msg.split("\n", 1)[1][:2000] if "\n" in msg else ""
            out.append({**base, "kind": "line", "line": clip(msg), "rest": rest})
    return out


def dedupe_refusals(rows: list[dict]) -> list[dict]:
    """Across consecutive refusals: an item seen before is `still ×N`, a new one `new`,
    and what the previous one had and this one lacks is `gone`."""
    seen: dict = {}
    for r in rows:
        if r.get("kind") != "refusal":
            continue
        keys = [(i.get("code"), i.get("where")) for i in r["items"]]
        r["items"] = [{**i, "mark": f"still ×{seen[k] + 1}" if k in seen else "new"} for i, k in zip(r["items"], keys)]
        r["gone"] = [{"code": c, "where": w} for (c, w) in seen if (c, w) not in keys]
        seen = {k: seen.get(k, 0) + 1 for k in keys}
    return rows
