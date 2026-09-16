"""G-CAST: a character is BOUND before a sheet is drawn from them, or refused.

MEASURED building episode 9 (`docs/analysis/ep08_ep09_why_worse.md`, cause 9):
the three Utah lead rows have no `sheet` block, so `sheet_prompts` built their
cards from the wardrobe sentence alone (235-253 words against Watson's 307-312)
with no "the same X beard" clause; the card template was MALE-ONLY, so Lucy's
card read "The same man ... He wears ... hanging back off her shoulders ... the
face of a man waiting to be photographed"; `cast_cards --prompts` skipped rows
without `sheet`, so no prompt reached disk; and `--check` never ran between the
cards (06:15) and the sheets (06:47).

Pure strings and tiny files.  Nothing here draws, uploads or prices an image.
"""
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

from studio import cast_refs, trailer_refs as tr
from studio.affirm import negations

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "library" / "20260822113400_a-study-in-scarlet"
_spec = importlib.util.spec_from_file_location("ep_cast_cards_binding",
                                               ROOT / "scripts" / "episode" / "cast_cards.py")
cards = importlib.util.module_from_spec(_spec)
sys.modules["ep_cast_cards_binding"] = cards
_spec.loader.exec_module(cards)

SHEET = {"same": "the same long chestnut hair parted in the centre",
         "head": "Her chestnut hair is parted in the centre and worn loose.",
         "garments": "She wears a plain white linen blouse buttoned to the throat.",
         "hands": "Both her hands are bare to the wrist.",
         "props": "Her hands hang open at her sides."}
LUCY = {"ref_id": "char-lucy_ferrier", "kind": "character", "entity_id": "lucy_ferrier",
        "name": "Lucy Ferrier", "pronouns": "she",
        "physical": "A young woman of about twenty, slight and straight-backed.",
        "wardrobe": {"outdoor": "wears a broad-brimmed cream straw hat hanging back off "
                                "her shoulders on its ribbon"},
        "rel_path": "refs/characters/char-lucy_ferrier.png", "sheet": SHEET,
        "cards": {"outdoor": "refs/characters/char-lucy_ferrier_outdoor.png"}}


class TestTheTemplateKnowsWhoItIsDrawing:
    def test_a_she_row_is_the_same_woman_and_she_wears(self):
        said = cast_refs.sheet_prompts(LUCY)["char-lucy_ferrier_outdoor"]
        assert said.startswith("The same woman as in the reference image")
        assert "She wears a broad-brimmed cream straw hat" in said
        assert "the face of a woman waiting to be photographed" in said
        assert "The frame holds this one woman alone." in said
        assert "everything she carries" in said and "behind her" in said
        assert " man" not in said and " he " not in said and " his " not in said

    def test_the_bust_of_a_she_row_says_her_hairline(self):
        said = cast_refs.sheet_prompts(LUCY)["char-lucy_ferrier"]
        assert "She is bare-headed and her whole hairline is visible" in said
        assert "She stands against" in said

    def test_a_he_row_reads_as_it_always_did(self):
        said = tr.card_prompt("He wears a coat.", pronouns="he")
        assert said.startswith("The same man as in the reference image")
        assert "everything he carries" in said and "behind him" in said

    def test_an_old_row_without_the_field_is_read_as_he(self):
        old = {k: v for k, v in LUCY.items() if k != "pronouns"}
        assert cast_refs.pronouns(old) == "he"
        assert cast_refs.sheet_prompts(old)["char-lucy_ferrier"].startswith("The same man")

    def test_an_unknown_pronoun_is_refused_not_guessed(self):
        with pytest.raises(ValueError):
            tr.person("they")

    def test_both_voices_stay_affirmative(self):
        for who in cast_refs.PRONOUNS:
            assert negations(tr.card_prompt("wears a coat.", hands="Bare hands.",
                                            props="A knob.", pronouns=who)) == []
            assert negations(tr.bust_prompt("Dark hair.", pronouns=who)) == []


class TestASheetBlockIsRequired:
    def test_a_row_with_no_sheet_block_is_refused_naming_every_missing_key(self):
        thin = {k: v for k, v in LUCY.items() if k != "sheet"}
        with pytest.raises(ValueError) as refused:
            cast_refs.sheet_prompts(thin)
        for key in cast_refs.SHEET_KEYS:
            assert key in str(refused.value)

    def test_a_half_written_sheet_names_only_what_is_missing(self):
        half = dict(LUCY, sheet={k: v for k, v in SHEET.items() if k not in ("same", "props")})
        assert cast_refs.sheet_missing(half) == ["same", "props"]

    def test_pronouns_are_required_on_a_row_whose_cards_are_not_yet_drawn(self):
        fresh = {k: v for k, v in LUCY.items() if k not in ("pronouns", "cards")}
        assert cast_refs.sheet_missing(dict(fresh, sheet=SHEET)) == ["pronouns"]

    def test_a_row_with_a_drawn_card_is_old_and_keeps_its_default(self):
        old = {k: v for k, v in LUCY.items() if k != "pronouns"}
        assert cast_refs.sheet_missing(old) == []

    def test_a_complete_row_is_missing_nothing(self):
        assert cast_refs.sheet_missing(LUCY) == []


def a_book(tmp_path, row=LUCY):
    from PIL import Image

    chars = tmp_path / "refs" / "characters"
    chars.mkdir(parents=True)
    Image.new("RGB", (200, 300), (128, 128, 128)).save(chars / "char-lucy_ferrier.png")
    (tmp_path / "refs" / "refs.json").write_text(
        json.dumps({"book_id": "b", "palette": "p", "refs": [row]}), encoding="utf-8")
    return tmp_path


class TestTheDrawWritesItsPromptBesideTheCard:
    def test_the_prompt_lands_beside_the_card_every_time(self, tmp_path, monkeypatch):
        book = a_book(tmp_path)
        monkeypatch.setattr(cards, "_edit",
                            lambda source, out, said, book_, stem: (out.write_bytes(b"png"), out)[1])
        out = cards.draw(book, "lucy_ferrier", "outdoor", approved=True)
        record = out.with_suffix(".prompt.txt")
        assert record.exists()
        said = record.read_text(encoding="utf-8")
        assert "The same woman as in the reference image" in said
        assert "char-lucy_ferrier.png" in said and "wardrobe CARD" in said

    def test_a_row_without_a_sheet_is_refused_before_the_api(self, tmp_path, monkeypatch):
        thin = {k: v for k, v in LUCY.items() if k != "sheet"}
        book = a_book(tmp_path, thin)
        monkeypatch.setattr(cards, "_edit", lambda *a: pytest.fail("spent"))
        with pytest.raises(SystemExit) as refused:
            cards.draw(book, "lucy_ferrier", "outdoor", approved=True)
        assert "sheet" in str(refused.value)

    def test_write_prompts_says_who_it_skipped(self, tmp_path, capsys):
        thin = {k: v for k, v in LUCY.items() if k != "sheet"}
        assert cards.write_prompts(a_book(tmp_path, thin), ["lucy_ferrier"]) == []
        assert "lucy_ferrier" in capsys.readouterr().out


class TestBound:
    def test_a_bound_character_has_no_reasons(self, tmp_path):
        book = a_book(tmp_path, dict(LUCY, identity={"traits": {"figure": "woman"}}))
        (book / "refs" / "characters" / "char-lucy_ferrier_outdoor.png").write_bytes(b"png")
        assert cast_refs.bound(book, "lucy_ferrier", "outdoor") == []

    def test_a_named_card_that_is_not_on_disk_is_a_reason(self, tmp_path):
        book = a_book(tmp_path, dict(LUCY, identity={"traits": {"figure": "woman"}}))
        said = cast_refs.bound(book, "lucy_ferrier", "outdoor")
        assert len(said) == 1 and "not on disk" in said[0]

    def test_a_state_with_no_card_bound_is_a_reason_even_when_a_file_exists(self, tmp_path):
        """A card the row does not name is a card nobody wrote a prompt for."""
        book = a_book(tmp_path, dict(LUCY, cards={}, identity={"traits": {"figure": "woman"}}))
        (book / "refs" / "characters" / "char-lucy_ferrier_outdoor.png").write_bytes(b"png")
        said = cast_refs.bound(book, "lucy_ferrier", "outdoor")
        assert len(said) == 1 and "cards[outdoor]" in said[0]

    def test_no_read_back_is_a_reason(self, tmp_path):
        book = a_book(tmp_path)
        (book / "refs" / "characters" / "char-lucy_ferrier_outdoor.png").write_bytes(b"png")
        said = cast_refs.bound(book, "lucy_ferrier", "outdoor")
        assert len(said) == 1 and "read-back" in said[0]

    def test_an_unbound_row_is_one_reason(self, tmp_path):
        said = cast_refs.bound(a_book(tmp_path), "nobody", "indoor")
        assert len(said) == 1 and "no row" in said[0]


def copy_of_the_book(tmp_path) -> Path:
    """The current refs.json, with an empty file standing in for every picture
    a row names -- the binding reads the record, not the pixels."""
    shutil.copy2(BOOK / "refs" / "refs.json", tmp_path / "refs.json")
    (tmp_path / "refs").mkdir()
    shutil.move(tmp_path / "refs.json", tmp_path / "refs" / "refs.json")
    for row in cast_refs.load(tmp_path)["refs"]:
        for rel in [row.get("rel_path"), *(row.get("cards") or {}).values()]:
            if rel:
                (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
                (tmp_path / rel).write_bytes(b"png")
    return tmp_path


@pytest.mark.skipif(not BOOK.exists(), reason="the library is not on this machine")
class TestTheBookAsItIs:
    def test_lucy_ferrier_is_unbound_for_three_reasons(self, tmp_path):
        said = cast_refs.bound(copy_of_the_book(tmp_path), "lucy_ferrier", "outdoor")
        assert len(said) == 3, said
        assert any("sheet" in s for s in said)
        assert any("cards[outdoor]" in s for s in said)
        assert any("read-back" in s for s in said)

    def test_john_watson_is_bound(self, tmp_path):
        assert cast_refs.bound(copy_of_the_book(tmp_path), "john_watson", "indoor") == []
