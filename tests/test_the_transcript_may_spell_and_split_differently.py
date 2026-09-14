"""A transcript is allowed to differ on SPELLING and on WORD BOUNDARIES.

`error_rate` already folds apostrophes, accents, fillers and honorifics -- all
places where a transcript says the same sound in different characters.  Two more
belong with them, and both cost episode 4 a QC failure on a line that was read
perfectly:

    planned   "We picked our way among dirty children and under lines of
               discoloured linen."
    heard     "We picked our way among dirty children and underlines of
               discolored linen."

    under + lines -> underlines   one sound, two words or one
    discoloured   -> discolored   one sound, British or American

Three word-errors in thirteen words is 0.231, over the 0.20 wall, and the audio
is fine.  The script is Victorian British prose and the transcriber writes
American; every "colour", "neighbour", "grey" and "realise" in eleven remaining
chapters would do this again.

The spelling fold does NOT have to be correct English, because it is applied to
BOTH sides -- it only has to be consistent.  What it must not do is collapse two
genuinely different words into one and hide a real mistake, which is why the
rules are suffix-shaped and narrow rather than a blanket vowel-strip.
"""
from studio.voice_qc import error_rate, normalised


def test_the_episode_four_line_passes():
    """0.231 before, over the 0.20 wall.  The spelling costs nothing and the
    merge costs ONE -- a merge is one difference, not none -- so 1/13 = 0.077."""
    meant = "We picked our way among dirty children and under lines of discoloured linen."
    heard = "We picked our way among dirty children and underlines of discolored linen."
    rate = error_rate(heard, meant)
    assert round(rate, 3) == 0.077 and rate < 0.20


# ---- spelling ---------------------------------------------------------------

def test_our_and_or_are_one_word():
    assert error_rate("the color of his neighbor's honor", "the colour of his neighbour's honour") == 0.0


def test_ise_and_ize_are_one_word():
    assert error_rate("he realized it", "he realised it") == 0.0


def test_re_and_er_are_one_word():
    assert error_rate("the center of the theater", "the centre of the theatre") == 0.0


def test_grey_and_gray_are_one_word():
    assert error_rate("a gray morning", "a grey morning") == 0.0


def test_a_doubled_l_is_one_word():
    assert error_rate("he traveled and marveled", "he travelled and marvelled") == 0.0


def test_short_our_words_are_left_alone():
    """`our`, `four`, `hour`, `your`, `pour` are not -our spellings."""
    for word in ("our", "four", "hour", "your", "pour", "tour", "sour"):
        assert normalised(word) == [word], word


# ---- word boundaries --------------------------------------------------------

def test_two_words_heard_as_one_cost_one_error():
    assert error_rate("underlines", "under lines") < 0.6


def test_one_word_heard_as_two_costs_one_error():
    assert error_rate("under lines", "underlines") <= 1.0


def test_a_merge_is_cheaper_than_a_wrong_word():
    """"under lines" -> "underlines" is one error, not two."""
    merged = error_rate("the underlines of linen", "the under lines of linen")
    wrong = error_rate("the elephant of linen", "the under lines of linen")
    assert merged < wrong


# ---- a real mistake is still a mistake --------------------------------------

def test_a_wrong_word_is_still_wrong():
    assert error_rate("the colour of his hat", "the colour of his cat") > 0.0


def test_a_dropped_word_is_still_dropped():
    assert error_rate("we picked way among children", "we picked our way among children") > 0.0


def test_two_different_words_are_not_folded_together():
    """The fold must not hide a real error by collapsing distinct words."""
    assert error_rate("he poured it", "he pored it") > 0.0
    assert error_rate("the floor", "the flour") > 0.0
