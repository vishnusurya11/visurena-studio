"""The panel step can afford its own reads (ep13, 2026-09-27).

MEASURED on ep13's clock: one pass of step 08 spends ~15 min on the content
read (a VLM call per panel, 25 panels) and ~13 min on the judge's reads -- 28
min of a 20-min share, so every run deferred before a single redraw rung.  The
share is re-priced inside the unchanged 5-hour ceiling: enough for the reads and
one full rung (a rung re-reads the board)."""
from __future__ import annotations

import pytest

from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES


def test_the_panel_share_covers_its_reads_and_one_rung():
    minutes = EPISODE_SHARES["08"] * EPISODE_CEILING_SECONDS / 60
    assert minutes >= 28 + 28


def test_the_shares_still_fill_the_ceiling_exactly():
    assert sum(EPISODE_SHARES.values()) == pytest.approx(1.0)


def test_the_takes_keep_what_they_measured():
    assert EPISODE_SHARES["09"] * EPISODE_CEILING_SECONDS >= 7176     # ep13's shoot asked 7176 s
