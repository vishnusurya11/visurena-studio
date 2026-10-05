"""The shell's data (plan G1, the v2 sidebar): what every page draws around its
body -- Home, the inbox count, Queue, Books, Architecture, a row per registered
department with its count and state dots, the pinned running units, the live
GPU card and the palette's index.  Pure reads over the views; nothing here is
a state a runner did not write.  `static_url` versions a static file by its
mtime so the board can cache it for a year."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from studio.command_center import library_paths, views

STATIC = Path(__file__).resolve().parent / "static"
DEPT_ICONS = {"analysis": "search", "screenplay": "scroll-text", "trailer": "film",
              "refs": "user-round", "episode": "clapperboard"}
DEFAULT_ICON = "layers"
FACES = ("storyboard/shot_*.png", "storyboard/anchors/*.png")
DOTS = (("run", "running"), ("fail", "failed"), ("flag", "flagged"))
PAGES = (("/", "house", "Home", "the GPU, what needs you, the lanes", "G H"),
         ("/#attention", "inbox", "Inbox", "what needs you", "G I"),
         ("/queue", "list-ordered", "Queue", "the GPU lane and what waits", "G Q"),
         ("/books", "library", "Books", "the shelf", "G B"),
         ("/architecture", "network", "Architecture", "the org chart", "G A"))


def static_url(path: str) -> str:
    """`/static/<path>?v=<mtime_ns hex>`: a changed file is a new URL; no stamp when it is gone."""
    try:
        return f"/static/{path}?v={(STATIC / path).stat().st_mtime_ns:x}"
    except OSError:
        return f"/static/{path}"


def section(path: str) -> str:
    """Which sidebar item a path lives under: home, queue, books, architecture or `d:<stage>`."""
    if path == "/":
        return "home"
    if path in ("/floor", "/queue"):
        return "queue"
    if path == "/books" or path.startswith("/b/"):
        return "books"
    if path == "/architecture":
        return "architecture"
    parts = path.split("/")
    return f"d:{parts[2]}" if len(parts) > 2 and parts[1] == "d" and parts[2] else ""


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
                      "total": lane["total"], "dots": d, "lead": d[0][0] if d else ""})
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


def palette(departments: list[dict], books: dict[str, str], pins: list[dict]) -> list[dict]:
    """The ⌘K index: the pages, the running units, the books, the departments."""
    out = [{"g": "Pages", "ic": ic, "l": label, "s": sub, "h": href, "k": k} for href, ic, label, sub, k in PAGES]
    out += [{"g": "Units", "ic": "loader", "l": f"{p['unit']} · {p['stage']}", "s": f"{p['book']} · {p['step']}",
             "h": p["href"]} for p in pins]
    out += [{"g": "Books", "ic": "book-open", "l": name, "s": codex, "h": f"/b/{codex}"} for codex, name in books.items()]
    out += [{"g": "Departments", "ic": d["icon"], "l": d["stage"], "s": f"{d['total']} units",
             "h": f"/d/{d['stage']}"} for d in departments]
    return out


def shell(conn: sqlite3.Connection, library: Path, path: str) -> dict:
    """Everything the shell draws for one page at `path`."""
    running, names = views.floor(conn)["running"], views.book_names(conn)
    pins = [pin(library, r, names) for r in running]
    departments = department_items(views.lanes(conn))
    at = "pin" if any(p["href"] == path for p in pins) else section(path)   # a pinned unit's page lights its pin
    return {"at": at, "path": path, "inbox": len(views.attention(conn)), "books": len(names),
            "queue": count(conn, "SELECT COUNT(*) FROM v_queue"), "departments": departments,
            "pins": pins, "gpu": gpu(pins, running), "palette": palette(departments, names, pins)}
