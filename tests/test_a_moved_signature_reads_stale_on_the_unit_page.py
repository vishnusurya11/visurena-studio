"""Board review 2026-10-12 (02 #10): WotW refs LOOK was signed over pack 4b0a9ecd;
the per-episode looks rewrote pack.jsonl (57f5f814) and the page still said
"✓ passed".  tick.verify -- the only caller of db.mark_stale_verdicts -- is
never called, so the stale meaning could never fire.  The unit page compares the
cheap signatures (PLAN, LOOK: small files) with the disk at render and names a
moved one `stale`; the row's state is left to the desk.  $0."""
from __future__ import annotations

from studio import refs_verdict
from studio.command_center import unit_view


def _book(tmp_path):
    book = tmp_path / "book"
    (book / "refs").mkdir(parents=True)
    (book / "refs" / "pack.jsonl").write_text('{"id": "a"}\n', encoding="utf-8")
    return book


def test_a_look_signed_over_another_pack_is_stale(tmp_path):
    book = _book(tmp_path)
    chips = [{"gate": "LOOK", "sha8": "4b0a9ecd"}]
    assert unit_view.moved_gates(book, "main", chips) == {"LOOK"}


def test_a_look_signed_over_this_pack_is_not(tmp_path):
    book = _book(tmp_path)
    chips = [{"gate": "LOOK", "sha8": refs_verdict.pack_sha8(book)}]
    assert unit_view.moved_gates(book, "main", chips) == set()


def test_an_expensive_or_unsigned_gate_is_never_hashed_at_render(tmp_path):
    chips = [{"gate": "MASTER", "sha8": "aaaa"}, {"gate": "EYE_TAKES", "sha8": "bbbb"}, {"gate": "LOOK", "sha8": ""}]
    assert unit_view.moved_gates(_book(tmp_path), "ep01", chips) == set()
    assert unit_view.moved_gates(None, "ep01", [{"gate": "LOOK", "sha8": "x"}]) == set()
