"""The master eye judges a frame's content with the panel gate's own J5 rules.

J5 (78df605, 2026-10-11) calibrated the panel and take content gates on the
owner-judged WotW episodes: no hour fault on a setup asking for the last
daylight, one more figure over a shoulder (never a copy), and a legacy plan's
crowd declared in the shot's words. `master_eye.content_faults` still judged
the hour by `at_night` and the crowd by the setup field alone
(docs/audit/2026-10-10_continuity_retro/C3_content_gate.md, section 2), so a
master could be refused for what every panel and take gate passed.

The master eye reads a plan.json as dicts and knows no book facts (flat
places, banned subjects, physical rows, look markers); on the same read, shot
and setup it must give exactly what `pc.judge_staged` gives without them.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from studio import panel_content as pc
from studio.judges import master_eye as me
from studio.panel_content import Seen

FIXTURE = Path(__file__).parent / "fixtures" / "content_gate" / "wotw_owner_fixtures.json"
PANELS = json.loads(FIXTURE.read_text(encoding="utf-8"))["panels"]


def plan_shot(row: dict) -> dict:
    """The shot as plan.json holds it: `extras` is a key only once declared."""
    s = row["shot"]
    out = {"frame": s["frame"], "at_rest": s["at_rest"], "size": s["size"], "faces": s["faces"]}
    return {**out, "extras": s["extras"]} if s["extras_declared"] else out


def panel_shot(row: dict) -> SimpleNamespace:
    s = row["shot"]
    declared = {"frame", "faces"} | ({"extras"} if s["extras_declared"] else set())
    return SimpleNamespace(frame=s["frame"], at_rest=s["at_rest"], size=s["size"], faces=s["faces"],
                           extras=s["extras"], model_fields_set=declared)


def eye(seen: Seen, shot: dict, setup: dict) -> list[str]:
    return me.content_faults(me.Read(at=0.0, shot=1, seen=seen), shot, setup)


@pytest.mark.parametrize("key", sorted(PANELS))
def test_the_master_eye_and_the_panel_gate_agree_on_every_fixture_panel(key):
    row = PANELS[key]
    panel = pc.judge_staged(Seen(**row["seen"]), panel_shot(row), SimpleNamespace(**row["setup"]), flat=False)
    assert eye(Seen(**row["seen"]), plan_shot(row), row["setup"]) == panel


def seen(**kw) -> Seen:
    return Seen(**{"landform": "flat", "people": 0, "lookalikes": 0, "text": False, "hour": "day", **kw})


def test_the_master_eye_takes_a_day_read_where_the_setup_asks_for_the_last_daylight():
    setup = {"described": "Horsell Common at night falling: the last daylight comes low from the LEFT"}
    assert not eye(seen(), {"frame": "Wide of the common", "faces": []}, setup)


def test_the_master_eye_still_refuses_a_day_read_on_a_plain_night():
    setup = {"described": "the common at night under a hard moon"}
    assert eye(seen(), {"frame": "Wide of the common", "faces": []}, setup)


def test_the_master_eye_lets_an_over_the_shoulder_frame_hold_one_more_figure():
    shot = {"frame": "Medium close over the neighbour's shoulder toward the Narrator", "faces": ["n"], "extras": 0}
    assert not eye(seen(people=2), shot, {"described": "a garden by day"})


def test_the_master_eye_never_lets_a_shoulder_excuse_a_copy():
    shot = {"frame": "over the shoulder of the wife toward the narrator", "faces": ["n"], "extras": 0}
    assert eye(seen(people=2, lookalikes=1), shot, {"described": "a garden by day"})


def test_the_master_eye_reads_a_legacy_plans_crowd_from_its_words():
    shot = {"frame": "a long black band of people along the skyline", "faces": []}
    assert not eye(seen(people=6), shot, {"described": "the common by day"})


def test_the_master_eye_holds_a_plan_that_declared_extras_to_them():
    shot = {"frame": "a long black band of people along the skyline", "faces": [], "extras": 0}
    assert eye(seen(people=6), shot, {"described": "the common by day"})
