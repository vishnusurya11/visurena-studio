"""A9: G-STOLEN, advisory (craft ruling 2026-10-21, wave 1).

A narration line that shares 3 or more content bigrams with a quoted span a cast member speaks in the
chapter has taken his words: Jekyll ep01 line 12 ("... Enfield named the place Black Mail House", 4
bigrams of Enfield's paragraph 9) and line 14 ("... the more a thing looked like Queer Street, the less
he asked", 5 of his paragraph 13).  A bigram of two stopwords is dropped; a first-person narrator's
own quotes are his.  The cure is NOT adopted (T1): the row only reports.  The replay's stolen-line
mutants are only lines the detector could see moved (wave 0 review, finding 7).
Fixtures: tests/fixtures/craft (Jekyll ep01 plan.json, ch_01.json).  No render, no network, no spend."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.episode import screenplay_replay as sr
from studio import quotes, story_layer as sl

CRAFT = Path(__file__).parent / "fixtures" / "craft"


def plan() -> dict:
    return json.loads((CRAFT / "episodes" / "ep01" / "plan.json").read_text(encoding="utf-8"))


def paragraphs() -> list[str]:
    doc = json.loads((CRAFT / "source" / "chapters" / "ch_01.json").read_text(encoding="utf-8"))
    return [p["text"] for p in doc["paragraphs"]]


def test_ep01_fires_on_lines_12_and_14_only():
    fires = sl.stolen_lines(plan(), paragraphs())
    assert [f.split(":")[0] for f in fires] == ["G-STOLEN line 12", "G-STOLEN line 14"]
    assert "4 content bigrams" in fires[0] and "paragraph 9" in fires[0]
    assert "5 content bigrams" in fires[1] and "paragraph 13" in fires[1]


def test_a_stopword_pair_is_no_bigram():
    assert ("the", "of") not in sl.content_bigrams("the of the and")
    assert ("queer", "street") in sl.content_bigrams("like Queer Street")


def test_quotes_carry_their_paragraph_and_speaker():
    spans = quotes.quote_spans(paragraphs())
    door = next(s for s in spans if s[1].startswith("Did you ever remark that door?"))
    assert door[0] == 5
    assert quotes.quote_spans(["“Yes,” said I, “I saw it.”"])[0] == (0, "Yes,", "i")
    assert quotes.quote_spans(["“Well,” said Mr. Utterson."])[0][2] == "utterson"


def test_a_first_person_narrators_own_quote_is_not_stolen():
    own = {"lines": [{"index": 0, "kind": "narration", "speaker": "narrator",
                      "text": "I saw the cylinder lying in the sand pit."}]}
    paras = ["“I saw the cylinder lying in the sand pit,” said I."]
    assert sl.stolen_lines(own, paras) == []


def test_the_replay_mutates_only_the_lines_the_detector_could_see():
    kinds = [m["name"] for m in sr.mutants(plan(), paragraphs()) if m["expect"] == "stolen_line"]
    assert len(kinds) == 6 and "quote 4 into narration" not in kinds and "quote 20 into narration" not in kinds
    assert sr.recall(plan(), paragraphs(), {"stolen_line": sr.CHECKS["stolen_line"]})["stolen_line"]["k"] == 6


def test_plan_check_prints_it_as_advice():
    import inspect
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
    import plan_check
    assert "stolen_lines" in inspect.getsource(plan_check.shadow_rows)
    assert "return 0" in inspect.getsource(plan_check.craft_shadow_gate)
