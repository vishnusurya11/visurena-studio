"""A character with no `design.sheet_prompt` gets its base sheet from the look table.

Jekyll's dossiers carry no `design` block (only WotW's designer wrote one), so
build_pack drew nothing and the one-sheet route (refs/characters/<who>/sheet.png,
the parent of every look, decision 2026-10-10) had no base to stand on.  The
look table already holds the base look's words; the sheet prompt is the base
drawn the way a fresh look is: its head layers first, the body, then the form.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.refs import build_pack, looks
from studio import look_timeline
from studio.continuity_spec import CharacterLooks, Layers, Look, LookBook, Markers, Span, StoryTime


def table(book: Path) -> None:
    card = CharacterLooks(base="base", body="A small, slight man.", looks={"base": Look(
        layers=Layers(hair="coarse black hair", face="black side-whiskers", headwear="a low felt hat",
                      top="a dark coat"), markers=Markers())},
        timeline=[Span(look="base", start=StoryTime(chapter=1))])
    path = look_timeline.path_of(book)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(LookBook(book=book.name, characters={"hyde": card}).model_dump_json(), encoding="utf-8")


def dossier(book: Path, who: str, design: dict | None = None) -> None:
    folder = book / "analysis" / "characters"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{who}.json").write_text(json.dumps({"id": who, "profile": {"design": design} if design else {}}),
                                        encoding="utf-8")


def test_a_designless_character_in_the_table_gets_a_base_sheet_job(tmp_path):
    table(tmp_path)
    dossier(tmp_path, "hyde")
    jobs = build_pack.all_jobs(tmp_path, ["characters"], [])
    assert [(j.entity, j.name) for j in jobs] == [("hyde", "sheet")]
    assert jobs[0].prompt.startswith("Coarse black hair. Black side-whiskers. A low felt hat.")
    assert "A small, slight man." in jobs[0].prompt and looks.FORM in jobs[0].prompt


def test_a_design_prompt_still_wins(tmp_path):
    table(tmp_path)
    dossier(tmp_path, "hyde", {"sheet_prompt": "the designer's words"})
    assert [j.prompt for j in build_pack.all_jobs(tmp_path, ["characters"], [])] == ["the designer's words"]


def test_a_designless_character_outside_the_table_draws_nothing(tmp_path):
    dossier(tmp_path, "poole")
    assert build_pack.all_jobs(tmp_path, ["characters"], []) == []
