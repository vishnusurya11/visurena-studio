"""Every refs picture is drawn in the BOOK's look, never the house look.

Owner 2026-10-11 ("book look, not house look") fixed the title plates; the refs
drawers -- the base sheet (build_pack), a fresh look (looks.py) and a place
master (places.py) -- still hardwired WotW's Krea2 + Cinematic LoRA look and
`refs_pack.styled`.  Jekyll (owner 2026-10-12, style A) is photoreal gothic:
Krea2 turbo with no LoRA, led by the book's own words.  A book declares it in
`library/<book>/refs/look.json`; without one the house look stays.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import book_look, refs_pack

LEAD = "Cinematic live-action photograph, photoreal. A Victorian gothic film still: fog, gaslight, deep shadow. "
TAIL = " No text, no lettering, no signage, no watermark."


def declare(book: Path) -> Path:
    (book / "refs").mkdir(parents=True, exist_ok=True)
    (book / "refs" / "look.json").write_text(json.dumps(
        {"look": "photoreal", "lead": LEAD, "tail": TAIL, "decision": "2026-10-12 style A", "by": "owner"}),
        encoding="utf-8")
    return book


def test_no_declaration_keeps_the_house_look(tmp_path):
    workflow, values = book_look.t2i(tmp_path, "a man", width=1536, height=1024, seed=7, prefix="p")
    assert workflow == refs_pack.T2I
    assert values == {"prompt": refs_pack.styled("a man"), "seed": 7, "width": 1536, "height": 1024,
                      "filename_prefix": "p"}


def test_a_photoreal_book_draws_on_krea2_turbo_without_the_lora(tmp_path):
    workflow, values = book_look.t2i(declare(tmp_path), "a man", width=1536, height=1024, seed=7, prefix="p")
    assert workflow == "image_krea2_turbo_t2i"
    assert values["prompt"] == LEAD + "a man" + TAIL
    assert (values["enable_lora"], values["refine_prompt"], values["megapixels"]) == (False, False, 2)
    assert values["aspect_ratio"] == "3:2 (Photo)" and values["seed"] == 7


@pytest.mark.parametrize("w,h,said", [(1024, 1024, "1:1 (Square)"), (1280, 720, "16:9 (Widescreen)"),
                                      (1536, 1024, "3:2 (Photo)"), (768, 1024, "3:4 (Portrait Standard)")])
def test_the_nearest_aspect_is_asked(w, h, said):
    assert book_look.aspect_for(w, h) == said


def test_a_malformed_declaration_is_the_house_look(tmp_path):
    (tmp_path / "refs").mkdir()
    (tmp_path / "refs" / "look.json").write_text("{not json", encoding="utf-8")
    assert book_look.declared(tmp_path) == {}


def capture(monkeypatch, module, name="run"):
    seen = []

    def fake(workflow, values, *a, **k):
        seen.append((workflow, values))
        out = Path(values.get("filename_prefix", "x").replace("/", "_") + ".png")
        return [out]
    monkeypatch.setattr(module, name, fake)
    return seen


def test_the_base_sheet_is_drawn_in_the_books_look(tmp_path, monkeypatch):
    from scripts.refs import build_pack
    seen = capture(monkeypatch, build_pack)
    monkeypatch.setattr(build_pack.shutil, "copyfile", lambda a, b: None)
    job = refs_pack.Job("characters", "hyde", "sheet", refs_pack.T2I, "a small man", 1536, 1024)
    build_pack.draw(declare(tmp_path), job)
    assert seen[0][0] == "image_krea2_turbo_t2i" and seen[0][1]["prompt"].startswith(LEAD)
    assert seen[0][1]["seed"] == refs_pack.seed_for("refs/characters/hyde/sheet.png")


def test_a_fresh_look_is_drawn_in_the_books_look(tmp_path, monkeypatch):
    from scripts.refs import looks
    from studio import comfy
    seen = capture(monkeypatch, comfy)
    monkeypatch.setattr("shutil.copyfile", lambda a, b: None)
    looks.comfy_draws(declare(tmp_path))["fresh"]("a bald man", tmp_path / "x.png", 3)
    assert seen[0][0] == "image_krea2_turbo_t2i" and seen[0][1]["prompt"] == LEAD + "a bald man" + TAIL


def test_a_place_master_is_drawn_in_the_books_look(tmp_path, monkeypatch):
    from scripts.refs import places
    from studio import comfy
    seen = capture(monkeypatch, comfy)
    monkeypatch.setattr(places.shutil, "copyfile", lambda a, b: None)
    places.krea(declare(tmp_path))("a blistered door", tmp_path / "refs" / "locations" / "door" / "wide.png")
    assert seen[0][0] == "image_krea2_turbo_t2i" and seen[0][1]["prompt"] == LEAD + "a blistered door" + TAIL
    row = json.loads((tmp_path / "refs" / "pack.jsonl").read_text(encoding="utf-8"))
    assert row["workflow"] == "image_krea2_turbo_t2i"


def test_a_title_plate_opens_with_the_declared_lead(tmp_path):
    from studio import book_title
    assert book_title.lead_for(declare(tmp_path), "") == LEAD
