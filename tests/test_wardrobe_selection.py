"""A repair may not change the wardrobe, and a missing card may not be substituted.

TWO FAULTS, both measured on episode 3 on 2026-09-13, both of the same family:
a wardrobe card that does not exist becomes a DIFFERENT card instead of an error.

  W1  `scripts/episode/redraw_panel.py` called `cast_sheet(book, who, name)`
      while `scripts/episode/seq_boards.py` calls it with `setup.state`.  So the
      hall SHEET referenced `char-john_watson_indoor.png` and a $0.08 redraw of
      one of its own panels referenced `char-john_watson_bench.png` -- the same
      man holding a brown bowler, in an episode whose prose says "bare-headed"
      in every shot.  A repair that changes the wardrobe is not a repair.

  W2  `char-john_watson_outdoor.png` DOES NOT EXIST -- only its `.prompt.txt`
      does.  `cast_sheet` then falls through to
      `sorted(glob("char-<who>_*.png"))[0]`, and "bench" sorts before every
      other state, so every OUTDOOR setup in the episode silently referenced the
      bench wardrobe.  Nothing in any log said so.

This is the fault `cast_sheet`'s own docstring was written about: "the bust is
the picture with the hat on. All 19 episode 2 takes referenced Holmes in a
deerstalker and Watson in his bowler while their own prose said bare-headed."
It came back because the rule lived in a docstring and not in a test.
"""
from studio.episode_seq_board import cast_sheet


def cards(tmp_path, *names):
    out = tmp_path / "refs" / "characters"
    out.mkdir(parents=True)
    for n in names:
        (out / n).write_bytes(b"")
    return tmp_path


def test_the_state_card_is_chosen_when_it_exists(tmp_path):
    book = cards(tmp_path, "char-john_watson.png", "char-john_watson_indoor.png",
                 "char-john_watson_bench.png")
    assert cast_sheet(book, "john_watson", "hall", "indoor").name == "char-john_watson_indoor.png"


def test_dropping_the_state_is_what_picked_the_bench_card(tmp_path):
    """W1 exactly: the same call without `state`, against the same files on disk,
    returns a different wardrobe. This is the test that would have caught it."""
    book = cards(tmp_path, "char-john_watson.png", "char-john_watson_indoor.png",
                 "char-john_watson_bench.png")
    with_state = cast_sheet(book, "john_watson", "hall", "indoor")
    without = cast_sheet(book, "john_watson", "hall")
    assert with_state.name == "char-john_watson_indoor.png"
    # The alphabetical rung is gone, so a dropped state now lands on the BUST --
    # still the wrong picture for an indoor sheet, still a divergence worth
    # failing on, but no longer a silent claim to be a wardrobe it is not.
    assert without.name == "char-john_watson.png"
    assert with_state != without


def test_a_missing_state_card_no_longer_falls_back_alphabetically(tmp_path):
    """W2, FIXED.  This used to pin the substitution as behaviour so that it was
    at least NAMED somewhere.  The rung is now deleted: `outdoor` is asked for,
    `outdoor` is absent, and the bust comes back rather than `bench`."""
    book = cards(tmp_path, "char-john_watson.png", "char-john_watson_bench.png",
                 "char-john_watson_indoor.png")
    assert cast_sheet(book, "john_watson", "garden_path", "outdoor").name == "char-john_watson.png"


def test_the_bust_is_the_last_resort_only(tmp_path):
    book = cards(tmp_path, "char-john_watson.png")
    assert cast_sheet(book, "john_watson", "hall", "indoor").name == "char-john_watson.png"


def test_the_per_setup_card_still_beats_a_state_card_that_is_absent(tmp_path):
    book = cards(tmp_path, "char-john_watson.png", "char-john_watson_lab.png")
    assert cast_sheet(book, "john_watson", "lab", "indoor").name == "char-john_watson_lab.png"
