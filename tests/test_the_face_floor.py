"""G-FACE-FLOOR (face-blur plan fix #3, 2026-10-19): a face the plan cares about is
planned big enough for H3 to draw its eyes.

H3 draws a 768 take on 32 px tokens, so a face under about 96 px (3 tokens) has an
eye under half a VAE cell and comes back mush (docs/audit/2026-10-19_face_blur,
PLAN section 1).  The projection is ep01's own measurement: the smallest confident
face of every delivered take, by planned size (fixture ep01_face_heights.json).

The cure is free and deterministic: a wide or full shot whose face matters (its
own voice or a reaction) steps ONE size closer, wide -> full -> medium, when the
step breaks no grammar rule; establishing wides, inserts and back views are never
touched.  Every faced shot still under the floor is listed as a guaranteed face
refine candidate.  Advice only: it never refuses a plan or calls the writer.  $0.
"""
from __future__ import annotations

import copy
import json
import statistics
from pathlib import Path

from studio import face_floor as ff, framing_grammar as fg, grammar_battery, plan_gates
from studio.episode_spec import Episode

FIX = Path(__file__).parent / "fixtures"
PLAN = FIX / "ep01_replay" / "P02" / "plan.json"


def ep01() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))


def heights() -> dict:
    return json.loads((FIX / "ep01_face_heights.json").read_text(encoding="utf-8"))["takes"]


def shot(doc: dict, index: int) -> dict:
    return next(s for s in doc["shots"] if s["index"] == index)


def later_wide(doc: dict) -> dict:
    """ep01 shot 23 (a walk_on_day dialogue shot) made a later wide told in his own voice,
    its at_rest carrying a person fraction the cure replaces (the skeptic's case)."""
    s = shot(doc, 23)
    s.update(size="wide", frame="Wide down the street as " + s["frame"][len("Medium close on "):],
             at_rest="THE FOCUS OF THE PICTURE IS the man about town at the CENTRE on the near pavement, "
                     "his figure a fifth of the frame's height.")
    doc["lines"] = [dict(l, kind="tale") if l["shot"] == 23 else l for l in doc["lines"]]
    return doc


def bare_full(doc: dict) -> dict:
    """ep01 shot 6 (Enfield telling his tale under the lamp) without the boots:
    a full whose face matters and whose staging a medium can hold."""
    s = shot(doc, 6)
    s["at_rest"] = ("THE FOCUS OF THE PICTURE IS the man about town under the corner gas lamp, his figure at "
                    "the LEFT third, two thirds of the frame's height. The corner gas lamp stands at the RIGHT "
                    "third reaching the TOP edge, its flame yellow.")
    s["motion"] = ("The camera holds a locked-off frame across the whole shot; he swings his black walking cane; "
                   "the lamp flame wavers above him")
    return doc


# ---- the projection is ep01's measurement --------------------------------------------

def test_the_projection_is_the_median_smallest_face_ep01_measured_at_each_size():
    by_size: dict[str, list[float]] = {}
    for take in heights().values():
        if take["faces"] and take["smallest_px"] is not None and take["size"] != "insert":
            by_size.setdefault(take["size"], []).append(take["smallest_px"])
    for size, values in by_size.items():
        assert abs(ff.FACE_PX[size] - statistics.median(values)) <= 1, size


def test_wide_full_and_medium_project_under_the_floor_and_the_closes_over_it():
    assert [s for s in ("wide", "full", "medium") if ff.projected_px(s) < ff.FLOOR_PX] == ["wide", "full", "medium"]
    assert all(ff.projected_px(s) > ff.FLOOR_PX for s in ("medium_close", "close", "extreme_close"))
    assert ff.projected_px("insert") is None


# ---- whose face matters ------------------------------------------------------------------

def test_a_face_matters_when_it_speaks_its_own_line_or_reacts():
    doc = ep01()
    assert ff.face_matters(doc, shot(doc, 6))        # Enfield's own tale over his walk
    assert ff.face_matters(doc, shot(doc, 26))       # the handshake reaction
    assert not ff.face_matters(doc, shot(doc, 1))    # the narrator over the walkers
    assert not ff.face_matters(doc, shot(doc, 8))    # Enfield tells it, Hyde and the girl are shown
    assert not ff.face_matters(doc, shot(doc, 7))    # an insert


def test_a_back_view_is_no_face():
    doc = ep01()
    s = shot(doc, 26)
    s["frame"] = "Medium on the two men from behind as they shake hands under the gas lamp."
    assert not ff.face_matters(doc, s)


def test_the_opener_and_a_setups_first_wide_are_establishing():
    doc = ep01()
    assert ff.establishing(doc, shot(doc, 1))        # street_day's first wide
    assert ff.establishing(doc, shot(doc, 18))       # walk_on_day's first shot
    later = copy.deepcopy(shot(doc, 23))
    later["size"] = "wide"
    assert not ff.establishing(doc, later)           # a second wide on walk_on_day


# ---- the cure -------------------------------------------------------------------------------

def test_ep01_as_shipped_moves_nothing_and_its_doc_is_untouched():
    doc = ep01()
    cured, moved = ff.cure(copy.deepcopy(doc))
    assert moved == [] and cured == doc


def test_a_full_whose_face_matters_steps_to_a_medium_with_its_words():
    doc = bare_full(ep01())
    cured, moved = ff.cure(doc)
    s = shot(cured, 6)
    assert s["size"] == "medium" and s["frame"].startswith("Medium shot of the man about town")
    assert "two thirds of the frame's height" not in s["at_rest"]
    assert "head a quarter of the frame's height" in s["at_rest"]
    assert [m.split(":")[0] for m in moved] == ["G-FACE-FLOOR shot 6"] and "full -> medium" in moved[0]


def test_a_wide_steps_once_to_full_never_twice():
    doc = ep01()
    s = shot(doc, 23)                                 # a walk_on_day dialogue shot made a later wide
    s.update(size="wide", frame="Wide down the street as " + s["frame"][len("Medium close on "):],
             at_rest="THE FOCUS OF THE PICTURE IS the man about town at the CENTRE on the near pavement.")
    doc["lines"] = [dict(l, kind="tale") if l["shot"] == 23 else l for l in doc["lines"]]
    cured, moved = ff.cure(doc)
    got = shot(cured, 23)
    assert got["size"] == "full" and got["frame"].startswith("Full shot down the street")
    assert "two thirds of the frame's height" in got["at_rest"] and len(moved) == 1


def test_a_shot_the_cure_already_stepped_is_never_stepped_again_by_a_later_rung():
    first, moved = ff.cure(later_wide(ep01()))
    assert shot(first, 23)["size"] == "full" and len(moved) == 1
    again, moved_again = ff.cure(copy.deepcopy(first), previous=first)   # an improve rung kept the full
    assert moved_again == [] and shot(again, 23)["size"] == "full"
    assert shot(again, 23)["at_rest"] == shot(first, 23)["at_rest"]


def test_a_writer_that_puts_the_wide_back_gets_one_step_from_its_own_size():
    first, _ = ff.cure(later_wide(ep01()))
    redrawn, moved = ff.cure(later_wide(ep01()), previous=first)         # the rung wrote the wide again
    assert shot(redrawn, 23)["size"] == "full" and len(moved) == 1


def test_the_size_word_is_rewritten_only_where_it_is_the_frames_size():
    compound = "Full-length view of the man under the lamp."
    assert ff.new_frame(compound, "medium") == compound
    assert ff.new_frame("A wide shot of the street at noon.", "full") == "Full shot of the street at noon."
    assert ff.new_frame("Wide on the door.", "full") == "Full shot on the door."


def test_a_step_that_would_break_the_staging_or_the_grammar_is_refused_with_its_reason():
    doc = ep01()
    assert "body" in ff.blocker(doc, shot(doc, 6))            # the boots stride in a medium's cut
    crane = bare_full(ep01())
    shot(crane, 6)["motion"] = "The camera rises above the man, looking down over the corner; he walks; the lamp flares"
    assert "move" in ff.blocker(crane, shot(crane, 6))        # crane_up is no medium's move
    orphan = bare_full(ep01())
    orphan["setups"]["night_corner"]["crowd"] = "a knot of night cabmen by the kerb"
    for s in orphan["shots"]:
        if s["setup"] == "night_corner" and s["index"] != 6:
            s["size"], s["extras"] = "medium_close", 0
    assert "crowd" in ff.blocker(orphan, shot(orphan, 6))     # G-CROWD-ORPHAN would be born


def test_the_cure_adds_no_grammar_or_crowd_fault():
    doc = bare_full(ep01())
    before = Episode.model_validate(doc)
    after = Episode.model_validate(ff.cure(copy.deepcopy(doc))[0])
    def rows(ep):
        return set(grammar_battery.framing_faults(ep, {}) + plan_gates.crowd_faults(ep)
                   + plan_gates.orphan_crowd_faults(ep) + plan_gates.move_faults(ep))
    assert rows(after) <= rows(before)


# ---- the advisory ------------------------------------------------------------------------

def test_every_faced_shot_under_the_floor_is_a_refine_candidate():
    doc = ep01()
    assert ff.refine_candidates(doc) == [1, 6, 8, 10, 18, 26]
    rows = ff.advisories(doc)
    assert [r.split(":")[0] for r in rows] == [f"G-FACE-FLOOR shot {i}" for i in (1, 6, 8, 10, 18, 26)]
    assert "measured 28 against 96" in rows[0]


def test_the_battery_prints_the_floor_as_advice_never_as_a_fault():
    ep = Episode.model_validate(ep01())
    assert any(a.startswith("G-FACE-FLOOR shot 1") for a in grammar_battery.advisories(ep, 2.45))
    assert not [r for r in grammar_battery.faults(ep, 2.45) if r.startswith("G-FACE-FLOOR")]


def test_the_writer_is_told_the_floor():
    band = grammar_battery.band()
    assert band["face_floor_px"] == ff.FLOOR_PX and band["face_px_by_size"]["wide"] == ff.FACE_PX["wide"]
    assert fg.band()["face_floor_px"] == ff.FLOOR_PX


# ---- the plan ladder runs it on every fresh draft ------------------------------------------

class FloorWriter:
    """Writes ep01's plan with shot 6 as a full a medium can hold."""

    def write(self, brief, refusals=None, previous=None, _agent=None, **kw):
        return Episode.model_validate(bare_full(ep01()))


def floor_desk(tmp_path):
    from studio import plan_ladder
    from tests.test_a_climb_that_moves_no_row_stops import Ctx
    desk = plan_ladder.Desk(Ctx(tmp_path), tmp_path / "plan.json", writer=FloorWriter())
    desk.brief = {}
    return desk


def test_a_fresh_writer_draft_gets_the_floor_cure_and_says_what_moved(tmp_path):
    desk = floor_desk(tmp_path)
    desk.write(None)
    assert shot(json.loads(desk.plan.read_text(encoding="utf-8")), 6)["size"] == "medium"
    assert any("G-FACE-FLOOR shot 6" in m for m in desk.ctx.said)


class KeepWriter:
    """Writes ep01 with shot 23 a later wide; an improve rung hands the plan back as it got it."""

    def write(self, brief, refusals=None, previous=None, _agent=None, **kw):
        return Episode.model_validate(previous if previous is not None else later_wide(ep01()))


def test_every_rung_of_the_ladder_leaves_a_shot_one_step_from_the_writers_size(tmp_path):
    from studio import plan_ladder
    from tests.test_a_climb_that_moves_no_row_stops import Ctx
    desk = plan_ladder.Desk(Ctx(tmp_path), tmp_path / "plan.json", writer=KeepWriter())
    desk.brief = {}
    desk.write(None)
    desk.write(["a refusal"], previous=desk.refused_plan())             # improve
    desk.write(["a refusal"], previous=desk.refused_plan())             # model_tier
    assert shot(json.loads(desk.plan.read_text(encoding="utf-8")), 23)["size"] == "full"
    assert sum("G-FACE-FLOOR shot 23" in m for m in desk.ctx.said) == 1


def test_a_floor_cure_that_raises_keeps_the_draft(tmp_path, monkeypatch):
    def boom(doc):
        raise RuntimeError("cure bug")
    monkeypatch.setattr(ff, "cure", boom)
    desk = floor_desk(tmp_path)
    desk.write(None)
    assert shot(json.loads(desk.plan.read_text(encoding="utf-8")), 6)["size"] == "full"


def test_an_uncured_steppable_shot_says_the_cure_would_step_it():
    doc = bare_full(ep01())
    row = next(r for r in ff.advisories(doc) if r.startswith("G-FACE-FLOOR shot 6"))
    assert "the free cure steps it to medium" in row
