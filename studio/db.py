"""SQLite layer: codex master table + events log.

Design: docs/db/SCHEMA.md and docs/db/EVENT_MODEL.md.
- codex.id is THE id across the system: 14-char YYYYMMDDHHMMSS, UTC.
- events is append-only; current status is DERIVED (latest event per step).
- step_id uses fixed-width 2-digit segments (01, 01_01) so text sort = pipeline order.
- Logs live in files, never in these tables.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path("db") / "visurena_studio.db"

EVENT_VOCABULARY = ("started", "completed", "failed", "skipped")

_DDL = """
CREATE TABLE IF NOT EXISTS codex (
  id           TEXT PRIMARY KEY CHECK (length(id) = 14),
  name         TEXT NOT NULL,
  universe     TEXT,
  world        TEXT,
  series       TEXT,
  series_index INTEGER,
  source_type  TEXT CHECK (source_type IN ('gutenberg', 'epub', 'local')),
  source_ref   TEXT,
  updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  id       INTEGER PRIMARY KEY,
  event_ts TEXT NOT NULL,
  codex_id TEXT NOT NULL REFERENCES codex(id),
  stage    TEXT NOT NULL,
  step_id  TEXT NOT NULL,
  event    TEXT NOT NULL CHECK (event IN ('started', 'completed', 'failed', 'skipped')),
  run_id   TEXT,
  detail   TEXT
);

CREATE INDEX IF NOT EXISTS ix_events_status
  ON events (codex_id, stage, step_id, event_ts);
"""


def get_connection(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    """Open a connection with row access by name and FK enforcement on."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Per-stage summary columns on codex (owner design: 3 per stage — status, started,
# updated). Denormalized at-a-glance view; the events table stays the detailed record.
# New stages get their trio here when they are built.
STAGES = ("analysis",)
STAGE_STATUSES = ("pending", "running", "completed", "failed")


def _stage_columns(stage: str) -> list[str]:
    return [f"{stage}_status", f"{stage}_started_at", f"{stage}_updated_at"]


def _migrate(conn: sqlite3.Connection) -> None:
    """Add any missing per-stage summary columns to codex (idempotent)."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(codex)")}
    for stage in STAGES:
        status_col, started_col, updated_col = _stage_columns(stage)
        if status_col not in existing:
            conn.execute(f"ALTER TABLE codex ADD COLUMN {status_col} TEXT"
                         f" NOT NULL DEFAULT 'pending'")
            conn.execute(f"ALTER TABLE codex ADD COLUMN {started_col} TEXT")
            conn.execute(f"ALTER TABLE codex ADD COLUMN {updated_col} TEXT")


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables and indexes if missing; migrate columns. Safe to call repeatedly."""
    conn.executescript(_DDL)
    _migrate(conn)
    conn.commit()


def mark_stage(conn: sqlite3.Connection, codex_id: str, stage: str, status: str) -> None:
    """Update a stage's summary trio: status now, started_at set once, updated_at always."""
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}; known: {STAGES}")
    if status not in STAGE_STATUSES:
        raise ValueError(f"unknown status {status!r}; allowed: {STAGE_STATUSES}")
    status_col, started_col, updated_col = _stage_columns(stage)
    now = utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")
    conn.execute(
        f"UPDATE codex SET {status_col} = ?, {updated_col} = ?,"
        f" {started_col} = COALESCE({started_col}, ?) WHERE id = ?",
        (status, now, now, codex_id),
    )
    conn.commit()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_codex_id() -> str:
    """THE id: 14-char YYYYMMDDHHMMSS from UTC now (never local time)."""
    return utc_now().strftime("%Y%m%d%H%M%S")


def _bump_id(codex_id: str) -> str:
    """Next id one second later — collision retry, per DECISIONS.md."""
    parsed = datetime.strptime(codex_id, "%Y%m%d%H%M%S")
    return (parsed + timedelta(seconds=1)).strftime("%Y%m%d%H%M%S")


def _insert_codex_row(conn: sqlite3.Connection, codex_id: str, name: str, fields: dict) -> None:
    conn.execute(
        "INSERT INTO codex (id, name, universe, world, series, series_index,"
        " source_type, source_ref, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            codex_id,
            name,
            fields.get("universe"),
            fields.get("world"),
            fields.get("series"),
            fields.get("series_index"),
            fields.get("source_type"),
            fields.get("source_ref"),
            utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
    )


def insert_codex(
    conn: sqlite3.Connection,
    name: str,
    *,
    codex_id: str | None = None,
    max_retries: int = 5,
    **fields,
) -> str:
    """Insert a book; returns the id.

    Auto-generated ids retry with +1s on same-second collision. An EXPLICIT id
    (e.g. matching an existing library folder) never bumps — conflicts raise.
    """
    if codex_id is not None:
        _insert_codex_row(conn, codex_id, name, fields)
        conn.commit()
        return codex_id
    codex_id = generate_codex_id()
    for _ in range(max_retries + 1):
        try:
            _insert_codex_row(conn, codex_id, name, fields)
            conn.commit()
            return codex_id
        except sqlite3.IntegrityError as exc:
            if "codex.id" not in str(exc):
                raise
            codex_id = _bump_id(codex_id)
    raise RuntimeError(f"could not insert codex row after {max_retries} id retries")


def get_codex(conn: sqlite3.Connection, codex_id: str) -> sqlite3.Row:
    """Fetch one codex row; loud if the id does not exist."""
    row = conn.execute("SELECT * FROM codex WHERE id = ?", (codex_id,)).fetchone()
    if row is None:
        raise ValueError(f"no codex row with id {codex_id!r}")
    return row


CODEX_UPDATABLE = frozenset(
    {"name", "universe", "world", "series", "series_index", "source_type", "source_ref"}
)


def update_codex(conn: sqlite3.Connection, codex_id: str, **fields) -> None:
    """Update codex columns (whitelisted); refreshes updated_at; loud on unknowns."""
    bad = set(fields) - CODEX_UPDATABLE
    if bad:
        raise ValueError(f"unknown codex column(s): {sorted(bad)}")
    assignments = ", ".join(f"{col} = ?" for col in fields)
    cur = conn.execute(
        f"UPDATE codex SET {assignments}, updated_at = ? WHERE id = ?",
        (*fields.values(), utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"), codex_id),
    )
    if cur.rowcount == 0:
        raise ValueError(f"no codex row with id {codex_id!r}")
    conn.commit()


def add_event(
    conn: sqlite3.Connection,
    codex_id: str,
    stage: str,
    step_id: str,
    event: str,
    *,
    run_id: str | None = None,
    detail: str | None = None,
) -> str:
    """Append one event. Returns its timestamp. Long detail belongs in logs, not here."""
    event_ts = utc_now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    conn.execute(
        "INSERT INTO events (event_ts, codex_id, stage, step_id, event, run_id, detail)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (event_ts, codex_id, stage, step_id, event, run_id, detail),
    )
    conn.commit()
    return event_ts


def codex_pending_stage(
    conn: sqlite3.Connection, stage: str, final_step_id: str
) -> list[str]:
    """Books that have NOT completed a stage (no 'completed' event for its final step)."""
    rows = conn.execute(
        "SELECT c.id FROM codex c WHERE NOT EXISTS ("
        " SELECT 1 FROM events e WHERE e.codex_id = c.id AND e.stage = ?"
        " AND e.step_id = ? AND e.event = 'completed') ORDER BY c.id",
        (stage, final_step_id),
    )
    return [row["id"] for row in rows]


def stage_status(conn: sqlite3.Connection, codex_id: str, stage: str) -> dict[str, str]:
    """Derived status: latest event per step, in pipeline (= text sort) order."""
    rows = conn.execute(
        "SELECT step_id, event, MAX(event_ts) AS event_ts FROM events"
        " WHERE codex_id = ? AND stage = ?"
        " GROUP BY step_id ORDER BY step_id",
        (codex_id, stage),
    )
    return {row["step_id"]: row["event"] for row in rows}
