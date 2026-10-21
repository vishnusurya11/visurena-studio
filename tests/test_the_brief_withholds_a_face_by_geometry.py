"""Five-iterations builds B7.1-B7.4 and B2's dialogue word budget (2026-10-20).

B7: ep01's Hyde lit up at the second the take text commanded it ("lifts his chin
... from 00:00", "chin raised", "a low angle", "the lamp flame flickers across
his pale cheek": plan shots 9-11; T10 held its shadow until its commanded
00:02).  The writer wrote those words, so the writer is told: a face the
chapter keeps back is withheld by geometry, never undone by a lift, a low
angle or cheek light, speaks no lip line before the answer, and is lit once,
on the answer's shot, by one timed verb.

B2: chapter 2's dialogue ceiling is 0.27 (ch1 0.35).  The writer is given the
ceiling as words of the plan's 310, not only as a share.  No API."""
from __future__ import annotations

from studio import episode_spec, plan_brief, plan_gates

# the lift words of ep01 plan.json shots 9-11 (copied), each one a thing the rule names
EP01_LIFTS = ["turns his pale face up toward him", "tilts his head back", "lifts his chin",
              "A low angle", "the lamp flame flickers across his pale cheek"]


def withheld_rule() -> str:
    hits = [r for r in plan_brief.PICTURE_RULES if "keeps back" in r]
    assert len(hits) == 1
    return hits[0]


def test_one_picture_rule_withholds_a_face_by_geometry():
    rule = withheld_rule()
    for form in ("from behind", "shoulder", "insert", "brim", "eye level"):
        assert form in rule


def test_the_rule_forbids_every_lift_ep01_commanded():
    rule = withheld_rule().lower()
    for said in ("lifts his chin", "tilts his head back", "looks up", "low angle", "cheek"):
        assert said in rule
    assert len(EP01_LIFTS) == 5


def test_the_withheld_figure_speaks_no_lip_line_and_is_lit_by_one_timed_verb():
    rule = withheld_rule()
    assert "no dialogue line" in rule and "narrator" in rule
    assert "answer" in rule and "At 00:02" in rule


def test_the_rule_reaches_the_rendered_brief():
    text = plan_brief.render({"picture_rules": plan_brief.PICTURE_RULES})
    assert "keeps back" in text[text.index(plan_brief.SECTIONS["picture_rules"]):]


def test_dialogue_words_max_is_the_ceiling_in_words():
    assert plan_brief.dialogue_words_max(0.35) == 108      # ch1: 0.279 speech -> 0.35
    assert plan_brief.dialogue_words_max(0.27) == 83       # ch2: 0.194 speech -> 0.27
    assert plan_gates.MAX_PLAN_WORDS == 310


def test_the_band_carries_the_word_budget_of_its_own_ceiling():
    band = plan_brief.band()
    assert band["dialogue_words_max"] == plan_brief.dialogue_words_max(band["dialogue_share"][1])
    assert band["dialogue_share"][1] == episode_spec.DIALOGUE_SHARE[1]
