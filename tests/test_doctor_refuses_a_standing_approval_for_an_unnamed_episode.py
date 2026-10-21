"""Five-iterations build B1.3 (2026-10-20): the standing publish approval names
its episodes.  Owner rule 2026-10-12 ("no upload unless asked"): the Jekyll
file was signed after the owner said "Upload it" for ep01 (master_iter3), and
as written it approved every later chapter too -- a resumed series would have
built ep02 and uploaded it unasked.  Now `ok(book, n)` holds only for an
episode the file lists; a file with no `episodes` approves nothing new, the
autopilot holds every unlisted master at HELD_PUBLISH, and the dry check says
so per episode.  $0: no call."""
from __future__ import annotations

import json
from types import SimpleNamespace

from scripts.episode import step_13_publish
from studio import standing_approval
from studio.escalate import Escalation
from tests.publish_fixtures import FakeCtx, book_with, episode_with, standing

import pytest

JEKYLL_AS_SIGNED = {"kind": "publish", "decision": standing_approval.DECISION,
                    "by": "ViSuReNa (owner)", "at": "2026-10-20"}


def _write(book, said):
    (book / "publish").mkdir(parents=True, exist_ok=True)
    (book / "publish" / "standing.json").write_text(json.dumps(said), encoding="utf-8")


def test_the_file_as_signed_for_ep01_approves_no_episode(tmp_path):
    book = book_with(tmp_path)
    _write(book, JEKYLL_AS_SIGNED)
    assert standing_approval.ok(book, 1) is False and standing_approval.ok(book, 2) is False


def test_a_listed_episode_is_approved_and_the_next_is_not(tmp_path):
    book = book_with(tmp_path)
    _write(book, {**JEKYLL_AS_SIGNED, "episodes": [1]})
    assert standing_approval.ok(book, 1) is True
    assert standing_approval.ok(book, 2) is False


def test_a_malformed_episode_list_approves_nothing(tmp_path):
    book = book_with(tmp_path)
    _write(book, {**JEKYLL_AS_SIGNED, "episodes": "all"})
    assert standing_approval.ok(book, 1) is False


def test_the_escalation_names_the_episode_to_list(tmp_path):
    esc = standing_approval.escalation(book_with(tmp_path), 2)
    assert esc.gate == "G-STANDING" and '"episodes": [2]' in str(esc)


def test_step_13_parks_an_unlisted_episode_before_anything_is_sent(tmp_path):
    book = book_with(tmp_path)
    home, _sha8 = episode_with(book, 3)
    standing(book, episodes=(1, 2))
    boom = lambda *a, **k: (_ for _ in ()).throw(AssertionError("nothing may be sent"))  # noqa: E731
    with pytest.raises(Escalation) as got:
        step_13_publish.run(FakeCtx(book, home, 3), send=boom, build_api=boom, http=boom)
    assert got.value.gate == "G-STANDING" and '"episodes": [1, 2, 3]' in str(got.value)


def test_the_autopilot_reads_the_approval_per_episode(tmp_path):
    from scripts.episode import autopilot
    book = book_with(tmp_path)
    standing(book, episodes=(1,))
    assert autopilot.standing_ok(book, 1) is True
    assert autopilot.standing_ok(book, 2) is False


def test_pick_unit_lifts_only_the_listed_holds(tmp_path):
    from scripts.episode import autopilot
    book = book_with(tmp_path)
    standing(book, episodes=(1,))
    held = [{"episode": 1}, {"episode": 2}]
    assert autopilot.holds_still_owed(book, held) == [{"episode": 2}]
