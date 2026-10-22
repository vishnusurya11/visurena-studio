"""A4: the brief states the dialogue room the gate allows (craft ruling 2026-10-21, wave 1).

The brief told the writer "108 dialogue words" (`dialogue_words_max` = 0.35 x the 310-word wall).
G-DIAL divides by the plan's OWN total (`plan_gates.dial_faults`): Jekyll ep01 had 82 of 239 = 0.343,
so 1-2 words were spare, not 26, and four round-1 cures were built on the false number.  The band now
says the ceiling as a share of the plan's own words with a worked row.  The 0.35 and the gate do not
change.  Fixtures: tests/fixtures/craft (Jekyll ch_01, ch_02).  No render, no network, no spend."""
from __future__ import annotations

import math
import re
from pathlib import Path

from studio import plan_brief, plan_gates

BOOK = Path(__file__).parent / "fixtures" / "craft"
ROW = re.compile(r"at (\d+)(?: words)?, (\d+)")


def test_the_ch1_band_states_the_room_at_every_total_it_prints():
    band = plan_brief.band(BOOK, 1)
    ceiling, room = band["dialogue_share"][1], band["dialogue_room"]
    pairs = [(int(t), int(w)) for t, w in ROW.findall(room)]
    assert ceiling == 0.35 and len(pairs) >= 2
    assert all(words == math.floor(ceiling * total) for total, words in pairs)
    assert "share of the plan's own words" in room


def test_the_worked_row_is_the_rulings():
    assert plan_brief.dialogue_room(0.35) == ("a share of the plan's own words, dialogue only: 0.35 x its total "
                                              "(at 240 words, 84 dialogue words; at 310, 108)")


def test_the_ch2_room_follows_its_own_ceiling():
    room = plan_brief.band(BOOK, 2)["dialogue_room"]
    assert "0.27 x its total" in room and "at 240 words, 64 dialogue words; at 310, 83" in room


def test_the_gate_still_divides_by_the_plans_own_total():
    from types import SimpleNamespace
    lines = [SimpleNamespace(kind="dialogue", text=" ".join(["w"] * 82)),
             SimpleNamespace(kind="narration", text=" ".join(["w"] * 157))]
    assert plan_gates.dial_faults(SimpleNamespace(lines=lines), 0.279) == []     # 82 / 239 = 0.343
    lines[0] = SimpleNamespace(kind="dialogue", text=" ".join(["w"] * 86))     # 86 / 243 = 0.354
    assert plan_gates.dial_faults(SimpleNamespace(lines=lines), 0.279)
