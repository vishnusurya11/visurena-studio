"""The shell's data (plan G1, the v2 sidebar): what every page draws around its
body -- Home, the inbox count, Queue, Books, Architecture, a row per registered
department with its count and state dots, the pinned running units, the live
GPU card and the palette's index -- plus (panel ruling PKG-2) the one KEYS
registry, the crumbs from Home, the studio hold for the header's bar, the
heartbeat chip's thresholds and every unit for ⌘K.  Pure reads over the views; nothing here is
a state a runner did not write.  `static_url` versions a static file by its
mtime so the board can cache it for a year."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from studio.command_center import library_paths, views

STATIC = Path(__file__).resolve().parent / "static"
DEPT_ICONS = {"analysis": "search", "screenplay": "scroll-text", "trailer": "film",
              "refs": "user-round", "episode": "clapperboard"}
DEFAULT_ICON = "layers"
FACES = ("storyboard/shot_*.png", "storyboard/anchors/*.png")
DOTS = (("run", "running"), ("fail", "failed"), ("flag", "flagged"))
PAGES = (("/", "house", "Home", "the GPU, what needs you, the lanes", "home"),
         ("/inbox", "inbox", "Needs you", "what is waiting on you", "inbox"),
         ("/queue", "list-ordered", "Queue", "the GPU lane and what waits", "queue"),
         ("/books", "library", "Books", "the shelf", "books"),
         ("/architecture", "network", "Architecture", "the org chart", "architecture"))
"""(href, icon, label, palette subtitle, sidebar id) of every page the sidebar names."""
KEYS = (
    {"keys": "ctrl+k", "does": "search & jump (⌘K on a Mac)", "group": "Everywhere", "act": "palette"},
    {"keys": "/", "does": "search", "group": "Everywhere", "act": "palette"},
    {"keys": "?", "does": "this sheet", "group": "Everywhere", "act": "keys"},
    {"keys": "t", "does": "Studio black / Graphite", "group": "Everywhere", "act": "theme"},
    {"keys": "g h", "does": "Home", "group": "Go to", "go": "/"},
    {"keys": "g i", "does": "Needs you", "group": "Go to", "go": "/inbox"},
    {"keys": "g q", "does": "Queue", "group": "Go to", "go": "/queue"},
    {"keys": "g b", "does": "Books", "group": "Go to", "go": "/books"},
    {"keys": "g a", "does": "Architecture", "group": "Go to", "go": "/architecture"},
    {"keys": "g r", "does": "the unit on the GPU", "group": "Go to", "act": "gpu"},
    {"keys": "j", "does": "next row", "group": "On this page", "act": "row-next"},
    {"keys": "k", "does": "previous row", "group": "On this page", "act": "row-prev"},
    {"keys": "[", "does": "previous unit", "group": "On this page", "click": "["},
    {"keys": "]", "does": "next unit", "group": "On this page", "click": "]"},
    {"keys": "w", "does": "watch the master", "group": "On this page", "click": "w"},
    {"keys": "A", "does": "acknowledge all", "group": "On this page", "click": "A"},
)
"""The one key registry (C4): the `?` sheet, the titles, `aria-keyshortcuts` and
board.js's map are all drawn from it.  `go` navigates, `act` is a shell action,
`click` presses the page's control marked `data-key="<keys>"`."""
CAPS = {"ctrl": ("Ctrl", "Control"), "shift": ("Shift", "Shift")}
HEARTBEAT = {"period": 2, "hidden": 10, "stale": 5, "timeout": 8, "backoff": [2, 4, 8, 16, 30]}
"""The pulse's clock (seconds): every 2 s, 10 s while hidden; older than 5 s is
stale; a request is abandoned after 8 s; failures back off 2→30 s."""
HOLD_REASONS = ("checking a fault", "need the GPU", "end of the day", "testing a change")
NEEDS = ("failed", "deferred", "escalated", "stale", "flagged")


def static_url(path: str) -> str:
    """`/static/<path>?v=<mtime_ns hex>`: a changed file is a new URL; no stamp when it is gone."""
    try:
        return f"/static/{path}?v={(STATIC / path).stat().st_mtime_ns:x}"
    except OSError:
        return f"/static/{path}"


def section(path: str) -> str:
    """Which sidebar item a path lives under: home, inbox, queue, books, architecture or `d:<stage>`."""
    if path == "/":
        return "home"
    if path == "/inbox":
        return "inbox"
    if path in ("/floor", "/queue"):
        return "queue"
    if path == "/books" or path.startswith("/b/"):
        return "books"
    if path == "/architecture":
        return "architecture"
    parts = path.split("/")
    return f"d:{parts[2]}" if len(parts) > 2 and parts[1] == "d" and parts[2] else ""


def key_for(href: str) -> str:
    """The `go` chord that reaches `href` ('' when none does)."""
    return next((k["keys"] for k in KEYS if k.get("go") == href), "")


def keycaps(keys: str) -> list[str]:
    """A chord as the keycaps the sheet draws: `g h` -> G H, `ctrl+k` -> Ctrl K, `A` -> Shift A."""
    caps = []
    for part in keys.split(" "):
        mods, _, key = part.rpartition("+")
        caps += [CAPS[m][0] for m in mods.split("+") if m]
        caps += ["Shift", key] if key.isalpha() and key.isupper() else [key.upper() if key.isalpha() else key]
    return caps


def aria_keys(keys: str) -> str:
    """`aria-keyshortcuts` for a single key or a modified key; '' for a two-key
    chord, which the attribute cannot say."""
    if " " in keys:
        return ""
    mods, _, key = keys.rpartition("+")
    return "+".join([CAPS[m][1] for m in mods.split("+") if m] + keycaps(key))


def key_rows() -> list[dict]:
    """KEYS as the templates and board.js read them: each row with its keycaps and
    its `aria-keyshortcuts` value."""
    return [{**k, "caps": keycaps(k["keys"]), "aria": aria_keys(k["keys"])} for k in KEYS]


def chip_state(age: float, err: bool, boot_changed: bool) -> str:
    """The heartbeat chip (mirrors pulse.js `chipState`): `restart` when the board
    came back as a new process, `offline` when the last pulse failed, `stale` when
    the last good one is older than HEARTBEAT['stale'] seconds, else `live`."""
    if boot_changed:
        return "restart"
    if err:
        return "offline"
    return "stale" if age > HEARTBEAT["stale"] else "live"


def crumbs(path: str, names: dict[str, str]) -> list[tuple[str, str | None]]:
    """The breadcrumb from Home to `path`: (label, href), the last one unlinked."""
    trail = [("Home", "/")] + _trail(path.rstrip("/") or "/", names)
    return trail[:-1] + [(trail[-1][0], None)]


def _trail(path: str, names: dict[str, str]) -> list[tuple[str, str]]:
    """The crumbs after Home for one route shape (page, book, department, unit)."""
    pages = {href: label for href, _, label, _, _ in PAGES} | {"/floor": "Queue"}
    if path in pages:
        return [] if path == "/" else [(pages[path], path)]
    parts = path.strip("/").split("/")
    if len(parts) == 2 and parts[0] == "b":
        return [("Books", "/books"), (names.get(parts[1], parts[1]), path)]
    if len(parts) == 4 and parts[0] == "d":
        stage, codex, unit = parts[1:]
        return [("Books", "/books"), (names.get(codex, codex), f"/b/{codex}"),
                (stage, f"/d/{stage}?book={codex}"), (unit, path)]
    return [(parts[-1], path)]


def dept_label(item: dict) -> str:
    """A department row's accessible name, `episode, 1 running, 5 flagged`; the
    unit count only when nothing moves."""
    words = [w for _, _, w in item["dots"]] or [f"{item['total']} units"]
    return ", ".join([item["stage"], *words])


def studio_hold(conn: sqlite3.Connection) -> dict | None:
    """The open studio-wide hold as {id, since, reason}; None while the studio runs."""
    row = conn.execute("SELECT id, held_at, reason FROM holds WHERE scope = 'studio' AND lifted_at IS NULL"
                       " ORDER BY id DESC LIMIT 1").fetchone()
    return {"id": row["id"], "since": row["held_at"], "at": hm(row["held_at"]), "reason": row["reason"]} if row else None


def hm(iso: str | None) -> str:
    """`19:21` in this machine's local time from an ISO timestamp (UTC when it names
    no zone); '' when it does not parse."""
    try:
        t = datetime.fromisoformat((iso or "").replace("Z", "+00:00"))
    except ValueError:
        return ""
    return (t if t.tzinfo else t.replace(tzinfo=timezone.utc)).astimezone().strftime("%H:%M")


def needs_count(conn: sqlite3.Connection) -> int:
    """How many rows Needs you holds: `views.inbox_count`, C1's one source."""
    return views.inbox_count(conn)


def dots(counts: dict, total: int) -> list[tuple[str, int, str]]:
    """A department's state dots: running, failed, flagged with their counts; one
    `done` dot when every unit is done; none when nothing has moved."""
    out = [(key, counts[state], f"{counts[state]} {state}") for key, state in DOTS if counts.get(state)]
    if not out and total and counts.get("done") == total:
        out.append(("done", total, f"all {total} done"))
    return out


def department_items(lanes: list[dict]) -> list[dict]:
    """A sidebar row per lane: the stage, its icon, its unit count, its dots."""
    items = []
    for lane in lanes:
        d = dots(lane["counts"], lane["total"])
        items.append({"stage": lane["stage"], "icon": DEPT_ICONS.get(lane["stage"], DEFAULT_ICON),
                      "total": lane["total"], "dots": d, "lead": d[0][0] if d else "",
                      "label": dept_label({"stage": lane["stage"], "total": lane["total"], "dots": d})})
    return items


def face(library: Path, row: dict) -> str | None:
    """The unit's newest storyboard picture as a 160 px thumb; None without one."""
    book = library_paths.book_folder(library, row["codex_id"])
    if book is None or not row.get("home"):
        return None
    home = book / row["home"]
    for pattern in FACES:
        hits = sorted(home.glob(pattern), key=lambda p: (p.stat().st_mtime_ns, p.name))
        if hits:
            rel = library_paths.book_relative(hits[-1], row["codex_id"])
            return library_paths.thumb_url(row["codex_id"], rel, 40, library_paths.stamp(hits[-1])) if rel else None
    return None


def pin(library: Path, row: dict, names: dict[str, str]) -> dict:
    """A running unit as the sidebar pins it: where it links, its face, its step,
    and the progress JSON the GPU card reads its finish time from (episodes only)."""
    step = " ".join(x for x in (row.get("step_id"), row.get("step_name"), row.get("progress")) if x)
    episode = row["stage"] == "episode"
    return {"unit": row["unit"], "stage": row["stage"], "codex_id": row["codex_id"],
            "book": names.get(row["codex_id"], row["codex_id"]), "state": row["shown"], "step": step,
            "href": f"/d/{row['stage']}/{row['codex_id']}/{row['unit']}", "face": face(library, row),
            "progress_url": f"/api/progress/episode/{row['codex_id']}/{row['unit']}.json" if episode else None}


def gpu(pins: list[dict], running: list[dict]) -> dict | None:
    """The GPU card: the pinned row whose work order holds the GPU, else the first running; None idle."""
    held = [p for p, r in zip(pins, running) if r.get("gpu")]
    return (held or pins or [None])[0]


def count(conn: sqlite3.Connection, sql: str) -> int:
    """One COUNT(*) as an int."""
    return int(conn.execute(sql).fetchone()[0])


def unit_entries(rows: list[dict], needs: set[tuple], names: dict[str, str]) -> list[dict]:
    """Every unit for the palette, ranked running, then what needs you, then the
    most recently changed; each with its state, its glyph and its book."""
    rows = sorted(rows, key=lambda r: r.get("updated_at") or "", reverse=True)
    rows.sort(key=lambda r: 0 if r["shown"] == "running" else 1 if (r["codex_id"], r["stage"], r["unit"]) in needs else 2)
    return [{"g": "Units", "ic": views.ICONS.get(r["shown"], "circle"), "st": r["shown"], "gl": r["glyph"],
             "l": f"{r['unit']} · {r['stage']}", "s": f"{names.get(r['codex_id'], r['codex_id'])} · {r['shown']}",
             "h": f"/d/{r['stage']}/{r['codex_id']}/{r['unit']}"} for r in rows]


def action_entries(hold: dict | None, flagged: list[dict]) -> list[dict]:
    """The palette's only verbs: hold the studio (or lift its hold) and acknowledge
    a unit that shipped with flags -- nothing that starts GPU work."""
    first = ({"g": "Actions", "ic": "play", "l": "Lift the studio hold", "s": hold["reason"], "a": "lift", "id": hold["id"]}
             if hold else {"g": "Actions", "ic": "pause", "l": "Hold the studio…", "s": "pick a reason", "a": "hold",
                           "reasons": list(HOLD_REASONS)})
    return [first] + [{"g": "Actions", "ic": "check", "l": f"Acknowledge {r['unit']} · {r['stage']}",
                       "s": r.get("reason", ""), "a": "ack", "codex": r["codex_id"], "stage": r["stage"],
                       "unit": r["unit"]} for r in flagged]


def palette(departments: list[dict], books: dict[str, str], units: list[dict], actions: list[dict]) -> list[dict]:
    """The ⌘K index: the pages, every unit, the actions, the books, the departments."""
    out = [{"g": "Pages", "ic": ic, "l": label, "s": sub, "h": href, "k": " ".join(keycaps(key_for(href)))}
           for href, ic, label, sub, _ in PAGES]
    out += units + actions
    out += [{"g": "Books", "ic": "book-open", "l": name, "s": codex, "h": f"/b/{codex}"} for codex, name in books.items()]
    out += [{"g": "Departments", "ic": d["icon"], "l": d["stage"], "s": f"{d['total']} units",
             "h": f"/d/{d['stage']}"} for d in departments]
    return out


def palette_index(conn: sqlite3.Connection, library: Path, departments: list[dict] | None = None) -> list[dict]:
    """The palette's data on its own (the page embeds it; a refetch on open reads it)."""
    names, attention = views.book_names(conn), views.attention(conn)
    rows = [views.row_view(r) for r in conn.execute("SELECT * FROM work_orders")]
    needs = {(r["codex_id"], r["stage"], r["unit"]) for r in attention}
    flagged = [r for r in attention if r.get("reason") == views.FLAGGED_REASON]
    return palette(departments if departments is not None else department_items(views.lanes(conn)), names,
                   unit_entries(rows, needs, names), action_entries(studio_hold(conn), flagged))


def shell(conn: sqlite3.Connection, library: Path, path: str) -> dict:
    """Everything the shell draws for one page at `path`."""
    running, names = views.floor(conn)["running"], views.book_names(conn)
    pins = [pin(library, r, names) for r in running]
    departments = department_items(views.lanes(conn))
    at = "pin" if any(p["href"] == path for p in pins) else section(path)   # a pinned unit's page lights its pin
    needs = needs_count(conn)
    return {"at": at, "path": path, "inbox": needs, "needs": needs, "books": len(names),
            "queue": count(conn, "SELECT COUNT(*) FROM v_queue"), "departments": departments,
            "pins": pins, "gpu": gpu(pins, running), "hold": studio_hold(conn), "crumbs": crumbs(path, names),
            "key_rows": key_rows(), "aria": {k["keys"]: aria_keys(k["keys"]) for k in KEYS},
            "chord": {href: " ".join(keycaps(key_for(href))) for href, *_ in PAGES}, "heartbeat": HEARTBEAT, "palette": palette_index(conn, library, departments)}
