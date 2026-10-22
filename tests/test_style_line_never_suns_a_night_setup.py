"""A night, lamp, moon or candle setup never gets a sun clause in its take's style line (shot framework D-e).

Jekyll Kawajiri ep01 shipped "low sun from the west" on its 3 a.m. corner (T06) and its night door (T10):
the prompt bench (docs/audit/2026-10-21_prompt_bench, finding 3) read it on the delivered words.  Commit
b83eac4 gave `house_style.light_for` a night branch; these tests read the prompt the production writer
builds for those two takes today, so the fix stays locked to the artefact.  Fixture: tests/fixtures/
shot_framework/ (copies of ep01's plan, placement, refs and delivered words)."""
from __future__ import annotations

import pytest

import shot_framework_fixtures as sf


def style_line(text: str) -> str:
    return sf.detailed(text).split("\n")[0]


@pytest.mark.parametrize("index", [6, 10])
def test_the_delivered_night_takes_said_sun(index):
    assert "sun" in style_line(sf.delivered(index)).lower()


def test_ep01_night_corner_keeps_its_lamp():
    line = style_line(sf.take_prompt(6))
    assert "sun" not in line.lower() and "lamp" in line.lower()


def test_ep01_night_door_keeps_its_lamp():
    line = style_line(sf.take_prompt(10))
    assert "sun" not in line.lower() and "lamp" in line.lower()
