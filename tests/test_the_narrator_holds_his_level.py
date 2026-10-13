"""The narrator holds his level; the feeling is in the performance, not the fader.

Jekyll ep01 review (SOUND.md R4): `offset_of` dropped "hushed" lines 5 LU and
"grieving" 2, so the narration wandered 1.8 LU line to line against WotW's
0.6 -- l07, l08, l12, l13 and l18 sat at -17 to -19.6 under a -14.5
neighbourhood.  Narration offsets are clamped to +-1.5 LU; dialogue keeps its
full range (a shout over a whisper between two people is the scene)."""
from __future__ import annotations

from studio import episode_emotion as ee


def test_the_clamp_is_one_and_a_half_lu():
    assert ee.NARRATION_CLAMP_LU == 1.5


def test_a_hushed_narration_line_drops_at_most_the_clamp():
    assert ee.offset_of("hushed", "narration") == -1.5
    assert ee.offset_of("shouting", "narration") == 1.5
    assert ee.offset_of("urgent", "narration") == 1.0


def test_dialogue_keeps_its_full_range():
    assert ee.offset_of("hushed", "dialogue") == -5.0
    assert ee.offset_of("hushed") == -5.0
