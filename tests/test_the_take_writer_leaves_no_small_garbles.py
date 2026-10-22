"""The take writer leaves none of the small mechanical garbles the craft census counted on ep01 (craft ruling A18).

Census on ep01's 28 rebuilt takes before this fix: garble 1 (T01 "walk in profile,, feet": the amount strip took
" a long stride" and left both commas), beat at block end 2 (T03 and T11 "At 00:05" in a block that ends at
00:05: nothing can start on the last frame), insert scope with a second body 1 (T07 "only that object and what
touches it is in frame" over the girl running in).  4 to 0.
Fixture: tests/fixtures/shot_framework/ (the ep01 records the production writer builds from)."""
from __future__ import annotations

import shot_framework_fixtures as sf
from scripts.episode import craft_lint as cl
from studio import episode_ref_official as ro


def test_the_amount_strip_leaves_one_comma():
    said = ro.without_amount("The camera tracks beside them as they walk in profile, a long stride, feet east")
    assert ",," not in said and " ," not in said
    assert "in profile, feet east" in said


def test_t01_carries_no_doubled_comma():
    assert cl.garbles(sf.detailed(sf.take_prompt(1))) == 0


def test_a_follow_on_is_never_stamped_on_the_blocks_last_second():
    said = ro.beat_sentences("The camera holds; he speaks; his hand spreads open", 0, 5, line_end=5)
    assert not any(s.startswith("At 00:05") for s in said)
    assert said[0].startswith("At 00:04")


def test_t03_and_t11_stamp_no_beat_at_their_end():
    assert [cl.beat_at_end(sf.detailed(sf.take_prompt(i))) for i in (3, 11)] == [0, 0]


def test_an_insert_a_second_body_enters_drops_its_scope_tail():
    assert cl.insert_second_body(sf.detailed(sf.take_prompt(7))) == 0
    assert cl.INSERT_SCOPE not in sf.detailed(sf.take_prompt(7))


def test_an_insert_on_one_body_keeps_its_scope_tail():
    seg = {"frame": "Insert on his black boots on the wet cobbles", "motion": "his boots stride east",
           "size": "insert", "t": 0.0}
    assert ro.INSERT_TAIL in ro.framing(1, seg, None, ["Hyde"], ("Hyde",))


def test_l19_names_a_doubled_comma():
    text = "detailed_description:\nStyle.\n[Shot 1] From 00:00 to 00:03. He walks,, east.\n"
    assert any("',,'" in f for f in ro.l19_crowd(text, {}))
