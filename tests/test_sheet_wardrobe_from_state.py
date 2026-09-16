"""The sheet's WARDROBE block reads `wardrobe[state]`, and it names a garment.

MEASURED on episode 9 (`docs/analysis/ep08_ep09_why_worse.md`, cause 8): the
WARDROBE block was EMPTY of clothes for every Part Two character, because
`seq_boards.physicals()` read garments from refs.json `physical` and the Utah
rows keep their garments in `wardrobe[state]`.  "These stay the same in every
panel" held nothing, and the drawer dressed Lucy, Hope and Ferrier afresh on
every sheet.

So `physicals()` carries the wardrobe states beside the invariant physical,
the block joins the two for THIS setup's state, and a named cast member whose
line names no garment is a HARD fault at the free gate.
"""
import importlib.util
import json
from pathlib import Path

import pytest

from studio import episode_seq_board as sq, sheet_gate as gate
from studio.affirm import negations
from studio.episode_spec import Setup

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures" / "episodes"

LUCY = {"physical": "A young woman of about twenty, long chestnut hair parted in the centre and worn loose.",
        "wardrobe": {"outdoor": "wears a broad-brimmed cream straw hat hanging back off her shoulders on its "
                                "ribbon, a slate-blue divided riding skirt over brown riding boots, and both "
                                "hands bare on the reins",
                     "indoor": "is bare-headed with the chestnut hair gathered back, in a plain grey-blue "
                               "cotton house dress with a narrow white collar, and both hands bare"}}
WATSON = ("A man in his late twenties, as thin as a lath, wearing a fawn tweed overcoat; a brown bowler "
          "hat, on his head outdoors and in his left hand indoors.")

PARLOUR = Setup(described="The parlour of a log villa.", cast=["lucy_ferrier"], outdoors=False)
ROAD = Setup(described="The high road into the city.", cast=["lucy_ferrier"], outdoors=True)


def seq_boards():
    spec = importlib.util.spec_from_file_location("ep_seq_boards", ROOT / "scripts/episode/seq_boards.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture_prompts(name: str) -> dict[str, str]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ---- the source -----------------------------------------------------------------

def test_physicals_carries_the_wardrobe_states_beside_the_physical(tmp_path):
    refs = tmp_path / "refs"
    refs.mkdir()
    (refs / "refs.json").write_text(json.dumps({"refs": [
        {"kind": "character", "entity_id": "lucy_ferrier", **LUCY},
        {"kind": "character", "entity_id": "john_watson", "physical": WATSON},
        {"kind": "prop", "entity_id": "violin", "physical": "a violin"}]}), encoding="utf-8")
    rows = seq_boards().physicals(tmp_path)
    assert set(rows) == {"lucy_ferrier", "john_watson"}
    assert rows["lucy_ferrier"]["physical"] == LUCY["physical"]
    assert rows["lucy_ferrier"]["wardrobe"]["indoor"].startswith("is bare-headed")
    assert rows["john_watson"]["physical"] == WATSON and rows["john_watson"]["wardrobe"] == {}


# ---- the block -----------------------------------------------------------------

def test_an_indoor_sheet_dresses_the_cast_from_the_indoor_state():
    text = sq.wardrobe_block(PARLOUR, {"lucy_ferrier": LUCY})
    assert "LUCY FERRIER: " in text
    assert "plain grey-blue cotton house dress" in text
    assert "riding skirt" not in text
    assert "Lucy Ferrier is bare-headed" in text
    assert negations(text) == [] and "indoors" not in text and "outdoors" not in text


def test_an_outdoor_sheet_dresses_the_cast_from_the_outdoor_state():
    text = sq.wardrobe_block(ROAD, {"lucy_ferrier": LUCY})
    assert "divided riding skirt" in text and "house dress" not in text
    assert "Lucy Ferrier wears a broad-brimmed cream straw hat" in text
    assert "on his head" not in text  # the state line IS the hat fact; no template hat line over it


def test_the_invariant_physical_still_opens_the_line():
    text = sq.wardrobe_block(PARLOUR, {"lucy_ferrier": LUCY})
    line = next(l for l in text.splitlines() if l.startswith("LUCY FERRIER:"))
    assert line.index("long chestnut hair") < line.index("house dress")


def test_a_plain_string_row_still_reads_as_it_always_did():
    """The London rows and every older caller hand a bare string; the hat line
    is still derived from its conditional clauses."""
    street = Setup(described="A street.", cast=["john_watson"], outdoors=True)
    text = sq.wardrobe_block(street, {"john_watson": WATSON})
    assert "brown bowler hat is on his head in every panel" in text and "fawn tweed overcoat" in text


def test_the_references_block_names_the_clothes_it_asks_to_keep():
    text = sq.references_block(PARLOUR, {"lucy_ferrier": LUCY})
    assert "house dress" in text and "Keep exactly this face, hair, build and these clothes" in text


def test_a_row_with_no_line_for_this_state_falls_back_to_the_physical():
    half = {"physical": LUCY["physical"], "wardrobe": {"outdoor": LUCY["wardrobe"]["outdoor"]}}
    text = sq.wardrobe_block(PARLOUR, {"lucy_ferrier": half})
    assert "long chestnut hair" in text and "riding skirt" not in text


def test_contract_faults_reads_the_physical_of_a_wardrobe_row():
    long = ("A man in his late twenties, as thin as a lath, as brown as a nut, dark hair swept back, "
            "a thin waxed moustache, a brown bowler hat, a brown tweed overcoat over a tweed "
            "waistcoat with a watch chain and a white cravat pinned with a stud, both hands bare to "
            "the wrist and sunburnt. The stick stands hip high, its shaft as thick as one finger.")
    assert gate.contract_faults({"x": {"physical": long, "wardrobe": {}}})
    assert not gate.contract_faults({"x": {"physical": "A short man.", "wardrobe": {}}})


# ---- the gate ------------------------------------------------------------------

def test_a_cast_line_that_names_no_garment_is_a_hard_fault():
    prompt = ("WARDROBE\nThese stay the same in every panel of this sheet.\n"
              "LUCY FERRIER: A young woman of about twenty, long chestnut hair cut to the collar. "
              "Lucy Ferrier is bareheaded in every panel of this sheet.\n"
              "JOHN WATSON: A thin man in a fawn tweed overcoat.\n"
              "Every hand in every panel is bare skin.\n\nPANELS\n")
    found = gate.garments_named(prompt)
    assert [(f.check, f.panel, f.hard) for f in found] == [("WARDROBE", "sheet", True)]
    assert found[0].note == "WARDROBE names no garment for LUCY FERRIER"


def test_a_sheet_with_no_cast_has_no_garment_to_name():
    assert gate.garments_named("WARDROBE\nThese stay the same in every panel of this sheet.\n"
                               "Every hand in every panel is bare skin.\n\nPANELS\n") == []


def test_the_rebuilt_block_passes_its_own_gate():
    text = "WARDROBE\n" + sq.wardrobe_block(PARLOUR, {"lucy_ferrier": LUCY}) + "\n\nPANELS\n"
    assert gate.garments_named(text) == []


def test_the_whole_sheet_runs_the_garment_check():
    prompt = ("SHEET\nA film storyboard sheet: a 3 by 1 grid of 3 equal square 1:1 panels\n\n"
              "WARDROBE\nThese stay the same in every panel of this sheet.\nLUCY FERRIER: A young woman.\n"
              "Every hand in every panel is bare skin.\n\nPANELS\n")
    segs = [{"shot": k, "sub": 0, "size": "medium", "path": 0.1, "faces": [], "camera": "", "frame": "x",
             "motion": "y", "at_rest": "", "end_frame": "", "changed": "", "crowd": ""} for k in range(3)]
    found = gate.sheet_findings(segs, PARLOUR, prompt, (3, 1, (1536, 512)))
    assert any(f.check == "WARDROBE" and f.hard for f in found)


# ---- the fixtures --------------------------------------------------------------

def test_ep09_as_drawn_fails_for_lucy_hope_and_ferrier():
    prompts = fixture_prompts("ep09_sheet_prompts.json")
    found = gate.garments_named(prompts["seq_farm_parlour_0.prompt.txt"])
    assert sorted(f.text for f in found) == ["JEFFERSON HOPE", "JOHN FERRIER", "LUCY FERRIER"]
    assert all(f.hard for f in found)
    assert all(gate.garments_named(t) for n, t in prompts.items() if "LUCY FERRIER:" in t)


def test_ep07_as_drawn_passes_on_every_sheet():
    for text in fixture_prompts("ep07_sheet_prompts.json").values():
        assert gate.garments_named(text) == []


def test_ep05_as_drawn_passes_except_for_madame_sawyer():
    """A true finding on a sheet the owner liked: Madame Sawyer's `physical`
    names a face and hair and no clothes, and her refs row keeps her wardrobe in
    `wardrobe[state]` like the Utah rows -- so the two ep05 sheets she stands on
    dressed her from nothing.  Every other ep05 line names a garment."""
    for name, text in fixture_prompts("ep05_sheet_prompts.json").items():
        assert [f.text for f in gate.garments_named(text)] == (
            ["MADAME SAWYER"] if "MADAME SAWYER:" in text else []), name
