"""SHEET-ROW: a base sheet shows what its row says (Jekyll ep01 v2, owner 2026-10-15).

The girl's row said a small knitted woollen bonnet and a plain grey pinafore; her
sheet drew a black lace bonnet, a black pinafore and hollow solid-black eyes, every
gate passed it, and the takes split between the words and the picture -- a
different girl in each shot.  The reader LISTS (headwear, its colour and material,
the main garment's colour, the eyes) in a closed vocabulary; code judges against the
row's own words.  The reader is a FakeModel: no test reaches a VLM.
"""
from __future__ import annotations

import json
from pathlib import Path

from studio import sheet_ladder
from studio.continuity_spec import Layers, Markers
from studio.judges import look, sheet_row
from tests import look_fixtures as lf

OLD_GIRL = Layers(headwear="small knitted woollen bonnet", hair="fair hair in two plaits",
                  face="smooth-cheeked", top="plain grey pinafore dress and black boots")
NEW_GIRL = Layers(headwear="small soft grey woollen bonnet", hair="fair hair in two plaits",
                  face="smooth-cheeked, blue eyes",
                  top="plain grey pinafore dress over a dark-red long-sleeved blouse, and black boots")
GIRL = Markers(headwear="bonnet", hair_colour="fair", facial_hair="none", top="dress")
LACE_SHEET = {"headwear": "bonnet", "headwear_colour": "black", "headwear_material": "lace",
              "top_colour": "black", "eyes": "hollow"}
"""What a reader lists on the superseded sheet (sheet_2026-10-14_hellsing_v2_lace.png)."""
GOOD_SHEET = {"headwear": "bonnet", "headwear_colour": "grey", "headwear_material": "cloth",
              "top_colour": "grey", "eyes": "irises"}


class FakeModel:
    """The VLM, canned: it returns one answer and records every question it was asked."""

    def __init__(self, answer):
        self.answer, self.asked = answer, []

    def __call__(self, picture, question):
        self.asked.append(question)
        return self.answer if isinstance(self.answer, str) else json.dumps(self.answer)


def kinds(verdict) -> set[str]:
    return {f.kind for f in verdict.faults}


def test_the_lace_sheet_contradicts_its_knitted_grey_row_three_ways():
    v = sheet_row.judge(Path("s.png"), OLD_GIRL, GIRL, FakeModel(LACE_SHEET))
    assert not v.passed
    assert {"row_headwear_material", "row_top_colour", "row_eyes"} <= kinds(v)


def test_the_redrawn_sheet_passes_its_aligned_row():
    v = sheet_row.judge(Path("s.png"), NEW_GIRL, GIRL, FakeModel(GOOD_SHEET))
    assert v.passed and v.faults == []


def test_a_bonnet_of_another_colour_than_the_row_refuses():
    v = sheet_row.judge(Path("s.png"), NEW_GIRL, GIRL, FakeModel({**GOOD_SHEET, "headwear_colour": "black"}))
    assert not v.passed and kinds(v) == {"row_headwear_colour"}


def test_a_hat_where_the_row_says_a_bonnet_only_flags():
    """The replay read a wideawake as a top hat and a bell helmet as a cap on correct sheets;
    LOOK-STATE judges the kind by family on every look picture."""
    v = sheet_row.judge(Path("s.png"), NEW_GIRL, GIRL, FakeModel({**GOOD_SHEET, "headwear": "top_hat"}))
    assert v.passed and kinds(v) == {"row_headwear"} and v.faults[0].severity == "advisory"


def test_small_cel_eyes_are_not_hollow_eyes():
    assert sheet_row.judge(Path("s.png"), NEW_GIRL, GIRL, FakeModel({**GOOD_SHEET, "eyes": "small"})).passed


def test_a_silk_top_hat_read_as_felt_is_one_material():
    silk = Layers(headwear="black silk top hat", top="black frock coat")
    hat = Markers(headwear="top_hat")
    read = {"headwear": "top_hat", "headwear_colour": "black", "headwear_material": "felt", "top_colour": "black",
            "eyes": "small"}
    assert sheet_row.judge(Path("s.png"), silk, hat, FakeModel(read)).passed


def test_the_garment_colour_is_the_first_colour_the_row_gives_the_top():
    assert sheet_row.colour_of(NEW_GIRL.top) == "grey"
    assert sheet_row.colour_of("a dark-red long-sleeved blouse") == "red"
    assert sheet_row.colour_of("charcoal frock coat") == "grey"
    assert sheet_row.colour_of("fashionable frock coat") == ""


def test_a_row_naming_no_colour_or_material_judges_nothing_on_it():
    bare = Layers(headwear="a bonnet", top="a pinafore dress")
    v = sheet_row.judge(Path("s.png"), bare, GIRL, FakeModel({**LACE_SHEET, "eyes": "irises"}))
    assert v.passed


def test_a_plain_read_of_a_knitted_bonnet_is_not_a_contradiction():
    """At sheet scale a cel-shaded knit reads as cloth; only ANOTHER distinct material refuses."""
    v = sheet_row.judge(Path("s.png"), OLD_GIRL, GIRL, FakeModel({**GOOD_SHEET, "headwear_material": "cloth"}))
    assert "row_headwear_material" not in kinds(v)


def test_hidden_or_closed_eyes_are_not_hollow_eyes():
    for eyes in ("hidden", "closed"):
        assert sheet_row.judge(Path("s.png"), NEW_GIRL, GIRL, FakeModel({**GOOD_SHEET, "eyes": eyes})).passed


def test_an_unreadable_answer_is_unread_never_a_pass_of_the_row():
    v = sheet_row.judge(Path("s.png"), NEW_GIRL, GIRL, FakeModel("I cannot tell"))
    assert kinds(v) == {"unread"} and v.confidence == 0.0


def test_a_fault_names_the_word_the_ladder_puts_first():
    v = sheet_row.judge(Path("s.png"), OLD_GIRL, GIRL, FakeModel(LACE_SHEET))
    material = next(f for f in v.faults if f.kind == "row_headwear_material")
    assert material.evidence["want"] == "knitted" and material.evidence["seen"] == "lace"
    assert "knitted" in sheet_ladder.nouns_missing([material])


# ---- wired into the LOOK gate (refs/04) ------------------------------------------

def a_table(book: Path, who: str, layers: Layers) -> None:
    doc = {"book": "b", "characters": {who: {
        "base": "base", "body": "A small girl of about nine.",
        "looks": {"base": {"layers": layers.model_dump(), "markers": GIRL.model_dump(), "made_by": "base"}},
        "timeline": [{"look": "base", "start": {"chapter": 1}}]}}}
    (book / "refs" / "looks.json").write_text(json.dumps(doc), encoding="utf-8")


def girl_row(book: Path) -> dict:
    lf.bind(book, "girl")
    return lf.add_row(book, "refs/characters/girl/sheet.png")


def reader_for(sheet: dict):
    """The LOOK judge's one reader: the sheet-row question gets the canned list, every
    other question (look-back, trait card) what the house fixtures answer."""
    other = lf.tools()["reader"]

    def read(picture, question):
        return json.dumps(sheet) if question in (sheet_row.ASK, sheet_row.EYES_ASK) else other(picture, question)
    return read


def test_the_look_gate_refuses_a_sheet_that_contradicts_its_row(tmp_path):
    book = lf.a_book(tmp_path)
    a_table(book, "girl", OLD_GIRL)
    row = girl_row(book)
    v = look.judge(book, [row], **{**lf.tools(), "reader": reader_for(LACE_SHEET)})
    assert not v.passed
    assert {"row_top_colour", "row_eyes"} <= {f.kind for f in v.faults if f.where == row["path"]}


def test_the_look_gate_passes_the_aligned_sheet(tmp_path):
    book = lf.a_book(tmp_path)
    a_table(book, "girl", NEW_GIRL)
    row = girl_row(book)
    v = look.judge(book, [row], **{**lf.tools(), "reader": reader_for(GOOD_SHEET)})
    assert not any(f.kind.startswith("row_") for f in v.faults)


def test_a_book_without_a_look_table_asks_nothing(tmp_path):
    book = lf.a_book(tmp_path)
    row = girl_row(book)
    model = FakeModel(GOOD_SHEET)
    fallback = lf.tools()["reader"]
    look.judge(book, [row], **{**lf.tools(), "reader": lambda p, q: model(p, q) if q in (sheet_row.ASK, sheet_row.EYES_ASK)
                               else fallback(p, q)})
    assert model.asked == []


def test_the_sheet_ladder_climbs_on_a_row_fault():
    assert {"row_headwear_colour", "row_headwear_material", "row_top_colour", "row_eyes"} <= sheet_ladder.HARD
    assert "row_headwear" not in sheet_ladder.HARD
    assert sheet_row.KINDS <= look.HARD


# ---- the eyes are read on the head, not the whole sheet ---------------------------

def test_the_head_box_is_the_top_of_the_figure_on_a_gradient():
    import numpy as np
    a = np.zeros((600, 400, 3), dtype=np.uint8)
    a[:] = np.linspace(40, 120, 600, dtype=np.uint8)[:, None, None]       # a vertical gradient backdrop
    a[100:500, 180:220] = (230, 200, 60)                                    # the figure
    left, top, right, bottom = sheet_row.head_box(a)
    assert top == 100 and 180 <= left and right <= 220 and bottom - top == int(400 * sheet_row.HEAD_SHARE)


def test_the_eyes_question_goes_to_the_head_crop(tmp_path):
    from PIL import Image
    import numpy as np
    a = np.full((600, 400, 3), 90, dtype=np.uint8)
    a[100:500, 180:220] = (230, 200, 60)
    sheet = tmp_path / "sheet.png"
    Image.fromarray(a).save(sheet)
    seen = []
    model = FakeModel(GOOD_SHEET)
    sheet_row.judge(sheet, NEW_GIRL, GIRL, lambda p, q: seen.append((Path(p), q)) or model(p, q))
    eyes = [p for p, q in seen if q == sheet_row.EYES_ASK]
    assert len(eyes) == 1 and eyes[0] != sheet and Image.open(eyes[0]).size[1] < 600


def test_an_unread_eye_is_no_contradiction():
    answers = iter([json.dumps(GOOD_SHEET), "no idea"])
    assert sheet_row.judge(Path("s.png"), NEW_GIRL, GIRL, lambda p, q: next(answers)).passed


def test_a_red_read_of_the_girl_in_a_grey_pinafore_over_a_red_blouse_is_her_row():
    """The row names both garments; a read of either colour is the row (replay: a second load
    read the redrawn girl's large red sleeves as the main garment)."""
    assert sheet_row.garment_colours(NEW_GIRL.top) == {"grey", "red"}
    assert sheet_row.judge(Path("s.png"), NEW_GIRL, GIRL, FakeModel({**GOOD_SHEET, "top_colour": "red"})).passed


def test_boots_are_not_the_garment():
    assert sheet_row.garment_colours(OLD_GIRL.top) == {"grey"}


def test_hollow_eyes_need_both_reads_to_agree():
    """Whole sheet and head crop each read once: Poole's white eyes read hollow on the head
    and small on the sheet, the lace girl hollow on both."""
    answers = iter([json.dumps({**GOOD_SHEET, "eyes": "hollow"}), json.dumps({"eyes": "irises"})])
    assert sheet_row.judge(Path("s.png"), NEW_GIRL, GIRL, lambda p, q: next(answers)).passed
