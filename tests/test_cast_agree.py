"""The caption and the picture must be the same statement.

Free, model-free, deterministic: the fixtures are tiny synthetic PNGs written
by PIL into tmp_path, plus the real strings out of `refs.json`.  No API is
called, no credit is spent, no image is drawn.
"""
import json

import pytest
from PIL import Image, ImageDraw

from studio import cast_agree as ca

GREY = (128, 128, 128)

WATSON_OLD = ("A man in his late twenties, as thin as a lath, as brown as a nut, dark hair "
              "swept back, a thin waxed moustache, wearing a fawn tweed overcoat and a white "
              "cravat pinned with a stud; no gloves; a brown bowler hat, on his head outdoors "
              "and in his left hand indoors; a bare sunburnt right hand on the silver ball "
              "knob of a black walking stick.")
WATSON_NEW = ("A man in his late twenties, as thin as a lath, as brown as a nut, dark hair "
              "swept back, a thin waxed moustache, a fawn tweed overcoat over a tweed "
              "waistcoat with a watch chain and a white cravat pinned with a stud; both hands "
              "bare to the wrist and sunburnt, the right hand on the silver ball knob of a "
              "black walking stick.")
STAMFORD_OLD = ("A stout young man in his mid-twenties, round clean-shaven face, dark hair "
                "parted at the side, small bright eyes, wearing a black frock coat over a grey "
                "waistcoat, white shirt and dark cravat; a black bowler hat outdoors, in his "
                "hand indoors.")


def flat(path, size=(300, 400), colour=GREY):
    """A picture that is nothing but backdrop."""
    Image.new("RGB", size, colour).save(path)
    return path


def with_bar(path, size=(300, 400)):
    """The same backdrop with a dark brick pillar standing in the side strip."""
    image = Image.new("RGB", size, GREY)
    ImageDraw.Draw(image).rectangle([0, 0, 20, size[1]], fill=(20, 20, 20))
    image.save(path)
    return path


def figure(path, bottom, size=(300, 400)):
    """One dark figure on the backdrop, ending `bottom` px above the frame's foot."""
    image = Image.new("RGB", size, GREY)
    ImageDraw.Draw(image).rectangle([100, 40, 200, size[1] - 1 - bottom], fill=(30, 30, 30))
    image.save(path)
    return path


class TestTheTextIsPositiveAndUnconditional:
    def test_a_negation_in_the_caption_is_named(self):
        assert ca.positive(WATSON_OLD) == ["no"]

    def test_the_proposed_caption_negates_nothing(self):
        assert ca.positive(WATSON_NEW) == []

    def test_a_conditional_caption_names_both_of_its_states(self):
        assert ca.unconditional(WATSON_OLD) == ["outdoors", "indoors"]
        assert ca.unconditional(STAMFORD_OLD) == ["outdoors", "indoors"]

    def test_the_split_caption_is_unconditional_and_the_state_carries_the_hat(self):
        assert ca.unconditional(WATSON_NEW) == []
        assert ca.unconditional("the brown bowler hat squarely on his head") == []


class TestThePictureIsOneManOnAPlainBackdrop:
    def test_a_flat_backdrop_passes_and_a_pillar_in_the_side_strip_fails(self, tmp_path):
        assert ca.plain_backdrop(flat(tmp_path / "flat.png")) is True
        assert ca.plain_backdrop(with_bar(tmp_path / "bar.png")) is False

    def test_the_backdrop_measurement_is_a_number_the_report_can_quote(self, tmp_path):
        assert ca.backdrop_std(flat(tmp_path / "flat.png")) == pytest.approx(0.0, abs=0.01)
        assert ca.backdrop_std(with_bar(tmp_path / "bar.png")) > ca.BACKDROP_LIMIT

    def test_exactly_one_detected_face_is_one_man(self, tmp_path):
        path = flat(tmp_path / "f.png")
        assert ca.one_man(path, detect=lambda p: [(10, 10, 40, 60)]) is True
        assert ca.one_man(path, detect=lambda p: [(10, 10, 40, 60), (90, 9, 40, 60)]) is False
        assert ca.one_man(path, detect=lambda p: []) is False


class TestTheFaceIsBigEnoughToCopy:
    def test_the_fraction_is_the_tallest_box_over_the_frame_height(self, tmp_path):
        path = flat(tmp_path / "f.png")          # 300x400
        assert ca.face_fraction(path, detect=lambda p: [(0, 0, 50, 200)]) == pytest.approx(0.50)
        assert ca.face_fraction(path, detect=lambda p: [(0, 0, 50, 40)]) == pytest.approx(0.10)
        assert ca.face_fraction(path, detect=lambda p: []) == 0.0

    def test_a_bust_needs_more_face_than_a_card(self, tmp_path):
        path = flat(tmp_path / "f.png")
        small = lambda p: [(0, 0, 50, 80)]       # 0.20 of 400
        assert ca.face_ok(path, "bust", detect=small) is False
        assert ca.face_ok(path, "card", detect=small) is True
        assert ca.face_ok(path, "card", detect=lambda p: [(0, 0, 50, 40)]) is False


class TestTheHandsAreInsideTheFrame:
    def test_a_figure_running_off_the_bottom_edge_fails(self, tmp_path):
        assert ca.hands_clear(figure(tmp_path / "cut.png", bottom=0)) is False
        assert ca.hands_clear(figure(tmp_path / "air.png", bottom=60)) is True

    def test_the_bottom_share_is_the_measurement_the_complaint_quotes(self, tmp_path):
        assert ca.bottom_share(figure(tmp_path / "cut.png", bottom=0)) == pytest.approx(1 / 3, abs=0.02)
        assert ca.bottom_share(figure(tmp_path / "air.png", bottom=60)) == 0.0


class TestTheTextAndThePicturesReadBackAgree:
    def test_side_whiskers_on_a_clean_shaven_picture_is_one_line_of_output(self):
        said = ca.agrees("A stout young man, fair side-whiskers, wearing a frock coat.",
                         {}, {"facial_hair": "clean-shaven"})
        assert said == ["facial_hair: the text says whiskers, the picture says clean-shaven"]

    def test_a_caption_that_names_no_hat_asserts_a_bare_head(self):
        said = ca.agrees(WATSON_NEW, {}, {"headgear": "bowler"})
        assert said == ["headgear: the text says none, the picture says bowler"]

    def test_the_state_sentence_is_what_the_card_is_read_against(self):
        wardrobe = {"outdoor": "wears the brown bowler hat squarely on his head"}
        assert ca.agrees(WATSON_NEW, wardrobe, {"headgear": "bowler"}) == []

    def test_a_reading_the_vocabulary_calls_the_same_thing_is_not_a_disagreement(self):
        assert ca.agrees("dark hair swept back", {}, {"hair_length": "short"}) == []
        assert ca.agrees("a pale indoor complexion", {}, {"complexion": "fair"}) == []

    def test_a_slot_the_text_says_nothing_about_raises_no_complaint(self):
        assert ca.agrees("A man on a grey backdrop.", {}, {"build": "heavy"}) == []


def a_book(tmp_path, row, pictures=("char-x.png",)):
    """A book folder with one character row and whatever pictures it names."""
    chars = tmp_path / "refs" / "characters"
    chars.mkdir(parents=True)
    for name in pictures:
        flat(chars / name)
    (tmp_path / "refs" / "refs.json").write_text(
        json.dumps({"book_id": "b", "palette": "p", "refs": [row]}), encoding="utf-8")
    return tmp_path


class TestTheWholeCheck:
    def test_a_sheet_that_never_passed_the_gate_says_so(self, tmp_path):
        book = a_book(tmp_path, {"ref_id": "char-x", "kind": "character", "entity_id": "x",
                                 "physical": WATSON_NEW})
        assert "no read-back: this sheet never passed the cast gate" in ca.check(book, "x")

    def test_the_bust_is_read_against_the_invariant_caption_alone(self, tmp_path):
        """`identity.traits` is the BUST's read-back and the bust is bare-headed
        by rule, so a hat in a STATE sentence may not excuse a hat on the bust."""
        book = a_book(tmp_path, {"ref_id": "char-x", "kind": "character", "entity_id": "x",
                                 "physical": WATSON_NEW,
                                 "wardrobe": {"outdoor": "wears the brown bowler on his head"},
                                 "identity": {"traits": {"headgear": "bowler"}}})
        assert "headgear: the text says none, the picture says bowler" in ca.check(book, "x")

    def test_a_stored_prompt_is_a_second_writer_and_is_refused(self, tmp_path):
        book = a_book(tmp_path, {"ref_id": "char-x", "kind": "character", "entity_id": "x",
                                 "physical": WATSON_NEW, "prompt": "anything at all",
                                 "identity": {"traits": {"headgear": "none"}}})
        assert any("R1" in line for line in ca.check(book, "x"))

    def test_a_clean_row_with_a_clean_picture_has_nothing_to_say(self, tmp_path):
        book = a_book(tmp_path, {"ref_id": "char-x", "kind": "character", "entity_id": "x",
                                 "physical": WATSON_NEW,
                                 "wardrobe": {"indoor": "is bare-headed"},
                                 "identity": {"traits": {"headgear": "none",
                                                         "facial_hair": "moustache"}}})
        assert ca.check(book, "x") == []

    def test_the_missing_card_of_a_declared_state_is_a_complaint(self, tmp_path):
        book = a_book(tmp_path, {"ref_id": "char-x", "kind": "character", "entity_id": "x",
                                 "physical": WATSON_NEW,
                                 "wardrobe": {"indoor": "is bare-headed"},
                                 "cards": {"indoor": "refs/characters/char-x_indoor.png"},
                                 "identity": {"traits": {"headgear": "none"}}})
        assert any("char-x_indoor.png" in line for line in ca.check(book, "x"))
