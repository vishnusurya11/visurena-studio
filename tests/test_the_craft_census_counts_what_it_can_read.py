"""The craft census counts only what it can read, and sees A18's garbles (wave 0 review, major 3).

Before: a prompt with no `detailed_description` scored 0 in every class and still counted in "N
takes", so a changed section header printed a clean episode; the garble class saw only T01 of A18's
four (T01 ',,'; T03 and T11 a beat stamped "At 00:05" in a block that ends at 00:05; T07 the insert
scope sentence over a second body); "he pans for gold" was an `end` written as a camera; and a census
exception other than four kinds stopped step 06 between prompts.json and the HARD lint wall.
Fixtures: tests/fixtures/craft (Jekyll ep01, copied by name).  No render, no network, no spend."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from scripts.episode import craft_lint as cl

EP01 = Path(__file__).parent / "fixtures" / "craft" / "episodes" / "ep01"


def prompt(dd: str) -> str:
    return f"subject_definitions:\nx\n\ndetailed_description:\n{dd}\n\noverall_soundscape: rain"


def block(text: str, end: str = "00:06") -> str:
    return f"Cel noir, London, 1886, low sun from the west.\n[Shot 1] From 00:00 to {end}. {text}"


def test_an_unreadable_prompt_is_not_a_counted_take():
    counts, n = cl.readable_census({0: "garbage", 1: None, 2: prompt(block("The camera keeps the frame."))},
                                   {}, [])
    assert n == 1 and counts["renamed hold"] == {2: 1}


def test_a_census_that_read_no_card_says_not_measured():
    episode = SimpleNamespace(setups={}, shots=[])
    said = cl.built_line(episode, [{"index": 0, "prompt": "no sections"}])
    assert said == "craft census: not measured (0 of 1 cards carry a detailed_description)"


def test_a_beat_stamped_at_the_blocks_last_second_is_counted():
    assert cl.beat_at_end(block("At 00:05, as the line ends, he turns.", end="00:05")) == 1
    assert cl.beat_at_end(block("At 00:04, as the line ends, he turns.", end="00:05")) == 0


def test_the_insert_scope_over_a_second_body_is_counted():
    two = block("The shot opens on an insert as <Subject 1>'s boots stump and <Subject 2> runs in; only that "
                "object and what touches it is in frame.")
    one = block("The shot opens on an insert on <Subject 1>'s hand; only that object and what touches it is in frame.")
    assert cl.insert_second_body(two) == 1 and cl.insert_second_body(one) == 0


def test_ep01_shows_a18s_four_garbles_in_three_classes():
    counts, n = cl.episode_census(EP01)
    assert n == 28
    assert sorted(counts["beat at block end"]) == [3, 11]
    assert sorted(counts["insert scope with a second body"]) == [7]
    assert 1 in counts["garble"]


def test_a_bare_verb_in_an_end_is_not_a_camera_sentence():
    shots = [{"index": 6, "end": "The camera tilts up from the wet cobbles to the lamp"},
             {"index": 7, "end": "he pans for gold"}, {"index": 8, "end": "cart tracks run to the gate"},
             {"index": 9, "end": "the lamp at the CENTRE as the camera pushes in on it"}]
    assert cl.end_camera(shots) == [6, 9]
    assert sorted(cl.episode_census(EP01)[0]["end as camera"]) == [6]


def test_the_repeat_class_names_its_unit():
    counts, n = cl.episode_census(EP01)
    assert "repeated 6-grams 66 in 13" in cl.line(counts, n)


def test_one_night_rule_serves_the_census_and_the_words_line():
    from studio import take_inputs
    assert cl.night_of is take_inputs.night_of


def test_any_census_exception_is_not_measured_never_a_stopped_step(monkeypatch):
    from scripts.episode import takes_r2v

    def boom(*a):
        raise IndexError("a block with no stamp")
    monkeypatch.setattr(cl, "built_line", boom)
    assert takes_r2v.craft_census(SimpleNamespace(setups={}, shots=[]), []).startswith("craft census: not measured")
