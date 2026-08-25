"""What a run actually cost. Recorded at the gateway, priced from models.yaml.

Every cost figure in this project was an estimate until this existed, because nothing
persisted usage — 64 log files and zero usage records. Each step logged its own token
counts to text, which is unreadable in aggregate and silently absent whenever a step
forgot to pass `usage={}`.

So the recording lives in `studio.llm`, at the one place every paid call goes through.
A step cannot forget to record, because a step is not asked to.

An unpriced model records its TOKENS and a NULL cost. It never prices at zero: an
unknown cost quietly becoming $0.00 is how an estimate turns into a lie.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

MODELS_PATH = Path("models.yaml")

_DDL = """
CREATE TABLE IF NOT EXISTS usage (
  id            INTEGER PRIMARY KEY,
  recorded_at   TEXT NOT NULL,
  codex_id      TEXT NOT NULL,
  stage         TEXT NOT NULL,
  step_id       TEXT NOT NULL,
  tier          TEXT,
  model         TEXT,
  input_tokens  INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  cost_usd      REAL
);
CREATE INDEX IF NOT EXISTS ix_usage_codex ON usage (codex_id, stage, step_id);
"""


def load_rates(path: Path = MODELS_PATH) -> dict:
    """Rates live beside the model choice, so switching provider moves both."""
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh).get("rates") or {}


def rate_for(model: str) -> dict | None:
    """None means UNPRICED — never a default."""
    return load_rates().get(model)


def cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    rate = rate_for(model)
    if rate is None:
        return None
    return round(input_tokens * rate["input_per_m"] / 1e6
                 + output_tokens * rate["output_per_m"] / 1e6, 6)


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(_DDL)
    conn.commit()


def record(conn: sqlite3.Connection, codex_id: str, stage: str, step_id: str,
           tier: str | None, model: str | None,
           input_tokens: int, output_tokens: int) -> float | None:
    """Append one call's usage. Returns its cost, or None if the model is unpriced."""
    from studio import db

    init(conn)
    usd = cost(model or "", input_tokens, output_tokens)
    conn.execute(
        "INSERT INTO usage (recorded_at, codex_id, stage, step_id, tier, model,"
        " input_tokens, output_tokens, cost_usd) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (db.utc_now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"), codex_id, stage, step_id,
         tier, model, input_tokens, output_tokens, usd))
    conn.commit()
    return usd


_SUM = ("SELECT COUNT(*) AS calls,"
        " COALESCE(SUM(input_tokens), 0) AS input_tokens,"
        " COALESCE(SUM(output_tokens), 0) AS output_tokens,"
        " COALESCE(SUM(cost_usd), 0.0) AS cost_usd,"
        " COALESCE(SUM(CASE WHEN cost_usd IS NULL THEN 1 ELSE 0 END), 0)"
        " AS unpriced_calls FROM usage")


def _row(conn: sqlite3.Connection, where: str, args: tuple) -> dict:
    init(conn)
    row = conn.execute(f"{_SUM} WHERE {where}", args).fetchone()
    return {"calls": row["calls"], "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"],
            "cost_usd": round(row["cost_usd"], 6), "unpriced_calls": row["unpriced_calls"]}


def total(conn: sqlite3.Connection, codex_id: str) -> dict:
    return _row(conn, "codex_id = ?", (codex_id,))


def by_stage(conn: sqlite3.Connection, codex_id: str) -> dict:
    init(conn)
    stages = [r["stage"] for r in conn.execute(
        "SELECT DISTINCT stage FROM usage WHERE codex_id = ? ORDER BY stage",
        (codex_id,))]
    return {s: _row(conn, "codex_id = ? AND stage = ?", (codex_id, s)) for s in stages}


def by_step(conn: sqlite3.Connection, codex_id: str, stage: str) -> dict:
    init(conn)
    steps = [r["step_id"] for r in conn.execute(
        "SELECT DISTINCT step_id FROM usage WHERE codex_id = ? AND stage = ?"
        " ORDER BY step_id", (codex_id, stage))]
    return {s: _row(conn, "codex_id = ? AND stage = ? AND step_id = ?",
                    (codex_id, stage, s)) for s in steps}
