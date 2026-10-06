"""The brain's cost is a row in the same usage table as the writer's, stage `brain`,
unit `epNN` -- and the row is the DELTA of the session's running total, because a
resumed call's `total_cost_usd` includes the session's earlier spend (CLI >= 2.1.277):
two resumed turns are two rows that sum to the last total, never to twice it.

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


def test_the_first_turn_records_its_whole_total(conn):
    total = brain.ledger(conn, "book", "ep20", "08", "claude-sonnet-5-5", 0.0, _receipt(0.40))
    row = _rows(conn)[0]
    assert total == 0.40 and row["cost_usd"] == pytest.approx(0.40)
    assert row["stage"] == "brain" and row["unit"] == "ep20" and row["step_id"] == "08"
    assert row["input_tokens"] == 1000 and row["output_tokens"] == 100


def test_two_resumed_turns_are_two_rows_summing_to_the_last_total(conn):
    first = brain.ledger(conn, "book", "ep20", "08", "claude-sonnet-5-5", 0.0, _receipt(0.40))
    last = brain.ledger(conn, "book", "ep20", "08", "claude-sonnet-5-5", first, _receipt(0.65))
    costs = [r["cost_usd"] for r in _rows(conn)]
    assert costs == pytest.approx([0.40, 0.25]) and last == 0.65
    assert spend.unit_spent(conn, "book", "ep20") == pytest.approx(0.65)


def test_a_turn_without_a_total_is_priced_from_the_rate_table_not_null(conn):
    receipt = {**_receipt(0.0), "total_cost_usd": None}
    total = brain.ledger(conn, "book", "ep20", "08", "claude-sonnet-5-5", 0.10, receipt)
    row = _rows(conn)[0]
    assert row["cost_usd"] == pytest.approx(spend.cost("claude-sonnet-5-5", 1000, 100))
    assert row["cost_usd"] is not None and total == 0.10


def test_the_brain_models_are_priced_so_a_row_is_never_null():
    assert spend.rate_for("claude-sonnet-5-5") == {"input_per_m": 2.00, "output_per_m": 10.00}
    assert spend.rate_for("claude-opus-5-5") == {"input_per_m": 4.00, "output_per_m": 20.00}


def test_the_brain_tier_is_registered_for_the_ledgers_model_name():
    import yaml
    tier = yaml.safe_load(open("models.yaml", encoding="utf-8"))["tiers"]["brain"]
    assert tier["provider"] == "anthropic-sdk" and tier["model"] == "claude-sonnet-5-5"


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
