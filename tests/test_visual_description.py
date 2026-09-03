"""A reference description must say what a camera could photograph.

Every sentence below is real text from the shipped library.  The Holmes sheet
carried "He is able to travel rapidly, conduct close physical examinations,
follow a suspect, handcuff a cabman, and help restrain him" as his PHYSICAL
DESCRIPTION -- a list of capabilities, none of which is a picture.
"""
from __future__ import annotations

from studio.trailer_refs import is_photographable, visual_description

CAPABILITY = ("He is able to travel rapidly, conduct close physical "
              "examinations, follow a suspect, handcuff a cabman, and help "
              "restrain him.")
ACTION = "He pricks a finger while collecting blood and covers it with a small plaster."
POKER = ("He is physically capable of extended walks and of helping break down "
         "Jekyll's cabinet door; during that action he carries a heavy kitchen poker.")
LOOKS = "He is a tall spare man with a hawk-like nose and dark hair swept back."
HANDS = "His hands are mottled with plaster and discoloured by strong acids."


class TestIsPhotographable:
    def test_a_list_of_capabilities_is_not_a_picture(self):
        assert not is_photographable(CAPABILITY)

    def test_an_action_is_not_an_appearance(self):
        assert not is_photographable(ACTION)

    def test_the_poker_sentence_is_refused(self):
        """Kept by 'hat' matching inside 'that'.  That false positive made
        Utterson's description non-empty, which suppressed his invented marks,
        which is why he shipped with no distinguishing feature at all."""
        assert not is_photographable(POKER)

    def test_a_description_of_how_someone_looks_is_kept(self):
        assert is_photographable(LOOKS)

    def test_a_visible_detail_of_the_body_is_kept(self):
        assert is_photographable(HANDS)


class TestVisualDescription:
    def test_it_drops_capability_and_keeps_appearance(self):
        got = visual_description(" ".join([CAPABILITY, LOOKS, ACTION]))
        assert "hawk-like" in got and "handcuff" not in got and "pricks" not in got

    def test_a_profile_of_pure_capability_returns_nothing(self):
        """An honest empty answer: the caller then falls back to the reference
        image, which is what carries identity anyway."""
        assert visual_description(" ".join([CAPABILITY, ACTION, POKER])) == ""

    def test_word_boundaries_are_respected(self):
        assert not is_photographable("He knew that the room was empty.")


class TestCostumeByRole:
    """"detective" was in the same bucket as "constable", so the world's most
    famous CONSULTING detective was dressed as a Metropolitan policeman and
    handed a custodian helmet."""

    def test_a_consulting_detective_is_not_a_policeman(self):
        from studio.trailer_refs import costume_for
        assert "police" not in costume_for(["the consulting detective"]).lower()

    def test_a_scotland_yard_inspector_still_is_one(self):
        from studio.trailer_refs import costume_for
        assert "police" in costume_for(["the inspector"]).lower()

    def test_a_plain_detective_is_read_as_private(self):
        from studio.trailer_refs import costume_for
        assert "police" not in costume_for(["the detective"]).lower()


class TestAbsenceSentences:
    def test_not_otherwise_specified_is_dropped(self):
        from studio.trailer_refs import is_photographable
        assert not is_photographable(
            "Her clothing and facial features are not otherwise specified.")

    def test_not_specified_is_dropped(self):
        from studio.trailer_refs import is_photographable
        assert not is_photographable("His exact age and hair are not specified.")
