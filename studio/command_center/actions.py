"""The board's hand (decision 2026-09-25, "Owner actions": one writer, `orders`).
Each action checks what it names, then makes exactly ONE call into
studio/work_orders -- `hold`, `lift` or `order` -- and answers with a receipt:
the new orders row's id, whom it reaches and what it will do.  Nothing here
runs a step, starts a process or writes a row itself; a refusal is `Refused`
with an HTTP status and a plain sentence.  `local_origin` is the CSRF guard:
a POST from a page that is not the board's own host is refused."""
from __future__ import annotations

import re
import sqlite3
from collections.abc import Mapping
from urllib.parse import urlsplit

from studio import db, registry, work_orders
from studio.command_center import views

CODEX = re.compile(r"^\d{14}$")
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
QUEUED = "queued at next run"
EFFECTS = {
    "hold": "held — runs stop before the first GPU step",
    "lift": "lifted — the runs it held start again at their next run",
    "bump": f"{QUEUED} — the unit goes first in its department's queue",
    "retry": f"{QUEUED} — a deferred or failed unit goes back to the queue once",
    "requeue": f"{QUEUED} — the unit goes back to the queue (not while it runs)",
}
UNIT_KINDS = ("bump", "retry", "requeue")


class Refused(Exception):
    """An action the board will not take: an HTTP status and the reason in words."""

    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail


def effect(kind: str, step_id: str | None = None) -> str:
    """What the order will do, in the owner's words."""
    if kind == "redo":
        return (f"{QUEUED} — step {step_id} runs again although its output exists;"
                " the note is also a casebook row")
    return EFFECTS[kind]


def local_origin(headers: Mapping[str, str]) -> bool:
    """True when the POST came from the board's own host (127.0.0.1, localhost)
    or from no page at all (a local shell); a foreign Origin/Referer is False."""
    source = headers.get("origin") or headers.get("referer")
    if not source:
        return True
    return urlsplit(source).hostname in LOCAL_HOSTS


# --- the checks ---


def words(value: str | None, name: str) -> str:
    """A required free-text field, stripped; 422 when it is empty."""
    text = (value or "").strip()
    if not text:
        raise Refused(422, f"{name} is required: say it in words")
    return text


def check_stage(stage: str) -> None:
    if stage not in registry.stage_names():
        raise Refused(404, f"{stage!r} is not a registered department")


def check_codex(conn: sqlite3.Connection, codex: str) -> None:
    """A 14-digit id (422 otherwise) with a codex row (404 otherwise)."""
    if not CODEX.match(codex or ""):
        raise Refused(422, f"{codex!r} is not a 14-digit codex id")
    if codex not in views.book_names(conn):
        raise Refused(404, f"no book {codex} in the codex")


def check_unit(conn: sqlite3.Connection, codex: str, stage: str, unit: str) -> None:
    """The stage registered, the book known, the unit a work-order row."""
    check_stage(stage)
    check_codex(conn, codex)
    if db.work_order(conn, codex, stage, unit) is None:
        raise Refused(404, f"no work order {stage}/{codex}/{unit}")


def check_step(stage: str, step_id: str) -> None:
    if step_id not in {e["id"] for e in registry.steps(stage)}:
        raise Refused(422, f"{step_id!r} is not a step of {stage}")


def hold_ids(conn: sqlite3.Connection, scope: str, codex: str, stage: str, unit: str) -> dict:
    """The ids a hold of this scope reaches, checked; a studio hold reaches all."""
    if scope == "studio":
        return {}
    if scope == "book":
        check_codex(conn, codex)
        return {"codex_id": codex}
    if scope == "unit":
        check_unit(conn, codex, stage, unit)
        return {"codex_id": codex, "stage": stage, "unit": unit}
    raise Refused(422, f"scope {scope!r} is not one of {work_orders.SCOPES}")


# --- the actions: one work_orders call each ---


def receipt(order_id: int, kind: str, target: str, step_id: str | None = None, **extra) -> dict:
    return {"order_id": order_id, "kind": kind, "target": target,
            "effect": effect(kind, step_id), **extra}


def hold(conn: sqlite3.Connection, scope: str, reason: str, codex: str = "", stage: str = "",
         unit: str = "") -> dict:
    """A hold at the scope; the receipt names its orders row and its hold id."""
    reason = words(reason, "a reason")
    ids = hold_ids(conn, scope, codex, stage, unit)
    hold_id = work_orders.hold(conn, scope, reason, **ids)
    order_id = views.recent_orders(conn, limit=1)[0]["id"]
    return receipt(order_id, "hold", views.order_target({"scope": scope, "step_id": None, **ids}),
                   hold_id=hold_id)


def lift(conn: sqlite3.Connection, hold_id: int) -> dict:
    """Open one hold: 404 when there is none, 422 when it is already lifted."""
    try:
        order_id = work_orders.lift(conn, hold_id)
    except ValueError as exc:
        raise Refused(404 if "no hold" in str(exc) else 422, str(exc)) from None
    return receipt(order_id, "lift", f"hold {hold_id}", hold_id=hold_id)


def unit_order(conn: sqlite3.Connection, kind: str, codex: str, stage: str, unit: str) -> dict:
    """A bump, retry or requeue on one unit, for its runner to take."""
    check_unit(conn, codex, stage, unit)
    order_id = work_orders.order(conn, kind, "unit", codex_id=codex, stage=stage, unit=unit)
    return receipt(order_id, kind, f"{stage} › {unit}")


def redo(conn: sqlite3.Connection, codex: str, stage: str, unit: str, step_id: str, note: str,
         artefact: str = "") -> dict:
    """A redo of one step with the owner's note, which also lands in the casebook."""
    note = words(note, "a note")
    check_unit(conn, codex, stage, unit)
    check_step(stage, step_id)
    try:
        about = work_orders.default_artefact(stage, step_id, unit, artefact.strip() or None)
        order_id = work_orders.order(conn, "redo", "unit", codex_id=codex, stage=stage, unit=unit,
                                     step_id=step_id, note=note, artefact=about)
    except (ValueError, FileNotFoundError) as exc:
        raise Refused(422, str(exc)) from None
    return receipt(order_id, "redo", f"{stage} › {unit} · step {step_id}", step_id, artefact=about)
