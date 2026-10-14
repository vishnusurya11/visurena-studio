"""Step 01 is not done while a bound row wears a look the table no longer says (Jekyll HEL ep01, 2026-10-14).

refs.json was bound for chapter 1 with Enfield's look 'base'; the look table was
rebuilt afterwards (Hellsing cast v2) and now names his chapter-1 look
'frock_coat_topper'.  Step 01 was skipped ("output exists": the chapter stamp
held) and step 06's G-LOOK refused four setups with "rebind (step 01)" -- an
order the runner could not obey because the bind step called itself done.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.episode import step_01_bind as step
from studio import look_timeline as ltl
from studio.continuity_spec import CharacterLooks, Look, LookBook, Span, StoryTime


def book(tmp_path: Path, row_look: str) -> Path:
    (tmp_path / "refs").mkdir()
    rows = [{"entity_id": "richard_enfield", "kind": "character", "look": row_look},
            {"entity_id": "black_mail_house_door", "kind": "location"}]
    (tmp_path / "refs" / "refs.json").write_text(json.dumps({"refs": rows}), encoding="utf-8")
    card = CharacterLooks(base="frock_coat_topper", body="A man about town.",
                          looks={"frock_coat_topper": Look(made_by="base")},
                          timeline=[Span(look="frock_coat_topper", start=StoryTime(chapter=1),
                                         until=StoryTime(chapter=9))])
    table = LookBook(book="b", characters={"richard_enfield": card})
    ltl.path_of(tmp_path).write_text(json.dumps(table.model_dump(mode="json")), encoding="utf-8")
    return tmp_path


def test_a_stale_look_is_not_current(tmp_path):
    assert step.looks_current(book(tmp_path, "base"), 1) is False


def test_the_tables_look_is_current(tmp_path):
    assert step.looks_current(book(tmp_path, "frock_coat_topper"), 1) is True


def test_no_table_or_no_look_is_current(tmp_path):
    (tmp_path / "refs").mkdir()
    (tmp_path / "refs" / "refs.json").write_text(json.dumps({"refs": [{"entity_id": "x", "look": "base"}]}),
                                                 encoding="utf-8")
    assert step.looks_current(tmp_path, 1) is True


def test_done_needs_current_looks(tmp_path, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(step, "stamped", lambda b, n: True)
    ctx = SimpleNamespace(book_dir=book(tmp_path, "base"), number=1, extra=[])
    assert step.done(ctx) is False
