r"""G-LIGHT: a plan builds only under a light with a direction and a black.

docs/analysis/ep08_ep09_why_worse.md, cause 2 of episode 9: "The black floor
is gone. 5th-percentile luma 4-7 (ep05-07) -> 16.5 ... Cause: the palette
sentence replaced the London clause that made the series look like film --
'deep shadow; practical period light sources' -- with 'sunlight only' and a
colour inventory. The drawer obeys light-direction words; 'hard blue shadow'
never arrives." And cause 8: "The palette's objects stamped a gold wheat
foreground into five of six plates, including the bare rock shoulder."

The fixtures are the four episodes the owner judged. ep05 and ep07 carry no
palette and build under the house light; ep08 and ep09 carry a palette
paragraph and no `light`, and must fail this gate with the reason quoted.
A published plan still LOADS -- reading a historical plan is not endorsing
it (`Episode.long_shots`) -- and is refused where it would be BUILT.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import house_style as hs
from studio.episode_spec import Episode, Setup

FIXTURES = ROOT / "tests" / "fixtures" / "episodes"


def load(number: int) -> Episode:
    return Episode.model_validate_json((FIXTURES / f"ep{number:02d}_plan.json").read_text(encoding="utf-8"))


def plan_dict(number: int) -> dict:
    return json.loads((FIXTURES / f"ep{number:02d}_plan.json").read_text(encoding="utf-8"))


def frames_module():
    spec = importlib.util.spec_from_file_location("ep_frames", ROOT / "scripts" / "episode" / "frames.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["ep_frames"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _restore():
    yield
    hs.adopt("", "")


# ---- the fixtures ------------------------------------------------------------

@pytest.mark.parametrize("number", [5, 7])
def test_the_london_episodes_pass_under_the_house_light(number):
    assert hs.faults(load(number)) == []


@pytest.mark.parametrize("number", [8, 9])
def test_the_utah_episodes_fail_with_the_reason_quoted(number):
    bad = hs.faults(load(number))
    assert bad
    assert "light" in bad[0] and "palette" in bad[0], bad[0]


def test_episode_9_is_refused_for_its_objects_by_name():
    said = " ".join(hs.faults(load(9)))
    assert "wheat" in said and "dust" in said and "pine" in said


def test_episode_9_setups_without_a_directed_source_are_named():
    said = " ".join(hs.faults(load(9)))
    assert "ferrier_land" in said, "'hard morning sunlight' has no direction"
    assert "the_drove" in said, "'hard white sun overhead' throws no shadow into frame"
    assert "farm_parlour" not in said, "the hanging oil lamp is a practical with a place"


def test_a_published_palette_plan_still_loads():
    """ep08 and ep09 are published; their plan.json must keep loading."""
    for number in (8, 9):
        assert load(number).palette


# ---- the new form ------------------------------------------------------------

def new_form(number: int = 5, **fields) -> dict:
    plan = plan_dict(number)
    plan.pop("palette", None)
    plan.update(where="Utah valley, June 1860", light="low left sun, hard black shadows")
    plan.update(fields)
    return plan


def test_a_plan_in_the_new_form_validates_and_renders_short():
    episode = Episode.model_validate(new_form())
    assert episode.where and episode.light
    hs.adopt(episode.where, episode.light)
    assert len(hs.stills().split()) <= hs.MAX_STYLE_WORDS
    assert "shadow" in hs.stills()


def test_a_plan_whose_light_is_an_inventory_is_refused_at_load():
    with pytest.raises(ValueError, match="wheat"):
        Episode.model_validate(new_form(light="gold ripe wheat, red road dust and deep green pine"))


def test_a_plan_whose_light_has_no_direction_is_refused_at_load():
    with pytest.raises(ValueError, match="direction"):
        Episode.model_validate(new_form(light="hard sunlight, deep shadow"))


def test_a_plan_whose_where_runs_long_is_refused_at_load():
    with pytest.raises(ValueError, match="where"):
        Episode.model_validate(new_form(where="the Utah valley and Salt Lake City, June 1860"))


def test_a_plan_with_a_place_and_no_light_is_refused_at_load():
    with pytest.raises(ValueError, match="light"):
        Episode.model_validate(new_form(light=""))


def test_a_plan_whose_rendered_line_runs_past_sixteen_words_is_refused():
    with pytest.raises(ValueError, match="16"):
        Episode.model_validate(new_form(
            light="low sun from the left, long shadows across the ground, black under every eave"))


def test_faults_reads_the_house_light_when_the_plan_declares_nothing():
    """A plan that says nothing is London and passes the plan-level check."""
    plan = plan_dict(5)
    said = " ".join(hs.faults(Episode.model_validate(plan)))
    assert "light" not in said


# ---- the plate prompt --------------------------------------------------------

def test_the_plate_prompt_carries_where_and_the_setups_own_light():
    frames = frames_module()
    setup = Setup(described="A farm gate at evening, long level light from the west")
    said = frames.plate_prompt(setup, "Utah valley, June 1860", "low left sun, hard black shadows")
    assert "Utah valley, June 1860" in said and setup.described in said
    assert "low left sun" not in said, "the setup names its own light; the plan's is the default"


def test_the_plate_prompt_falls_back_to_the_plans_light():
    frames = frames_module()
    setup = Setup(described="A farm gate at evening")
    said = frames.plate_prompt(setup, "Utah valley, June 1860", "low left sun, hard black shadows")
    assert "low left sun, hard black shadows" in said


def test_the_plate_prompt_never_carries_the_palette():
    frames = frames_module()
    episode = load(9)
    for setup in episode.setups.values():
        said = frames.plate_prompt(setup, "Utah valley, June 1860", "low left sun, hard black shadows")
        assert "wheat" not in said.split(setup.described)[0], "the palette's objects reached the plate"


def test_the_plate_step_refuses_a_plan_that_fails_the_gate():
    frames = frames_module()
    with pytest.raises(SystemExit, match="G-LIGHT"):
        frames.refuse_unlit(load(9))
    frames.refuse_unlit(load(7))


# ---- the change reaches the artefact ------------------------------------------

def test_every_script_adopts_where_and_light_not_the_palette():
    """The ep08 fault: a fix wired into one path and called done. Every script
    that declares the run's place must hand `adopt` the two new fields."""
    for name in ("frames.py", "seq_boards.py", "takes_r2v.py"):
        said = (ROOT / "scripts" / "episode" / name).read_text(encoding="utf-8")
        assert "adopt(episode.palette)" not in said, name
        assert 'adopt(getattr(episode, "palette", ""))' not in said, name
        assert "adopt(episode.where, episode.light)" in said, name
