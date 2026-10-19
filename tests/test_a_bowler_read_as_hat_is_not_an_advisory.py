"""A bowler read as a plain hat is no ADVISORY; a refusal still tells a boater from a bowler.

Jekyll Kawajiri ep01 (2026-10-18): the eye reads a bowler as `other_hat`, so the advisory fired on
a correct take.  Only the advisory joins the two; the hard comparison keeps them apart (H7), and a
boater stays distinct from a bowler in both."""
from studio import look_table as lt


def test_the_advisory_reads_a_bowler_and_a_hat_as_one_family():
    assert lt.family("headwear", "bowler", advisory=True) == lt.family("headwear", "other_hat", advisory=True)


def test_the_hard_comparison_keeps_them_apart():
    assert lt.family("headwear", "bowler") == "bowler"
    assert lt.family("headwear", "bowler") != lt.family("headwear", "other_hat")


def test_a_boater_stays_distinct_from_a_bowler_everywhere():
    for advisory in (False, True):
        assert lt.family("headwear", "boater", advisory) != lt.family("headwear", "bowler", advisory)


def test_other_keys_ignore_the_advisory_flag():
    assert lt.family("hair_colour", "brown", advisory=True) == "dark"
    assert lt.family("top", "coat", advisory=True) == "coat"
