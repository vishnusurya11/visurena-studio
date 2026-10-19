"""The take's style line keeps a night setup's lamp when the book adopts a look and an atmosphere.

Jekyll Kawajiri ep01 (2026-10-18): with look "Hand-painted 1990s Madhouse noir cel animation" and
atmosphere "thin fog, haze" adopted, `fit` could not shorten "gas lamp", so the lamp phrase failed the
wall and the EPISODE light ("low sun from the west") was printed over the night door and corner.
Fixture: tests/fixtures/ep01_replay/P03/plan.json (copy of ep01's plan.json)."""
import json
from pathlib import Path

import pytest

from studio import house_style as hs
from studio.episode_spec import Setup

PLAN = json.loads((Path(__file__).parent / "fixtures" / "ep01_replay" / "P03" / "plan.json").read_text("utf-8"))
NIGHT = ("night_door", "night_corner")


def setup(name: str) -> Setup:
    return Setup(**{k: v for k, v in PLAN["setups"][name].items() if k in Setup.model_fields})


@pytest.fixture(autouse=True)
def ep01_style():
    keep = (hs._where, hs._light, hs._look, hs._atmosphere)
    hs.adopt(PLAN["where"], PLAN["light"])
    hs.adopt_look("Hand-painted 1990s Madhouse noir cel animation")
    hs.adopt_atmosphere("thin fog, haze")
    yield
    hs._where, hs._light, hs._look, hs._atmosphere = keep


@pytest.mark.parametrize("name", NIGHT)
def test_a_night_setup_never_returns_the_episode_light(name):
    assert hs.light_for(setup(name)) != PLAN["light"]
    assert "sun" not in hs.live(setup(name)).lower()


def test_the_night_door_is_lit_by_its_lamp():
    assert "lamp" in hs.light_for(setup("night_door"))
    assert "lamp" in hs.light_for(setup("night_corner"))


def test_a_gas_lamp_is_shortened_to_its_lamp():
    assert hs.shorter("gas lamp") == "lamp"
    assert hs.shorter("gas bracket") == "gas bracket"
    assert hs.shorter("morning sun") == "sun"


def test_a_day_street_is_lit_by_its_sun_not_by_a_shop_window_glint():
    assert "window" not in hs.light_for(setup("street_day"))
    assert "sun" in hs.light_for(setup("street_day"))


def test_the_budget_counts_the_look_and_the_atmosphere_the_line_prints():
    line = hs.live(setup("night_door"))
    assert len(line.split()) <= hs.MAX_STYLE_WORDS


def test_without_a_look_the_fixed_words_are_six(monkeypatch):
    hs.adopt_look("")
    hs.adopt_atmosphere("")
    assert hs.budget("London, 1886", None) == hs.MAX_STYLE_WORDS - 6 - 2


def recorded_style_lines() -> tuple[dict[int, str], dict[int, str]]:
    """R3: the style line and setup of each of ep01's 28 recorded take prompts (a copy of takes/r2v/shots.json)."""
    from studio import episode_ref_official as ro
    takes = json.loads((Path(__file__).parent / "fixtures" / "ep01_replay" / "P03" / "shots.json").read_text("utf-8"))
    return {t["index"]: (ro.sections(t["prompt"]).get("detailed_description") or "").split("\n")[0]
            for t in takes}, {t["index"]: t["setup"] for t in takes}


def test_replay_the_current_builder_reproduces_the_recorded_lines_before_the_fix(monkeypatch):
    """The recorded day lines are what the new builder says for every day setup except the street,
    whose 'gleaming window' glint gives way to the sun clause."""
    lines, setups = recorded_style_lines()
    now = {k: hs.live(setup(setups[k])) for k in lines}
    same = [k for k in lines if now[k] == lines[k]]
    assert same == [k for k in lines if setups[k] in ("door_step_day", "walk_on_day", "walk_on_day_2")]


def test_replay_no_night_take_says_sun_and_only_night_and_street_takes_change():
    lines, setups = recorded_style_lines()
    now = {k: hs.live(setup(setups[k])) for k in lines}
    changed = {setups[k] for k in lines if now[k] != lines[k]}
    assert changed == {"night_door", "night_corner", "street_day"}
    assert not [k for k in lines if setups[k].startswith("night") and "sun" in now[k].lower()]
    assert all("sun" in lines[k] for k in lines if setups[k].startswith("night"))        # before: all of them
