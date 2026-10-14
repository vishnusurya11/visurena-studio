"""A drawn book's refs are drawn on its own drawer, never the house Krea2 + Cinematic LoRA.

Jekyll anime chain test (2026-10-13, docs/audit/2026-10-13_jekyll_anime_chain/README.md,
"pipeline changes needed" #1): `book_look.t2i` and `sheet_ladder.redraw` knew two looks,
photoreal and the house, so a declared `anime_gothic` fell through to WotW's painted look.
A drawn look now files its drawer under `refs` in refs/look.json -- the workflow, the base
checkpoint, its LoRAs, a tag lead, a negative, per-kind framing words and per-entity
tags -- and the base sheets, the fresh looks and the place masters all read it.

A drawn sheet is ONE front figure (NoobAI's turnarounds came back as 8 copies): it is
drawn portrait, and `sheet_front` takes a portrait sheet whole.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from studio import book_look, refs_pack, sheet_front, sheet_ladder

RECIPE = {
    "workflow": "image_sdxl_t2i_2lora_hires_visurena",
    "ckpt": "NoobAI-XL-v1.1.safetensors",
    "loras": [["gothic_anime\\x.safetensors", 0.45]],
    "hires_denoise": 0.55,
    "lead": "masterpiece, best quality, hellsing ultimate ova, ",
    "negative": "lowres, (text:1.5), ",
    "frames": {"characters": {"tags": "full body, front view, simple background",
                              "negative": "multiple views, "},
               "locations": {"tags": "(no humans:1.3), scenery", "negative": "1boy, people, "}},
    "entities": {"edward_hyde": {"tags": "1boy, solo, insane grin, (mutton chops:1.2)",
                                 "negative": "top hat, "}},
}


def declare(book: Path, refs: dict | None = RECIPE, look: str = "anime_gothic") -> Path:
    (book / "refs").mkdir(parents=True, exist_ok=True)
    said = {"look": look, "lead": "Hand-drawn 2D gothic anime.", "take": "Hand-drawn 2D gothic anime"}
    if refs is not None:
        said["refs"] = refs
    (book / "refs" / "look.json").write_text(json.dumps(said), encoding="utf-8")
    return book


def test_a_drawn_book_with_no_drawer_keeps_the_house(tmp_path):
    workflow, _ = book_look.t2i(declare(tmp_path, refs=None), "a man", width=1536, height=1024, seed=1, prefix="p")
    assert workflow == refs_pack.T2I and book_look.refs_recipe(tmp_path) == {}


def test_a_photoreal_book_has_no_drawn_drawer(tmp_path):
    declare(tmp_path, look="photoreal")
    assert book_look.refs_recipe(tmp_path) == {} and book_look.drawer(tmp_path) == book_look.PHOTOREAL_T2I


def test_the_drawer_is_the_recipes_workflow(tmp_path):
    assert book_look.drawer(declare(tmp_path)) == RECIPE["workflow"]
    assert book_look.drawer(tmp_path / "nobook") == ""


def test_a_base_sheet_is_its_tags_one_front_figure_portrait(tmp_path):
    workflow, v = book_look.t2i(declare(tmp_path), "A sneering man. Character reference sheet: four views.",
                                width=1536, height=1024, seed=7, prefix="p", kind="characters", entity="edward_hyde")
    assert workflow == RECIPE["workflow"] and (v["width"], v["height"]) == (832, 1216)
    assert v["prompt"] == ("masterpiece, best quality, hellsing ultimate ova, 1boy, solo, insane grin, "
                           "(mutton chops:1.2), full body, front view, simple background")
    assert v["negative_prompt"] == "lowres, (text:1.5), multiple views, top hat"
    assert (v["ckpt_name"], v["seed"], v["hires_seed"], v["hires_denoise"]) == (RECIPE["ckpt"], 7, 7, 0.55)
    assert (v["lora1"], v["lora1_model"], v["lora1_clip"]) == ("gothic_anime\\x.safetensors", 0.45, 0.45)


def test_a_person_without_tags_is_drawn_from_words_without_the_turnaround(tmp_path):
    _, v = book_look.t2i(declare(tmp_path), "A stout inspector. Character reference sheet on grey: front, back.",
                         width=1536, height=1024, seed=7, prefix="p", kind="characters", entity="newcomen")
    assert "A stout inspector." in v["prompt"] and "reference sheet" not in v["prompt"]
    assert "top hat" not in v["negative_prompt"]


def test_a_place_is_landscape_with_its_frame(tmp_path):
    _, v = book_look.t2i(declare(tmp_path), "a foggy street corner", width=1536, height=1024, seed=3,
                         prefix="p", kind="locations", entity="corner/wide_establishing")
    assert (v["width"], v["height"]) == (1216, 832)
    assert v["prompt"].endswith("a foggy street corner, (no humans:1.3), scenery")
    assert v["negative_prompt"] == "lowres, (text:1.5), 1boy, people"


def test_the_sheet_ladder_redraws_on_the_drawn_drawer(tmp_path):
    seen = []
    run = lambda workflow, values: seen.append((workflow, values)) or [str(tmp_path / "out.png")]
    (tmp_path / "out.png").write_bytes(b"png")
    job = refs_pack.Job("characters", "edward_hyde", "sheet", refs_pack.T2I, "a man", 1536, 1024)
    (tmp_path / refs_pack.relpath(job)).parent.mkdir(parents=True, exist_ok=True)
    sheet_ladder.redraw(declare(tmp_path), job, "a man", 11, run)
    assert seen[0][0] == RECIPE["workflow"] and "insane grin" in seen[0][1]["prompt"]
    assert sheet_ladder.workflow_of(tmp_path, job) == RECIPE["workflow"]


def test_the_base_sheet_is_drawn_with_its_entity(tmp_path, monkeypatch):
    from scripts.refs import build_pack
    job = refs_pack.Job("characters", "edward_hyde", "sheet", refs_pack.T2I, "a man", 1536, 1024)
    workflow, v = build_pack.request(declare(tmp_path), job)
    assert workflow == RECIPE["workflow"] and "insane grin" in v["prompt"]


def test_a_place_master_is_drawn_with_its_key(tmp_path, monkeypatch):
    from scripts.refs import places
    from studio import comfy
    seen = []
    monkeypatch.setattr(comfy, "run", lambda w, v, *a, **k: seen.append((w, v)) or [Path("x.png")])
    monkeypatch.setattr(places.shutil, "copyfile", lambda a, b: None)
    places.krea(declare(tmp_path))("a door", tmp_path / "refs" / "locations" / "door" / "wide.png")
    assert seen[0][0] == RECIPE["workflow"] and "scenery" in seen[0][1]["prompt"]


def test_a_drawn_place_carries_no_3d_look_sentence(tmp_path):
    import importlib
    places = importlib.import_module("scripts.refs.places")
    assert places.look_of(declare(tmp_path), "Hand-drawn 2D gothic anime") == ""
    assert places.look_of(declare(tmp_path / "b", refs=None), "Hand-drawn") == "Hand-drawn 2D gothic anime"


def test_a_fresh_look_is_drawn_as_one_figure(tmp_path, monkeypatch):
    from scripts.refs import looks
    from studio import comfy
    seen = []
    monkeypatch.setattr(comfy, "run", lambda w, v, *a, **k: seen.append((w, v)) or [Path("x.png")])
    monkeypatch.setattr("shutil.copyfile", lambda a, b: None)
    looks.comfy_draws(declare(tmp_path))["fresh"]("a bald man", tmp_path / "x.png", 3)
    assert seen[0][0] == RECIPE["workflow"] and (seen[0][1]["width"], seen[0][1]["height"]) == (832, 1216)


def test_a_portrait_sheet_is_its_own_front(tmp_path):
    a = np.full((1216, 832, 3), 90, np.uint8)
    a[200:1100, 250:600] = np.random.default_rng(0).integers(0, 255, (900, 350, 3))
    assert sheet_front.first_figure_box(a) == (0, 832)
    path = tmp_path / "sheet.png"
    Image.fromarray(a).save(path)
    assert Image.open(sheet_front.front_of(path)).size == (832, 1216)


def test_a_landscape_sheet_is_still_cropped(tmp_path):
    a = np.full((1024, 1536, 3), 90, np.uint8)
    rng = np.random.default_rng(0)
    for x in (100, 500, 900):
        a[150:900, x:x + 250] = rng.integers(0, 255, (750, 250, 3))
    left, right = sheet_front.first_figure_box(a)
    assert left < 100 and right < 500
