"""The single-panel redraw is drawn under ITS EPISODE'S place and light.

Measured on episode 10: all four `boards/panels/*.prompt.txt` say
"Photoreal 35 mm still, 1881 London, gaslight from one side, deep shadow, film
grain." over Ferrier's Utah farm in 1860 -- the ep08 bug in a third module.
`seq_boards.main` calls `house_style.adopt(episode.where, episode.light)`
before it builds a sheet; `redraw_panel.main` never did, so `sq.single()`
printed the book's default.  The test asserts on the BUILT PROMPT.
"""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from studio import episode_seq_board as sq, house_style
from studio.episode_spec import Setup

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def rp():
    spec = importlib.util.spec_from_file_location("redraw_panel", ROOT / "scripts/episode/redraw_panel.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["redraw_panel"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _book_style():
    house_style.adopt("", "")
    yield
    house_style.adopt("", "")


FARM = SimpleNamespace(where="Ferrier's farm, Utah, 1860", light="low side sun, deep black shadow", aspect="1:1")
PARLOUR = Setup(described="The sitting-room of a log villa on a June morning.", cast=[])
PANEL = {"shot": 13, "sub": 0, "size": "medium_close", "path": 0.5, "faces": [], "end": False,
         "frame": "Medium close on Brigham Young from above, both hands flat on the pine table.",
         "camera": "above the table top looking straight down, a 50mm lens", "motion": "he looks up",
         "at_rest": "His sandy head fills the TOP half of the frame.", "end_frame": "", "changed": "", "crowd": ""}


def style_of(text: str) -> str:
    return text.split("STYLE\n")[1].split("\n\n")[0]


def test_single_style_line_matches_sheet(rp):
    single = rp.prompt_for(FARM, PANEL, PARLOUR, {})
    house_style.adopt(FARM.where, FARM.light)
    sheet = sq.prompt([PANEL], PARLOUR, {}, previous=False, first=True, geography=False, aspect="1:1")
    assert style_of(single) == style_of(sheet)
    assert "Utah, 1860" in style_of(single) and "1881 London" not in single


def test_the_redraw_adopts_the_place_itself_and_not_from_a_previous_run(rp):
    """The book's default is in force when the script starts; the prompt it
    builds must still carry the plan's place."""
    assert "1881 London" in house_style.stills()
    assert "1881 London" not in rp.prompt_for(FARM, PANEL, PARLOUR, {})


def test_the_single_opens_its_picture_with_the_size_word(rp):
    picture = rp.prompt_for(FARM, PANEL, PARLOUR, {}).split("THE PICTURE\n")[1].split("\n\n")[0]
    assert picture.startswith("MEDIUM CLOSE-UP, camera above the table top")


def test_an_end_panel_goes_through_the_end_writer(rp):
    end = dict(PANEL, end=True, changed="his head has come up a finger's breadth")
    text = rp.prompt_for(FARM, end, PARLOUR, {})
    assert "Image 1 is this same shot ONE MOMENT EARLIER" in text and "Utah, 1860" in text
