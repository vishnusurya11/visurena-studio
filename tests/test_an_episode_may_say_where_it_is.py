r"""Part Two is not in London, and the palette says it is.

`refs.json` carries ONE palette for the whole book:

    "Muted desaturated palette of soot-black, gaslight amber and cold grey, fog,
     deep shadow; 1881 London; practical period light sources."

`trailer_refs.location_prompt` puts it in front of every location plate
(`frames.py:61`), so every plate of every episode is told it is in London in
1881. That was true for seven episodes and it is false from the eighth: chapter
VIII opens on the Great Alkali Plain on 4 May 1847, and chapters IX to XIII stay
in Utah.

MEASURED. Episode 8's six plates were drawn against the book palette and three
of them came back as GEORGIAN TERRACED STREETS with the covered waggons driving
down them -- `caravan_column`, `bluff_base` and `young_waggon` -- and a fourth
framed its desert boulder through the doorway of a ruined brick building. The
setup prose said "the alkali plain, 1847" in every one of them; the sentence in
front of it said London, and London won.

So an episode may say where it is. The book palette stays the floor, because
seven episodes are built on it and nothing that does not declare a palette may
change; an episode that declares one overrides it for its own plates.

This is the same shape as `camera_end`, `FOREIGN_MIN`, `END_FLOOR`, `camera_ok`
and the witness gate: a constant that was measured on one world and applied to
the next. The cure is the same each time -- give the thing that KNOWS the answer
a way to say it, and default to the old behaviour when it does not.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import episode_home, episode_spec as es
from studio.trailer_refs import location_prompt

BOOK = ROOT / "library/20260822113400_a-study-in-scarlet"
LONDON = "1881 London"
PLAIN = "the alkali flats of Utah Territory, 1847"


def test_a_plan_may_carry_a_palette():
    assert "palette" in es.Episode.model_fields


def test_it_defaults_to_empty_so_nothing_changes_by_itself():
    assert es.Episode.model_fields["palette"].default == ""


def test_the_episode_palette_reaches_the_plate_prompt():
    said = location_prompt("The great alkali plain, 1847.", PLAIN)
    assert PLAIN in said
    assert LONDON not in said


def test_the_book_palette_is_still_used_when_the_episode_says_nothing():
    said = location_prompt("The sitting-room of 221B Baker Street.", LONDON)
    assert LONDON in said


def test_episode_8_declares_the_desert():
    """The episode that found this. If the plan stops declaring a palette its
    plates go back to being London streets."""
    if not (BOOK / "episodes/ep08/plan.json").exists():
        pytest.skip("episode 8 is not on this disk")
    episode = episode_home.load_plan(BOOK, 8)
    assert episode.palette, "episode 8 must declare its own palette"
    assert "London" not in episode.palette
    assert "1847" in episode.palette


def test_the_part_one_episodes_declare_nothing_and_keep_london():
    if not (BOOK / "episodes/ep07/plan.json").exists():
        pytest.skip("the book is not on this disk")
    for n in range(1, 8):
        episode = episode_home.load_plan(BOOK, n)
        assert episode.palette == "", f"ep{n:02d} gained a palette; its seven plates were "
