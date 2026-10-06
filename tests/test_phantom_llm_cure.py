"""The workhorse-tier rewrite for G-PHANTOM/G-LIGHT residue (ep18, 2026-10-05):
one `studio.llm.structured` call per setup through the `_agent` seam, validated
IN CODE with the gates' own measures (phantom_hits, has_light_direction, the
word floors), re-asked once with the refusal, then kept-original on a second
failure (default ESCALATE).  The FakeCaller is the only callable: no test may
call a paid API, and `guard_spend` lives inside the real caller these tests
never build."""
from __future__ import annotations

from types import SimpleNamespace

from studio import llm
from studio import plan_cures as pc
from studio import plan_gates as pg

NAMES = {"curate": "curate", "martian": "martians"}
FILL = ("The road runs straight between low brick walls and the mill chimney "
        "stands dark against a flat grey sky.")
GOOD_DESCRIBED = "Grey daylight comes in low from the LEFT, deep shadow past the wall. " \
    + " ".join([FILL] * 5)
GOOD_GEOMETRY = " ".join([FILL] * 4)


class FakeCaller:
    """The `_agent` seam of studio.llm.structured: canned answers, no network."""

    def __init__(self, answers):
        self.answers, self.prompts = list(answers), []

    def __call__(self, prompt, structured_output_model=None):
        self.prompts.append(prompt)
        return SimpleNamespace(structured_output=self.answers.pop(0))


def doc_of() -> dict:
    return {"setups": {"aperture": {
        "described": "The curate crouches by the aperture. " + " ".join([FILL] * 2),
        "geometry": "A Martian stands beyond the aperture."}}}


def test_a_valid_rewrite_updates_both_fields_and_clears_the_gates():
    good = pc.SetupRewrite(described=GOOD_DESCRIBED, geometry=GOOD_GEOMETRY)
    caller = FakeCaller([good])
    doc, uncured = pc.rewrite_setups(doc_of(), NAMES, set(), ["aperture"], caller=caller)
    assert uncured == []
    s = doc["setups"]["aperture"]
    assert pg.phantom_hits(s["described"], NAMES, set()) == []
    assert pg.phantom_hits(s["geometry"], NAMES, set()) == []
    assert pc.has_light_direction(s["described"])
    assert len(caller.prompts) == 1


def test_the_prompt_carries_the_banned_names_and_the_setup_text():
    good = pc.SetupRewrite(described=GOOD_DESCRIBED, geometry=GOOD_GEOMETRY)
    caller = FakeCaller([good])
    pc.rewrite_setups(doc_of(), NAMES, set(), ["aperture"], caller=caller)
    assert "curate" in caller.prompts[0] and "martian" in caller.prompts[0]
    assert "The curate crouches by the aperture." in caller.prompts[0]


def test_an_invalid_answer_is_reasked_once_then_the_original_is_kept():
    still_bad = pc.SetupRewrite(described="The curate waits. " + GOOD_DESCRIBED,
                                geometry=GOOD_GEOMETRY)
    caller = FakeCaller([still_bad, still_bad])
    doc, uncured = pc.rewrite_setups(doc_of(), NAMES, set(), ["aperture"], caller=caller)
    assert uncured == ["aperture"]
    assert doc["setups"]["aperture"] == doc_of()["setups"]["aperture"]  # original kept
    assert len(caller.prompts) == 2
    assert llm.REFUSED in caller.prompts[1]                 # the re-ask quotes the refusal
    assert "still names 'curate'" in caller.prompts[1]


def test_rewrite_faults_measure_like_the_gates():
    bad = pc.SetupRewrite(described="Hard morning sunlight. " + " ".join([FILL] * 2),
                          geometry="Short.")
    why = pc.rewrite_faults(bad, NAMES, set())
    assert any("light source" in w for w in why)            # a brightness is not a light
    assert any("described is under" in w for w in why)
    assert any("geometry is under" in w for w in why)
    assert pc.rewrite_faults(pc.SetupRewrite(described=GOOD_DESCRIBED,
                                             geometry=GOOD_GEOMETRY), NAMES, set()) == []


def test_the_round_is_capped_at_max_setups_calls():
    good = pc.SetupRewrite(described=GOOD_DESCRIBED, geometry=GOOD_GEOMETRY)
    caller = FakeCaller([good] * pc.MAX_SETUPS)
    many = {f"s{k}": {"described": "The curate waits.", "geometry": ""}
            for k in range(pc.MAX_SETUPS + 2)}
    doc, uncured = pc.rewrite_setups({"setups": many}, NAMES, set(), sorted(many), caller=caller)
    assert len(caller.prompts) == pc.MAX_SETUPS             # never more paid calls than the cap
    assert len(uncured) == 2
