"""SHEET-ROW reads the hair too (Jekyll ep01-06 retro, 2026-10-30).

ep06: Poole's base sheet drew dark hair where his row says thinning straw-coloured sandy hair.  SHEET-ROW asked
only for headwear, the main garment and the eyes, so the sheet passed LOOK; G-WHO then read Poole as Utterson on
four takes, the sheet was redrawn after the renders, and takes 17-27 were retaken and re-drawn at 2K (148 min).
The sheet now gets G-WHO's own ask before anything renders, and a figure whose hair colour the row rules out is a
HARD row_hair fault.  Hair only: G-WHO's calibration found coat and beard reads wrong on eye-passed takes."""
from studio.continuity_spec import Markers
from studio.judges import sheet_row

POOLE = Markers(hair_colour="fair", facial_hair="none")
DARK = '{"figures": [{"headwear": "none", "hair": "black", "facial_hair": "none", "coat": "black", "back_to_camera": "no"}]}'
SANDY = '{"figures": [{"headwear": "none", "hair": "blond", "facial_hair": "none", "coat": "black", "back_to_camera": "no"}]}'
GREY = '{"figures": [{"headwear": "none", "hair": "grey", "facial_hair": "none", "coat": "black", "back_to_camera": "no"}]}'
HIDDEN = '{"figures": [{"headwear": "top hat", "hair": "not_visible", "facial_hair": "none", "coat": "black"}]}'


def read(said):
    return lambda picture, prompt: said


def test_a_dark_haired_sheet_for_a_sandy_row_fails():
    faults = sheet_row.hair_faults("sheet.png", POOLE, read(DARK), "refs/characters/poole/sheet.png")
    assert [(f.kind, f.severity) for f in faults] == [("row_hair", "high")]


def test_the_rows_own_hair_passes():
    assert sheet_row.hair_faults("sheet.png", POOLE, read(SANDY), "w") == []


def test_fair_read_as_grey_is_no_contradiction():
    assert sheet_row.hair_faults("sheet.png", POOLE, read(GREY), "w") == []      # figure_who.CONFUSED


def test_hair_out_of_sight_judges_nothing():
    assert sheet_row.hair_faults("sheet.png", POOLE, read(HIDDEN), "w") == []


def test_a_row_that_names_no_hair_colour_judges_nothing():
    assert sheet_row.hair_faults("sheet.png", Markers(), read(DARK), "w") == []
