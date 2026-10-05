"""The board's hand (decision 2026-09-25, "Owner actions": one writer, `orders`).
Each action checks what it names, then makes exactly ONE call into
studio/work_orders -- `hold`, `lift` or `order` -- and answers with a receipt:
the new orders row's id, whom it reaches, what it will do, and which run will
take it -- or that none will (a unit order is applied only when a run of that
unit starts; a done, deferred, failed or escalated unit is never run by
itself).  An order already placed and not yet taken (a double press) answers
with the first order's receipt and writes nothing.  Nothing here
runs a step, starts a process or writes a row itself; a refusal is `Refused`
with an HTTP status and a plain sentence.  `local_origin` is the CSRF guard:
a POST from a page that is not the board's own host is refused."""
from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Mapping
from urllib.parse import urlsplit

from studio import db, registry, work_orders
from studio.command_center import views

CODEX = re.compile(r"^\d{14}$")
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
HOLD_EFFECT = ("The step on the GPU now finishes; then every run stops before its next GPU step."
               " Nothing new starts until you lift.")
"""The one hold sentence (P10 F3): the runner checks a hold before EACH GPU step."""
EFFECTS = {
    "hold": HOLD_EFFECT,
    "lift": "lifted — the runs it held start again at their next run",
    "bump": "the unit goes first in its department's queue",
    "retry": "a deferred or failed unit goes back to the queue once",
    "requeue": "the unit goes back to the queue (not while it runs)",
    "acknowledge": "acknowledged — off Needs you until its flags or verdicts change",
}
WAITS = {
    "queued": "the next run of {stage} takes it",
    "running": "{unit} is running; its run took its orders when it started, so this waits for {unit}'s next run",
    "held": "{unit} is held; the run after the lift takes it",
    "blocked": "{unit} is blocked; the run that starts once it is queued takes it",
    "stale": "{unit} is stale; its next run takes it",
}
"""Who takes a unit order: only a run of that unit (step_runner.run_steps -> take_orders)."""
DEAD = "no run will take it: {unit} is {state}, and nothing starts a run on a {state} unit by itself"
UNIT_KINDS = ("bump", "retry", "requeue")


class Refused(Exception):
    """An action the board will not take: an HTTP status and the reason in words."""

    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail


def effect(kind: str, step_id: str | None = None) -> str:
    """What the order will do, in the owner's words."""
    if kind == "redo":
        return (f"step {step_id} runs again although its output exists;"
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


# --- who takes an order, and how far it has got ---


def taker(conn: sqlite3.Connection, codex: str, stage: str, unit: str) -> dict:
    """What will take a unit order, by the unit's state -- or that nothing will:
    a done, deferred, failed or escalated unit is never run by itself (a dead letter)."""
    row = db.work_order(conn, codex, stage, unit)
    state = row["state"] if row is not None else "blocked"
    if state in WAITS:
        return {"taker": WAITS[state].format(stage=stage, unit=unit), "dead": False}
    return {"taker": DEAD.format(unit=unit, state=state), "dead": True}


def trigger(done: dict) -> str:
    """The HX-Trigger header: `orders-changed`, its detail the order id, kind and state."""
    return json.dumps({"orders-changed": {"order": done["order_id"], "kind": done["kind"],
                                          "state": done["state"]}})


def say(done: dict) -> str:
    """The receipt as one spoken sentence (board.announce reads it)."""
    words_ = done.get("taker") or ""
    tail = f" {words_[:1].upper()}{words_[1:]}." if words_ else ""
    again = " Already placed." if done.get("again") else ""
    return f"Order {done['order_id']}, {done['kind']} {done['target']}: {done['state']}.{again}{tail}"


def receipt(order_id: int, kind: str, target: str, step_id: str | None = None, **extra) -> dict:
    """The receipt: the order, its effect, its state, and the sentence that says it."""
    done = {"order_id": order_id, "kind": kind, "target": target, "effect": effect(kind, step_id),
            "state": "applied" if kind in views.APPLIED else "pending", **extra}
    return {**done, "say": say(done)}


# --- the second wall against a double press ---


def pending_twin(conn: sqlite3.Connection, kind: str, codex: str, stage: str, unit: str,
                 step_id: str | None = None, note: str | None = None) -> int | None:
    """The id of an untaken order on this very unit with the same kind, step and note."""
    for row in work_orders.pending_orders(conn, codex, stage, unit):
        mine = (row["scope"], row["stage"], row["unit"]) == ("unit", stage, unit)
        if mine and (row["kind"], row["step_id"], row["note"]) == (kind, step_id, note):
            return row["id"]
    return None


def _same_target(ids: dict) -> tuple[str, tuple]:
    """The SQL that matches a row's (codex_id, stage, unit) to a hold's ids, NULL-safe."""
    sql = "IFNULL(codex_id, '') = ? AND IFNULL(stage, '') = ? AND IFNULL(unit, '') = ?"
    return sql, (ids.get("codex_id", ""), ids.get("stage", ""), ids.get("unit", ""))


def hold_twin(conn: sqlite3.Connection, scope: str, ids: dict, reason: str) -> tuple[int, int] | None:
    """(hold id, order id) of an open hold with the same scope, target and reason."""
    sql, args = _same_target(ids)
    found = conn.execute(f"SELECT id FROM holds WHERE lifted_at IS NULL AND scope = ? AND reason = ?"
                         f" AND {sql} ORDER BY id LIMIT 1", (scope, reason, *args)).fetchone()
    if found is None:
        return None
    order = conn.execute(f"SELECT id FROM orders WHERE kind = 'hold' AND scope = ? AND note = ?"
                         f" AND {sql} ORDER BY id DESC LIMIT 1", (scope, reason, *args)).fetchone()
    return (found["id"], order["id"]) if order else None


def last_acknowledge(conn: sqlite3.Connection, codex: str, stage: str, unit: str) -> int | None:
    """The newest acknowledge order on the unit when its CURRENT stamp is acknowledged."""
    if not db.acknowledged(conn, codex, stage, unit):
        return None
    row = conn.execute("SELECT id FROM orders WHERE kind = 'acknowledge' AND scope = 'unit' AND codex_id = ?"
                       " AND stage = ? AND unit = ? ORDER BY id DESC LIMIT 1", (codex, stage, unit)).fetchone()
    return row["id"] if row else None


# --- the actions: one work_orders call each (none when the order is already placed) ---


def hold(conn: sqlite3.Connection, scope: str, reason: str, codex: str = "", stage: str = "",
         unit: str = "") -> dict:
    """A hold at the scope; the receipt names its orders row and its hold id."""
    reason = words(reason, "a reason")
    ids = hold_ids(conn, scope, codex, stage, unit)
    twin = hold_twin(conn, scope, ids, reason)
    if twin:
        hold_id, order_id = twin
    else:
        hold_id = work_orders.hold(conn, scope, reason, **ids)
        order_id = views.recent_orders(conn, limit=1)[0]["id"]
    return receipt(order_id, "hold", views.order_target({"scope": scope, "step_id": None, **ids}),
                   hold_id=hold_id, again=bool(twin))


def lift(conn: sqlite3.Connection, hold_id: int) -> dict:
    """Open one hold: 404 when there is none, 422 when it is already lifted."""
    try:
        order_id = work_orders.lift(conn, hold_id)
    except ValueError as exc:
        raise Refused(404 if "no hold" in str(exc) else 422, str(exc)) from None
    return receipt(order_id, "lift", f"hold {hold_id}", hold_id=hold_id)


def unit_order(conn: sqlite3.Connection, kind: str, codex: str, stage: str, unit: str) -> dict:
    """A bump, retry or requeue on one unit; the receipt says which run will take it."""
    check_unit(conn, codex, stage, unit)
    twin = pending_twin(conn, kind, codex, stage, unit)
    order_id = twin or work_orders.order(conn, kind, "unit", codex_id=codex, stage=stage, unit=unit)
    return receipt(order_id, kind, f"{stage} › {unit}", again=bool(twin), **taker(conn, codex, stage, unit))


def redo(conn: sqlite3.Connection, codex: str, stage: str, unit: str, step_id: str, note: str,
         artefact: str = "") -> dict:
    """A redo of one step with the owner's note, which also lands in the casebook."""
    note = words(note, "a note")
    check_unit(conn, codex, stage, unit)
    check_step(stage, step_id)
    twin = pending_twin(conn, "redo", codex, stage, unit, step_id, note)
    try:
        about = work_orders.default_artefact(stage, step_id, unit, artefact.strip() or None)
        order_id = twin or work_orders.order(conn, "redo", "unit", codex_id=codex, stage=stage, unit=unit,
                                             step_id=step_id, note=note, artefact=about)
    except (ValueError, FileNotFoundError) as exc:
        raise Refused(422, str(exc)) from None
    return receipt(order_id, "redo", f"{stage} › {unit} · step {step_id}", step_id, artefact=about,
                   again=bool(twin), **taker(conn, codex, stage, unit))


def acknowledge(conn: sqlite3.Connection, codex: str, stage: str, unit: str, note: str = "") -> dict:
    """The owner has seen a shipped unit's flags: one acknowledge order stamped
    with its verdict state; 422 when the unit is not done with flags."""
    check_unit(conn, codex, stage, unit)
    row = db.work_order(conn, codex, stage, unit)
    if row["state"] != "done" or not row["flags"]:
        raise Refused(422, f"{stage} › {unit} carries no flags to acknowledge")
    twin = last_acknowledge(conn, codex, stage, unit)
    order_id = twin or work_orders.order(conn, "acknowledge", "unit", codex_id=codex, stage=stage,
                                         unit=unit, note=db.ack_note(row, note))
    return receipt(order_id, "acknowledge", f"{stage} › {unit}", again=bool(twin))
