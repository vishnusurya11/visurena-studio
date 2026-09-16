r"""The style line the drawer and the renderer are given names THIS episode's place.

`Episode.palette` was added for episode 8 because the book's palette ends
"1881 London" and put Georgian terraced streets in the Utah desert. It was wired
into `frames.py` — the LOCATION PLATE — and reported as fixed.

It reached nothing else. Measured on episode 8's own artefacts, after the fix
shipped:

    "1881 London" in the paid storyboard prompts   13 of 13 sheets
    "1881 London" in the take prompts sent to H3   28 of 28 takes

because the style sentence is a hard-coded constant in four modules:

    studio/episode_seq_board.py:709   STYLE   (the sheet: start, take and END)
    studio/episode_ref_official.py:44 STYLE   (the H3 take prompt)
    studio/episode_take_prompt.py:20  STYLE   (the other take prompt path)
    studio/episode_board.py:25        STILL   (board stills)

So episode 8 was DRAWN and RENDERED under an instruction that said 1881 London
over an 1847 desert, while the plate alone got the palette and the fix was
called done. That is the fault this repo keeps producing and the one it has a
note about: a change that looks right, passes its test, and reaches no artefact.
The test written with that fix only exercised `location_prompt`.

So this file asserts on the BUILT PROMPT, not on a function. `house_style.adopt`
follows `canvas.adopt` and the `W, H` globals that `assemble` and `takes_r2v`
already rebind from the plan — one place, set once per run, read everywhere.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import house_style

BOOK = ROOT / "library/20260822113400_a-study-in-scarlet"
DESERT = ("Bleached high-key palette of bone white and alkali grey; the alkali flats of "
          "Utah Territory, 1847; American frontier, sunlight only.")


@pytest.fixture(autouse=True)
def _restore():
    yield
    house_style.adopt("")


def test_the_house_default_is_the_book_it_was_written_for():
    house_style.adopt("")
    assert "1881 London" in house_style.stills()
    assert "1881 London" in house_style.live()


def test_an_adopted_palette_replaces_it():
    house_style.adopt(DESERT)
    for said in (house_style.stills(), house_style.live()):
        assert "1881 London" not in said
        assert "Utah Territory" in said


def test_the_photographic_half_survives():
    """The palette says the place; the style still says how it is photographed."""
    house_style.adopt(DESERT)
    assert "35 mm" in house_style.stills()
    assert "film grain" in house_style.stills()
    assert "live-action" in house_style.live()


def test_adopting_nothing_puts_the_book_back():
    house_style.adopt(DESERT)
    house_style.adopt("")
    assert "1881 London" in house_style.stills()


def test_the_sheet_builder_reads_it_rather_than_a_constant():
    from studio import episode_seq_board as sq
    house_style.adopt(DESERT)
    assert "1881 London" not in sq.style_line()
    assert "Utah Territory" in sq.style_line()


def test_the_take_builder_reads_it_too():
    from studio import episode_ref_official as ro
    house_style.adopt(DESERT)
    assert "1881 London" not in ro.style_line()
    assert "Utah Territory" in ro.style_line()


def test_no_module_still_hard_codes_the_place():
    """The grep that keeps this shut. A place name frozen into a constant is
    invisible to every episode that is somewhere else."""
    for name in ("episode_seq_board.py", "episode_ref_official.py",
                 "episode_take_prompt.py", "episode_board.py"):
        said = (ROOT / "studio" / name).read_text(encoding="utf-8")
        body = "\n".join(l for l in said.splitlines() if not l.strip().startswith("#"))
        assert 'STYLE = ("Photoreal' not in body and 'STYLE = "Photoreal' not in body, name
        assert 'STILL = ("Photoreal' not in body, name
