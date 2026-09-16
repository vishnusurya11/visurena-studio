r"""The style line is a place, a light with a direction and a black, and a grain.

MEASURED, docs/analysis/ep08_ep09_why_worse.md. The London clause that made
ep04-07 look like film was "deep shadow; practical period light sources" --
one source with a direction and a true black. Episode 9's `palette` replaced
it with a colour inventory ("gold ripe wheat, red road dust and deep green
pine ... sunlight only"), and the drawer obeyed the direction words it was
given, which were none: 5th-percentile luma 4-7 -> 16.5-31.5, 94 % of the
colour in one orange band, and the palette's OBJECTS stamped a gold wheat
foreground into five of six plates including a bare rock shoulder.

`house_style` pasted the whole palette paragraph into the sheet style line
(46 words) and the take style line (48 words, "only., 35 mm") where ep05-08
had 13. So the field is split: `where` says the place and date in six words,
`light` names a DIRECTION that throws shadow into frame and a BLACK, and the
rendered line is capped at the length that worked.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import house_style as hs

UTAH_WHERE = "Utah valley, June 1860"
UTAH_LIGHT = "low left sun, hard black shadows"
EP09_PALETTE = ("Warm high-summer palette of gold ripe wheat, red road dust and deep green "
                "pine, hard blue shadow under a clear bleached sky; the Utah valley and Salt "
                "Lake City, June 1860; American frontier, sunlight and lamplight only.")


@pytest.fixture(autouse=True)
def _restore():
    yield
    hs.adopt("", "")


def words(said: str) -> int:
    return len(said.split())


# ---- the house default ------------------------------------------------------

def test_the_house_is_london_with_the_deep_shadow_clause():
    hs.adopt("", "")
    assert hs.where() == "1881 London"
    assert "shadow" in hs.light()
    assert hs.light_faults(hs.light()) == []


def test_the_house_style_line_is_sixteen_words_or_fewer():
    hs.adopt("", "")
    assert words(hs.stills()) <= hs.MAX_STYLE_WORDS == 16, hs.stills()
    assert words(hs.live()) <= hs.MAX_STYLE_WORDS, hs.live()


def test_the_shape_is_photographic_where_light_grain():
    hs.adopt("", "")
    said = hs.stills()
    assert said.index("35 mm") < said.index("1881 London") < said.index("shadow") < said.index("grain")
    assert said.endswith("grain.")
    assert "live-action" in hs.live() and "35 mm" in hs.live() and "film grain" in hs.live()


# ---- an adopted place -------------------------------------------------------

def test_an_adopted_place_and_light_replace_london():
    hs.adopt(UTAH_WHERE, UTAH_LIGHT)
    for said in (hs.stills(), hs.live()):
        assert "1881 London" not in said
        assert UTAH_WHERE in said and UTAH_LIGHT in said
        assert words(said) <= hs.MAX_STYLE_WORDS, said


def test_the_line_has_no_pasted_period_and_no_mid_sentence_capital():
    """ep09's take line read "... lamplight only., 35 mm" -- a paragraph's own
    full stop pasted mid-line, and "Warm" capitalised in the middle."""
    hs.adopt(UTAH_WHERE + ".", UTAH_LIGHT + ".")
    for said in (hs.stills(), hs.live()):
        assert ".," not in said and ". " not in said[:-1]
        assert not any(w[0].isupper() for w in said.split()[1:] if w not in ("Utah", "June"))


def test_adopting_nothing_puts_the_book_back():
    hs.adopt(UTAH_WHERE, UTAH_LIGHT)
    hs.adopt("", "")
    assert "1881 London" in hs.stills()


def test_a_palette_paragraph_is_refused_as_a_place():
    """`seq_boards` and `takes_r2v` still call `adopt(episode.palette)`; a
    paragraph handed in as the place is the ep09 fault and must not render."""
    with pytest.raises(ValueError, match="palette"):
        hs.adopt(EP09_PALETTE)
    assert "1881 London" in hs.stills()


def test_a_place_alone_or_a_light_alone_is_refused():
    with pytest.raises(ValueError):
        hs.adopt(UTAH_WHERE, "")
    with pytest.raises(ValueError):
        hs.adopt("", UTAH_LIGHT)


# ---- the vocabulary ---------------------------------------------------------

@pytest.mark.parametrize("light", [
    "low sun from the left, long shadows across the ground, black under every eave",
    "gaslight from one side, deep shadow",
    "one oil lamp on the table, black beyond its reach",
    "window light from the right, the far wall in shadow",
    "low left sun, hard black shadows",
])
def test_a_light_with_a_direction_and_a_black_passes(light):
    assert hs.light_faults(light) == []


def test_a_light_with_no_direction_is_refused():
    bad = hs.light_faults("hard sunlight, deep shadow")
    assert bad and "direction" in bad[0]


def test_a_light_with_no_black_is_refused():
    bad = hs.light_faults("low sun from the left")
    assert bad and ("black" in bad[0] or "shadow" in bad[0])


@pytest.mark.parametrize("word", ["wheat", "dust", "pine", "sky"])
def test_the_palettes_objects_are_refused(word):
    bad = hs.light_faults(f"low sun from the left over the {word}, deep shadow")
    assert bad and word in bad[0]


def test_a_comma_list_of_three_nouns_is_an_inventory():
    bad = hs.light_faults("low sun from the left, red walls, green shutters and brown shingles, deep shadow")
    assert bad and "inventory" in bad[0]


def test_the_ep09_palette_fails_as_a_light_with_its_objects_named():
    bad = hs.light_faults(EP09_PALETTE)
    assert bad
    said = " ".join(bad)
    assert "wheat" in said and "palette" in said


def test_overhead_light_is_refused_outdoors():
    bad = hs.light_faults("hard sun overhead, black shadows")
    assert bad and "overhead" in bad[0]


def test_a_light_that_starts_with_a_capital_is_refused():
    assert hs.light_faults("Low sun from the left, deep shadow")


def test_where_is_six_words_or_fewer():
    assert hs.where_faults("Utah valley, June 1860") == []
    assert hs.where_faults("the Utah valley and Salt Lake City, June 1860")
    assert hs.where_faults("")


def test_the_vocabulary_is_stated_as_constants():
    for name in ("DIRECTIONS", "PRACTICALS", "BLACKS", "OBJECTS", "NO_SHADOW"):
        assert getattr(hs, name)


# ---- the consumers read it ---------------------------------------------------

def test_the_sheet_and_take_builders_read_it_rather_than_a_constant():
    from studio import episode_board as eb
    from studio import episode_ref_official as ro
    from studio import episode_seq_board as sq
    from studio import episode_take_prompt as tp
    hs.adopt(UTAH_WHERE, UTAH_LIGHT)
    for said in (sq.style_line(), ro.style_line(), tp.style_line(), eb.still_line()):
        assert "1881 London" not in said and UTAH_LIGHT in said
