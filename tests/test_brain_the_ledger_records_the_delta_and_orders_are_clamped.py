"""The brain's turn is a row in the same usage table as the writer's, stage `brain`,
unit `epNN`, model `<model>@subscription` with a NULL cost: the owner's login bills
nothing (2026-10-07), so the SDK's notional `total_cost_usd` is returned for the
log and never written as a cost the episode's wall would count.

The supervisor trusts the verdict's order only inside the registry: a kind outside
redo|retry|requeue or a step the episode stage does not have is clamped to `park`
with the reason saying so.  The brief carries repo-relative paths only; a drive
letter in a prompt is a path the next machine cannot read."""
from __future__ import annotations

import sqlite3

import pytest

from studio import brain, spend


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    spend.init(c)
    return c


def _receipt(total: float, tokens_in: int = 1000, tokens_out: int = 100) -> dict:
    return {"session_id": "sess-1", "total_cost_usd": total,
            "model_usage": {"claude-sonnet-5-5": {"input_tokens": tokens_in,
                                                  "output_tokens": tokens_out}}}


def _rows(conn) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM usage ORDER BY id").fetchall()


def test_a_brain_turn_is_ledgered_on_the_subscription_at_no_cost(conn):
    """Owner, 2026-10-07: nothing is billed -- the brain runs on the same login as
    the writer.  Its tokens are kept; the SDK's notional total never becomes a
    cost, so the episode's wall (unit_spent) does not count it (ep19's status
    read $3.10 'media spent' of which a third was brain triage)."""
    total = brain.ledger(conn, "book", "ep20", "08", "claude-sonnet-5-5", 0.0, _receipt(0.40))
    row = _rows(conn)[0]
    assert row["model"] == "claude-sonnet-5-5@subscription" and row["cost_usd"] is None
    assert row["stage"] == "brain" and row["unit"] == "ep20" and row["step_id"] == "08"
    assert row["input_tokens"] == 1000 and row["output_tokens"] == 100
    assert total == 0.40                      # the session's running total is still returned, for the log
    assert spend.unit_spent(conn, "book", "ep20") == 0.0


def test_two_resumed_turns_are_two_rows_and_still_no_cost(conn):
    first = brain.ledger(conn, "book", "ep20", "08", "claude-sonnet-5-5", 0.0, _receipt(0.40))
    last = brain.ledger(conn, "book", "ep20", "08", "claude-sonnet-5-5", first, _receipt(0.65))
    assert [r["cost_usd"] for r in _rows(conn)] == [None, None] and last == 0.65


def test_a_turn_without_a_total_keeps_the_previous_total(conn):
    receipt = {**_receipt(0.0), "total_cost_usd": None}
    assert brain.ledger(conn, "book", "ep20", "08", "claude-sonnet-5-5", 0.10, receipt) == 0.10
    assert _rows(conn)[0]["cost_usd"] is None


def test_the_brain_tier_runs_on_the_subscription_like_every_other():
    import yaml
    tier = yaml.safe_load(open("models.yaml", encoding="utf-8"))["tiers"]["brain"]
    assert tier["provider"] == "claude-sdk" and tier["model"] == "claude-sonnet-5"


# --- allowed(): the registry clamps the order ------------------------------------

def _verdict(**over) -> brain.Verdict:
    return brain.Verdict(**{"response": "cure", "order": {"kind": "redo", "step_id": "08"},
                            "reason": "stale cell", "finding_row": "| F1 | x | 0 | y | z |", **over})


STEPS = {"01", "02", "08", "10"}


def test_a_registry_order_passes_untouched():
    assert brain.allowed(_verdict(), STEPS) == _verdict()


def test_an_order_kind_outside_the_desk_is_parked():
    out = brain.allowed(_verdict(order={"kind": "sign", "step_id": "02"}), STEPS)
    assert out.response == "park" and out.order is None
    assert out.reason.startswith("clamped:") and "sign" in out.reason


def test_an_unknown_step_is_parked():
    out = brain.allowed(_verdict(order={"kind": "redo", "step_id": "99"}), STEPS)
    assert out.response == "park" and out.reason.startswith("clamped:")


def test_a_cure_without_an_order_is_parked():
    out = brain.allowed(_verdict(order=None), STEPS)
    assert out.response == "park" and "order" in out.reason


def test_a_park_or_retry_without_an_order_is_left_alone():
    for response in ("park", "retry", "relaunch"):
        out = brain.allowed(_verdict(response=response, order=None), STEPS)
        assert out.response == response and not out.reason.startswith("clamped:")


def test_the_episode_step_ids_come_from_the_registry():
    ids = brain.episode_step_ids()
    assert {"01", "02", "13"} <= ids and all(len(i) == 2 for i in ids)


# --- brief(): relative paths only ------------------------------------------------

def test_the_brief_carries_no_drive_letter():
    log = ("2026-10-06 D:\\Projects\\KingdomOfViSuReNa\\alpha\\visurena_studio\\library\\book\\"
           "episodes\\ep20\\drive_run01.log: refused at C:\\Users\\vishn\\x.py")
    text = brain.brief("library/book/episodes/ep20", log, ["G-STORY narration-only 89.6 > 75"],
                       [{"gate": "G-STORY", "terminal": "deferred"}], 0.42, ["redo", "retry"])
    assert "D:\\" not in text and "C:\\" not in text and "D:/" not in text
    assert "library/book/episodes/ep20" in text and "G-STORY narration-only 89.6 > 75" in text
    assert "$0.42" in text and "redo" in text and '"terminal": "deferred"' in text


def test_the_brief_says_what_the_answer_must_be():
    text = brain.brief("library/book/episodes/ep20", "", [], [], 0.0, ["redo"])
    for word in ("retry", "cure", "park", "relaunch", "finding_row"):
        assert word in text
