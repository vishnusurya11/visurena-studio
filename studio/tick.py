"""The desk: the tick that drives the department tables (decision 2026-09-25,
"How a department is driven" -- tick + pull).

    slate        what a stage has on disk today: every `episodes/epNN` folder for
                 the chapter-grain line, the book-level unit name for the rest
    materialize  one `blocked` row per (book, department, unit) the slate names,
                 INSERT OR IGNORE, `source='queue'`
    settle       a blocked or queued row whose every declared output is on disk
                 is `done` (C2's map leaves a skipped unit blocked; this closes it);
                 an episode with a publish record (youtube.json + an upload row,
                 backfill.publish_row) is `done` when its row is blocked, queued,
                 or running/stale on a lease that ran out (2026-10-11: units
                 published outside the runner sat queued, blocked or stale)
    promote      blocked -> queued when every `requires` row is done and the first
                 step's `in:` exist; queued -> blocked when they stop; nothing else
    hold         a hold at the unit's scope parks a blocked or queued row as `held`;
                 on lift it returns to `blocked` and the same tick promotes it again.
                 The pre-hold state is NOT stored: blocked/queued was never a fact,
                 only a projection of requires + inputs, so it is re-derived.
    costs        gpu_seconds off the unit's clock, cost_usd off usage
    sweep        a running row whose lease ran out is `stale`, never requeued
    verify       rows against the disk: a disagreement is named and marked `stale`;
                 nothing is resolved (a run or an order moves it)

Every runner's first act is `tick_book` for its own book (the Tracker's start):
one book, cheap, and never a stop -- an error is logged and the run goes on.
The runner claims and settles through add_event; nothing here runs a step or
reads the table to decide whether a step is done.
"""
from __future__ import annotations

import logging
import re
import sqlite3
from collections import Counter
from pathlib import Path

from studio import (approval, backfill, db, episode_home, ledger_settle, manifest, registry, timing_sum,
                    verdict_rows, work_orders)
from studio.youtube_publish import sha8

LOG = logging.getLogger("studio.tick")
EPISODE_UNIT = re.compile(r"^ep(\d\d)$")
BOOK_UNIT = {"refs": "main"}
"""How each book-level runner names its unit in events: refs says `main`
(studio/refs_run); every other book-level stage writes NULL, which
project_event reads as `book`."""
QUEUEABLE = ("blocked", "queued")
"""The two states the tick moves between; every other state belongs to a run,
a judge, a lease or the owner."""
PUBLISHED_STAGE = "episode"
"""The one department whose unit is uploaded: its publish record settles it."""


def _now() -> str:
    return db.utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


# --- the slate and the grammar ---


def book_unit(stage: str) -> str:
    """The unit name a book-level stage's rows carry."""
    return BOOK_UNIT.get(stage, "book")


def episode_units(book_dir: Path) -> list[str]:
    """Every `episodes/epNN` folder, ascending; a folder outside the grammar
    (ep01_short) is not a unit."""
    root = Path(book_dir) / "episodes"
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and EPISODE_UNIT.match(p.name))


def slate(codex_id: str, stage: str, book_dir: Path) -> list[str]:
    """The units a stage has on disk today."""
    if "chapter" in registry.unit_of(stage):
        return episode_units(book_dir)
    return [book_unit(stage)]


def unit_grammar(stage: str, unit: str) -> dict:
    """home and kind from the one grammar function, plus number and sequence
    when the unit carries a number (epNN -> NN)."""
    fields = db._order_defaults(stage, unit)
    found = EPISODE_UNIT.match(unit)
    if found:
        fields.update(number=int(found.group(1)), sequence=int(found.group(1)))
    return fields


def materialize(conn: sqlite3.Connection, codex_id: str, stage: str, units: list[str]) -> int:
    """One blocked row per unit that has none yet (INSERT OR IGNORE through the
    one writer); a row a run already wrote is left as it is.  Rows created."""
    made = 0
    for unit in units:
        if db.work_order(conn, codex_id, stage, unit) is None:
            db.upsert_work_order(conn, codex_id, stage, unit, state="blocked", source="queue",
                                 requested_at=_now(), **unit_grammar(stage, unit))
            made += 1
    return made


# --- requires and inputs ---


def required_unit(required_stage: str, stage: str, unit: str) -> str:
    """The unit of the required stage's row: the same unit at the same grain,
    else the required stage's book-level name."""
    if registry.unit_of(required_stage) == registry.unit_of(stage):
        return unit
    return book_unit(required_stage)


def requirements_met(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str) -> tuple[bool, str]:
    """Every `requires` edge is a done row (the upstream manifest's row, never a
    sentence); (ok, the first unmet edge as text, e.g. 'refs/04')."""
    for requirement in registry.requires_of(stage):
        required_stage = requirement.split("/")[0]
        row = db.work_order(conn, codex_id, required_stage, required_unit(required_stage, stage, unit))
        if row is None or row["state"] != "done":
            return False, requirement
    return True, ""


def first_inputs(stage: str, unit: str) -> list[str]:
    """The first step's declared inputs: the only ones that gate the queue."""
    entries = registry.steps(stage)
    return registry.inputs_of(stage, entries[0]["id"], unit) if entries else []


def missing_inputs(book_dir: Path, stage: str, unit: str) -> list[str]:
    """The first step's input globs that match no file, in declared order."""
    return [glob for glob in first_inputs(stage, unit) if not manifest.matched(book_dir, [glob])]


def inputs_exist(book_dir: Path, stage: str, unit: str) -> bool:
    return not missing_inputs(book_dir, stage, unit)


def promote(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str, book_dir: Path) -> str:
    """blocked -> queued when the requires are done and the inputs exist; queued
    -> blocked when they stop holding, `blocked_on` naming the first want.  A row
    in any other state is not touched.  The state after; '' for no row."""
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None or row["state"] not in QUEUEABLE:
        return row["state"] if row else ""
    ok, waiting = requirements_met(conn, codex_id, stage, unit)
    missing = missing_inputs(book_dir, stage, unit) if ok else []
    state = "queued" if ok and not missing else "blocked"
    blocked_on = None if state == "queued" else (waiting or f"in: {missing[0]}")
    if (state, blocked_on) != (row["state"], row["blocked_on"]):
        db.upsert_work_order(conn, codex_id, stage, unit, state=state, blocked_on=blocked_on)
    return state


# --- settling from the disk ---


def outputs_on_disk(book_dir: Path, stage: str, unit: str) -> bool:
    """Every declared output of every step matches at least one file."""
    for entry in registry.steps(stage):
        for glob in registry.outputs_of(stage, entry["id"], unit):
            if not manifest.matched(book_dir, [glob]):
                return False
    return True


def settle_skipped(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str, book_dir: Path) -> bool:
    """A blocked or queued row whose every output and deliverable are on disk is
    done -- the unit whose every step was skipped (the note under C7).  `source`
    is kept.  A stage that declares no deliverable never settles from disk."""
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None or row["state"] not in QUEUEABLE:
        return False
    deliverable = verdict_rows.deliverable(book_dir, stage, unit)
    if deliverable is None or not outputs_on_disk(book_dir, stage, unit):
        return False
    db.upsert_work_order(conn, codex_id, stage, unit, state="done", deliverable=deliverable,
                         step_id=registry.steps(stage)[-1]["id"], blocked_on=None, finished_at=_now())
    return True


def settle_from_ledger(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str) -> bool:
    """A book-level row the ledger already calls finished is done: runners write
    codex.<stage>_status = 'completed' (db.mark_stage).  Only for the book grain,
    whose one unit that column describes; a per-unit stage settles from disk."""
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None or row["state"] not in QUEUEABLE or unit != book_unit(stage):
        return False
    status = db.get_codex(conn, codex_id)[f"{stage}_status"]
    if status != "completed":
        return False
    db.upsert_work_order(conn, codex_id, stage, unit, state="done", blocked_on=None,
                         step_id=registry.steps(stage)[-1]["id"], finished_at=_now())
    return True


def settle_from_events(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str) -> str:
    """A blocked or queued book-level row is what the events ledger says
    (ledger_settle.reading): `settled` when it wrote done or failed, `cursor` when
    it only moved the step, '' when the ledger is silent or the row is not the tick's."""
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None or row["state"] not in QUEUEABLE or unit != book_unit(stage):
        return ""
    said = ledger_settle.reading(ledger_settle.step_events(conn, codex_id, stage, unit),
                                 registry.steps(stage)[-1]["id"], stage)
    if said is None:
        return ""
    if said["state"] is None:
        if row["step_id"] != said["step_id"]:
            db.upsert_work_order(conn, codex_id, stage, unit, step_id=said["step_id"])
        return "cursor"
    db.upsert_work_order(conn, codex_id, stage, unit, state=said["state"], step_id=said["step_id"],
                         flags=said["flags"], note=said["note"], blocked_on=None,
                         finished_at=said["finished_at"] or row["finished_at"])
    return "settled"


def published_consumers(book_dir: Path) -> int:
    """How many of the book's episodes are on the channel (backfill.publish_row)."""
    return sum(1 for u in episode_units(book_dir) if backfill.publish_row(book_dir, "", u) is not None)


def settle_consumed(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str, book_dir: Path) -> bool:
    """A blocked or queued book-level row the episode requires is done once an
    episode built on it is published: work from before the runners (Scarlet's
    legacy refs, consumed by 14 published episodes) was made, whatever its layout."""
    row = db.work_order(conn, codex_id, stage, unit)
    wanted = {r.split("/")[0] for r in registry.requires_of(PUBLISHED_STAGE)}
    if row is None or row["state"] not in QUEUEABLE or unit != book_unit(stage) or stage not in wanted:
        return False
    n = published_consumers(book_dir)
    if not n:
        return False
    db.upsert_work_order(conn, codex_id, stage, unit, state="done", blocked_on=None, finished_at=_now(),
                         note=f"legacy: consumed by {n} published episode{'s' if n != 1 else ''}")
    return True


def uploaded_file(book_dir: Path, unit: str, digest: str, hasher=sha8) -> str | None:
    """The unit's master the upload's sha8 names, book-relative posix: the
    newest cut/*.mp4 (then any mp4 under the home) whose bytes hash to it;
    None when no file on disk does.  `hasher` lets the board memoise."""
    home = Path(book_dir) / manifest.home_of(PUBLISHED_STAGE, unit)
    cuts = sorted((home / "cut").glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in cuts + sorted(home.glob("*.mp4")):
        if hasher(path) == digest:
            return path.relative_to(book_dir).as_posix()
    return None


def lease_ran_out(row) -> bool:
    """A running row whose lease is past, or the stale row the sweep made of one."""
    if row["state"] == "stale":
        return row["blocked_on"] == "lease expired"
    return row["state"] == "running" and bool(row["lease_until"]) and row["lease_until"] < _now()


def settle_published(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str, book_dir: Path) -> bool:
    """An episode with a publish record is done: a blocked or queued row, or one
    whose run lost its lease.  The deliverable is the uploaded file (else the
    youtube.json), the note names the record, `source` is kept."""
    row = db.work_order(conn, codex_id, stage, unit)
    if stage != PUBLISHED_STAGE or row is None or not (row["state"] in QUEUEABLE or lease_ran_out(row)):
        return False
    record = backfill.publish_row(book_dir, codex_id, unit)
    if record is None:
        return False
    digest = record["unit"].split("@")[0]
    db.upsert_work_order(conn, codex_id, stage, unit, state="done", blocked_on=None, finished_at=_now(),
                         deliverable=uploaded_file(book_dir, unit, digest) or record["deliverable"],
                         step_id=registry.steps(stage)[-1]["id"],
                         note=f"settled from the publish record: {record['note']}")
    return True


def clear_done_wait(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str) -> bool:
    """A done row waits on nothing: a blocked_on it still carries is cleared."""
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None or row["state"] != "done" or row["blocked_on"] is None:
        return False
    db.upsert_work_order(conn, codex_id, stage, unit, blocked_on=None)
    return True


# --- holds on the rows ---


def park_held(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str) -> str:
    """A blocked or queued row a hold reaches is `held`, the hold's reason on
    the row and its id in blocked_on.  The state after; '' for no row."""
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None:
        return ""
    holds = work_orders.active_holds(conn, codex_id, stage, unit)
    if not holds or row["state"] not in QUEUEABLE:
        return row["state"]
    db.upsert_work_order(conn, codex_id, stage, unit, state="held",
                         hold_reason=holds[0]["reason"], blocked_on=f"hold {holds[0]['id']}")
    return "held"


def release_held(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str) -> str:
    """A held row no hold reaches any more goes back to `blocked`; promote, in
    the same tick, decides whether it is queued.  The state after."""
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None:
        return ""
    if row["state"] != "held" or work_orders.active_holds(conn, codex_id, stage, unit):
        return row["state"]
    db.upsert_work_order(conn, codex_id, stage, unit, state="blocked", hold_reason=None, blocked_on=None)
    return "blocked"


# --- costs, leases, verify ---


def project_costs(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str, book_dir: Path) -> dict:
    """gpu_seconds off the unit's clock (every GPU pass, retries included) and
    cost_usd off usage (None while a call is unpriced), written when they moved.
    The fields; {} for no row."""
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None:
        return {}
    fields = {"gpu_seconds": timing_sum.gpu_seconds_of(Path(book_dir) / row["home"]),
              "cost_usd": db.unit_cost(conn, codex_id, stage, unit)}
    if (fields["gpu_seconds"], fields["cost_usd"]) != (row["gpu_seconds"], row["cost_usd"]):
        db.upsert_work_order(conn, codex_id, stage, unit, **fields)
    return fields


def sweep_leases(conn: sqlite3.Connection, now: str) -> int:
    """Every running row whose lease_until is before `now` is `stale` under
    'lease expired' -- never requeued: that is an order.  Rows swept."""
    rows = list(conn.execute(
        "SELECT codex_id, stage, unit FROM work_orders"
        " WHERE state = 'running' AND lease_until IS NOT NULL AND lease_until < ?", (now,)))
    for row in rows:
        db.upsert_work_order(conn, row["codex_id"], row["stage"], row["unit"],
                             state="stale", blocked_on="lease expired")
    return len(rows)


def verify(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str, book_dir: Path) -> list[str]:
    """Rows against the disk: a moved signature (db.mark_stale_verdicts) and a
    done row whose deliverable is gone are marked `stale` and named, one line
    each.  Nothing is resolved here -- a stale row stays stale when the file
    returns; a run or an order moves it."""
    lines = [f"{stage}/{unit}: {gate} signed another sha8"
             for gate in db.mark_stale_verdicts(conn, codex_id, stage, unit, book_dir)]
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None:
        return lines + [f"{stage}/{unit}: no row"]
    if row["state"] == "done" and row["deliverable"] and not (Path(book_dir) / row["deliverable"]).exists():
        db.upsert_work_order(conn, codex_id, stage, unit, state="stale", blocked_on="deliverable missing")
        lines.append(f"{stage}/{unit}: deliverable missing: {row['deliverable']}")
    return lines


# --- the tick ---


def tick_unit(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str, book_dir: Path) -> Counter:
    """One row through the desk: settle (the events ledger first; the disk only where
    the ledger is silent; the publish record; the codex column; consumption), clear
    a done row's wait, release, promote, park, cost."""
    before = db.work_order(conn, codex_id, stage, unit)["state"]
    ledger = settle_from_events(conn, codex_id, stage, unit)
    settled = (ledger == "settled"
               or (not ledger and settle_skipped(conn, codex_id, stage, unit, book_dir))
               or settle_published(conn, codex_id, stage, unit, book_dir)
               or settle_from_ledger(conn, codex_id, stage, unit)
               or (not ledger and settle_consumed(conn, codex_id, stage, unit, book_dir)))
    clear_done_wait(conn, codex_id, stage, unit)
    release_held(conn, codex_id, stage, unit)
    promote(conn, codex_id, stage, unit, book_dir)
    state = park_held(conn, codex_id, stage, unit)
    project_costs(conn, codex_id, stage, unit, book_dir)
    return Counter(settled=int(settled),
                   promoted=int(state == "queued" and before != "queued"),
                   held=int(state == "held" and before != "held"))


def tick_stage(conn: sqlite3.Connection, codex_id: str, stage: str, book_dir: Path) -> Counter:
    """One department of one book: the slate materialized, every row ticked,
    the unit's paid calls linked to its row."""
    units = slate(codex_id, stage, book_dir)
    counts = Counter(materialized=materialize(conn, codex_id, stage, units))
    for unit in units:
        counts.update(tick_unit(conn, codex_id, stage, unit, book_dir))
    db.link_usage_to_orders(conn)
    return counts


def tick_one(conn: sqlite3.Connection, codex_id: str, book_dir: Path) -> Counter:
    """Every registered department of one book."""
    counts = Counter()
    for stage in registry.stage_names():
        counts.update(tick_stage(conn, codex_id, stage, book_dir))
    return counts


def book_folder(library: Path, codex_id: str) -> Path | None:
    """The book's folder under a library root, by id prefix; None when absent."""
    root = Path(library)
    if not root.is_dir():
        return None
    hits = sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith(codex_id))
    return hits[0] if hits else None


def registered(conn: sqlite3.Connection) -> list[str]:
    """Every book the codex table knows, in id order."""
    return [row["id"] for row in conn.execute("SELECT id FROM codex ORDER BY id")]


def tick(conn: sqlite3.Connection, library: Path, codex_ids: list[str] | None = None, *,
         hold_path: Path = approval.HOLD, now: str | None = None) -> dict:
    """The whole desk: RENDER_HOLD mirrored first (so the rows see it), every
    registered book with a library folder ticked, expired leases swept.  Counts:
    materialized, settled, promoted, held, holds (open), stale (swept now)."""
    work_orders.mirror_render_hold(conn, hold_path)
    counts = Counter(materialized=0, settled=0, promoted=0, held=0)
    for codex_id in codex_ids or registered(conn):
        book = book_folder(library, codex_id)
        if book is not None:
            counts.update(tick_one(conn, codex_id, book))
    counts["holds"] = len(work_orders.active_holds(conn))
    counts["stale"] = sweep_leases(conn, now or _now())
    return dict(counts)


def _ledger_id(codex_id: str) -> str:
    """A library folder name keys the ledger by its 14-digit id (stage_run.ledger_id,
    repeated here so the desk imports nothing that imports the tracker)."""
    return codex_id[:14] if len(codex_id) > 14 and codex_id[14] == "_" else codex_id


def tick_book(conn: sqlite3.Connection, codex_id: str) -> dict | None:
    """A runner's first act: its own book's rows refreshed.  None, and no stop,
    when the codex table or the library does not know the book, or anything
    goes wrong -- a run never fails on its bookkeeping."""
    codex_id = _ledger_id(codex_id)
    try:
        if conn.execute("SELECT 1 FROM codex WHERE id = ?", (codex_id,)).fetchone() is None:
            return None
        return dict(tick_one(conn, codex_id, episode_home.book_dir(codex_id)))
    except (FileNotFoundError, NotADirectoryError):
        return None
    except Exception:
        LOG.exception("tick_book %s: the desk could not be refreshed; the run goes on", codex_id)
        return None
