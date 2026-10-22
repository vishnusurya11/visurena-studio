"""A14: who keeps a voice (craft ruling 2026-10-21, wave 1).

ch2 has more speakers than the cap of 4.  The ruling keeps the ones whose lines carry the answer or the
series motif and folds the rest into narration (Poole stays: "Mr. Hyde has a key." pays off ep01's key;
Lanyon is folded).  The band names the motif right beside `max_voices`, so the writer reads the rule
where it reads the cap.  The cap stays 4.  Fixtures: tests/fixtures/craft (Jekyll ep01 plan's motif,
ch_02).  No render, no network, no spend."""
from __future__ import annotations

import json
import re
from pathlib import Path

from studio import episode_spec, plan_brief

BOOK = Path(__file__).parent / "fixtures" / "craft"
SKILL = Path(__file__).resolve().parents[1] / "agents" / "skills" / "episode_writer.md"


def test_the_ch2_band_line_names_the_motif_next_to_the_cap():
    lines = json.dumps(plan_brief.band(BOOK, 2), ensure_ascii=False, indent=1).splitlines()
    at = next(k for k, l in enumerate(lines) if '"max_voices"' in l)
    assert '"max_voices": 4' in lines[at]
    assert '"voices_kept"' in lines[at + 1] and "the blistered door and the bright key that opens it" in lines[at + 1]
    assert episode_spec.MAX_SPEAKING == 4


def test_the_rule_folds_the_rest_into_narration():
    said = plan_brief.voices_kept("the key")
    assert said == ("past max_voices speakers, keep the ones whose lines carry the answer or the motif "
                    "(the key); fold the rest into narration")


def test_a_book_with_no_motif_still_states_the_rule():
    assert "the motif" in plan_brief.voices_kept("")


def test_the_skill_points_at_it_from_the_cap():
    text = re.sub(r"\s+", " ", SKILL.read_text(encoding="utf-8"))
    assert "at most `max_voices` voices, narrator in; `voices_kept`: who." in text
