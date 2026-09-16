"""BACKGROUND LIFE only where the crowd is people.

MEASURED on episode 9 (`docs/analysis/ep08_ep09_why_worse.md`, cause 8):
`crowd_block()` told a private parlour whose crowd is MOTHS that "this is a
public place in a working city and people fill it in every panel", on all six
setups, and appended the setup crowd verbatim to every wide panel with its own
full stop kept -- ".," 32 times across the episode.

So the preamble fires only when `Setup.crowd` names people, from a closed noun
list; the per-panel clause fires once, on a panel wide enough to hold a place,
with the crowd's own stop stripped.
"""
import json
from pathlib import Path

from studio import episode_seq_board as sq
from studio.episode_spec import Episode, Setup

FIXTURES = Path(__file__).parent / "fixtures" / "episodes"

PARLOUR = Setup(described="A parlour by lamplight.", cast=[],
                crowd="Moths cross the lamp glass in ones and twos and the low fire settles in the hearth.")
GATE = Setup(described="A farm gate.", cast=[], outdoors=True,
             crowd="A roan horse stands at the fence with its bridle over the rail, swinging its head at the flies.")
ROAD = Setup(described="The high road.", cast=[], outdoors=True,
             crowd="Thirty pack mules file west with six drivers walking at their heads at a normal walking pace.")
BLUFF = Setup(described="The foot of a bluff.", cast=[], outdoors=True,
              crowd="a dozen more mounted men in homespun sit their horses along the foot of the bluff")


def seg(size="wide", crowd="", frame="Wide of the place."):
    return {"size": size, "crowd": crowd, "frame": frame}


# ---- the preamble -----------------------------------------------------------------

def test_moths_are_not_a_crowd():
    assert sq.crowd_block(PARLOUR) == ""


def test_a_horse_is_not_a_crowd():
    assert sq.crowd_block(GATE) == ""


def test_drivers_are_a_crowd():
    assert "public place" in sq.crowd_block(ROAD)


def test_mounted_men_are_a_crowd():
    assert "public place" in sq.crowd_block(BLUFF)


def test_the_people_nouns_are_a_closed_list():
    assert sq.people("forty immigrants kneel along the rock shoulder")
    assert sq.people("two farm hands pitch cut wheat")
    assert sq.people("four Indians lead ponies loaded with pelts")
    assert not sq.people("moths cross the lamp glass")
    assert not sq.people("a yoke of oxen stands in the shafts")
    assert not sq.people("")


# ---- the per-panel clause ---------------------------------------------------------

def test_the_crowds_own_full_stop_is_stripped_so_the_clause_closes_once():
    said = sq.crowd_clause(seg("wide"), PARLOUR)
    assert said == " Behind them, moths cross the lamp glass in ones and twos and the low fire settles in the hearth, out of focus."
    assert ".," not in said


def test_the_clause_fires_once_per_panel():
    """A frame that already carries the crowd sentence is not told it again."""
    already = seg("wide", frame=f"Wide of the road. {ROAD.crowd}")
    assert sq.crowd_clause(already, ROAD) == ""


def test_a_close_still_carries_no_crowd():
    assert sq.crowd_clause(seg("close"), ROAD) == ""


# ---- the fixture ------------------------------------------------------------------

def rebuilt(name: str) -> dict[str, list[str]]:
    episode = Episode.model_validate_json((FIXTURES / "ep09_plan.json").read_text(encoding="utf-8"))
    out = {}
    for setup_name, setup in episode.setups.items():
        if name and setup_name != name:
            continue
        segs = sq.segments(episode.shots, setup_name)
        out[setup_name] = [sq.prompt(group, setup, {}, previous=False, first=(k == 0), geography=route,
                                     aspect=episode.aspect)
                           for k, (group, route, _grid) in enumerate(sq.sheets(segs, setup, episode.aspect))]
    return out


def test_ep09_farm_parlour_rebuilt_is_no_longer_a_public_place():
    for text in rebuilt("farm_parlour")["farm_parlour"]:
        assert "public place" not in text and "people fill it" not in text
        assert "Behind them, moths cross the lamp glass" in text


def test_no_rebuilt_ep09_prompt_carries_a_stop_before_a_comma():
    for name, prompts in rebuilt("").items():
        for text in prompts:
            assert ".," not in text, name


def test_ep09_as_drawn_had_the_fault():
    prompts = json.loads((FIXTURES / "ep09_sheet_prompts.json").read_text(encoding="utf-8"))
    assert "public place" in prompts["seq_farm_parlour_0.prompt.txt"]
    assert sum(t.count(".,") for t in prompts.values()) == 32
