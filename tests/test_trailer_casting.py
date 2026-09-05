"""Who is actually in this shot.

The plan cast sherlock_holmes in all nine beats of A Study in Scarlet --
including the Utah chapters, which he is not in.  `beat_of` put the lead at the
head of the order and then took [:1], so the element's own cast was read and
discarded.  Every shot was the same man, which is both the repetition the
viewer saw and a claim about the book that is false.
"""
from __future__ import annotations

from studio.trailer_story import principal_of, subjects_of

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


UTAH = ["group_mormons", "jefferson_hope", "john_ferrier", "lucy_ferrier",
        "unnamed_hunter_companion"]


class TestSubjectsOf:
    """Who a SHOT names, not who the scene holds.  Run 9 bound a beat on the
    whole scene cast: every Utah setup held an unsheeted Mormon or hunter
    somewhere in its ninety seconds, so a close-up of Hope alone was refused,
    plated, and finally dropped -- and the opposition vanished from the
    trailer while his sheet sat unused."""

    def test_a_close_up_of_hope_is_a_shot_of_hope(self):
        text = "Locked-off medium close-up of Jefferson Hope riding and speaking."
        assert subjects_of(text, UTAH) == ["jefferson_hope"]

    def test_a_shot_naming_nobody_binds_nobody(self):
        assert subjects_of("Wide locked-off frame beneath the boulder, the grey shawl "
                           "in the foreground and the empty desert beyond.", UTAH) == []

    def test_a_possessive_still_names_its_owner(self):
        assert subjects_of("Close on Hope\u2019s hand closing around the ring.", UTAH) == ["jefferson_hope"]
        assert subjects_of("Holmes studies Watson's coat.", ["john_watson", "sherlock_holmes"]) == [
            "john_watson", "sherlock_holmes"]

    def test_a_surname_beside_a_first_name_is_one_person(self):
        assert subjects_of("Close on Lucy Ferrier at the window.", UTAH) == ["lucy_ferrier"]

    def test_a_surname_standing_apart_from_a_first_name_is_the_other_one(self):
        """'Lucy looking up at Ferrier' is two people: her by her own name,
        him by the surname she is not using."""
        assert subjects_of("Close locked-off frame on Lucy looking up at Ferrier.", UTAH) == [
            "john_ferrier", "lucy_ferrier"]

    def test_a_bare_shared_surname_credits_every_sharer(self):
        """Nothing in 'addressing Ferrier' says which Ferrier; both are
        credited, and a sheet for both is asked for.  Better a face bound
        that was not there than a face there that was not bound."""
        assert subjects_of("Young seated, addressing Ferrier with authority.",
                           ["brigham_young", "john_ferrier", "lucy_ferrier"]) == [
            "brigham_young", "john_ferrier", "lucy_ferrier"]

    def test_a_two_shot_is_not_a_shot_of_two_detectives(self):
        cast = ["group_two_detectives", "john_watson", "sherlock_holmes"]
        assert subjects_of("Locked-off medium two-shot of Watson and Holmes.", cast) == [
            "john_watson", "sherlock_holmes"]
        assert subjects_of("The two detectives wait by the door.", cast) == ["group_two_detectives"]

    def test_a_name_written_with_spaces_is_still_a_name(self):
        assert subjects_of("The Police Inspector writes at the desk.",
                           ["Police Inspector", "jefferson_hope"]) == ["Police Inspector"]

    def test_only_the_scene_cast_can_be_named(self):
        """Hope remembering Lucy in London is a shot of Hope."""
        assert subjects_of("Hope's hand closes around Lucy Ferrier's ring.",
                           ["enoch_j_drebber", "jefferson_hope"]) == ["jefferson_hope"]
