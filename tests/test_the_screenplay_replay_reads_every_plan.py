"""A3, the screenplay replay (craft ruling 2026-10-21, wave 0): ONE read-only harness for every
screenplay check the ruling adopts (G-MUTE, G-STOLEN, ORPHAN-REPLY, PARAGRAPH-HOLE, G-REVEAL).
It prints how many plans each check could READ, the fires per plan, and the recall on code-made
mutations of ep01.  A plan whose shots cite no span of its chapter is "unreadable", never "0 fires".
The checks themselves land in wave 1, so this test injects doubles: what is under test is the
harness's contract (reading, counting, mutating, recall), never a detector's judgment.
Fixtures: Jekyll ep01 plan.json, placed.json and ch_01.json, copied by name into tests/fixtures/craft.
No render, no network, no spend."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.episode import screenplay_replay as sr

CRAFT = Path(__file__).parent / "fixtures" / "craft"
EP01 = CRAFT / "episodes" / "ep01"


def clean() -> dict:
    return json.loads((EP01 / "plan.json").read_text(encoding="utf-8"))


def paragraphs() -> list[str]:
    doc = json.loads((CRAFT / "source" / "chapters" / "ch_01.json").read_text(encoding="utf-8"))
    return [p["text"] for p in doc["paragraphs"]]


def orphan_double(plan: dict, paras: list[str]) -> list[str]:
    """Oracle double: a reply whose line before it in the CLEAN ep01 is gone from this plan."""
    texts = [l["text"] for l in plan["lines"]]
    gone = {l["text"] for l in clean()["lines"]} - set(texts)
    before = {b["text"]: a["text"] for a, b in zip(clean()["lines"], clean()["lines"][1:])}
    return [f"line {k}" for k, t in enumerate(texts) if before.get(t) in gone]


def stolen_double(plan: dict, paras: list[str]) -> list[str]:
    """Oracle double: a narration line that a cast member spoke in the CLEAN ep01."""
    spoken = {l["text"] for l in clean()["lines"] if l["speaker"] != "narrator"}
    return [f"line {l['index']}" for l in plan["lines"] if l["kind"] == "narration" and l["text"] in spoken]


DOUBLES = {"orphan_reply": sr.Check("orphan_reply", orphan_double, "spans"),
           "stolen_line": sr.Check("stolen_line", stolen_double, "spans")}


def book_with(tmp_path: Path, plans: dict[int, dict]) -> Path:
    """A book of these plans, each with ep01's chapter and placed.json."""
    for n, plan in plans.items():
        home = tmp_path / "episodes" / f"ep{n:02d}"
        home.mkdir(parents=True)
        (home / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        shutil.copy(EP01 / "placed.json", home / "placed.json")
        shutil.copy(CRAFT / "source" / "chapters" / "ch_01.json", tmp_path / f"ch_{n:02d}.json")
    (tmp_path / "source" / "chapters").mkdir(parents=True)
    for n in plans:
        shutil.move(tmp_path / f"ch_{n:02d}.json", tmp_path / "source" / "chapters" / f"ch_{n:02d}.json")
    return tmp_path


def planted() -> dict:
    """ep01 with one orphan reply (line 3, Enfield's question, deleted) and one stolen line (then
    line 16, Enfield's "It was a man of the name of Hyde.", moved into narration)."""
    return sr.quote_to_narration(sr.delete_line(clean(), 3), 16)


def no_spans() -> dict:
    plan = clean()
    for shot in plan["shots"]:
        shot["source"] = []
    return plan


# ---- the red row: both plants reported, the span-less plan unreadable -----------------------------

def test_a_planted_orphan_reply_and_stolen_line_are_both_reported(tmp_path):
    book = book_with(tmp_path, {1: planted()})
    row = sr.replay(book, book / "episodes" / "ep01" / "plan.json", DOUBLES)
    assert row["fires"]["orphan_reply"] == ["line 3"]          # "Indeed? And what was that?", now line 3
    assert row["fires"]["stolen_line"] == ["line 16"]


def test_a_plan_with_no_source_spans_is_unreadable_never_zero_fires(tmp_path):
    book = book_with(tmp_path, {1: clean(), 2: no_spans()})
    rows = [sr.replay(book, p, DOUBLES) for p in sr.plan_paths(book)]
    assert rows[0]["readable"] == {"orphan_reply": True, "stolen_line": True}
    assert rows[1]["readable"] == {"orphan_reply": False, "stolen_line": False}
    assert rows[1]["fires"] == {"orphan_reply": None, "stolen_line": None}
    assert sr.summary(rows, DOUBLES)["orphan_reply"] == "orphan_reply: read 1 of 2 plans, 0 fires on 0 plans"


def test_a_check_whose_code_is_not_built_says_so():
    check = sr.Check("silent_speaker", "studio.screenplay_grammar:no_such_check", "plan")
    assert sr.runner(check) is None
    assert sr.summary([{"readable": {}, "fires": {}}], {"silent_speaker": check})["silent_speaker"] == \
        "silent_speaker: not built; 0 of 1 plans readable"


# ---- reading a plan -----------------------------------------------------------------------------

def test_a_span_resolves_to_its_list_index():
    assert sr.span_paragraph("Did you ever remark that door?", paragraphs()) == 5     # n 6


def test_a_plan_reads_when_one_span_lands_in_its_chapter():
    assert sr.readable(clean(), paragraphs(), "spans") is True
    assert sr.readable(no_spans(), paragraphs(), "spans") is False
    assert sr.readable(clean(), [], "plan") is True
    assert sr.readable(clean(), [], "chapter") is False
    assert sr.readable({"lines": []}, paragraphs(), "plan") is False


# ---- the code-made mutations of ep01 --------------------------------------------------------------

def test_delete_line_renumbers_and_leaves_the_rest():
    plan = sr.delete_line(clean(), 3)
    assert len(plan["lines"]) == 21 and plan["lines"][3]["text"] == "Indeed? And what was that?"
    assert [l["index"] for l in plan["lines"]] == list(range(21))


def test_quote_to_narration_gives_the_line_to_the_narrator_word_for_word():
    line = sr.quote_to_narration(clean(), 16)["lines"][16]
    assert (line["kind"], line["speaker"]) == ("narration", "narrator")
    assert line["text"] == "I want to ask the name of that man who walked over the child."


def test_drop_paragraph_takes_its_spans_and_its_lines():
    plan = sr.drop_paragraph(clean(), paragraphs(), 5)
    assert not any(sr.span_paragraph(s, paragraphs()) == 5 for shot in plan["shots"] for s in shot["source"])
    assert "Did you ever remark that door? It holds a very odd story." not in [l["text"] for l in plan["lines"]]


def test_ep01_mutants_name_the_check_each_should_wake():
    kinds = [m["expect"] for m in sr.mutants(clean(), paragraphs())]
    assert kinds.count("orphan_reply") == 2              # the prompts at lines 3 and 4
    assert kinds.count("stolen_line") == 8               # every dialogue line
    assert kinds.count("paragraph_hole") >= 1


def test_recall_counts_a_mutant_only_when_its_check_fires_more_than_on_the_clean_plan():
    out = sr.recall(clean(), paragraphs(), DOUBLES)
    assert out["orphan_reply"]["k"] == out["orphan_reply"]["n"] == 2
    assert out["stolen_line"]["k"] == out["stolen_line"]["n"] == 8
    assert out["stolen_line"]["wilson_low"] >= 0.6
    assert "paragraph_hole" not in out                    # no check registered for it here


# ---- the audience LOG rows (P6), printed here and never in the plan battery ---------------------------

def test_the_middle_node_is_the_longest_window_with_no_node_on_ep01():
    placed = json.loads((EP01 / "placed.json").read_text(encoding="utf-8"))
    assert sr.middle_node(clean(), placed) == (62.7, 86.8, 24.1)


def test_the_bed_floor_lists_the_plain_spans_in_the_intro_or_over_15_s_on_ep01():
    placed = json.loads((EP01 / "placed.json").read_text(encoding="utf-8"))
    assert sr.bed_floor(clean(), placed) == [(4.2, 28.5, 24.4), (66.1, 83.8, 17.7)]


def test_a_placed_json_that_no_longer_matches_its_plan_is_not_measured_never_a_crash(tmp_path):
    book = book_with(tmp_path, {1: clean()})
    placed = json.loads((EP01 / "placed.json").read_text(encoding="utf-8"))
    placed["shots"] = placed["shots"][1:]                       # an older cut without shot 0
    (book / "episodes" / "ep01" / "placed.json").write_text(json.dumps(placed), encoding="utf-8")
    assert sr.log_rows(book / "episodes" / "ep01" / "plan.json").startswith("LOG not measured (")
    assert sr.log_rows(EP01 / "plan.json").startswith("LOG middle node: longest window with no node 24.1 s")
