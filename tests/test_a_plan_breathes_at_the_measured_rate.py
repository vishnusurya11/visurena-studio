"""Pacing (Jekyll ep01 review, 2026-10-13): 362 words, 9.4 s of planned pauses,
projected at a guessed 3.0 words a second against a measured 2.46 -- the plan
ran 173 s on a 146 s projection and step 05 then shaved the holds.  The liked
WotW ep01-03 spoke 266-307 words with 18-20 s of beats and codas.

Now: a new book projects at the studio's measured 2.45, a plan carries at most
310 words and at least 15 s of pauses, and a plan over budget CUTS A LINE,
never a breath.  $0."""
from __future__ import annotations

import copy

from studio import episode_spec as spec
from studio import plan_brief, plan_cures, plan_gates
from studio.episode_spec import Episode
from tests.test_episode_writer import canned_plan


def test_a_book_with_nothing_measured_projects_at_the_studio_rate():
    assert spec.STUDIO_RATE == 2.45
    assert plan_gates.measured_rate([]) == spec.STUDIO_RATE
    assert plan_brief.spoken_rate(None, None) == spec.STUDIO_RATE


def test_a_book_projects_at_its_own_measure_once_it_has_one():
    rows = [{"text": "one two three four five", "seconds": 2.0}]
    assert plan_gates.measured_rate(rows) == 2.5


def _plan(words_per_line: int = 12, beat: float = 0.0) -> dict:
    doc = {**canned_plan(), "words_per_second": 2.45}
    for line in doc["lines"]:
        line["text"] = " ".join(["word"] * words_per_line)
    for shot in doc["shots"][:-2]:
        shot["beat_s"] = beat
    return doc


def test_a_plan_over_the_word_ceiling_is_refused():
    ep = Episode.model_validate(_plan(14, beat=0.7))          # 24 x 14 = 336 words
    got = plan_gates.pace_faults(ep)
    assert any(f.startswith("G-PACE plan: words spoken") and "336" in f for f in got)


def test_a_plan_under_the_pause_floor_is_refused():
    ep = Episode.model_validate(_plan(12, beat=0.0))          # 1.0 s of pauses
    got = plan_gates.pace_faults(ep)
    assert any(f.startswith("G-PACE plan: planned pauses") for f in got)


def test_a_plan_inside_both_walls_is_clean():
    ep = Episode.model_validate(_plan(12, beat=0.7))          # 288 words, 16.4 s
    assert plan_gates.pace_faults(ep) == []


def _two_line_shots(doc: dict, shots: list[int]) -> dict:
    """Move the line of each shot n+1 onto shot n, so shot n carries two."""
    for n in shots:
        doc["lines"][n + 1]["shot"] = n
        doc["shots"][n + 1]["beat_s"] = 1.0
    return doc


def test_an_over_budget_plan_cuts_a_line_and_keeps_every_breath():
    doc = _two_line_shots(_plan(14, beat=0.7), [2, 5, 18])
    before = [(s["beat_s"], s.get("coda_s", 0)) for s in doc["shots"]]
    cut = plan_cures.cut_lines(copy.deepcopy(doc), rate=2.45)
    assert sum(len(l["text"].split()) for l in cut["lines"]) <= plan_gates.MAX_PLAN_WORDS
    assert [(s["beat_s"], s.get("coda_s", 0)) for s in cut["shots"]] == before
    assert [l["index"] for l in cut["lines"]] == list(range(len(cut["lines"])))
    same = lambda a, b: {**a, "index": 0} == {**b, "index": 0}
    assert same(cut["lines"][0], doc["lines"][0]) and same(cut["lines"][-1], doc["lines"][-1])


def test_the_cure_table_routes_pace_and_overrun_to_the_line_cut():
    assert plan_cures.cure_for("G-PACE plan: words spoken over the ceiling, measured 362 against 310") == "cut_lines"
    assert plan_cures.cure_for("CONTRACT : projects to 181 s; an episode is 120-174 s (words at 2.45 a second)") == "cut_lines"
    assert plan_cures.cure_for("CONTRACT : projects to 112 s; an episode is 120-174 s (words at 2.45 a second)") == "holds"
    assert plan_cures.cure_for("G-PACE plan: planned pauses (beats + codas) in seconds, measured 9.4 against 15.0") == "breathe"


def test_a_short_breath_plan_gains_beats_up_to_the_floor():
    doc = _plan(12, beat=0.0)
    out = plan_cures.breathe(copy.deepcopy(doc), rate=2.45)
    assert plan_gates.planned_pauses(out) >= plan_gates.MIN_PAUSE_S
    assert all(s["beat_s"] <= plan_cures.MAX_BEAT_S for s in out["shots"])
    Episode.model_validate(out)


def test_the_battery_holds_pace_hard_on_a_plan_nothing_was_drawn_from(tmp_path):
    from scripts.episode import plan_check
    from studio import episode_home
    ep = Episode.model_validate(_plan(14, beat=0.0))
    # words + pauses, and since c65583f the breathless cuts: the gate returns every fault, hard
    assert plan_check.pace_gate(ep, tmp_path, 3) == len(plan_gates.pace_faults(ep)) >= 3
    (episode_home.home(tmp_path, 3) / "takes").mkdir(parents=True)
    assert plan_check.pace_gate(ep, tmp_path, 3) == 0           # rendered: printed as advice


def test_a_micro_line_never_pushes_a_plan_past_the_word_ceiling():
    from scripts.episode import plan_repair
    doc = _plan(12, beat=0.7)                                     # 288 words
    doc["lines"][1]["text"] = " ".join(["word"] * 20)             # 296: 14 more is 310 -- at the wall
    assert not plan_repair.rate_blocked(doc, 2.45)
    doc["lines"][2]["text"] = " ".join(["word"] * 14)             # 298 + 14 > 310
    assert plan_repair.rate_blocked(doc, 2.45)
