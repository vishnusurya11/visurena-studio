"""A1, the craft census (craft ruling 2026-10-21, wave 0): one $0 counter over plan.json and the
RENDERED take graphs (27 of ep01's 28 prompts.json entries are not what rendered).  It reports and
never parks.  The ep01 numbers below are the ruling's base rates; the fixtures are copied by name
from Jekyll ep01 into tests/fixtures/craft/episodes/ep01 (plan.json, takes/r2v/shots.json, the 28 graphs).
No render, no network, no spend."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from scripts.episode import craft_lint as cl

BOOK = Path(__file__).parent / "fixtures" / "craft"
EP01 = BOOK / "episodes" / "ep01"


def block(text: str) -> str:
    """A one-block detailed_description with a style line, the way the builder writes it."""
    return f"Cel noir, London, 1886, low sun from the west.\n[Shot 1] From 00:00 to 00:06. {text}"


def prompt(dd: str) -> str:
    return f"subject_definitions:\nx\n\ndetailed_description:\n{dd}\n\noverall_soundscape: rain"


# ---- ep01: the ruling's printed numbers ---------------------------------------------------------

def test_the_census_prints_the_rulings_numbers_on_ep01():
    counts, n = cl.episode_census(EP01)
    assert n == 28
    assert len(counts["renamed hold"]) == 12
    assert len(counts["now in frame"]) == 19
    assert sum(counts["walking pace"].values()) == 8 and len(counts["walking pace"]) == 5
    assert sorted(counts["speech beside a closed mouth"]) == [13]
    assert len(counts["sky word at night"]) == 8
    assert sorted(counts["end as camera"]) == [6]


def test_the_census_counts_the_repeats_and_garbles_it_sees_on_ep01():
    counts, _ = cl.episode_census(EP01)
    assert len(counts["repeated 6-grams"]) == 13
    assert sorted(counts["garble"]) == [1, 6]          # T01 ',,'  T06 'with the camera tilts up now in frame'


def test_the_line_states_every_class_and_that_it_only_reports():
    counts, n = cl.episode_census(EP01)
    said = cl.line(counts, n)
    assert said.startswith("craft census, 28 takes (report only):")
    assert "renamed hold 12" in said and "walking pace 8 in 5" in said
    assert "speech beside a closed mouth 1 (T13)" in said and "end as camera 1 (shot 6)" in said


# ---- each class on its own words -------------------------------------------------------------------

def test_detailed_reads_only_the_detailed_description():
    assert cl.detailed(prompt("A.\n[Shot 1] B.")) == "A.\n[Shot 1] B."
    assert cl.detailed("no sections at all") == ""


def test_a_keeps_head_is_a_renamed_hold_and_a_move_is_not():
    assert cl.renamed_hold(block("The camera keeps a locked-off frame as he waits.")) == 1
    assert cl.renamed_hold(block("The camera is low. The camera pushes in as he waits.")) == 0


def test_now_in_frame_is_counted_per_sentence():
    assert cl.now_in_frame(block("By 00:06 the camera is rising, with the lamp now in frame.")) == 1


def test_walking_pace_counts_every_pace_the_cure_wrote():
    assert cl.walking_pace(block("He walks at a walking pace; she strides at a normal walking pace.")) == 2


def test_a_speech_verb_beside_a_closed_mouth_is_one_hit():
    said = block("<Subject 1>'s mouth is closed from 00:00 to 00:06 while he speaks and taps his cane.")
    assert cl.speech_closed(said) == 1
    assert cl.speech_closed(block("<Subject 1>'s mouth is closed while he listens.")) == 0


def test_a_sky_word_counts_only_on_a_night_setup():
    assert cl.sky_at_night(block("The lamp burns."), night=True) == 1      # the style line's sun
    assert cl.sky_at_night(block("The lamp burns."), night=False) == 0


def test_a_six_word_run_said_twice_is_one_repeat_and_boilerplate_is_not():
    twice = block("He taps his black walking cane. Then he taps his black walking cane.")
    assert cl.six_word_repeat(twice) >= 1
    assert cl.six_word_repeat(block("It continues to the last frame of the shot. It continues to the "
                                    "last frame of the shot.")) == 0


def test_garbles_are_doubled_commas_and_a_camera_verb_in_frame():
    assert cl.garbles(block("as they walk in profile,, feet in the picture.")) == 1
    assert cl.garbles(block("By 00:06, with the camera tilts up now in frame, it continues.")) == 1
    assert cl.garbles(block("By 00:06, with the lamp now in frame, it continues.")) == 0


def test_an_end_that_is_a_camera_sentence_is_named_by_shot():
    shots = [{"index": 0, "end": "the lamp at the TOP edge"},
             {"index": 6, "end": "The camera tilts up from the wet cobbles to the lamp"},
             {"index": 7, "end": "he pans for gold"}, {"index": 8}]
    assert cl.end_camera(shots) == [6]          # a bare verb is no camera (wave 0 review, finding 10)


def test_the_census_never_parks_on_an_unreadable_prompt():
    counts = cl.census({0: "garbage", 1: None}, {0: True}, [{"index": 0, "end": None}])
    assert all(not hits for hits in counts.values())


def test_the_step_06_line_reads_the_built_cards_and_the_plans_setups():
    night = SimpleNamespace(described="a street at night", place_state="every lamp lit")
    episode = SimpleNamespace(setups={"night_corner": night},
                              shots=[SimpleNamespace(index=0, end="The camera pans to the lamp")])
    built = [{"index": 0, "setup": "night_corner",
              "prompt": prompt(block("The camera keeps a locked-off frame, with the lamp now in frame."))}]
    said = cl.built_line(episode, built)
    assert said.startswith("craft census, 1 takes (report only):")
    assert "renamed hold 1" in said and "sky word at night 1" in said and "end as camera 1 (shot 0)" in said


# ---- step 06 prints it and never parks on it -----------------------------------------------------

def test_step_06_prints_the_census_beside_its_cards():
    from scripts.episode import takes_r2v
    episode = SimpleNamespace(setups={"day": SimpleNamespace(described="a street", place_state="noon")}, shots=[])
    built = [{"index": 0, "setup": "day", "prompt": prompt(block("The camera keeps the frame."))}]
    assert takes_r2v.craft_census(episode, built).startswith("craft census, 1 takes (report only): renamed hold 1")


def test_a_census_that_cannot_read_the_cards_says_so_and_never_parks():
    from scripts.episode import takes_r2v
    assert takes_r2v.craft_census(SimpleNamespace(setups=None, shots=[]), [{"index": "x"}]).startswith(
        "craft census: not measured")
