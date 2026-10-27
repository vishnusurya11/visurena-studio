"""A figure that LEANS in the last frame is placed like one that stands or sits.

Jekyll ep03 shots 3 and 16 wrote their `end` as "The lawyer leans at the CENTRE, ...".  `end_noun` cut
the noun at its first posture verb or preposition, and `leans` was in neither list, so the arrival read
"with <Subject 1> leans now in frame": prompt lint P9 refused the takes at step 06, twice (2026-10-27).
A lean is a posture like `stands`/`sits`/`lies`, so it ends the noun the same way."""
from __future__ import annotations

from studio import episode_ref_official as ro


def test_a_lean_ends_the_noun_like_a_stand():
    end = "The lawyer leans at the CENTRE, his head a third of the frame's height, his clasped hands at the BOTTOM edge"
    assert ro.end_noun(end) == "the lawyer"


def test_a_leaning_figure_lends_its_noun():
    assert ro.end_noun("The doctor leaning on the mantel fills the LEFT edge") == "the doctor"


def test_lean_as_an_adjective_stays_in_the_noun():
    assert ro.end_noun("The lean clerk stands at the RIGHT edge") == "the lean clerk"
