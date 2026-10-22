"""A10 ORPHAN-REPLY and A11 PARAGRAPH-HOLE, shadow rows (craft ruling 2026-10-21, wave 1).

ORPHAN-REPLY is the judges' probe made the one implementation: on Jekyll ep01 it fires on line 20 only
("With all my heart, Richard." answers Enfield's "Let us make a bargain never to refer to this again",
which the plan cut), and on each code-made deletion of a prompt with the spans that show it.
PARAGRAPH-HOLE lists the dialogue paragraphs (40 words or more) whose speech the plan leaves mostly
unsaid: ep01's list holds index 9 ("the very pink of the proprieties"), 21 ("I can't describe him") and
26 (the bargain), each row citing the list index and the paragraph's first 8 verbatim words, weighted
up when chapter 2 uses the dropped words.  Both only report.
Fixtures: tests/fixtures/craft (Jekyll ep01 plan.json, ch_01.json, ch_02.json).  No spend."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.episode import screenplay_replay as sr
from studio import screenplay_checks as sc

CRAFT = Path(__file__).parent / "fixtures" / "craft"


def plan() -> dict:
    return json.loads((CRAFT / "episodes" / "ep01" / "plan.json").read_text(encoding="utf-8"))


def chapter(n: int) -> list[str]:
    doc = json.loads((CRAFT / "source" / "chapters" / f"ch_{n:02d}.json").read_text(encoding="utf-8"))
    return [p["text"] for p in doc["paragraphs"]]


# ---- ORPHAN-REPLY -----------------------------------------------------------------------------------

def test_ep01_fires_on_line_20_only():
    fires = sc.orphan_replies(plan(), chapter(1))
    assert len(fires) == 1 and fires[0].startswith('ORPHAN-REPLY line 20: "With all my heart, Richard."')
    assert "paragraph 26" in fires[0]


def test_a_prompt_said_in_the_lines_before_pairs_the_reply():
    lines = [{"index": 0, "kind": "dialogue", "speaker": "e", "shot": 0,
              "text": "Let us make a bargain never to refer to this again."},
             {"index": 1, "kind": "dialogue", "speaker": "u", "shot": 1, "text": "With all my heart, Richard."}]
    assert sc.orphan_replies({"lines": lines, "shots": []}, chapter(1)) == []


def test_a_prompt_shown_on_a_shot_pairs_the_reply():
    lines = [{"index": 0, "kind": "dialogue", "speaker": "u", "shot": 1, "text": "With all my heart, Richard."}]
    shots = [{"index": 1, "source": ["Let us make a bargain never to refer to this again."]}]
    assert sc.orphan_replies({"lines": lines, "shots": shots}, chapter(1)) == []


def test_both_ep01_prompt_deletions_are_caught():
    out = sr.recall(plan(), chapter(1), {"orphan_reply": sr.CHECKS["orphan_reply"]})["orphan_reply"]
    assert out["k"] == out["n"] == 2 and out["unreadable"] == 0


# ---- PARAGRAPH-HOLE ---------------------------------------------------------------------------------

def rows() -> dict[int, dict]:
    return {h["index"]: h for h in sc.holes(plan(), chapter(1), chapter(2))}


def test_ep01s_holes_include_the_rulings_three_with_their_verbatim_words():
    found = rows()
    assert {9, 21, 26} <= set(found)
    assert any("pink of the proprieties" in s for s in found[9]["sentences"])
    assert any("I can’t describe him" in s for s in found[21]["sentences"])
    assert any("Let us make a bargain" in s for s in found[26]["sentences"])
    assert found[26]["words"] == "Mr. Utterson sighed deeply but said never a"


def test_a_row_cites_the_list_index_and_eight_words():
    said = sc.paragraph_holes(plan(), chapter(1), chapter(2))
    assert any(r.startswith("PARAGRAPH-HOLE paragraph 21 (94 of 94 quoted words unreached") and
               r.endswith('"“He is not easy to describe. There is"') for r in said)


def test_the_next_chapter_weighs_a_row_up():
    assert rows()[21]["weight"] > 1.0
    assert {h["index"]: h["weight"] for h in sc.holes(plan(), chapter(1))}[21] == 1.0


def test_a_paragraph_the_lines_keep_is_no_hole():
    assert 9 not in {h["index"] for h in sc.holes({"lines": [], "shots": [{"index": 0, "source": [
        s for s in sc.sentences(chapter(1)[9])]}]}, chapter(1))}


def test_plan_check_prints_both_as_advice():
    import inspect
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
    import plan_check
    source = inspect.getsource(plan_check.shadow_rows)
    assert "orphan_replies" in source and "paragraph_holes" in source
