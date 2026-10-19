"""L28 STYLE-LIGHT: a take on a night setup whose style line says sun is refused.

Jekyll Kawajiri ep01 (2026-10-18): "..., thin fog, haze, low sun from the west." was printed over the
night door and corner (the episode light fell back onto setups that name a lamp)."""
import json
from pathlib import Path

from studio import episode_ref_official as ro
from studio import house_style as hs
from studio.episode_spec import Setup

PLAN = json.loads((Path(__file__).parent / "fixtures" / "ep01_replay" / "P03" / "plan.json").read_text("utf-8"))


def prompt(style: str) -> str:
    return f"detailed_description: {style}\n[Shot 1] From 00:00 to 00:03. The man stands.\noverall_soundscape: Air."


def test_a_sun_in_the_style_line_of_a_night_setup_is_a_fault():
    out = ro.l28_style_light(prompt("Cel animation, London, 1886, low sun from the west."), {"night": True})
    assert out and out[0].startswith("L28 STYLE-LIGHT")


def test_a_lamp_on_a_night_setup_is_clean():
    assert ro.l28_style_light(prompt("Cel animation, London, 1886, lamp from the left, shadows."), {"night": True}) == []


def test_a_sun_on_a_day_setup_is_clean():
    assert ro.l28_style_light(prompt("Cel animation, London, 1886, sun from the left, shadow."), {"night": False}) == []
    assert ro.l28_style_light(prompt("Cel animation, sun from the left."), {}) == []


def test_l28_is_one_of_the_rules():
    assert ro.l28_style_light in ro.RULES


def test_the_prompt_facts_know_a_night_setup():
    night = Setup(**{k: v for k, v in PLAN["setups"]["night_door"].items() if k in Setup.model_fields})
    day = Setup(**{k: v for k, v in PLAN["setups"]["street_day"].items() if k in Setup.model_fields})
    assert ro.night_fact(night) is True and ro.night_fact(day) is False
    assert hs.is_night(night) and not hs.is_night(day)
