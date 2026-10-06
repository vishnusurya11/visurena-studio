"""ep19 (2026-10-06): a cure bug wrote "the opened the Martian cylinder", "a
metallic the Martian handling-machine-crab", "three long the Martian
handling-machine" into the plan, and no gate saw it -- garble that reaches every
take prompt.  A determiner, one or two modifiers, then "the" and a capitalised
name is never English: G-ARTICLE refuses it, and the free cure drops that "the".
Function words ("beside the Martian") and verbs ("occupies the") are left alone.  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_cures, plan_gates


def ep(text):
    return SimpleNamespace(shots=[SimpleNamespace(index=0, frame=text, motion="", at_rest="", end="")],
                           setups={})


def test_a_content_word_before_the_name_is_garble():
    assert plan_gates.article_faults(ep("while the opened the Martian cylinder steams"))
    assert plan_gates.article_faults(ep("a metallic the Martian handling-machine-crab"))
    assert plan_gates.article_faults(ep("a colossal hollow the Martian dug"))


def test_function_words_before_the_name_are_english():
    assert not plan_gates.article_faults(ep("the curate beside the Martian cylinder and the Thames"))


def test_a_verb_before_the_name_is_english():
    """ep19's first draft of this gate refused 'the pump occupies the ...' and
    'broken crockery marks the ...' -- a verb, not a stray article."""
    assert not plan_gates.article_faults(ep("the pump occupies the Kitchen; broken crockery marks the Pit"))
    assert not plan_gates.article_faults(ep("plaster dust crosses the Martian cylinder"))


def test_delivered_plans_read_as_english():
    """ep10 and ep18 shipped these; the gate run over the last twelve plans found them."""
    assert not plan_gates.article_faults(ep("her filling the Lantern with oil"))
    assert not plan_gates.article_faults(ep("the narrator nearest the Curate"))
    assert not plan_gates.article_faults(ep("his horse fill the Upper third; the barrow cross the Road"))
    assert not plan_gates.article_faults(ep("the porch the LEFT third, the grey sky the TOP band"))


def test_the_cure_drops_the_stray_article():
    doc = {"shots": [{"index": 0, "frame": "three long the Martian handling-machine arms", "motion": "",
                      "at_rest": "", "end": ""}], "setups": {}}
    assert plan_cures.drop_stray_articles(doc)["shots"][0]["frame"] == \
        "three long Martian handling-machine arms"
    assert plan_cures.cure_for("G-ARTICLE shot 0: 'long the Martian'") == "drop_stray_articles"


def test_a_noun_before_the_name_gets_a_comma_not_a_cut():
    """WotW ep02: 'under the porch the Narrator' is a missing comma; dropping
    'the' would write 'the porch Narrator'."""
    doc = {"shots": [{"index": 0, "frame": "far off under the porch the Narrator waits", "motion": "",
                      "at_rest": "", "end": ""}], "setups": {}}
    assert plan_cures.drop_stray_articles(doc)["shots"][0]["frame"] == \
        "far off under the porch, the Narrator waits"
