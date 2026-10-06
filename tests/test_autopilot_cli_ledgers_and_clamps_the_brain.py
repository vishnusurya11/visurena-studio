"""The first live triage turn (ep20, 2026-10-06, $0.28) left no row in the usage
table and its order was never clamped: the CLI called `turn` but not lane C's
`ledger` or `allowed`.  Every brain turn is a `stage='brain'` row for the
episode's unit, and an order outside {redo, retry, requeue} x the registry's
step ids parks.  $0."""
from __future__ import annotations

from studio import brain, db, spend
from tests.autopilot_cli_fixtures import CODEX, book, load


def _turn(verdict):
    async def fake_turn(prompt, options, *, transport=None):
        return verdict, {"session_id": "s9", "total_cost_usd": 0.28,
                         "model_usage": {"claude-sonnet-5-5": {"input_tokens": 32336, "output_tokens": 855}}}
    return fake_turn


def test_a_brain_turn_is_a_brain_row_for_the_unit(tmp_path, monkeypatch):
    cli = load()
    root = book(tmp_path)
    (root / "episodes" / "ep02").mkdir(parents=True)
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    monkeypatch.setattr(brain, "turn", _turn(brain.Verdict(response="park", reason="r", finding_row="| F1 |")))
    monkeypatch.setattr(brain, "triage_options", lambda repo: None)
    monkeypatch.setattr(cli, "ledger_conn", lambda: conn)
    doc = cli.run_brain(root, CODEX, 2, {"home": "episodes/ep02"}, root / "episodes" / "ep02" / "brain" / "attempt_01.json")
    row = conn.execute("select stage, unit, model, input_tokens, output_tokens, cost_usd from usage").fetchone()
    assert tuple(row)[:5] == ("brain", "ep02", "claude-sonnet-5-5", 32336, 855)
    assert abs(row[5] - 0.28) < 1e-6 and doc["verdict"] == "park"
    assert abs(spend.unit_spent(conn, CODEX, "ep02") - 0.28) < 1e-6


def test_an_order_outside_the_desk_is_clamped_to_park(tmp_path, monkeypatch):
    cli = load()
    root = book(tmp_path)
    (root / "episodes" / "ep02").mkdir(parents=True)
    monkeypatch.setattr(brain, "turn", _turn(brain.Verdict(response="cure", order={"kind": "waiver", "step_id": "02"},
                                                           reason="r", finding_row="| F1 |")))
    monkeypatch.setattr(brain, "triage_options", lambda repo: None)
    monkeypatch.setattr(cli, "ledger_conn", lambda: None)
    doc = cli.run_brain(root, CODEX, 2, {"home": "episodes/ep02"}, root / "episodes" / "ep02" / "brain" / "attempt_01.json")
    assert doc["verdict"] == "park" and doc["why"].startswith("clamped:")
