"""A missing wardrobe card falls back to the BUST, never to another state.

`cast_sheet` tried, in order: the state card, the per-setup variant, then
`sorted(glob("char-<who>_*.png"))[0]`, then the bust.  That third rung is an
ALPHABETICAL choice among semantically incompatible wardrobes, and alphabetical
order has no opinion about clothes.

MEASURED on this book, 2026-09-13.  No `char-*_outdoor.png` exists for anyone --
only the `.prompt.txt` files; the cards were written and never drawn.  So every
outdoor setup resolved to whatever sorted first:

    john_watson      outdoor -> char-john_watson_bench.png      (an indoor bench)
    sherlock_holmes  outdoor -> char-sherlock_holmes_bench.png  (= _lab, the muffler card)
    g_lestrade       outdoor -> char-g_lestrade_indoor.png
    tobias_gregson   outdoor -> char-tobias_gregson_indoor.png

Episode 3's `cab` and `garden_path` are both outdoors, so two paid sheets and
four rendered takes drew the wrong wardrobe while `hat_line` printed "the bowler
hat is on his head in every panel of this sheet".  The words said hat-on and the
attached picture showed a man bare-headed indoors.

THE BUST IS THE HONEST FLOOR, and it is the one `cast_sheet`'s own docstring
already names.  It is also, for an OUTDOOR setup, the closer picture: the bust is
the one drawn with the hat on.  What it is not is a silent claim to be a
wardrobe it isn't.
"""
from pathlib import Path

from studio.episode_seq_board import cast_sheet


def a_book(tmp_path: Path, *names: str) -> Path:
    out = tmp_path / "refs" / "characters"
    out.mkdir(parents=True)
    for name in names:
        (out / name).write_bytes(b"")
    return tmp_path


def test_the_state_card_wins_when_it_exists(tmp_path):
    book = a_book(tmp_path, "char-john_watson.png", "char-john_watson_outdoor.png",
                  "char-john_watson_bench.png")
    assert cast_sheet(book, "john_watson", "cab", "outdoor").name == "char-john_watson_outdoor.png"


def test_a_missing_state_card_takes_the_bust_not_another_wardrobe(tmp_path):
    """The live case: no `_outdoor.png`, and `_bench` must not stand in for it."""
    book = a_book(tmp_path, "char-john_watson.png", "char-john_watson_bench.png",
                  "char-john_watson_indoor.png", "char-john_watson_lab.png")
    assert cast_sheet(book, "john_watson", "cab", "outdoor").name == "char-john_watson.png"


def test_the_per_setup_variant_still_beats_the_bust(tmp_path):
    """Episode 1's naming, which is a deliberate per-setup card and not a guess."""
    book = a_book(tmp_path, "char-john_watson.png", "char-john_watson_lab.png")
    assert cast_sheet(book, "john_watson", "lab", "indoor").name == "char-john_watson_lab.png"


def test_the_bust_is_the_floor_when_nothing_was_drawn(tmp_path):
    book = a_book(tmp_path, "char-stamford.png")
    assert cast_sheet(book, "stamford", "criterion", "indoor").name == "char-stamford.png"


def test_no_state_named_still_reaches_the_per_setup_card(tmp_path):
    book = a_book(tmp_path, "char-john_watson.png", "char-john_watson_lab.png")
    assert cast_sheet(book, "john_watson", "lab").name == "char-john_watson_lab.png"


def test_no_state_named_and_no_setup_card_takes_the_bust(tmp_path):
    """A caller that forgets the state gets the FLOOR, not an arbitrary wardrobe --
    which is what `redraw_panel.py` was silently doing to the hall's panels."""
    book = a_book(tmp_path, "char-john_watson.png", "char-john_watson_bench.png",
                  "char-john_watson_indoor.png")
    assert cast_sheet(book, "john_watson", "hall").name == "char-john_watson.png"


def test_indoor_still_finds_its_own_card(tmp_path):
    book = a_book(tmp_path, "char-john_watson.png", "char-john_watson_indoor.png",
                  "char-john_watson_bench.png")
    assert cast_sheet(book, "john_watson", "hall", "indoor").name == "char-john_watson_indoor.png"
