"""grids.py after the Jekyll ep01 grid audit (2026-10-15, 02_prompts.md G2-G7 and
01_staged_refs.md 3.2): a chained grid's room IS the place, so two people keep
their slots; an unstaged person is said by his look layers, never his raw row;
epithets bind to their slot; the book's own negative reaches the grid; the
manifest records what was staged and who was drawn from words; and a prompt the
lint refuses never reaches the GPU.  $0: fixture book, no ComfyUI."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("grids_once", ROOT / "scripts" / "episode" / "grids.py")
grids = importlib.util.module_from_spec(spec)
sys.modules["grids_once"] = grids
spec.loader.exec_module(grids)

ROWS = {
    "gabriel_john_utterson": ("Mr. Utterson", "male", "Lank grey hair; long, gaunt, unsmiling face; black bowler hat. "
                              "A lean, long, bony man of about forty, younger than Jekyll. Wearing: lawyer's dark suit",
                              {"headwear": "black bowler hat", "hair": "lank grey hair", "face": "long, gaunt, unsmiling face",
                               "top": "long black overcoat with white buttons"}),
    "richard_enfield": ("Mr. Enfield", "male", "Receding brown hair; clean-shaven; light-brown top hat. He is presented as "
                        "a gentleman who walks with Utterson and Hyde. A compact man of about thirty-five. Wearing: "
                        "fashionable dark frock coat; compact, upright, broad-shouldered, heavy jaw",
                        {"headwear": "light-brown top hat", "hair": "receding brown hair", "face": "clean-shaven",
                         "top": "mid-grey frock coat, cream waistcoat; compact, upright, broad-shouldered, heavy jaw"}),
    "edward_hyde": ("Mr. Hyde", "male", "Coarse black hair; pale cheeks; soft black felt hat. A small man associated with "
                    "access to Jekyll's house, a Soho residence. Wearing: respectable clothing on a small, slight frame",
                    {"headwear": "soft black felt wideawake hat", "hair": "coarse, unkempt black hair",
                     "face": "clean-shaven, pale smooth cheeks",
                     "top": "respectable, well-fitting clothing on a small, slight, narrow-shouldered frame"}),
    "child_of_hyde_incident": ("the child", "female", "Fair hair in two plaits; small grey bonnet. A small girl of about "
                               "nine. Wearing: plain grey pinafore dress, and black boots",
                               {"headwear": "small soft grey woollen bonnet", "hair": "fair hair in two plaits",
                                "face": "smooth-cheeked, blue eyes", "top": "plain grey pinafore dress, and black boots"}),
}

HELLSING_LOOK = {"look": "anime_gothic", "lead": "Hand-drawn 2D gothic anime.", "take": "Gothic anime",
                 "atmosphere": "fog, damp haze",
                 "refs": {"workflow": "image_sdxl_t2i", "ckpt": "x.safetensors", "loras": [],
                          "lead": "masterpiece", "negative": "nsfw, lowres, text, (green theme:1.3), sign, signage",
                          "frames": {}, "entities": {}}}


def book_of(tmp_path: Path) -> Path:
    refs = tmp_path / "refs"
    refs.mkdir()
    rows, looks = [], {}
    for who, (display, gender, physical, layers) in ROWS.items():
        rows.append({"entity_id": who, "kind": "character", "name": display, "display": display, "gender": gender,
                     "physical": physical, "wardrobe": {"outdoor": physical}, "look": "base"})
        looks[who] = {"base": "base", "body": "", "looks": {"base": {"layers": layers, "made_by": "base"}}}
        folder = refs / "characters" / who
        folder.mkdir(parents=True)
        Image.new("RGB", (8, 8)).save(folder / "sheet.png")
        Image.new("RGB", (4, 8)).save(folder / "sheet_front.png")
    (refs / "refs.json").write_text(json.dumps({"refs": rows}), encoding="utf-8")
    (refs / "looks.json").write_text(json.dumps({"book": "b", "characters": looks}), encoding="utf-8")
    (refs / "look.json").write_text(json.dumps(HELLSING_LOOK), encoding="utf-8")
    Image.new("RGB", (8, 8)).save(tmp_path / "plate.png")
    Image.new("RGB", (8, 8)).save(tmp_path / "room.png")
    return tmp_path


def shot(i, size, faces, frame, at_rest="", extras=0):
    return SimpleNamespace(index=i, setup="street", size=size, faces=list(faces), cuts=[], frame=frame,
                           at_rest=at_rest, end="", motion="", extras=extras)


SETUP = SimpleNamespace(location="street", view="wide", described="A by-street with polished brass plates",
                        geometry="", landmark="", landmark_at="far_end", landmark_size="", light="", props=[],
                        looks=[], outdoors=True)

WIDE = shot(22, "wide", ["gabriel_john_utterson", "richard_enfield"],
            "Wide of the by-street as the lawyer (black bowler hat, lawyer's dark suit) and Mr. Enfield "
            "(light-brown top hat) walk away and a tramp strikes a match on the panels of the blistered door")
FULL = shot(7, "full", ["richard_enfield", "edward_hyde", "child_of_hyde_incident"],
            "Full shot as Mr. Enfield (light-brown top hat) hauls the little man (soft black felt wideawake hat, "
            "small, slight, narrow-shouldered frame) back to the girl (fair hair in two plaits) on the cobbles")
GIRL = shot(5, "medium", ["child_of_hyde_incident"], "Medium of the girl (fair hair in two plaits) as she runs")


def episode(*shots):
    return SimpleNamespace(shots=list(shots), setups={"street": SETUP})


@pytest.fixture
def book(tmp_path, monkeypatch):
    b = book_of(tmp_path)
    monkeypatch.setattr(grids, "wide_for", lambda bk, setup: b / "plate.png")
    return b


def test_a_chained_wide_stages_both_men_and_not_the_plate(book):
    text, slots, cast = grids.built(book, episode(WIDE), "street", [WIDE], 1, 1, room=book / "room.png")
    assert [Path(p).name for p in slots.values()] == ["sheet_front.png", "sheet_front.png", "room.png"]
    assert "the man in <image1> (" not in text and "lawyer" not in text and "Enfield" not in text
    assert "the man in <image1> and the man in <image2> walk away" in text
    assert "the panels of the blistered door" in text


def test_an_unchained_wide_stages_the_plate(book):
    _, slots, _ = grids.built(book, episode(WIDE), "street", [WIDE], 1, 1, room=None)
    assert [Path(p).name for p in slots.values()][-1] == "plate.png"


def test_over_the_ceiling_a_person_is_said_by_his_layers(book):
    text, _, cast = grids.built(book, episode(FULL), "street", [FULL], 1, 1, room=book / "room.png")
    words = [p for p in cast if p["ref"] is None]
    assert len(words) == 1
    line = words[0]["line"]
    assert len(line.split()) < 30 and line in text
    for bad in ("jekyll", "utterson", "hyde", "associated", "access to", "residence", "presented as", "frame"):
        assert bad not in line.lower()


def test_a_staged_girl_is_the_girl(book):
    text, _, _ = grids.built(book, episode(GIRL), "street", [GIRL], 1, 1, room=book / "room.png")
    assert "the girl in <image1>" in text and "the person in" not in text


def test_wears_reads_the_look_layers_clothes_only(book):
    text, _, _ = grids.built(book, episode(WIDE), "street", [WIDE], 1, 1, room=book / "room.png")
    assert "wears: light-brown top hat; mid-grey frock coat, cream waistcoat." in text
    assert "compact" not in text and "heavy jaw" not in text


def test_a_named_person_with_no_slot_and_no_clean_line_refuses(book, monkeypatch):
    monkeypatch.setattr(grids, "layers_line", lambda noun, layers, names: "")
    with pytest.raises(SystemExit, match="REFUSED"):
        grids.built(book, episode(FULL), "street", [FULL], 1, 1, room=book / "room.png")


def test_the_books_own_negative_reaches_the_grid(book):
    said = grids.negative_for(book)
    assert "lowres" in said and "green theme" in said and ":1.3" not in said and "signage" in said
    assert "mountains" not in said and "cliffs" not in said


def test_the_manifest_names_the_staged_pictures_and_the_words_only(book):
    _, slots, cast = grids.built(book, episode(FULL), "street", [FULL], 1, 1, room=book / "room.png")
    said = grids.staging(book, slots, cast)
    assert said["load_images"][-1] == "room.png" and len(said["load_images"]) == 3
    assert said["load_images"][0] == "refs/characters/richard_enfield/sheet_front.png"
    assert len(said["words_only"]) == 1


def test_a_linted_prompt_never_reaches_the_gpu(book):
    with pytest.raises(SystemExit, match="grid lint"):
        grids.lint_wall("its picture streaked black", [], [])


def test_the_dry_mode_builds_and_lints_every_grid(book, monkeypatch, capsys):
    ep = episode(WIDE, GIRL)
    rows = [{"setup": "street", "cols": 1, "rows": 1, "shots": [22], "tag": "a"},
            {"setup": "street", "cols": 1, "rows": 1, "shots": [5], "tag": "b"}]
    monkeypatch.setattr(grids, "room_of", lambda *a: None)
    assert grids.dry_run(book, 1, ep, rows) == 0
    out = capsys.readouterr().out
    assert "ep01_grid_street_1x1_a" in out and "lint: clean" in out


def test_an_unstaged_name_is_plain_words_naming_his_hat():
    assert grids.plain_name("man", {"headwear": "light-brown top hat, brown band"}) == "the man in the light-brown top hat"
    assert grids.plain_name("girl", {"headwear": ""}) == "the girl"


def test_a_noun_follows_gender_and_age():
    assert grids.person_noun({"gender": "female", "physical": "A small girl of about nine"}) == "girl"
    assert grids.person_noun({"gender": "male", "physical": "A man of about forty"}) == "man"
    assert grids.person_noun({"gender": "creature"}) == "creature"
    assert grids.person_noun({}) == "person"
