"""J5 (retro 2026-10-11): the content gate against the owner's own judgement.

The 3B replay read every shipped panel of four owner-judged War of the Worlds
episodes once (seed 11) and judged them under the content rules. The gate
refused 23/28 panels of the GOOD ep05 and 5/27 of the GOOD ep07, and 0 of the
BAD ep08/ep09. Each refusal was checked against its picture by eye
(docs/audit/2026-10-10_continuity_retro/C3_content_gate.md); the fixture keeps
the cached reads, the judge's inputs and the eye's label per rule.

Fixed, each measured false on >= 2 panels and true on none:
- 'hills' on a flat place: 11 false (a low far horizon over flat heath). Now an
  ADVISORY; 'mountains' stays a fault, 'cliffs' stays one unless the place is a pit.
- the hour: 4 false, every one on a setup that asks for the LAST DAYLIGHT.
- the figure count: 2 over-the-shoulder shots (the near shoulder is a person);
  5 crowds a plan written before the crowd/extras fields described in its prose.

Kept, true on the picture: the doll, the stranger on an empty wide, a stray
second head, an extra boy, a man stood up where the shot lays or seats him.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from studio import panel_content as pc
from studio.panel_content import Seen

FIXTURE = Path(__file__).parent / "fixtures" / "content_gate" / "wotw_owner_fixtures.json"
PANELS = json.loads(FIXTURE.read_text(encoding="utf-8"))["panels"]

STILL_REFUSED = {"ep05/s10", "ep05/s16", "ep05/s18", "ep05/s19", "ep05/s21", "ep05/s25",
                 "ep07/s03", "ep07/s04", "ep07/s05", "ep07/s09",
                 "ep09/s04"}
"""Refused after the fix: every TRUE fault, plus four false refusals logged open
(named walk-ons in a legacy plan, a crowd's silhouettes read as copies)
and ep09/s04 (2026-10-19, P06): a wide of nine sappers on an extras-0 shot -- the plan
declared its crowd only on the setup, which no longer stands the count down; G-CROWD
refuses such a plan before drawing."""


def shot_of(row: dict) -> SimpleNamespace:
    s = row["shot"]
    declared = {"frame", "faces"} | ({"extras"} if s["extras_declared"] else set())
    return SimpleNamespace(frame=s["frame"], at_rest=s["at_rest"], size=s["size"], faces=s["faces"],
                           extras=s["extras"], model_fields_set=declared)


def judged(key: str) -> list[str]:
    row = PANELS[key]
    return pc.judge_staged(Seen(**row["seen"]), shot_of(row), SimpleNamespace(**row["setup"]),
                           flat=row["flat"], banned=row["banned"], physical=row["physical"],
                           markers=row["markers"])


def refused(prefix: str) -> set[str]:
    return {k for k in PANELS if k.startswith(prefix) and judged(k)}


def test_the_judge_reproduces_the_3b_replay_on_the_untouched_rules():
    """The fixture is the replay: every refusal the replay saw on a rule this
    fix leaves alone is still produced, word for word."""
    kept = ("banned from this book", "posture")
    for key, row in PANELS.items():
        for line in row["before"]:
            if line.startswith(kept):
                assert line in judged(key), key


@pytest.mark.parametrize("ep", ["ep05", "ep07", "ep08", "ep09"])
def test_each_episode_refuses_only_what_the_eye_kept(ep):
    assert refused(ep) == {k for k in STILL_REFUSED if k.startswith(ep)}


def test_every_true_fault_the_eye_found_is_still_refused():
    true = {k for k, r in PANELS.items() if any(v.startswith("TRUE") for v in r["eye"].values())}
    assert true and true <= {k for k in true if judged(k)}


def test_the_good_ep05_is_refused_far_less_than_before():
    before = sum(1 for k, r in PANELS.items() if k.startswith("ep05") and r["before"])
    assert (before, len(refused("ep05"))) == (23, 6)


# ---- the rules, one by one -----------------------------------------------------

def seen(**kw) -> Seen:
    return Seen(**{"landform": "flat", "people": 0, "lookalikes": 0, "text": False, "hour": "night", **kw})


def test_hills_on_a_flat_place_are_an_advisory_not_a_fault():
    assert not pc.forbidden_landform(seen(landform="hills"), flat=True)
    assert pc.landform_advisory(seen(landform="hills"), flat=True)


@pytest.mark.parametrize("land", ["flat", "gentle rise", "indoors"])
def test_level_ground_carries_no_landform_advisory(land):
    assert pc.landform_advisory(seen(landform=land), flat=True) is None


def test_mountains_on_a_flat_place_are_still_a_fault():
    assert pc.forbidden_landform(seen(landform="mountains"), flat=True)


def test_cliffs_on_a_flat_place_are_a_fault_unless_the_place_is_a_pit():
    assert pc.forbidden_landform(seen(landform="cliffs"), flat=True, staged="open heather")
    assert not pc.forbidden_landform(seen(landform="cliffs"), flat=True,
                                     staged="a ring of sand round the crater")


def test_a_setup_that_asks_for_the_last_daylight_takes_a_day_read():
    assert not pc.judged_at_night("Horsell Common at twilight: the last daylight comes low from the LEFT")


def test_a_night_setup_without_daylight_is_still_judged_at_night():
    assert pc.judged_at_night("the common at night under a hard moon")


def test_an_over_the_shoulder_shot_holds_one_more_figure():
    frame = "Medium close over the neighbour's striped flannel shoulder toward the Narrator"
    assert not pc.faults(seen(people=2), frame=frame, planned=1, crowd=False, flat=False, night=False)


def test_a_second_stranger_without_a_shoulder_is_still_a_fault():
    assert pc.faults(seen(people=2), frame="Medium on the narrator alone", planned=1,
                     crowd=False, flat=False, night=False)


def test_a_shoulder_does_not_excuse_a_copy():
    frame = "over the shoulder of the wife toward the narrator"
    assert pc.faults(seen(people=2, lookalikes=1), frame=frame, planned=1, crowd=False,
                     flat=False, night=False)


def legacy(frame: str, declared: bool) -> SimpleNamespace:
    return SimpleNamespace(frame=frame, at_rest="", extras=0,
                           model_fields_set={"frame"} | ({"extras"} if declared else set()))


def test_a_plan_before_the_extras_field_declares_its_crowd_in_prose():
    shot = legacy("a long black band of people along the skyline", declared=False)
    assert pc.crowd_declared(shot, SimpleNamespace(crowd=""))


def test_a_plan_that_declares_extras_is_held_to_them():
    shot = legacy("a long black band of people along the skyline", declared=True)
    assert not pc.crowd_declared(shot, SimpleNamespace(crowd=""))


def test_a_declared_setup_crowd_is_a_crowd():
    """Only on a shot that declares extras > 0 (retro 2026-10-19, P06: a setup's
    crowd no longer stands the count down on every extras-0 shot of the setup)."""
    shot = legacy("the narrator", declared=True)
    assert not pc.crowd_declared(shot, SimpleNamespace(crowd="passengers"))
    shot.extras = 2
    assert pc.crowd_declared(shot, SimpleNamespace(crowd="passengers"))
