"""The panel step can afford its own reads (ep13, 2026-09-27).

MEASURED on ep13's clock: one pass of step 08 spends ~15 min on the content
read (a VLM call per panel, 25 panels) and ~13 min on the judge's reads -- 28
min of a 20-min share, so every run deferred before a single redraw rung.  The
share is re-priced inside the unchanged 5-hour ceiling: enough for the reads and
one full rung (a rung re-reads the board)."""
from __future__ import annotations

import pytest

from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES


def test_the_panel_share_covers_its_measured_p50():
    """REWRITTEN (C3_verdict #6, D10): 08 holds its measured P50 (C3_T §3.3:
    P50 20, P90 36 min after the VL resident window); a rung past the share is
    paid by headroom, never refused below the ceiling."""
    minutes = EPISODE_SHARES["08"] * EPISODE_CEILING_SECONDS / 60
    assert minutes >= 20


def test_the_shares_still_fill_the_ceiling_exactly():
    assert sum(EPISODE_SHARES.values()) == pytest.approx(1.0)


def test_the_takes_keep_what_they_measured():
    """REWRITTEN (C3_verdict #6): ep13's 7176 s was before CK8 narration; the
    measured P50 is 118 min x 0.83 = 98 min, held as 105."""
    assert EPISODE_SHARES["09"] * EPISODE_CEILING_SECONDS >= 98 * 60
