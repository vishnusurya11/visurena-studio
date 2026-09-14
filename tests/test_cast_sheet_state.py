"""A take references the WARDROBE CARD, not the bare identity bust.

`cast_sheet` looked for `char-<who>_<setup>.png` -- episode 1's naming, where a
variant was drawn per SETUP (`char-john_watson_lab.png`).  The contract moved to
one card per wardrobe STATE (`char-john_watson_indoor.png`, `cast_refs.STATES`),
so the lookup missed every time and fell back to the identity bust.

Measured on episode 2: all 19 takes attached `char-sherlock_holmes.png`, which
draws him in a tweed deerstalker with a scarf at his throat, and
`char-john_watson.png`, which draws him wearing the brown bowler -- while every
one of those takes' prose says "bare-headed".  The three indoor cards drawn for
this episode were wired to nothing.  It is the same fault as the moustache: the
reference picture and the words must be one statement.
"""
from studio.episode_seq_board import cast_sheet


def a_book(tmp_path, *names):
    chars = tmp_path / "refs" / "characters"
    chars.mkdir(parents=True)
    for n in names:
        (chars / n).write_bytes(b"png")
    return tmp_path


def test_the_state_card_is_preferred(tmp_path):
    book = a_book(tmp_path, "char-john_watson.png", "char-john_watson_indoor.png")
    assert cast_sheet(book, "john_watson", "breakfast", "indoor").name == "char-john_watson_indoor.png"


def test_the_outdoor_card_is_picked_for_an_outdoor_setup(tmp_path):
    book = a_book(tmp_path, "char-john_watson.png", "char-john_watson_indoor.png",
                  "char-john_watson_outdoor.png")
    assert cast_sheet(book, "john_watson", "street", "outdoor").name == "char-john_watson_outdoor.png"


def test_episode_ones_per_setup_variant_still_wins_where_it_exists(tmp_path):
    """ep01 drew variants per setup and its takes must keep resolving to them."""
    book = a_book(tmp_path, "char-john_watson.png", "char-john_watson_lab.png")
    assert cast_sheet(book, "john_watson", "lab", "indoor").name == "char-john_watson_lab.png"


def test_the_bust_is_the_floor_when_no_card_was_drawn(tmp_path):
    book = a_book(tmp_path, "char-stamford.png")
    assert cast_sheet(book, "stamford", "criterion", "indoor").name == "char-stamford.png"


def test_a_missing_state_falls_back_to_the_bust_not_to_another_wardrobe(tmp_path):
    """AMENDED 2026-09-13. This used to assert that an INDOOR card stands in for a
    missing outdoor one, on the reasoning that the bust is the one with the hat
    on. Measured, that reasoning is backwards: outdoors the hat IS on, so the
    bust is the closer picture -- and the rung that delivered the indoor card was
    `sorted(glob(...))[0]`, which chose by alphabet, not by clothes. It sent two
    paid ep03 sheets and four takes out in a bench wardrobe. See
    `test_no_wardrobe_substitution.py`."""
    book = a_book(tmp_path, "char-john_watson.png", "char-john_watson_indoor.png")
    assert cast_sheet(book, "john_watson", "street", "outdoor").name == "char-john_watson.png"


def test_the_state_is_optional_so_old_callers_keep_working(tmp_path):
    book = a_book(tmp_path, "char-john_watson.png", "char-john_watson_lab.png")
    assert cast_sheet(book, "john_watson", "lab").name == "char-john_watson_lab.png"
