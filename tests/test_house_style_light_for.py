r"""The style line takes the SETUP's own light, with the episode `light` as
the fallback.

MEASURED, episode 10 (dq10/C.md §5, J.md §6): `light: "low side sun, deep
black shadow"` reached 8/8 sheets and 30/30 take blocks INCLUDING the moon,
lamp and candle setups -- the exact shape of ep08's "gaslight-amber over a
noon desert", survived here only because every `described` names its own
source and the drawer weighted it.  So `light_for(setup)` reads the clause
that names the source and renders a direction and a black in the words the
style wall leaves.

Free and offline.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import house_style as hs
from studio.episode_spec import Setup

EP10 = ROOT / "library" / "20260822113400_a-study-in-scarlet" / "episodes" / "ep10" / "plan.json"
FARM = ("Ferrier's farm, Utah, 1860", "low side sun, deep black shadow")

LAMP = Setup(described=(
    "Interior, inside the sitting-room of John Ferrier's log villa on the same evening, 1860, "
    "the camera within the room with squared log walls closed on all four sides: the one oil "
    "lamp burning on the scrubbed pine table is the only light and it comes from the lamp alone, "
    "low and warm, on the two faces at the table, the cold hearth and the far corners in darkness"))
PATH = Setup(outdoors=True, described=(
    "The beaten path from the gate to the porch of John Ferrier's log villa on a fine June "
    "morning, 1860: a five-bar gate at the near end; the low morning sun comes from the right, "
    "low enough to rake across the path and throw the porch's black shadow half across it"))
WINDOW = Setup(described=(
    "Interior, inside the sitting-room on a June morning, 1860: one deep window in the left wall "
    "is the only source, and the light comes from the left window alone, a hard slab of morning "
    "sun lying across the pine table and leaving the far corners of the room in deep shadow"))
BARE = Setup(described="A bare rock shoulder above the valley, June 1860: sagebrush and boulders.")


@pytest.fixture(autouse=True)
def _restore():
    hs.adopt(*FARM)
    yield
    hs.adopt("", "")


def words(said: str) -> int:
    return len(said.split())


def test_the_lit_clause_is_the_one_that_names_a_source():
    assert "oil lamp burning" in hs.lit_clause(LAMP.described)
    assert hs.lit_clause(PATH.described).strip() == "the low morning sun comes from the right"
    assert hs.lit_clause(BARE.described) == ""


def test_a_lamp_setup_under_a_sun_episode_renders_the_lamp_and_no_sun():
    said = hs.light_for(LAMP)
    assert "lamp" in said and "sun" not in said
    assert hs.light_faults(said) == []


def test_a_sky_source_keeps_its_direction_and_the_black():
    said = hs.light_for(PATH)
    assert said.startswith("sun from the right") or said.startswith("morning sun from the right")
    assert hs.BLACKS.search(said)
    assert hs.light_faults(said) == []


def test_a_window_is_a_practical_with_a_side():
    said = hs.light_for(WINDOW)
    assert said.startswith("window from the left")
    assert "deep shadow" in said


def test_a_setup_with_no_source_falls_back_to_the_episode_light():
    assert hs.light_for(BARE) == hs.light()
    assert hs.light_for(None) == hs.light()


def test_the_rendered_line_stays_under_the_style_wall_for_every_setup():
    for setup in (LAMP, PATH, WINDOW, BARE):
        assert words(hs.live(setup)) <= hs.MAX_STYLE_WORDS, hs.live(setup)
        assert words(hs.stills(setup)) <= hs.MAX_STYLE_WORDS, hs.stills(setup)
        assert "." not in hs.live(setup)[:-1]


def test_the_line_with_no_setup_is_the_episode_line():
    assert "low side sun" in hs.live() and "low side sun" in hs.stills()
    assert hs.live(None) == hs.live()


def test_the_setup_light_sits_where_the_episode_light_sat():
    assert hs.live(LAMP) == hs.LIVE.format(where=hs.where(), light=hs.light_for(LAMP))
    assert hs.stills(LAMP) == hs.STILLS.format(where=hs.where(), light=hs.light_for(LAMP))


def test_ep10s_evening_and_bedroom_lines_carry_no_sun():
    """J6 / C5: 16 of 34 ep10 blocks said "low side sun" over a moon, a lamp
    and a candle.  Read from the plan on disk; the line is what the take
    builder prints (`episode_ref_official.style_line(setup)`)."""
    if not EP10.exists():
        pytest.skip("the ep10 plan is not on this machine")
    from studio import episode_ref_official as ro
    plan = json.loads(EP10.read_text(encoding="utf-8"))
    hs.adopt(plan["where"], plan["light"])
    for name in ("parlour_evening", "bedroom_night", "mountain_track_night"):
        line = ro.style_line(Setup(**plan["setups"][name]))
        assert "sun" not in line.lower(), (name, line)
        assert words(line) <= hs.MAX_STYLE_WORDS, line
    assert "sun" in ro.style_line(Setup(**plan["setups"]["farm_path_morning"]))
