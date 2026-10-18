"""A drawn book whose refs drawer is Krea2 draws in PROSE, the Prism way (Jekyll Kawajiri, 2026-10-18).

The owner chose Kawajiri Madhouse noir drawn by Krea2 (POC docs/audit/2026-10-18_jekyll_kawajiri_poc/,
style card prism/styles/anime_kawajiri_madhouse_90s.json).  The drawn drawer knew one shape -- an SDXL
checkpoint fed comma tags, a negative and its own bucket sizes -- so a look.json naming Krea2 would have
posted SDXL keys to a Krea2 graph.  Krea2 runs at cfg 1 (a negative does nothing) and reads sentences:
the POC's words were the card's style, the avoid list said positively, the subject, the camera, the
card's recap; 8 steps, 1 MP, no prompt refiner, no LoRA; a sheet 2:3 portrait, one front figure.
"""
from __future__ import annotations

import json
from pathlib import Path

from studio import book_look

KREA = {
    "workflow": "image_krea2_turbo_t2i",
    "lead": "Hand-painted 1990s cel animation, as in Ninja Scroll. Flat unblended colour on the figures.",
    "recap": "Rendered throughout as hand-painted 1990s cel animation.",
    "megapixels": 1,
    "frames": {"characters": {"tags": "Full-length front view at eye level, the lone figure centred."},
               "locations": {"tags": "Wide establishing shot at eye level."}},
    "entities": {"edward_hyde": {"tags": "Mr Hyde, a small sinister young man, grins."}},
}


def declare(book: Path, refs: dict = KREA) -> Path:
    (book / "refs").mkdir(parents=True, exist_ok=True)
    said = {"look": "anime_kawajiri_noir", "lead": "a Qwen line", "take": "Madhouse noir cel", "refs": refs}
    (book / "refs" / "look.json").write_text(json.dumps(said), encoding="utf-8")
    return book


def test_the_drawer_is_krea2(tmp_path):
    assert book_look.drawer(declare(tmp_path)) == "image_krea2_turbo_t2i"


def test_a_sheet_is_prose_style_first_recap_last(tmp_path):
    workflow, v = book_look.t2i(declare(tmp_path), "A stout inspector. Character reference sheet on grey: front, back.",
                                width=1536, height=1024, seed=7, prefix="p", kind="characters", entity="newcomen")
    assert workflow == "image_krea2_turbo_t2i"
    assert v["prompt"] == ("Hand-painted 1990s cel animation, as in Ninja Scroll. Flat unblended colour on the "
                           "figures. A stout inspector. Full-length front view at eye level, the lone figure "
                           "centred. Rendered throughout as hand-painted 1990s cel animation.")


def test_a_sheet_posts_krea2_keys_never_sdxl_keys(tmp_path):
    _, v = book_look.t2i(declare(tmp_path), "a man", width=1536, height=1024, seed=7, prefix="p",
                         kind="characters", entity="x")
    assert v == {"prompt": v["prompt"], "seed": 7, "steps": 8, "cfg": 1, "aspect_ratio": "2:3 (Portrait Photo)",
                 "megapixels": 1, "refine_prompt": False, "enable_lora": False, "filename_prefix": "p"}


def test_an_entity_with_its_own_words_is_drawn_from_them(tmp_path):
    _, v = book_look.t2i(declare(tmp_path), "the row's words", width=1536, height=1024, seed=1, prefix="p",
                         kind="characters", entity="edward_hyde")
    assert "Mr Hyde, a small sinister young man, grins." in v["prompt"] and "row's words" not in v["prompt"]


def test_a_place_keeps_its_asked_shape(tmp_path):
    _, v = book_look.t2i(declare(tmp_path), "A foggy street corner.", width=1536, height=1024, seed=3,
                         prefix="p", kind="locations", entity="corner/wide")
    assert v["aspect_ratio"] == "3:2 (Photo)"
    assert "A foggy street corner. Wide establishing shot at eye level. Rendered" in v["prompt"]


def test_a_kind_with_no_frame_is_lead_body_recap(tmp_path):
    _, v = book_look.t2i(declare(tmp_path), "a square title picture", width=1024, height=1024, seed=3,
                         prefix="p", kind="title", entity="title")
    assert v["aspect_ratio"] == "1:1 (Square)"
    assert v["prompt"].endswith("figures. a square title picture. Rendered throughout as hand-painted 1990s cel animation.")
