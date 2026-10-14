"""A drawn book's title card is drawn on its own drawer (Jekyll Hellsing remake, 2026-10-14).

`series_title.base_art` asked `book_title.plate_request`, which knows two looks --
photoreal Krea2 and the house Krea2 + LoRA -- and read the look from ep01's plan.
Jekyll's ep01 card was baked photoreal on 2026-10-12; after the book switched to
Hellsing gothic anime, a re-bake would have been photoreal again (ep01 set aside:
no plan) or WotW's painted look.  A book whose refs/look.json files a drawn
drawer now draws its card's art there, from the `title` entity's tags when the
book files them (NoobAI draws tags, not prose), else from motif.txt.  The card's
animation stops quoting WotW: no heath, no metallic hoot, no red light.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from scripts.episode import series_title as st

RECIPE = {
    "workflow": "image_sdxl_t2i_2lora_hires_visurena",
    "ckpt": "NoobAI-XL-v1.1.safetensors",
    "loras": [],
    "lead": "masterpiece, hellsing ultimate ova",
    "negative": "lowres, text",
    "frames": {"locations": {"tags": "wide shot", "negative": "1boy, people"}},
    "entities": {"title": {"tags": "night street, gas lamp, fog, small figure in a felt hat",
                           "negative": "letters"}},
}


def book(tmp_path: Path, recipe: dict | None = RECIPE) -> Path:
    root = tmp_path / "library" / "123_book"
    (root / "refs").mkdir(parents=True)
    (root / "title").mkdir()
    said = {"look": "anime_gothic", "lead": "Hand-drawn 2D gothic anime."}
    if recipe is not None:
        said["refs"] = recipe
    (root / "refs" / "look.json").write_text(json.dumps(said), encoding="utf-8")
    (root / "title" / "motif.txt").write_text("a foggy London by-street at night", encoding="utf-8")
    return root


def fake(tmp_path: Path, calls: list):
    def run(workflow, values, **kw):
        calls.append((workflow, values))
        out = tmp_path / f"made_{len(calls)}.png"
        Image.new("RGB", (8, 8)).save(out)
        return [out]
    return run


def wire(monkeypatch, tmp_path, calls):
    monkeypatch.setattr(st, "run", fake(tmp_path, calls))
    monkeypatch.setattr(st, "run_text", lambda *a, **k: "NONE")
    monkeypatch.setattr(st, "stage_image", lambda p: str(p))


def test_a_drawn_book_draws_its_card_art_on_its_own_drawer(tmp_path, monkeypatch):
    calls: list = []
    wire(monkeypatch, tmp_path, calls)
    out = st.base_art(book(tmp_path) / "title")
    assert out.name == "series_base.png" and out.exists()
    workflow, values = calls[0]
    assert workflow == RECIPE["workflow"] and values["ckpt_name"] == RECIPE["ckpt"]
    assert values["prompt"].startswith("masterpiece, hellsing ultimate ova")
    assert "small figure in a felt hat" in values["prompt"]           # the book's title tags, not the prose
    assert "1boy" not in values["negative_prompt"]                   # a place's people ban never reaches the card
    assert (values["width"], values["height"]) == (1024, 1024)


def test_a_drawn_book_without_title_tags_draws_its_motif(tmp_path, monkeypatch):
    calls: list = []
    wire(monkeypatch, tmp_path, calls)
    recipe = {k: v for k, v in RECIPE.items() if k != "entities"}
    st.base_art(book(tmp_path, recipe) / "title")
    assert "a foggy London by-street at night" in calls[0][1]["prompt"]


def test_the_card_motion_names_no_other_book():
    said = st.motion_prompt(["THE BOOK", "EPISODE 1", "THE DOOR"]).lower()
    for wotw in ("heath", "metallic hoot", "red light"):
        assert wotw not in said
    assert '"episode 1"' in said
