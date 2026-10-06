"""G-STANDING: library/<book>/publish/standing.json is the owner's standing
hand at the publish door -- written once per book, by the owner, never by
code.  Absent or malformed, step 13 parks the unit with an Escalation BEFORE
anything is generated or sent; valid, the built argv carries the unchanged
gate flags (--watched=<sha8>, --approved=publish)."""
from __future__ import annotations

import pytest

from scripts.episode import step_13_publish
from studio import standing_approval
from studio.escalate import Escalation
from tests.publish_fixtures import FakeCtx, book_with, episode_with, standing


def test_no_standing_file_approves_nothing(tmp_path):
    book = book_with(tmp_path)
    assert standing_approval.ok(book) is False
    esc = standing_approval.escalation(book)
    assert esc.gate == "G-STANDING" and "standing.json" in esc.verdict


def test_a_wrong_decision_id_approves_nothing(tmp_path):
    book = book_with(tmp_path)
    standing(book, decision="2026-09-16-watch-it-yourself")
    assert standing_approval.ok(book) is False


def test_an_unnamed_owner_approves_nothing(tmp_path):
    book = book_with(tmp_path)
    standing(book, by="  ")
    assert standing_approval.ok(book) is False


def test_a_valid_file_approves_and_the_argv_carries_the_gates(tmp_path):
    book = book_with(tmp_path)
    standing(book)
    assert standing_approval.ok(book) is True
    argv = step_13_publish.upload_argv(book.name, 3, "faf11c8f")
    assert "--watched=faf11c8f" in argv and "--approved=publish" in argv
    flip = step_13_publish.privacy_argv(book.name, 3)
    assert "public" in flip and "--approved=publish" in flip
    assert f"--why={standing_approval.DECISION}" in flip


def test_run_parks_with_g_standing_before_anything_is_sent(tmp_path):
    book = book_with(tmp_path)
    home, _sha8 = episode_with(book, 3)
    boom = lambda *a, **k: (_ for _ in ()).throw(AssertionError("nothing may be sent"))  # noqa: E731
    with pytest.raises(Escalation) as got:
        step_13_publish.run(FakeCtx(book, home, 3), send=boom, build_api=boom, http=boom)
    assert got.value.gate == "G-STANDING"
