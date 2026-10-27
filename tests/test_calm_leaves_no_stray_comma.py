"""A stillness word dropped by `calm` takes its gap with it, never leaving a stray comma.

Jekyll ep04 shot 2's at_rest said "smaller still, a heavy cane in his hand"; `calm` dropped `still`
and the block read "smaller , a heavy cane", which L19 refuses as a stray comma (G-TAKELINT at plan,
2026-10-27).  A word between two commas leaves one comma, not two."""
from __future__ import annotations

from studio import episode_ref_official as ro


def test_a_dropped_still_before_a_comma_leaves_no_space():
    assert ro.calm("smaller still, a heavy cane in his hand") == "smaller, a heavy cane in his hand"


def test_a_dropped_word_between_commas_leaves_one_comma():
    assert ro.calm("the lamp, motionless, glows") == "the lamp, glows"


def test_the_lint_finds_no_stray_comma_after_calm():
    assert ro.stray_commas(ro.calm("He stands smaller still, a cane. The door, frozen, shuts.")) == []
