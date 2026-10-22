"""The take's hour is read from one night vocabulary, and an hour the text never names is unread, not "day".

Wave-2 review of craft ruling A17: `house_style.time_of` fell back to "day" for any setup with no hour word, so
WotW's moonlit and dark setups (ep15 halliford_ditch "Moonlight from the east touches the road", ep05 "Horsell
Common in the dark") got a "by day" style line, and L33, reading its own wider NIGHT_WORD, then refused the
words the writer built.  `\\bnight\\b` read "night-watchman" and "last night" as the hour, so a noon street said
"at night" and L33 refused its own sun.  A cut inside a shot set at another hour took the setup's light (its
`time` was ""), and QC and the craft census read `is_night`, which knew no shot hour.  Now: one NIGHT (shared by
`time_of` and L33), an outdoor place lit by a burning lamp and no day word is night, an unread hour is "" (the
style line says none and L33's day check does not run), a cut keeps its shot's hour, and `is_night` and
`take_inputs.night_of` are `time_of`'s answer."""
from __future__ import annotations

import json
from pathlib import Path

import shot_framework_fixtures as sf
from studio import episode_ref_official as ro, house_style as hs, take_inputs
from studio.episode_spec import Episode, Setup, SubShot

PLAN = Path(__file__).parent / "fixtures" / "craft" / "episodes" / "ep01" / "plan.json"


def outdoors(described: str) -> Setup:
    return Setup(described=described, outdoors=True)


def test_a_night_compound_is_no_hour():
    assert hs.time_of(outdoors("A by-street, the night-watchman passing at noon")) == "day"
    assert hs.time_of(outdoors("The square where he walked last night, bright sun on the stones")) == "day"


def test_the_moon_and_the_dark_are_night():
    assert hs.time_of(outdoors("The Halliford road by a ditch. Moonlight from the east touches the road")) == "night"
    assert hs.time_of(outdoors("Horsell Common in the dark in 1894: a low fire of burning furze on the LEFT")) == "night"


def test_an_evening_is_dusk():
    assert hs.time_of(outdoors("The gate of the farm on a summer evening, 1860")) == "dusk"


def test_a_street_under_burning_lamps_is_night():
    assert hs.time_of(outdoors("A narrow street, the gas lamps burning at the kerb")) == "night"


def test_an_hour_no_word_names_is_unread():
    assert hs.time_of(Setup(described="A scullery: a brick copper and a shallow brown sink")) == ""
    assert hs.time_of(None) == ""


def test_an_unread_hour_puts_no_hour_in_the_style_line():
    with sf.adopted():
        line = hs.take_line(Setup(described="A scullery: a brick copper and a shallow brown sink"))
    assert not any(said in line for said in hs.TIME_SAID.values())


def prompt(block: str) -> str:
    return f"summary:\nx\n\ndetailed_description:\nInk, London, 1886, shadow.\n[Shot 1] From 00:00 to 00:04. {block}\n"


def test_l33_reads_the_same_night_words():
    watchman = prompt("A tall night-watchman leans on the rail; low sun from the LEFT.")
    assert ro.l33_light_once(watchman, {"time": "day"}) == []
    assert len(ro.l33_light_once(prompt("The moon hangs over the roofs."), {"time": "day"})) == 1


def test_l33_checks_no_day_on_an_unread_hour():
    assert ro.l33_light_once(prompt("The moon hangs over the roofs."), {"time": ""}) == []


def test_a_cut_keeps_its_shots_hour():
    ep = Episode.model_validate(json.loads(PLAN.read_text(encoding="utf-8")))
    cut = SubShot(frame="his hand on the knocker", motion="the hand lifts", at_s=1.0, size="insert")
    shot = ep.shots[1].model_copy(update={"time": "night", "cuts": [cut]})
    segs = ro.segments([shot], [{"index": shot.index, "t_start": 0.0}], 0.0, 96, ep.setups[shot.setup])
    assert [s["time"] for s in segs] == ["night", "night"]


def test_is_night_and_night_of_are_the_hour_reader():
    moon = {"described": "The Halliford road. Moonlight from the east touches the road", "outdoors": True}
    assert hs.is_night(Setup(**moon)) and take_inputs.night_of(moon)
    day = {"described": "A by-street on a Sunday afternoon", "outdoors": True}
    assert take_inputs.night_of(day) is False
    vigil = Episode.model_validate(json.loads(PLAN.read_text(encoding="utf-8"))).shots[1]
    assert take_inputs.night_of(day, vigil.model_copy(update={"time": "night"})) is True


def test_qc_and_the_census_read_each_takes_hour_off_its_first_shot():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    records = [{"index": 0, "setup": "night_door", "shots": [0]}, {"index": 1, "setup": "street_day", "shots": [1]}]
    assert take_inputs.take_hours(records, plan["setups"], plan["shots"]) == {0: "night", 1: "day"}
    plan["shots"][1]["time"] = "night"
    assert take_inputs.take_hours(records, plan["setups"], plan["shots"])[1] == "night"
