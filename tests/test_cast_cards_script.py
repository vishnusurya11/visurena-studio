"""The cast-card step: `--check` is free and runs every time, `--draw` is the
ESCALATE gate.  Nothing in this file draws, uploads or prices an image."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("ep_cast_cards",
                                               ROOT / "scripts" / "episode" / "cast_cards.py")
cards = importlib.util.module_from_spec(_spec)
sys.modules["ep_cast_cards"] = cards
_spec.loader.exec_module(cards)

ROW = {"ref_id": "char-x", "kind": "character", "entity_id": "x", "name": "Mr X",
       "pronouns": "he",
       "physical": "A man in his late twenties, as thin as a lath.",
       "wardrobe": {"indoor": "is bare-headed and carries the brown bowler in his left hand",
                    "outdoor": "wears the brown bowler hat squarely on his head"},
       "rel_path": "refs/characters/char-x.png",
       # every SHEET_KEY: a row that has not said enough is refused, not drawn thin
       "sheet": {"same": "the same thin waxed moustache",
                 "head": "His dark hair is swept back.",
                 "garments": "He wears a fawn tweed overcoat.",
                 "hands": "Both his hands are bare to the wrist.",
                 "props": "His hands hang open at his sides."},
       "identity": {"traits": {"headgear": "none"}}}


def a_book(tmp_path, row=ROW):
    chars = tmp_path / "refs" / "characters"
    chars.mkdir(parents=True)
    Image.new("RGB", (200, 300), (128, 128, 128)).save(chars / "char-x.png")
    # ROW declares an indoor AND an outdoor wardrobe, and R5 wants a picture for
    # each: a state promising clothes no card shows falls through to the bust.
    for state in ("indoor", "outdoor"):
        Image.new("RGB", (200, 300), (128, 128, 128)).save(chars / f"char-x_{state}.png")
    (tmp_path / "refs" / "refs.json").write_text(
        json.dumps({"book_id": "b", "palette": "p", "refs": [row]}), encoding="utf-8")
    return tmp_path


class TestTheFreeCheck:
    def test_a_clean_character_reports_nothing(self, tmp_path):
        assert cards.check_all(a_book(tmp_path), ["x"]) == {}

    def test_a_character_with_a_stored_prompt_is_reported_by_name(self, tmp_path):
        book = a_book(tmp_path, dict(ROW, prompt="a second writer"))
        assert "R1" in " ".join(cards.check_all(book, ["x"])["x"])

    def test_a_character_the_book_never_bound_is_reported_rather_than_crashing(self, tmp_path):
        assert "no row in refs.json" in " ".join(cards.check_all(a_book(tmp_path), ["y"])["y"])


class TestThePromptsAreWrittenForApprovalNotDrawn:
    def test_one_text_file_per_picture_beside_the_picture(self, tmp_path):
        book = a_book(tmp_path)
        made = cards.write_prompts(book, ["x"])
        assert sorted(p.name for p in made) == ["char-x.prompt.txt",
                                                "char-x_indoor.prompt.txt",
                                                "char-x_outdoor.prompt.txt"]
        assert all(p.parent == book / "refs" / "characters" for p in made)

    def test_each_file_names_the_model_the_size_and_the_reference_it_edits(self, tmp_path):
        book = a_book(tmp_path)
        said = (cards.write_prompts(book, ["x"])[0]).read_text(encoding="utf-8")
        assert "gpt-image-2.5-sunburst" in said and "1024x1536" in said
        assert "char-x.png" in said

    def test_a_character_whose_pictures_are_unauthored_gets_no_prompt(self, tmp_path):
        book = a_book(tmp_path, {k: v for k, v in ROW.items() if k != "sheet"})
        assert cards.write_prompts(book, ["x"]) == []

    def test_the_command_line_may_name_who_to_look_at(self, tmp_path):
        book = a_book(tmp_path)
        assert cards.named(["cast_cards.py", "b", "--check"], book) == ["x"]
        assert cards.named(["cast_cards.py", "b", "--draw", "x", "indoor"], book) == ["x"]

    def test_writing_the_prompts_spends_nothing(self, tmp_path):
        book = a_book(tmp_path)
        cards.write_prompts(book, ["x"])
        assert not (book / "spend.jsonl").exists()


class TestTheSpendGate:
    def test_drawing_without_an_explicit_go_refuses_before_it_reaches_the_api(self, tmp_path):
        book = a_book(tmp_path)
        with pytest.raises(SystemExit) as stop:
            cards.draw(book, "x", "indoor", approved=False)
        assert "approve" in str(stop.value).lower()
        assert not (book / "spend.jsonl").exists()

    def test_the_planned_and_ceiling_costs_are_stated_in_the_module(self):
        assert cards.PLANNED_USD == 0.64 and cards.CEILING_USD == 1.28


class TestTheOldPictureIsKept:
    def test_a_redraw_copies_the_old_sheet_aside_before_replacing_it(self, tmp_path):
        book = a_book(tmp_path)
        old = book / "refs" / "characters" / "char-x.png"
        kept = cards.supersede(old)
        assert kept.exists() and kept.parent.name == ".superseded"
        assert kept.read_bytes() == old.read_bytes()

    def test_a_picture_that_does_not_exist_yet_supersedes_nothing(self, tmp_path):
        """A name `a_book` does NOT draw: it writes the bust and both declared
        wardrobe cards, because R5 wants a picture for every promise."""
        book = a_book(tmp_path)
        assert cards.supersede(book / "refs" / "characters" / "char-x_lab.png") is None
