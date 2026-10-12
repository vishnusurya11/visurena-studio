"""The look writers never file text G-ROWTEXT refuses (Jekyll ep01, 2026-10-12).

Utterson's authored head said 'a face that is never lighted by a smile' and his
look-table body 'walking through London' with no pace.  head_author and the look
table wrote both without running the row lint, so G-ROWTEXT (pack_refs) refused
the row at bind time, step 01 of a live episode, about 3 h in.  The writers now
cure first (stillness table, negation affirmatives, the pace append) and REFUSE
whatever the cures leave, every fault listed, before writing anything.
"""
from __future__ import annotations

import json

import pytest

from scripts.refs import looks_table
from studio import head_author, look_timeline, row_lint
from studio.continuity_spec import CharacterLooks, Layers, Look, Markers

NEVER = "a face that is never lighted by a smile"
WALK = "He is walking through London."


def test_the_fixture_texts_are_what_g_rowtext_refuses():
    assert any("L1" in f for f in row_lint.row_faults(NEVER))
    assert any("L8" in f for f in row_lint.row_faults(WALK))


def test_a_never_smile_becomes_its_affirmative():
    assert row_lint.cure_row_text(NEVER) == "a face that is unsmiling"


def test_a_cure_is_idempotent_and_clean():
    once = row_lint.cure_row_text(f"{WALK} A lean man with {NEVER}.")
    assert row_lint.cure_row_text(once) == once and row_lint.row_faults(once) == []


def test_a_negation_with_no_affirmative_is_left_to_refuse():
    assert row_lint.cure_row_text("a coat that is not new") == "a coat that is not new"


def looks(body: str, face: str) -> CharacterLooks:
    base = Look(made_by="base", markers=Markers(top="coat"),
                layers=Layers(hair="Lank fair hair.", face=face, headwear="A bowler hat.", top="A dark coat."))
    return CharacterLooks(base="base", body=body, looks={"base": base})


def test_cured_looks_carry_the_affirmative_and_the_pace():
    card = look_timeline.cured(looks(WALK, f"clean-shaven, {NEVER}"))
    assert look_timeline.text_faults("utterson", card) == []
    assert "unsmiling" in card.looks["base"].layers.face and "walking pace" in card.body


def test_text_faults_name_the_character_and_the_look():
    faults = look_timeline.text_faults("utterson", looks("A man.", "a face that is not handsome"))
    assert faults == ["utterson [base]: L1 NEGATION: ['not']"]


def test_build_writes_the_cured_table(tmp_path, monkeypatch):
    monkeypatch.setattr(looks_table, "table_for", lambda book, who, _agent=None: looks(WALK, NEVER))
    looks_table.build(tmp_path, ["utterson"])
    card = look_timeline.load(tmp_path).characters["utterson"]
    assert row_lint.row_faults(look_timeline.look_words(card, "base")) == []


def test_build_refuses_an_uncurable_row_before_it_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(looks_table, "table_for", lambda book, who, _agent=None: looks("A man.", "not handsome"))
    with pytest.raises(SystemExit, match=r"(?s)G-ROWTEXT.*utterson \[base\]: L1 NEGATION"):
        looks_table.build(tmp_path, ["utterson"])
    assert not look_timeline.path_of(tmp_path).exists()


TEXT = {1: "a lean, long, dusty, dreary man whose face was never lighted by a smile"}
UTTERSON = {"words": f"A lean man, with {NEVER}. Lank fair hair; clean-shaven; a black bowler hat.",
            "sources": [{"chapter": 1, "quote": "face was never lighted by a smile"}]}


def book(tmp_path, physical: str, heads: dict):
    (tmp_path / "analysis" / "characters").mkdir(parents=True)
    (tmp_path / "analysis" / "chapters").mkdir()
    for n, text in TEXT.items():
        (tmp_path / "analysis" / "chapters" / f"ch_{n:02d}.json").write_text(json.dumps({"text": text}), encoding="utf-8")
    for who in heads:
        (tmp_path / "analysis" / "characters" / f"{who}.json").write_text(
            json.dumps({"id": who, "profile": {"physical": physical}}), encoding="utf-8")
    (tmp_path / "analysis" / "heads.json").write_text(json.dumps(heads), encoding="utf-8")
    return tmp_path


def physical_of(root, who: str) -> str:
    card = json.loads((root / "analysis" / "characters" / f"{who}.json").read_text(encoding="utf-8"))
    return card["profile"]["physical"]


def test_apply_writes_a_cured_head(tmp_path):
    root = book(tmp_path, WALK, {"utterson": UTTERSON})
    head_author.apply(root, rows=[])
    said = physical_of(root, "utterson")
    assert row_lint.row_faults(said) == [] and "unsmiling" in said and "walking pace" in said


def test_a_re_run_still_finds_the_cured_head(tmp_path):
    root = book(tmp_path, WALK, {"utterson": UTTERSON})
    head_author.apply(root, rows=[])
    head_author.apply(root, rows=[])
    assert physical_of(root, "utterson").count("bowler") == 1


def test_apply_refuses_an_uncurable_physical_before_it_writes(tmp_path):
    root = book(tmp_path, "A coat that is not new.", {"utterson": UTTERSON})
    with pytest.raises(SystemExit, match=r"utterson: G-ROWTEXT L1 NEGATION"):
        head_author.apply(root, rows=[])
    assert physical_of(root, "utterson") == "A coat that is not new."
