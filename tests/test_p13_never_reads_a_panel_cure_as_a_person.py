"""Lint P13 never reads the panel ladder's own cure sentences as a person in the scene.

Jekyll ep02, 2026-10-26: shot 5's panel drew three figures for two, the panel ladder's `clones` cure
wrote "Each person in the picture is a different man with his own face, build and dress." into the
frame, and step 09's P13 read "man" as an unstaged person -- every relaunch refused on the cure's
own words and the brain parked the episode (brain_exhausted)."""
from studio import panel_ladder, prompt_lint as pl

FACTS = {"faces": ["reginald_lanyon", "gabriel_john_utterson"], "aliases": {}, "extras": 0, "crowd": ""}


def test_every_cure_sentence_is_silent_to_p13():
    for cure in set(panel_ladder.CURES.values()):
        assert pl.p13_people(f"{cure} Medium on the table under the candles.", FACTS) == [], cure


def test_a_real_unstaged_man_beside_a_cure_is_still_refused():
    text = f"{panel_ladder.CURES['clones']} A man waits in the doorway."
    assert any("man" in f for f in pl.p13_people(text, FACTS))
