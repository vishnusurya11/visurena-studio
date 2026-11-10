"""Jekyll ep07 retro S4 (brick 2 appendix): the brain ordered `redo 09` three times on 10-31; every
take was 'cached (bytes unchanged)' and G-DEAD named T10 and T17 again each time.  A cure order that
already ran and left the same refusal lines is spent: the episode parks `cure_no_change` instead of
placing it again.  The signature comes from the log's refusal lines (the ledger keeps only the class)."""
from __future__ import annotations

from studio import autopilot as ap
from tests import autopilot_cli_fixtures as fx

RUN07 = """G-DEAD refuses the master:
  G-DEAD T10: a failed take
  G-DEAD T17: a failed take
no free cut cures these: retake them (the take ladder's move_type)
RuntimeError: REFUSED: scripts/episode/assemble.py exit 1"""
RUN10 = "RuntimeError: REFUSED: G-PEOPLE: a fault on the ship-block list stands at shot_07 after the rounds"
REDO = {"kind": "redo", "step_id": "09"}


def test_the_signature_is_the_refusal_lines():
    assert ap.refusal_sig(RUN07) == "G-DEAD T10|G-DEAD T17"
    assert ap.refusal_sig(RUN10) == "stands at shot_07"
    assert ap.refusal_sig("Traceback\nValueError: x") == "ValueError: x"


def test_a_repeated_order_on_an_unchanged_signature_is_spent():
    cures = [{"event": "brain_cure", "episode": 7, "order": REDO, "sig": "G-DEAD T10|G-DEAD T17"}]
    assert ap.cure_spent(cures, 7, REDO, "G-DEAD T10|G-DEAD T17")


def test_a_moved_signature_or_another_order_is_not_spent():
    cures = [{"event": "brain_cure", "episode": 7, "order": REDO, "sig": "G-DEAD T06|G-DEAD T08"}]
    assert not ap.cure_spent(cures, 7, REDO, "G-DEAD T10|G-DEAD T17")
    assert not ap.cure_spent(cures, 7, {"kind": "redo", "step_id": "08"}, "G-DEAD T06|G-DEAD T08")
    assert not ap.cure_spent(cures, 8, REDO, "G-DEAD T06|G-DEAD T08")


def test_triage_parks_a_spent_cure_and_places_a_fresh_one(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    home = book / "episodes" / "ep07"
    home.mkdir(parents=True)
    (home / "drive_run07.log").write_text(RUN07 + "\n", encoding="utf-8")
    d = fx.deps(tmp_path)
    first = cli.triage_action(book, fx.CODEX, 7, "cure", {"order": REDO}, d)
    assert first["action"] == "brain_cure" and len(d.calls["orders"]) == 1
    again = cli.triage_action(book, fx.CODEX, 7, "cure", {"order": REDO}, d)
    assert again["state"] == "PARKED" and len(d.calls["orders"]) == 1
    parked = cli.rows_of(book / "autopilot" / "parked.jsonl")
    assert parked[-1]["reason"].startswith("cure_no_change: redo 09 G-DEAD T10|G-DEAD T17")
