"""Who is actually in this shot.

The plan cast sherlock_holmes in all nine beats of A Study in Scarlet --
including the Utah chapters, which he is not in.  `beat_of` put the lead at the
head of the order and then took [:1], so the element's own cast was read and
discarded.  Every shot was the same man, which is both the repetition the
viewer saw and a claim about the book that is false.
"""
from __future__ import annotations

from studio.trailer_story import principal_of

REFS = {"char-sherlock_holmes", "char-john_watson", "char-jefferson_hope",
        "char-john_ferrier", "char-g_lestrade"}


class TestPrincipalOf:
    def test_the_lead_is_chosen_when_the_lead_is_present(self):
        assert principal_of(["john_watson", "sherlock_holmes"], REFS,
                            "sherlock_holmes", "jefferson_hope") == "sherlock_holmes"

    def test_the_lead_is_not_imported_into_a_scene_he_is_absent_from(self):
        """The Utah chapters.  This is the bug, stated as a test."""
        assert principal_of(["john_ferrier", "jefferson_hope"], REFS,
                            "sherlock_holmes", "jefferson_hope") == "jefferson_hope"

    def test_the_opposition_carries_a_scene_the_lead_is_absent_from(self):
        assert principal_of(["john_ferrier"], REFS,
                            "sherlock_holmes", "jefferson_hope") == "john_ferrier"

    def test_someone_present_beats_nobody(self):
        assert principal_of(["g_lestrade", "john_watson"], REFS,
                            "sherlock_holmes", "jefferson_hope") in REFS_NAMES

    def test_a_character_with_no_reference_sheet_is_never_chosen(self):
        """A cast member with no sheet cannot be bound, so casting them is a
        shot that will silently render a stranger."""
        assert principal_of(["madame_sawyer", "john_watson"], REFS,
                            "sherlock_holmes", "jefferson_hope") == "john_watson"

    def test_an_empty_scene_returns_nobody_rather_than_inventing_someone(self):
        assert principal_of([], REFS, "sherlock_holmes", "jefferson_hope") is None

    def test_a_scene_of_strangers_returns_nobody(self):
        assert principal_of(["madame_sawyer"], REFS,
                            "sherlock_holmes", "jefferson_hope") is None

    def test_it_is_deterministic(self):
        cast = ["g_lestrade", "john_watson", "john_ferrier"]
        first = principal_of(cast, REFS, "sherlock_holmes", "jefferson_hope")
        assert all(principal_of(list(reversed(cast)), REFS, "sherlock_holmes",
                                "jefferson_hope") == first for _ in range(3))


REFS_NAMES = {r.replace("char-", "") for r in REFS}
