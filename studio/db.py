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

from studio import registry, spend

DB_PATH = Path("db") / "visurena_studio.db"

EVENT_VOCABULARY = ("started", "completed", "failed", "skipped", "escalated", "deferred")
"""`escalated`: the step parked its unit for an owner signature (decision
2026-09-24, owner gates); the next run resumes past it once the verdict exists.
`deferred`: a judge's terminal set the unit aside (a plan the battery never let
through); the unit stops and the next pass authors again."""

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
  event    TEXT NOT NULL CHECK (event IN ('started', 'completed', 'failed', 'skipped', 'escalated', 'deferred')),
  run_id   TEXT,
  detail   TEXT,
  unit     TEXT
);

CREATE INDEX IF NOT EXISTS ix_events_status
  ON events (codex_id, stage, step_id, event_ts);
"""

# The Command Center (decision 2026-09-25): one work-order row per (book, department,
# unit) drives the departments; a view per registered stage is that department's table.
# A sibling of _DDL so _events_ddl() keeps slicing the codex + events block alone.
_WORK_ORDERS_DDL = """
CREATE TABLE IF NOT EXISTS work_orders (
  id           INTEGER PRIMARY KEY,
  codex_id     TEXT NOT NULL REFERENCES codex(id),
  stage        TEXT NOT NULL,
  unit         TEXT NOT NULL DEFAULT 'book',
  number       INTEGER,
  kind         TEXT NOT NULL DEFAULT 'book',
  home         TEXT NOT NULL,
  state        TEXT NOT NULL CHECK (state IN ('blocked','queued','running','stale','held',
                                              'deferred','escalated','failed','done')),
  step_id      TEXT,
  progress     TEXT,
  priority     INTEGER NOT NULL DEFAULT 0,
  sequence     INTEGER,
  gpu          INTEGER NOT NULL DEFAULT 0,
  attempts     INTEGER NOT NULL DEFAULT 0,
  flags        INTEGER NOT NULL DEFAULT 0,
  input_sha8   TEXT, blocked_on TEXT,
  claimed_by   TEXT, lease_until TEXT, run_id TEXT,
  requested_at TEXT, started_at TEXT, updated_at TEXT NOT NULL, finished_at TEXT,
  gpu_seconds  REAL NOT NULL DEFAULT 0, cost_usd REAL,
  deliverable  TEXT, verdicts TEXT,
  hold_reason  TEXT, redo TEXT, note TEXT,
  source       TEXT NOT NULL DEFAULT 'run',
  UNIQUE (codex_id, stage, unit)
);
CREATE INDEX IF NOT EXISTS ix_work_orders_queue ON work_orders (stage, state, priority, sequence);
CREATE UNIQUE INDEX IF NOT EXISTS ux_gpu_lease ON work_orders (gpu) WHERE gpu = 1 AND state = 'running';

CREATE TABLE IF NOT EXISTS work_steps (
  order_id INTEGER NOT NULL REFERENCES work_orders(id), step_id TEXT NOT NULL,
  state TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 0, run_id TEXT,
  started_at TEXT, ended_at TEXT, seconds REAL NOT NULL DEFAULT 0, gpu INTEGER NOT NULL DEFAULT 0,
  verdict_path TEXT, verdict_by TEXT, verdict_word TEXT, terminal TEXT NOT NULL DEFAULT '',
  outputs TEXT, detail TEXT,
  PRIMARY KEY (order_id, step_id)
);

CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY, ts TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('hold','lift','redo','bump','retry','requeue')),
  scope TEXT NOT NULL CHECK (scope IN ('studio','book','unit')),
  codex_id TEXT, stage TEXT, unit TEXT, step_id TEXT,
  note TEXT, by TEXT NOT NULL DEFAULT 'owner', taken_ts TEXT, taken_by_run TEXT
);
CREATE TABLE IF NOT EXISTS holds (
  id INTEGER PRIMARY KEY, scope TEXT NOT NULL, codex_id TEXT, stage TEXT, unit TEXT,
  reason TEXT NOT NULL, held_by TEXT, held_at TEXT NOT NULL, lifted_at TEXT
);

CREATE VIEW IF NOT EXISTS v_queue AS
  SELECT * FROM work_orders WHERE state = 'queued' ORDER BY stage, priority, sequence, unit;
CREATE VIEW IF NOT EXISTS v_attention AS
  SELECT * FROM work_orders WHERE state IN ('failed', 'deferred', 'escalated', 'stale')
  ORDER BY updated_at, id;
"""

WORK_ORDER_STATES = ("blocked", "queued", "running", "stale", "held",
                     "deferred", "escalated", "failed", "done")


def get_connection(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    """Open a connection with row access by name and FK enforcement on."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Per-stage summary columns on codex (owner design: 3 per stage — status, started,
# updated). Denormalized at-a-glance view; the events table stays the detailed record.
# The registry decides which stages exist; a new stage gets its trio by being registered.
STAGES = tuple(registry.stage_names())
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
    _migrate_events(conn)
    _migrate_work_orders(conn)


def _migrate_events(conn: sqlite3.Connection) -> None:
    """Bring an older events table forward: the `unit` column, and every word of
    the vocabulary in the CHECK.  SQLite cannot edit a CHECK, so a table that lacks
    a word is rebuilt row for row under the current DDL (idempotent: a current
    table is left alone)."""
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(events)")}
    if "unit" not in cols:
        conn.execute("ALTER TABLE events ADD COLUMN unit TEXT")
    sql = conn.execute("SELECT sql FROM sqlite_master WHERE name = 'events'").fetchone()["sql"]
    if all(word in sql for word in EVENT_VOCABULARY):
        return
    conn.execute("ALTER TABLE events RENAME TO events_old")
    conn.execute("DROP INDEX IF EXISTS ix_events_status")
    conn.executescript(_events_ddl())
    conn.execute("INSERT INTO events (id, event_ts, codex_id, stage, step_id, event, run_id, detail, unit)"
                 " SELECT id, event_ts, codex_id, stage, step_id, event, run_id, detail, unit FROM events_old")
    conn.execute("DROP TABLE events_old")


def _events_ddl() -> str:
    """The events table's CREATE statements alone (table + index), from the DDL."""
    start = _DDL.index("CREATE TABLE IF NOT EXISTS events")
    return _DDL[start:]


def _add_column(conn: sqlite3.Connection, table: str, column: str, type_: str) -> None:
    """ADD one column if the table lacks it (idempotent, by PRAGMA table_info)."""
    cols = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_}")


def _migrate_work_orders(conn: sqlite3.Connection) -> None:
    """The Command Center's tables, brought in beside a live runner: only CREATE IF
    NOT EXISTS and ADD COLUMN -- nothing here renames, drops or rebuilds a table.
    `usage` is created from its own DDL first (an old DB may not have it), then
    widened; one view per registered department, generated from the registry."""
    conn.executescript(spend._DDL)
    conn.executescript(_WORK_ORDERS_DDL)
    _add_column(conn, "events", "order_id", "INTEGER")
    _add_column(conn, "usage", "unit", "TEXT")
    _add_column(conn, "usage", "order_id", "INTEGER")
    for stage in STAGES:
        conn.execute(f"CREATE VIEW IF NOT EXISTS {stage}_orders AS"
                     f" SELECT * FROM work_orders WHERE stage = '{stage}'")


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
    # Ids are second-resolution timestamps and a collision bumps by +1s, so the retry
    # budget is really "how many books may be registered in the same second". Five died
    # on the seventh book of a 22-book corpus; registering a corpus is not exotic.
    max_retries: int = 120,
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
    unit: str | None = None,
) -> str:
    """Append one event. Returns its timestamp. Long detail belongs in logs, not here.
    `unit` names the production below the book (an episode, a cue); NULL for a
    book-level stage."""
    event_ts = utc_now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    conn.execute(
        "INSERT INTO events (event_ts, codex_id, stage, step_id, event, run_id, detail, unit)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (event_ts, codex_id, stage, step_id, event, run_id, detail, unit),
    )
    conn.commit()
    return event_ts


def unit_status(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str) -> dict[str, str]:
    """Derived status of ONE unit of a stage: latest event per step, pipeline order."""
    rows = conn.execute(
        "SELECT step_id, event, MAX(event_ts) AS event_ts FROM events"
        " WHERE codex_id = ? AND stage = ? AND unit = ?"
        " GROUP BY step_id ORDER BY step_id",
        (codex_id, stage, unit),
    )
    return {row["step_id"]: row["event"] for row in rows}


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


def codex_ready_for_stage(
    conn: sqlite3.Connection,
    stage: str,
    final_step_id: str,
    after_stage: str,
    after_final_step_id: str,
) -> list[str]:
    """Books that finished `after_stage` but have not finished `stage`.

    A dependent stage (screenplay needs analysis) cannot use codex_pending_stage:
    that returns every book that has not done the stage, including books with no
    analysis at all. Building a screenplay on a half-finished dossier grounds it in
    nothing, so the prerequisite is part of the query, not a caller's courtesy check.
    """
    rows = conn.execute(
        "SELECT c.id FROM codex c WHERE EXISTS ("
        " SELECT 1 FROM events e WHERE e.codex_id = c.id AND e.stage = ?"
        " AND e.step_id = ? AND e.event = 'completed') AND NOT EXISTS ("
        " SELECT 1 FROM events e WHERE e.codex_id = c.id AND e.stage = ?"
        " AND e.step_id = ? AND e.event = 'completed') ORDER BY c.id",
        (after_stage, after_final_step_id, stage, final_step_id),
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


# --- work orders: the department table (decision 2026-09-25) ---


def work_order(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str) -> sqlite3.Row | None:
    """The one row of a (book, department, unit); None before anything ordered it."""
    return conn.execute(
        "SELECT * FROM work_orders WHERE codex_id = ? AND stage = ? AND unit = ?",
        (codex_id, stage, unit),
    ).fetchone()


def _order_defaults(stage: str, unit: str) -> dict[str, str]:
    """`home` and `kind` from the registry's unit grammar: an episode lives under
    episodes/<unit> and is a chapter; every other department is book-level and
    lives in its own folder (`refs`, `analysis`, `trailer`, ...)."""
    if stage == "episode":
        return {"home": f"episodes/{unit}", "kind": "chapter"}
    return {"home": stage, "kind": "book"}


def _insert_work_order(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str,
                       fields: dict) -> int:
    """INSERT the row with the grammar's defaults under the given fields; its id."""
    values = {**_order_defaults(stage, unit), "state": "blocked", **fields,
              "codex_id": codex_id, "stage": stage, "unit": unit,
              "updated_at": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")}
    cols = ", ".join(values)
    marks = ", ".join("?" * len(values))
    cur = conn.execute(f"INSERT INTO work_orders ({cols}) VALUES ({marks})", tuple(values.values()))
    conn.commit()
    return cur.lastrowid


def _update_work_order(conn: sqlite3.Connection, order_id: int, fields: dict) -> int:
    """UPDATE the given columns of one row; updated_at always; the same id back."""
    fields = {**fields, "updated_at": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")}
    assignments = ", ".join(f"{col} = ?" for col in fields)
    conn.execute(f"UPDATE work_orders SET {assignments} WHERE id = ?",
                 (*fields.values(), order_id))
    conn.commit()
    return order_id


def upsert_work_order(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str,
                      **fields) -> int:
    """One row per (book, department, unit): INSERT it (home/kind from the unit
    grammar) or UPDATE the given columns.  Returns the row id.  A column the
    table lacks is an OperationalError -- the DDL is the contract, not a kwarg."""
    row = work_order(conn, codex_id, stage, unit)
    if row is None:
        return _insert_work_order(conn, codex_id, stage, unit, fields)
    return _update_work_order(conn, row["id"], fields)


def department_rows(conn: sqlite3.Connection, stage: str) -> list[sqlite3.Row]:
    """A department's table: its registry-generated view, queue order."""
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}; known: {STAGES}")
    return list(conn.execute(
        f"SELECT * FROM {stage}_orders ORDER BY priority, sequence, unit"))


def claim_gpu(conn: sqlite3.Connection, order_id: int) -> None:
    """Mark a row running on the GPU.  The partial unique index ux_gpu_lease makes
    a second running GPU row an IntegrityError: one GPU, one claim."""
    conn.execute(
        "UPDATE work_orders SET state = 'running', gpu = 1, updated_at = ? WHERE id = ?",
        (utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"), order_id),
    )
    conn.commit()
