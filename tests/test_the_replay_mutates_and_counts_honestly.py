"""The screenplay replay's mutations and counts are honest (wave 0 review, majors 4-6, findings 6, 12).

Before: deleting a prompt line kept the shot that still cited it, so a correct ORPHAN-REPLY (a prompt
"in none of the previous 3 lines or shown shots") had to stay silent; a narration or inner "?" line
counted as a prompt; `--mutate` read one plan (ep01 gives 2 orphan mutants, and 2 of 2 has a Wilson
low of 0.342 against A10's 0.7); an unreadable mutant counted as a miss; a fire that only moved its
line number counted as a hit; and nothing said how many APPROVED plans a check could read (ruling
section 7, binding).  Fixtures: tests/fixtures/craft (Jekyll ep01).  No render, no network, no spend."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.episode import screenplay_replay as sr

CRAFT = Path(__file__).parent / "fixtures" / "craft"
EP01 = CRAFT / "episodes" / "ep01"


def clean() -> dict:
    return json.loads((EP01 / "plan.json").read_text(encoding="utf-8"))


def paragraphs() -> list[str]:
    doc = json.loads((CRAFT / "source" / "chapters" / "ch_01.json").read_text(encoding="utf-8"))
    return [p["text"] for p in doc["paragraphs"]]


def cited(plan: dict) -> list[str]:
    return [s for shot in plan["shots"] for s in shot.get("source") or []]


def test_deleting_a_prompt_line_also_takes_the_shot_spans_that_show_it():
    mutant = sr.delete_prompt(clean(), 3)
    assert "Did you ever remark that door?" not in cited(mutant)
    assert "Did you ever remark that door? It holds a very odd story." not in [l["text"] for l in mutant["lines"]]
    assert len(cited(mutant)) == len(cited(clean())) - 1


def test_a_narrator_or_a_thought_never_prompts_a_reply():
    plan = {"lines": [{"kind": "inner", "speaker": "a", "text": "Who signed it?"},
                      {"kind": "dialogue", "speaker": "b", "text": "Nobody."},
                      {"kind": "narration", "speaker": "narrator", "text": "Will you come?"},
                      {"kind": "dialogue", "speaker": "b", "text": "Yes."},
                      {"kind": "dialogue", "speaker": "a", "text": "Shall we go?"},
                      {"kind": "tale", "speaker": "b", "text": "We went."}]}
    assert sr.prompt_lines(plan) == [4]


def counting(name: str, fn, needs: str = "plan") -> dict:
    return {name: sr.Check(name, fn, needs)}


def test_a_fire_that_only_moved_its_line_number_is_not_a_hit():
    moved = counting("orphan_reply", lambda plan, paras: [f"ORPHAN line {len(plan['lines'])}: same reply"])
    out = sr.recall(clean(), paragraphs(), moved)
    assert out["orphan_reply"]["k"] == 0


def test_a_new_fire_at_the_mutation_is_a_hit_even_when_an_old_one_left():
    def swapped(plan, paras):
        return ["ORPHAN line 20: the clean plan's"] if len(plan["lines"]) == 22 else ["ORPHAN line 3: the mutant's"]
    out = sr.recall(clean(), paragraphs(), counting("orphan_reply", swapped))
    assert out["orphan_reply"]["k"] == out["orphan_reply"]["n"] == 2


def test_an_unreadable_mutant_is_left_out_of_n_and_named():
    fires = counting("paragraph_hole", lambda plan, paras: ["HOLE"], "spans")
    plan = clean()
    for shot in plan["shots"]:
        if shot["index"] != 9:
            shot["source"] = []                 # one span only (shot 9, in a 40-word dialogue paragraph)
    out = sr.recall(plan, paragraphs(), fires)
    assert out["paragraph_hole"]["unreadable"] >= 1 and out["paragraph_hole"]["n"] == 0


def test_recall_pools_the_mutants_of_every_plan_named():
    every = counting("orphan_reply", lambda plan, paras: [l["text"] for l in plan["lines"]][:0] or
                     ([] if len(plan["lines"]) == len(clean()["lines"]) else ["ORPHAN"]), "spans")
    pooled = sr.pooled_recall([(clean(), paragraphs()), (clean(), paragraphs())], every)
    assert pooled["orphan_reply"]["n"] == 4 and pooled["orphan_reply"]["k"] == 4


def test_mutate_takes_several_plans():
    assert sr.mutate_targets(["a", "--mutate=2026:1,2026:3", "--mutate=2027:2"]) == [
        ("2026", 1), ("2026", 3), ("2027", 2)]


def test_the_summary_says_how_many_approved_plans_each_check_read():
    rows = [{"book": "2026_wotw", "number": 1, "readable": {"orphan_reply": False}, "fires": {"orphan_reply": None}},
            {"book": "2026_wotw", "number": 2, "readable": {"orphan_reply": True}, "fires": {"orphan_reply": []}},
            {"book": "2026_jekyll", "number": 1, "readable": {"orphan_reply": True},
             "fires": {"orphan_reply": ["x"]}}]
    check = counting("orphan_reply", lambda plan, paras: [], "spans")
    said = sr.summary(rows, check, approved=["2026_wotw:1", "2026_wotw:2"])["orphan_reply"]
    assert said.endswith("; approved: read 1 of 2, 0 fires")
    assert sr.summary(rows, check)["orphan_reply"].endswith("; approved: none named")


def test_a_replay_row_carries_its_episode_number(tmp_path):
    home = tmp_path / "episodes" / "ep01"
    home.mkdir(parents=True)
    (home / "plan.json").write_text(json.dumps(clean()), encoding="utf-8")
    assert sr.replay(tmp_path, home / "plan.json", {})["number"] == 1
