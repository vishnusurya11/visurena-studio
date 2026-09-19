"""A references-only take stages the setup's PROP sheet after the place.

WotW ep02 (2026-09-19): the cylinder is the story object of chapter 2 and the
one location picture of the pit draws it as a tile patchwork. The owner's pack
has ONE sheet per key prop (`refs/props/<id>/sheet.png`); a take whose setup
names that prop must stage the sheet and define it, or the picture the graph
stages has no definition and L11 counts one picture short.
"""
import json
import re

import pytest

from studio import episode_ref_official as ro
from studio import pack_refs
from studio.episode_spec import Line, Shot

SHOT = Shot(index=5, section="setup", setup="pit", size="wide", faces=[], path=0.2,
            frame="Wide of the pit on the heath at dawn: the huge crusted cylinder lying half-buried in the sand.",
            camera="on the rim of the pit at a standing man's eye, a 35mm lens. The low sun comes from the "
                   "RIGHT onto the crust and leaves the far side of the pit black",
            at_rest="The cylinder fills the CENTRE of the frame from the LEFT third to the RIGHT third, the "
                    "sand walls rise at the BOTTOM edge and the heath lies across the TOP edge.",
            motion="The camera tilts down from the pines to the cylinder; thin smoke rises off the crust.")
PLACED = [{"index": 5, "t_start": 30.0, "seconds": 5.0}]
LINES = [Line(index=4, kind="narration", speaker="n", text="The Thing lay half-buried.", shot=5)]
AT = {4: (30.25, 2.0)}
PIT = "A raw sand crater on a heath at dawn in 1894."
PROP = ("the Martian cylinder", "A colossal crusted metal cylinder, thirty yards across.")


def built(**kw):
    kw = {"faces": [], "physical": {}, "described": PIT, "narrator": "n", "refs": 2,
          "has_plate": True, "cells_staged": False, "check_lint": False, "props": [PROP], **kw}
    return ro.build([SHOT], PLACED, LINES, AT, 121, **kw)


def test_the_prop_is_the_picture_after_the_plate():
    text = built()
    assert "<Subject 2> is the Martian cylinder in <Picture 2>: A colossal crusted metal cylinder" in text


def test_the_prop_is_retained_as_a_definition():
    text = built()
    assert re.search(r"<Subject 2> \(the Martian cylinder[^)]*\): partially_preserved", text)


def test_the_lint_counts_the_prop_among_the_staged_pictures():
    assert not [f for f in ro.lint(built(check_lint=False), {"refs": 2}) if f.startswith("L11")]


def test_a_prop_beside_a_storyboard_cell_is_refused():
    with pytest.raises(ValueError, match="references-only"):
        built(cells_staged=True)


def test_no_prop_leaves_the_prompt_as_it_was():
    assert built(props=[], refs=1) == built(props=None, refs=1)


def test_the_prop_sheet_is_found_in_the_pack(tmp_path):
    sheet = tmp_path / "refs" / "props" / "martian_cylinder" / "sheet.png"
    sheet.parent.mkdir(parents=True)
    sheet.write_bytes(b"png")
    assert pack_refs.prop_sheet(tmp_path, "martian_cylinder") == sheet
    assert pack_refs.prop_sheet(tmp_path, "red_weed") is None


def test_the_prop_row_is_the_body_and_the_scale_and_no_later_state(tmp_path):
    (tmp_path / "analysis" / "props").mkdir(parents=True)
    (tmp_path / "analysis" / "props" / "martian_cylinder.json").write_text(json.dumps({
        "name": "Martian cylinder",
        "profile": {"physical": "A colossal hollow cylinder. Once open, a dark cavity faces the sky.",
                    "scale": "Thirty yards across."}}), encoding="utf-8")
    name, text = pack_refs.prop_row(tmp_path, "martian_cylinder")
    assert name == "the Martian cylinder"
    assert text == "A colossal hollow cylinder. Thirty yards across."


def test_only_drawn_props_of_the_setup_are_staged(tmp_path):
    (tmp_path / "analysis" / "props").mkdir(parents=True)
    for pid in ("martian_cylinder", "red_weed"):
        (tmp_path / "analysis" / "props" / f"{pid}.json").write_text(json.dumps(
            {"name": pid, "profile": {"physical": "A thing.", "scale": "Big."}}), encoding="utf-8")
    sheet = tmp_path / "refs" / "props" / "martian_cylinder" / "sheet.png"
    sheet.parent.mkdir(parents=True)
    sheet.write_bytes(b"png")
    staged = pack_refs.props_for(tmp_path, ["martian_cylinder", "red_weed"])
    assert staged == [(sheet, ("the martian_cylinder", "A thing. Big."))]


def test_a_name_that_carries_its_article_is_not_doubled_and_the_scale_is_its_first_clause(tmp_path):
    (tmp_path / "analysis" / "props").mkdir(parents=True)
    (tmp_path / "analysis" / "props" / "martian_cylinder.json").write_text(json.dumps({
        "name": "the Martian cylinder",
        "profile": {"physical": "A hollow cylinder.",
                    "scale": "End about thirty yards across (Wells); the screw-thread that emerges is two feet long."}}),
        encoding="utf-8")
    name, text = pack_refs.prop_row(tmp_path, "martian_cylinder")
    assert name == "the Martian cylinder"
    assert text == "A hollow cylinder. End about thirty yards across."
