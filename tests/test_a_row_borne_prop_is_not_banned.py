"""ep16 (2026-10-01): L18 banned 'glove' globally -- a Sherlock-era constant
("a tan glove on Watson, 2026-09-11") -- and the builder itself injects the
Elphinstone rows ("Black gauntlet gloves", "White kid gloves"), whose SIGNED
sheets were designed with them.  The lint banned the word the builder added:
two laws in contradiction.  A banned word borne by a bound cast row is exempt
-- the sheet already shows it, so the render copying it is correct; the ban
still guards a glove the text invents.  $0: a membership test."""
from __future__ import annotations

from studio.episode_ref_official import l18_banned_prop


def test_a_row_borne_word_is_exempt():
    text = "Miss Elphinstone wears black gauntlet gloves and holds the whip."
    rows = {"cast_rows": "black gauntlet gloves. carriage whip in one hand."}
    assert l18_banned_prop(text, rows) == []


def test_an_invented_glove_is_still_banned():
    text = "Watson pulls on a tan glove at the kerb."
    assert l18_banned_prop(text, {"cast_rows": "a brown ulster, black boots"})
    assert l18_banned_prop(text, {})
