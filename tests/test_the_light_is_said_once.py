"""The take's light is said once, by the block, under one closed hour per setup (craft ruling A17, L33).

ep01's 28 take prompts named the light twice (C1): the style line carried a source and a direction ("..., sun
from the left, shadow." / "..., lamp from the left, shadows.") beside the block's own light sentence ("low sun
from the LEFT", "the corner lamp light comes from the upper RIGHT"); 8 night takes had shipped with a sun in
that line.  Now `Setup.time` (night | dawn | day | dusk | interior-lamp, read by code from `described` and
`place_state`, overridden by `Shot.time`) is the one hour; the style line says the hour and a black, never a
source; L33 refuses a sky word anywhere in a night take, a night word in a day take, and two light directions
that disagree in one block.  Ch2's vigil (one door at morning, noon and night) is why the hour is per shot.
Fixtures: tests/fixtures/shot_framework/ (ep01 rebuilt by the production writer), tests/fixtures/craft/."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import shot_framework_fixtures as sf
from scripts.episode import craft_lint as cl
from studio import episode_ref_official as ro, house_style as hs
from studio.episode_spec import Episode, Setup

PLAN = Path(__file__).parent / "fixtures" / "craft" / "episodes" / "ep01" / "plan.json"
NIGHT_TAKES = (0, 6, 7, 8, 9, 10, 11, 12)


def episode() -> Episode:
    return Episode.model_validate(json.loads(PLAN.read_text(encoding="utf-8")))


def test_the_contract_holds_a_closed_hour():
    assert Setup(described="a by-street", time="dusk").time == "dusk"
    with pytest.raises(ValidationError):
        Setup(described="a by-street", time="noon")
    assert episode().shots[0].time == ""


def test_the_hour_is_read_from_described_and_place_state():
    setups = episode().setups
    assert hs.time_of(setups["night_corner"]) == hs.time_of(setups["night_door"]) == "night"
    assert hs.time_of(setups["street_day"]) == "day"
    assert hs.time_of(Setup(described="A lawyer's study, a candle burning on the desk")) == "interior-lamp"
    assert hs.time_of(Setup(described="The by-street at dusk, the lamps being lit", outdoors=True)) == "dusk"
    assert hs.time_of(Setup(described="The square at dawn, grey light from the east", outdoors=True)) == "dawn"


def test_a_shot_overrides_its_setups_hour():
    ep = episode()
    assert hs.time_of(ep.setups["street_day"], ep.shots[1].model_copy(update={"time": "night"})) == "night"


def test_ep01_light_said_twice_drops_from_28_to_0():
    assert sum(cl.light_twice(sf.detailed(sf.delivered(i))) for i in range(28)) == 28
    assert sum(cl.light_twice(sf.detailed(sf.take_prompt(i))) for i in range(28)) == 0


def test_no_night_take_says_a_sky_word():
    assert [i for i in NIGHT_TAKES if hs.SKY_SOURCE.search(sf.detailed(sf.take_prompt(i)))] == []


def test_the_style_line_says_the_hour_and_a_black_never_a_source():
    ep = episode()
    with sf.adopted():
        line = hs.take_line(ep.setups["street_day"])
        night = hs.take_line(ep.setups["night_door"])
    assert "by day" in line and not hs.SOURCES.search(line) and "from the" not in line
    assert "at night" in night and not hs.SOURCES.search(night)


def test_the_vigil_gets_three_hours():
    door = Setup(described="The blistered door on the by-street, a gas lamp at the kerb", outdoors=True)
    shot = episode().shots[13]
    with sf.adopted():
        said = [hs.take_line(door, shot.model_copy(update={"time": t})) for t in ("dawn", "day", "night")]
    assert len(set(said)) == 3
    assert ["at dawn" in said[0], "by day" in said[1], "at night" in said[2]] == [True, True, True]


def prompt(style: str, block: str) -> str:
    return f"summary:\nx\n\ndetailed_description:\n{style}\n[Shot 1] From 00:00 to 00:04. {block}\n"


def test_l33_refuses_a_sky_word_anywhere_in_a_night_take():
    said = prompt("Ink, London, 1886, at night, shadows.", "The camera is low; the corner lamp burns. A sunlit wall.")
    assert [f[:14] for f in ro.l33_light_once(said, {"night": True})] == ["L33 LIGHT-ONCE"]
    assert ro.l33_light_once(said, {"night": False}) == []


def test_l33_refuses_a_night_word_in_a_day_take():
    said = prompt("Ink, London, 1886, by day, shadow.", "The camera is low; low sun from the LEFT. The moon hangs.")
    assert len(ro.l33_light_once(said, {"night": False, "time": "day"})) == 1


def test_l33_refuses_two_light_directions_in_one_block():
    said = prompt("Ink, London, 1886, sun from the left, shadow.", "The corner lamp light comes from the upper RIGHT.")
    assert len(ro.l33_light_once(said, {})) == 1
    same = prompt("Ink, London, 1886, lamp from the left.", "The kerb gas lamp light comes from the LEFT.")
    assert ro.l33_light_once(same, {}) == []


def test_l33_is_a_hard_rule_beside_l28():
    assert ro.l33_light_once in ro.RULES and ro.l28_style_light in ro.RULES
