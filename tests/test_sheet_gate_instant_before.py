"""INSTANT BEFORE sees the participle; the LADDER may not contradict the at_rest.

Measured on episode 10 (docs/analysis/ep10_dq_synthesis.md, section D; the
storyboard analyst's 48-row obedience table):

  Q10  motion "lifts one heavy hand off the table and turns it palm up"
       at_rest "His raised hand comes into the BOTTOM RIGHT corner"     drawn palm-up, finished
  Q12  motion "throws the open hand out a forearm's length"
       at_rest "his open hand out into the light at the LEFT third"     drawn thrown
  Q27  motion "brings the back of one bare hand up to wipe her eyes"
       at_rest "Her raised hand comes up into the RIGHT half"           drawn at the eye

The drawer draws what at_rest says, so the render had nothing left to do: T12
drift 0.05, T10 0.62, T27 0.52.  `end_state` saw perfect tenses and "already /
about to" only, never a participle adjective on the motion's own object.

  Q03  ladder "The porch of the log house is the height of a thumbnail"
       at_rest "The porch and the open door stand ... the height of a hand"

One panel, two sizes for one noun; the drawer picked the at_rest.  The gate
refuses the contradiction for $0.
"""
import json
from pathlib import Path

import pytest

from studio import sheet_gate as gate
from studio.episode_spec import Episode, Setup

FIXTURES = Path(__file__).parent / "fixtures" / "episodes"


def seg(shot=0, sub=0, **kw):
    base = {"shot": shot, "sub": sub, "size": "medium_close", "path": 0.4, "faces": [], "camera": "",
            "frame": "Medium close on a man in a chair.", "motion": "he walks on", "at_rest": "",
            "end_frame": "", "changed": "", "crowd": ""}
    return base | kw


def hard(panel):
    return [f.text for f in gate.instant_before(panel) if f.hard]


# ---- D2  the participle of the panel's own motion ------------------------------

def test_participle_of_own_motion_is_end_state():
    q10 = seg(10, motion="The camera pushes in across the whole shot; he lifts one heavy hand off the "
                         "table and turns it palm up toward the right of frame; his head comes forward.",
              at_rest="Brigham Young's head and shoulders fill the CENTRE of the frame. His raised hand "
                      "comes into the BOTTOM RIGHT corner and the deep shadow fills the frame behind him.")
    assert hard(q10) == ["raised hand"]
    q12 = seg(12, motion="The camera pushes in; he throws the open hand out a forearm's length into the "
                         "window light; he brings it back to his chest with the whip.",
              at_rest="John Ferrier stands in the CENTRE of the frame, his open hand out into the light at "
                      "the LEFT third, the whip in his RIGHT hand along the RIGHT third.")
    assert hard(q12) == ["hand out"]
    q27 = seg(27, motion="The camera pushes in on Lucy; she laughs and brings the back of one bare hand up "
                         "to wipe her eyes; she lets the hand fall to her collar.",
              at_rest="Lucy's head and shoulders fill the CENTRE of the frame. Her raised hand comes up "
                      "into the RIGHT half of the frame and the black of the room fills the frame behind her.")
    assert hard(q27) == ["raised hand"]


def test_the_state_of_another_object_is_not_the_panel_s_own_end_state():
    """The HARD case is the motion's OWN object.  A raised glass on the table
    while the motion lifts a hand is set dressing."""
    panel = seg(5, motion="he lifts one hand off the table",
                at_rest="a raised glass stands on the table at the LEFT edge, his hand flat beside it")
    assert hard(panel) == []


def test_a_hand_at_rest_before_it_lifts_passes():
    panel = seg(10, motion="he lifts one heavy hand off the table and turns it palm up",
                at_rest="his heavy hand lies flat on the table in the BOTTOM RIGHT corner")
    assert gate.instant_before(panel) == []


def test_held_state_names_the_phrase_it_found():
    assert gate.held_state("she brings the back of one bare hand up to wipe her eyes",
                           "Her raised hand comes up into the RIGHT half") == "raised hand"
    assert gate.held_state("he throws the open hand out a forearm's length",
                           "his open hand out into the light") == "hand out"
    assert gate.held_state("he lifts the latch", "the latch lifted off its catch") == "latch lifted"
    assert gate.held_state("he walks on", "his raised hand on the stick") is None


def fixture_hits(ep: str) -> list[tuple[int, str]]:
    episode = Episode(**json.loads((FIXTURES / f"ep{ep}_plan.json").read_text(encoding="utf-8")))
    return [(s.index, f.text) for s in episode.shots
            for f in gate.instant_before(dict(s.model_dump(), shot=s.index, sub=0)) if f.hard]


def test_ep07_stays_clean():
    """The calibration set: ep07's 26 at_rests hold no gesture finished."""
    assert fixture_hits("07") == []


def test_ep05_has_exactly_the_one_hit_the_rule_is_for():
    """ep05 shot 18: motion "brings the ring up between finger and thumb and
    turns it out", at_rest "holding a plain gold ring up between a bare finger
    and thumb" -- the same shape as ep10's Q27 ("brings ... hand up" / "hand
    comes up").  Recorded here, not hidden: the owner liked ep05 and this is
    the one panel of its 25 that the rule would have sent back for a sentence."""
    assert fixture_hits("05") == [(18, "ring held up")]


# ---- D3  the ladder may not contradict the at_rest ----------------------------

PATH = Setup(described="The shingly path up to a log villa on a June morning.",
             landmark="the porch of the log house", landmark_at="far_end",
             landmark_size="is half the height of the frame",
             route="from the gate up the shingly path to the porch step")


def test_a_ladder_size_that_contradicts_the_at_rest_is_refused():
    q03 = seg(3, size="wide", path=0.0,
              frame="Wide up the shingly path to the porch of the log villa, the open gate in the near ground.",
              at_rest="The porch and the open door stand in the TOP CENTRE the height of a hand. The path "
                      "runs from the bottom LEFT corner up to the porch step.")
    found = gate.ladder_findings(q03, PATH)
    assert [(f.check, f.panel, f.hard, f.text) for f in found] == \
        [("LADDER", "Q03_0", True, "the height of a hand")]
    assert "thumbnail" in found[0].note


def test_an_at_rest_that_agrees_with_the_ladder_passes():
    q03 = seg(3, size="wide", path=0.0, frame="Wide up the shingly path to the porch of the log villa.",
              at_rest="The porch stands in the TOP CENTRE the height of a thumbnail.")
    assert gate.ladder_findings(q03, PATH) == []


def test_a_size_on_another_noun_is_not_the_ladder_s_business():
    q03 = seg(3, size="wide", path=0.0, frame="Wide up the shingly path to the porch of the log villa.",
              at_rest="The porch stands in the TOP CENTRE. The gate post is the height of a hand at the LEFT edge.")
    assert gate.ladder_findings(q03, PATH) == []


def test_a_panel_off_the_route_or_facing_away_carries_no_ladder_finding():
    close = seg(5, size="close", path=0.6, frame="Close on his face.",
                at_rest="The porch is the height of a hand behind him.")
    assert gate.ladder_findings(close, PATH) == []
    away = seg(4, size="medium", path=0.4, frame="Medium of a man coming up the path, the gate behind him.",
               at_rest="The porch is the height of a hand behind him.")
    assert gate.ladder_findings(away, PATH) == []


def test_the_whole_sheet_runs_the_ladder_check():
    q03 = seg(3, size="wide", path=0.0, frame="Wide up the path to the porch of the log villa.",
              at_rest="The porch stands in the TOP CENTRE the height of a hand.")
    prompt = "SHEET\nA film storyboard sheet: a 1 by 1 grid of 1 equal square 1:1 panels"
    found = gate.sheet_findings([q03], PATH, prompt, (1, 1, (2048, 2048)))
    assert "LADDER" in {f.check for f in found}
