"""The lists' pictures and charts (panel ruling 2026-10-04, PKG-4: 4.4, 4.5,
4.8, 4.9): what Home, the department, the book, the shelf and Needs you draw
that the views do not compute -- gate chips by severity with a capped count,
the department's state groups, GPU time paired from events into day columns
(server SVG with keyed mark ids, today's column under an "elapsed so far"
ceiling, no tick label within 36 px of now, no tween), a sparkline, the burn
line, and the poster a tile opens in the Viewer.

The top half is pure.  The bottom half reads (one read-only connection from
the app's own factory, files under the book folder) and is what the templates
call through the `viz` Jinja global.  Nothing here writes, decodes video or
runs a step."""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from studio import eta
from studio.command_center import library_paths, views

CAP = 99
SEVERITY = {"red": 0, "black": 0, "amber": 1, "purple": 2}
GROUPS = (("running", "Running", "loader"), ("needs", "Needs you", "flag"), ("queued", "Queued", "circle"),
          ("blocked", "Blocked", "circle-dashed"), ("done", "Done", "check"))
GROUP_OF = {"running": "running", "flagged": "needs", "failed": "needs", "deferred": "needs",
            "escalated": "needs", "stale": "needs", "queued": "queued", "blocked": "blocked",
            "held": "blocked", "done": "done", "skipped": "done"}
CLOSED = frozenset({"done"})
OUTCOME = {"completed": "ok", "failed": "burn", "deferred": "burn"}
SMALL_WORDS = frozenset({"the", "a", "an", "of", "and", "in", "to", "on"})
POSTERS = ("poster.jpg", "poster.png", "poster.webp")
TICK_GAP = 36
CHART_LEFT, CHART_TOP, CHART_FOOT = 34, 18, 28
BAR_CLASS = {"done": "done", "skipped": "skipped", "running": "running", "failed": "failed",
             "deferred": "deferred", "held": "held", "flagged": "flagged", "escalated": "failed"}


# --- chips ---


def cap(n: int, limit: int = CAP) -> str:
    """A count as a chip prints it: '' for none, `99+` past the cap."""
    return "" if not n else (f"{limit}+" if n > limit else str(n))


def chip_title(label: str, faults: int, word: str) -> str:
    """The plain words behind a chip: `531 panels faults, flagged` / `master: reject`."""
    if faults:
        noun = "fault" if faults == 1 else "faults"
        return f"{faults} {label} {noun}" + (f", {word}" if word else "")
    return f"{label}: {word}" if word else label


def gate_chips(strip: list[dict]) -> list[dict]:
    """The non-pass gates of a verdict strip, failures first, then by fault count."""
    out = [{**c, "label": views.gate_label(c["gate"]), "count": cap(c.get("faults") or 0),
            "title": chip_title(views.gate_label(c["gate"]), c.get("faults") or 0, c.get("word") or "")}
           for c in strip if c["css"] in SEVERITY]
    return sorted(out, key=lambda c: (SEVERITY[c["css"]], -(c.get("faults") or 0)))


# --- the department's state groups ---


def group_of(shown: str) -> str:
    """Which group a shown state sits in (an unknown state waits in Queued)."""
    return GROUP_OF.get(shown, "queued")


def state_groups(rows: list[dict]) -> list[dict]:
    """The rows by group in GROUPS order, empty groups left out; Done starts collapsed."""
    found: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        found[group_of(r["shown"])].append(r)
    return [{"key": key, "label": label, "icon": icon, "rows": found[key], "open": key not in CLOSED}
            for key, label, icon in GROUPS if found.get(key)]


def bar_class(state: str) -> str:
    """A step-bar segment's class from the step's state ('' for not yet)."""
    return BAR_CLASS.get(state, "")


# --- GPU time from events ---


def spans(rows, now: float, live_runs: set[str] | None = None) -> list[dict]:
    """Started -> completed/failed/deferred pairs inside one run, as {step, start, end, kind};
    a start still open in a live run is `live` up to now; a skip or a dead run's start counts nothing."""
    began: dict[tuple, float] = {}
    out = []
    for r in rows:
        key, at = (r["run_id"], r["step_id"]), eta.to_epoch(r["event_ts"])
        if r["event"] == "started" and at is not None:
            began[key] = at
        elif r["event"] in OUTCOME and began.get(key) is not None and at is not None:
            out.append({"step": r["step_id"], "start": began.pop(key), "end": at, "kind": OUTCOME[r["event"]]})
    live = live_runs or set()
    out += [{"step": step, "start": at, "end": now, "kind": "live"} for (run, step), at in began.items() if run in live]
    return out


def day_label(day, today) -> str:
    """`today`, else `Sat 3`."""
    return "today" if day == today else f"{day:%a} {day.day}"


def day_totals(spans_: list[dict], now: float, days: int = 7, tz=None) -> list[dict]:
    """Hours per local day (the day a step started), ok / burn / live, oldest first, today last."""
    today = datetime.fromtimestamp(now, tz).date()
    keys = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
    acc = {k: {"ok": 0.0, "burn": 0.0, "live": 0.0} for k in keys}
    for s in spans_:
        day = datetime.fromtimestamp(s["start"], tz).date()
        if day in acc:
            acc[day][s["kind"]] += (s["end"] - s["start"]) / 3600
    return [{"key": k.isoformat(), "label": day_label(k, today), "today": k == today,
             **{kind: round(v, 2) for kind, v in acc[k].items()}} for k in keys]


def step_burn(spans_: list[dict]) -> list[dict]:
    """Per step: hours burned, hours finished (ok + burn) and the burned share, most burned first."""
    burn: dict[str, float] = defaultdict(float)
    total: dict[str, float] = defaultdict(float)
    for s in spans_:
        if s["kind"] != "live":
            total[s["step"]] += (s["end"] - s["start"]) / 3600
            burn[s["step"]] += (s["end"] - s["start"]) / 3600 if s["kind"] == "burn" else 0.0
    out = [{"step": k, "burn": round(burn[k], 2), "total": round(total[k], 2),
            "share": round(100 * burn[k] / total[k]) if total[k] else 0} for k in total if burn[k]]
    return sorted(out, key=lambda s: -s["burn"])


def hours(x: float) -> str:
    """`34`, `7.8`, `0.5`: whole hours from ten up."""
    return f"{x:.0f}" if x >= 10 else f"{x:.1f}"


def burn_line(days: list[dict], steps: list[dict]) -> str:
    """`34 of 75 GPU-h burned · lever: 09 shoot 55 %`; '' when nothing ran."""
    total = sum(d["ok"] + d["burn"] + d["live"] for d in days)
    if not total:
        return ""
    line = f"{hours(sum(d['burn'] for d in days))} of {hours(total)} GPU-h burned"
    if steps:
        s = steps[0]
        line += f" · lever: {s['step']} {s.get('name', '')} {s['share']} %".replace("  ", " ")
    return line


# --- the column chart (server SVG; the template draws the marks) ---


def scale(height: float, top_h: float):
    """y for an hour value: 0 h at the baseline, top_h at the chart's top."""
    return lambda h: round(CHART_TOP + height - h / top_h * height, 1)


def stack(day: dict, x: float, w: float, y) -> list[dict]:
    """A column's segments bottom-up (ok, live, burn), zero ones left out, each keyed."""
    segs, base = [], 0.0
    for kind in ("ok", "live", "burn"):
        if day[kind] > 0:
            top = base + day[kind]
            segs.append({"kind": kind, "id": f"went-{day['key']}-{kind}", "x": x, "w": w,
                         "y": y(top), "h": round(max(y(base) - y(top), 1.0), 1)})
            base = top
    return segs


def column_chart(days: list[dict], elapsed_h: float, width: int = 640, height: int = 180) -> dict:
    """The day columns' marks: keyed column ids, stacked segments, a value label, today's
    "elapsed so far" ceiling, the 6/12/18 grid and the 24 h line of one GPU's day."""
    top_h = max([24.0] + [d["ok"] + d["burn"] + d["live"] for d in days])
    y, step = scale(height, top_h), (width - CHART_LEFT - 8) / max(len(days), 1)
    col_w = min(48.0, round(step * 0.6, 1))
    cols = []
    for i, d in enumerate(days):
        x = round(CHART_LEFT + i * step + (step - col_w) / 2, 1)
        total = d["ok"] + d["burn"] + d["live"]
        cols.append({"id": f"went-{d['key']}", "x": x, "w": col_w, "cx": round(x + col_w / 2, 1), "day": d,
                     "segs": stack(d, x, col_w, y), "total": total, "top": y(total),
                     "ceiling": y(elapsed_h) if d["today"] else None})
    grid = [{"h": h, "y": y(h)} for h in (6, 12, 18)]
    return {"cols": cols, "grid": grid, "line24": y(24), "base": y(0), "y": y, "width": width,
            "height": CHART_TOP + height + CHART_FOOT, "max": max((c["total"] for c in cols), default=0)}


def clear_of_now(ticks: list[dict], now_x: float, gap: int = TICK_GAP) -> list[dict]:
    """The tick labels that stay more than `gap` px away from the now-line."""
    return [t for t in ticks if abs(t["x"] - now_x) > gap]


def spark(values: list[float], width: float, height: float, vmax: float) -> str:
    """A sparkline's path, left to right, scaled so vmax sits 2 px under the top."""
    if not values:
        return ""
    n = max(len(values) - 1, 1)
    pts = [(i * width / n, 2 + height - (v / vmax if vmax else 0) * height) for i, v in enumerate(values)]
    return " ".join(f"{'L' if i else 'M'}{x:.1f} {yy:.1f}" for i, (x, yy) in enumerate(pts))



def initials(name: str) -> str:
    """A cover's letters: the first two words that matter (`Moby Dick` -> MD, `Dracula` -> D)."""
    words = [w for w in name.split() if w.lower() not in SMALL_WORDS and w[:1].isalnum()]
    return "".join(w[0] for w in words[:2]).upper()


# --- posters (the files a tile shows and opens) ---


def poster_file(home: Path) -> Path | None:
    """The unit's picture: the pipeline's poster, else its middle storyboard panel, else an anchor."""
    home = Path(home)
    for name in POSTERS:
        if (home / name).is_file():
            return home / name
    for pattern in ("storyboard/shot_*.png", "storyboard/anchors/*.png"):
        hits = sorted(home.glob(pattern)) if home.is_dir() else []
        if hits:
            return hits[len(hits) // 2] if pattern.startswith("storyboard/shot") else hits[0]
    return None


def poster(library: Path, codex_id: str, home: str | None, px: int = 320) -> dict | None:
    """A poster as a Viewer opener reads it: the book-relative path, the thumb and the full file."""
    book = library_paths.book_folder(Path(library), codex_id)
    hit = poster_file(book / home) if book and home else None
    rel = library_paths.book_relative(hit, codex_id) if hit else None
    if not rel:
        return None
    v = library_paths.stamp(hit)
    return {"rel": rel, "codex": codex_id, "thumb": library_paths.thumb_url(codex_id, rel, px, v),
            "thumb2": library_paths.thumb_url(codex_id, rel, px * 2, v),
            "src": library_paths.artefact_url(codex_id, rel), "label": rel.rsplit("/", 1)[-1]}


# --- the reads the templates call (viz.<name>(request, ...)) ---


@contextmanager
def reading(request) -> Iterator[sqlite3.Connection]:
    """One read-only connection from the app's own factory, closed after."""
    conn = request.app.state.conn_factory()
    try:
        yield conn
    finally:
        conn.close()


def fp(request, key: str) -> str:
    """The pulse fingerprint of one section key (pulse.fingerprint, C1), drawn as the
    section's data-v so the first pulse after a page load answers 204."""
    from studio.command_center import pulse
    with reading(request) as conn:
        return pulse.fingerprint(conn, key, datetime.now(timezone.utc).timestamp())


def face(request, row: dict, px: int = 80) -> dict | None:
    """A row's poster (a 36 px face, a 96 px card, a 320 px tile)."""
    return poster(request.app.state.library, row["codex_id"], row.get("home"), px)


def rail(request, row: dict) -> list[dict]:
    """The unit's step rail: one segment per registry step with its class."""
    with reading(request) as conn:
        chips = views.step_states(conn, [row["id"]])[row["id"]]
    return [{**s, "cls": bar_class(s["state"])} for s in views.step_bar(row, chips)]


def chips(row: dict) -> list[dict]:
    """A row's non-pass gate chips, from its verdicts in gates.yaml order."""
    return gate_chips(views.verdict_strip(row.get("verdicts") or {}, views.gate_order(row["stage"])))


def event_rows(conn: sqlite3.Connection, since: str) -> list:
    """The episode lane's step events since an ISO stamp, in write order."""
    return conn.execute("SELECT event_ts, step_id, event, run_id FROM events WHERE stage = 'episode'"
                        " AND event_ts >= ? ORDER BY id", (since,)).fetchall()


def live_runs(conn: sqlite3.Connection) -> set[str]:
    """The run ids of the units running now."""
    return {r[0] for r in conn.execute("SELECT run_id FROM work_orders WHERE state = 'running' AND run_id IS NOT NULL")}


def went(request, days: int = 7) -> dict:
    """Where the GPU went: day columns, steps by hours burned, the burn line, the chart."""
    now = datetime.now(timezone.utc).timestamp()
    local = datetime.now().astimezone()
    since = (local - timedelta(days=days)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    with reading(request) as conn:
        s = spans(event_rows(conn, since), now, live_runs(conn))
    names = views.step_names("episode")
    by_day, steps = day_totals(s, now, days, local.tzinfo), step_burn(s)[:5]
    steps = [{**x, "name": names.get(x["step"], "")} for x in steps]
    elapsed = local.hour + local.minute / 60
    return {"days": by_day, "steps": steps, "line": burn_line(by_day, steps),
            "chart": column_chart(by_day, elapsed), "spark": spark([d["ok"] + d["burn"] + d["live"] for d in by_day], 260, 30, 24),
            "today": by_day[-1] if by_day else None, "week": round(sum(d["ok"] + d["burn"] + d["live"] for d in by_day), 1),
            "max_step": max((x["total"] for x in steps), default=0)}


def queue_eta(request) -> dict | None:
    """The episode lane's finish (views.queue_eta, PKG-1), or None before it lands."""
    fn = getattr(views, "queue_eta", None)
    if fn is None:
        return None
    with reading(request) as conn:
        return fn(conn, "episode", tz=datetime.now().astimezone().tzinfo)


def season(request, codex_id: str) -> list[dict]:
    """The book's episodes as wall tiles: unit, shown state, glyph, step, flags, poster."""
    with reading(request) as conn:
        rows = [views.row_view(r) for r in conn.execute(
            "SELECT * FROM work_orders WHERE codex_id = ? AND stage = 'episode' ORDER BY sequence, unit", (codex_id,))]
    return [{**r, "poster": face(request, r, 320)} for r in rows]


def book_posters(request, codex_id: str, n: int = 8) -> list[dict]:
    """The book's newest episode pictures for a shelf card's mosaic, newest first."""
    with reading(request) as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT codex_id, unit, home, state, flags FROM work_orders WHERE codex_id = ? AND stage = 'episode'"
            " ORDER BY updated_at DESC, unit DESC LIMIT ?", (codex_id, n * 2))]
    out = [{**r, "poster": face(request, r, 160)} for r in rows]
    return [r for r in out if r["poster"]][:n]


def shelf_split(request, shelf: list[dict]) -> tuple[list[tuple[dict, list[dict]]], list[dict]]:
    """(books making episodes with their mosaic, every other book), each in shelf order."""
    making, rest = [], []
    for b in shelf:
        pics = book_posters(request, b["codex_id"]) if b.get("units") else []
        (making.append((b, pics)) if pics else rest.append(b))
    return making, rest
