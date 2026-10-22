"""The storyboard grid draws in the BOOK's declared look, never the house look.

Jekyll ep01 (2026-10-13): the book declares photoreal (refs/look.json, owner
2026-10-12 style A), its refs drew photoreal -- and its door panels came out
painted, because grids.py told every book's grid "flat angular stylised 3d CGI
... NO photographic depth of field ... NO photoreal skin or cloth" and put
"photographic" (and WotW's "beard on the narrator") in its negative.  A book
with no declaration keeps today's strings byte for byte.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from studio import book_look, sheet_ladder, refs_pack
from studio.storyboard_grid import STYLE_V2, grid_prompt_v2

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("grids", ROOT / "scripts" / "episode" / "grids.py")
grids = importlib.util.module_from_spec(spec)
sys.modules["grids"] = grids
spec.loader.exec_module(grids)

LEAD = "Cinematic live-action photograph, photoreal. A Victorian gothic film still: fog, gaslight, deep shadow. "
HOUSE_WORDS = ("angular", "brush", "stylis", "poster", "CGI", "NO photo", "no photo")


def declare(book: Path, **extra) -> Path:
    (book / "refs").mkdir(parents=True, exist_ok=True)
    (book / "refs" / "look.json").write_text(json.dumps(
        {"look": "photoreal", "lead": LEAD, "tail": " No text.", "by": "owner", **extra}), encoding="utf-8")
    return book


def test_the_house_strings_are_pinned_byte_for_byte():
    assert grids.STYLE == (
        "DRAWN IN EXACTLY THE ART STYLE OF <image{scene}>, copied from it and not invented: a flat "
        "angular stylised 3d CGI look with visible brush-stroke colour texture, broad simplified "
        "shapes, strong flat colour, high chroma, clean poster-like edges and NO photographic "
        "depth of field, NO camera blur, NO photoreal skin or cloth. Match the palette, the "
        "brush texture and the level of stylisation of <image{scene}> exactly")
    assert grids.NEGATIVE == (
        "text, caption, subtitles, watermark, signature, blurry, photographic, modern "
        "clothing, two men dressed alike, two men in the same hat, duplicated people, "
        "extra limbs, deformed hands, mountains, cliffs, lettering, letters, words, "
        "panel labels, numbers, beard on the narrator")
    assert STYLE_V2 == ("Drawn in the art style of <image{n}>: angular stylised 3D shapes, visible "
                        "brush-stroke colour texture, flat high-chroma colour.")


def test_a_book_with_no_declaration_keeps_the_house_grid(tmp_path):
    assert grids.look_for(tmp_path) == {}
    assert grids.negative_for(tmp_path) == grids.NEGATIVE
    assert book_look.grid_style(tmp_path) == ""


def test_a_photoreal_book_gets_a_film_still_in_its_own_words(tmp_path):
    said = book_look.grid_style(declare(tmp_path)).format(n=3)
    assert "PHOTOGRAPHIC FILM STILL" in said and "copied from <image3>" in said
    assert LEAD.strip() in said
    assert "natural depth of field" in said.lower() and "real skin and real cloth" in said
    assert not [w for w in HOUSE_WORDS if w in said]


def test_a_photoreal_negative_drops_photographic_and_every_book_word(tmp_path):
    said = grids.negative_for(declare(tmp_path))
    assert "photographic" not in said and "beard" not in said and "narrator" not in said
    assert said.startswith("text, caption, subtitles, watermark") and said.endswith("panel labels, numbers")


def test_a_book_files_its_own_negative_words(tmp_path):
    said = grids.negative_for(declare(tmp_path, negative="a top hat on the maid"))
    assert said.endswith("panel labels, numbers, a top hat on the maid")


def shot(size="wide"):
    return {"size": size, "body": "A green door in a blank wall.", "cut": "the whole door", "who": [],
            "extras": 0}


def test_v2_draws_the_given_style_and_medium():
    style = "A PHOTOGRAPHIC FILM STILL copied from <image{n}>."
    said = grid_prompt_v2([shot()], 1, 1, ([1], "a by-street"), [], 1, style=style, medium="film still")
    assert said.endswith("A PHOTOGRAPHIC FILM STILL copied from <image1>.")
    assert said.startswith("One full-frame film still,")
    assert not [w for w in HOUSE_WORDS if w in said]


def test_v2_without_a_style_is_the_house_line():
    said = grid_prompt_v2([shot()], 1, 1, ([1], "a by-street"), [], 1)
    assert said.endswith(STYLE_V2.format(n=1)) and said.startswith("One full-frame illustration,")


def test_v1_draws_the_given_style():
    said = grids._v1([shot()], 1, 1, ([1], "a by-street"), [], 1, style="A FILM STILL OF <image{n}>.")
    assert "A FILM STILL OF <image1>" in said and "angular" not in said


def test_the_look_kwargs_reach_the_prompt(tmp_path):
    look = grids.look_for(declare(tmp_path))
    assert look["medium"] == "film still" and look["style"] == book_look.grid_style(tmp_path)


def test_the_graph_carries_the_given_negative_only_where_cfg_reads_it():
    """Craft ruling A20: at the grid's cfg 1.0 the negative is never read, so the graph sends none
    (tests/test_the_grid_negative_is_said_dead.py); a cfg that reads one gets the book's words."""
    assert grids.sent_negative("text, watermark") == ""
    assert grids.sent_negative("text, watermark", cfg=4.0) == "text, watermark"


def test_a_photoreal_book_ignores_a_plan_look(tmp_path):
    assert book_look.plan_look(tmp_path, "Angular stylised 3D animation") == "Angular stylised 3D animation"
    assert book_look.plan_look(declare(tmp_path), "Angular stylised 3D animation") == ""


def test_a_sheet_redraw_draws_in_the_book_look(tmp_path):
    seen = []
    run = lambda workflow, values: seen.append((workflow, values)) or [str(tmp_path / "out.png")]
    (tmp_path / "out.png").write_bytes(b"png")
    job = refs_pack.Job("characters", "utterson", "sheet", refs_pack.T2I, "a lawyer", 1536, 1024)
    (tmp_path / refs_pack.relpath(job)).parent.mkdir(parents=True, exist_ok=True)
    sheet_ladder.redraw(declare(tmp_path), job, "a lawyer", 11, run)
    assert seen[0][0] == book_look.PHOTOREAL_T2I and seen[0][1]["prompt"].startswith(LEAD)
    assert seen[0][1]["seed"] == 11


def test_a_house_sheet_redraw_is_unchanged(tmp_path):
    seen = []
    run = lambda workflow, values: seen.append((workflow, values)) or [str(tmp_path / "out.png")]
    (tmp_path / "out.png").write_bytes(b"png")
    job = refs_pack.Job("characters", "watson", "sheet", refs_pack.OLD_T2I, "a doctor", 1536, 1024)
    (tmp_path / refs_pack.relpath(job)).parent.mkdir(parents=True, exist_ok=True)
    sheet_ladder.redraw(tmp_path, job, "a doctor", 11, run)
    assert seen[0] == (refs_pack.OLD_T2I, {**refs_pack.values_for(job), "prompt": refs_pack.styled("a doctor"),
                                           "seed": 11})


def test_the_ladder_records_the_workflow_it_drew_with(tmp_path):
    job = refs_pack.Job("characters", "utterson", "sheet", refs_pack.T2I, "a lawyer", 1536, 1024)
    assert sheet_ladder.workflow_of(tmp_path, job) == refs_pack.T2I
    assert sheet_ladder.workflow_of(declare(tmp_path), job) == book_look.PHOTOREAL_T2I


def load(name, rel):
    found = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(found)
    sys.modules[name] = module
    found.loader.exec_module(module)
    return module


def test_a_photoreal_take_adopts_no_plan_look(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from studio import house_style
    takes = load("takes_r2v_look", "scripts/episode/takes_r2v.py")
    monkeypatch.setattr(takes, "place_names", lambda book: {})
    plan = SimpleNamespace(aspect="1:1", where="", light="", look="Angular stylised 3D animation")
    try:
        takes.adopt_canon(declare(tmp_path), plan)
        assert house_style.live().startswith("Photoreal live-action, ")
    finally:
        house_style.adopt_look("")
        house_style.adopt("", "")


def test_a_photoreal_place_draws_no_plan_look(tmp_path, monkeypatch):
    places = load("places_look", "scripts/refs/places.py")
    assert places.look_of(tmp_path, "Angular stylised 3D") == "Angular stylised 3D"
    assert places.look_of(declare(tmp_path), "Angular stylised 3D") == ""
