"""A fault with no settled mark (the ladder never ended on it) admits nothing: G-DEAD still
refuses that take.  No eye verdict at all admits nothing either."""
from __future__ import annotations

from scripts.episode import assemble
from tests.test_a_still_terminal_does_not_hide_the_other_kept_takes import fault, sign


def test_an_unsettled_fault_is_not_kept(tmp_path):
    sign(tmp_path, [fault("T01"), fault("T02", "keep_best")])
    assert set(assemble.kept_of(tmp_path)) == {2}


def test_no_verdict_keeps_nothing(tmp_path):
    assert assemble.kept_of(tmp_path) == {}


def test_a_verdict_for_missing_takes_keeps_nothing(tmp_path):
    sign(tmp_path, [fault("T01", "keep_best")])
    (tmp_path / "T02.mp4").unlink()
    assert assemble.kept_of(tmp_path) == {}
