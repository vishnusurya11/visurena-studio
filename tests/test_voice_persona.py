"""The instruction contract refuses what rendered badly before."""
import pytest
from pydantic import ValidationError

from studio import voice_persona, voice_register

GOOD = dict(
    character="sherlock_holmes", name="Sherlock Holmes",
    voice_profile="A dry, precise male voice sitting low in the chest, delivered at an "
                  "unhurried pace with almost no vibrato and very little breath before "
                  "a phrase; projection stays level whether he is agreeing or accusing.",
    background="London, 1881. Educated in the south of England and trained in chemistry, "
               "he has spent his adult life indoors among books and reagents, and his "
               "speech carries the clipped precision of a lecture room rather than a street.",
    presence="Late thirties, rather over six feet and excessively lean, pale from indoor "
             "work, moving very little while he speaks and dressed plainly.",
    personality="Engages by stating conclusions rather than opening discussions; the "
                "delivery projects certainty and mild impatience with being asked twice.",
    gender="Male.", pitch="Low male pitch around 100 Hz, starting level and dropping "
                          "further as he closes a deduction.",
    speed="Begins measured, then quickens through a chain of reasoning.",
    volume="Even and conversational, never raised.", age="Late thirties.",
    clarity="Highly articulate, hard final consonants.",
    fluency="Very fluent, no hesitations or fillers.",
    accent="British English, Received Pronunciation.",
    texture="Dry and resonant with little warmth.",
    emotion="Detached interest, shifting to quiet satisfaction at the conclusion.",
    tone="Level and explanatory throughout.",
    personality_line="Composed and deliberate.",
)


def make(**over):
    return voice_persona.VoiceInstruction(**{**GOOD, **over})


class TestItInsistsOnDirection:
    def test_a_good_instruction_validates(self):
        assert make().hertz() == 100

    def test_pitch_without_a_frequency_is_refused(self):
        with pytest.raises(ValidationError, match="anchor to a frequency"):
            make(pitch="A low and pleasant male voice that starts level then drops.")

    def test_a_frequency_outside_human_speech_is_refused(self):
        with pytest.raises(ValidationError, match="human speech"):
            make(pitch="An impossibly deep voice around 20 Hz, starting low then lower.")

    def test_a_sheet_that_never_moves_is_refused(self):
        """Gradual Control: the blog's own values almost never sit still."""
        with pytest.raises(ValidationError, match="change across the line"):
            make(pitch="Low male pitch around 100 Hz, held steady throughout.",
                 speed="An unhurried measured pace of about 120 words per minute.",
                 volume="Even conversational projection, never raised.",
                 emotion="Detached and cool, with no warmth in it.",
                 tone="Level and explanatory, flat across every clause.")

    def test_movement_in_three_of_five_is_enough(self):
        got = make(volume="Even and conversational.", tone="Level and explanatory.")
        assert got.hertz() == 100


class TestTheTwoOfficialShapes:
    def test_the_sheet_uses_the_official_names_and_order(self):
        lines = [row.split(":")[0] for row in make().sheet().splitlines()]
        assert lines == list(voice_persona.ATTRIBUTES)
        assert "pace" not in lines and "timbre" not in lines

    def test_the_persona_carries_body_and_region(self):
        text = make().persona()
        assert text.startswith("Character Name: Sherlock Holmes")
        for field in ("Voice Profile:", "Background:", "Presence:", "Personality:"):
            assert field in text

    def test_both_shapes_can_be_sent_together(self):
        assert make().instruct("both").count("pitch:") == 1


class TestCastingApart:
    def test_two_men_in_the_same_few_hertz_are_flagged(self):
        """Brigham Young and Jefferson Hope were both cast at 82 Hz and
        measured 0.79 against each other -- the same person."""
        cast = voice_persona.Cast(voices=[
            make(character="a", pitch="Low male pitch around 82 Hz, starting level "
                                      "then dropping."),
            make(character="b", pitch="Low male pitch around 85 Hz, starting level "
                                      "then dropping.")])
        assert cast.collisions() == [("a", "b", 3)]

    def test_a_man_and_a_woman_at_the_same_pitch_are_not_a_collision(self):
        cast = voice_persona.Cast(voices=[
            make(character="a", pitch="Male pitch around 170 Hz, rising then settling."),
            make(character="b", gender="Female.",
                 pitch="Female pitch around 170 Hz, rising then settling.")])
        assert cast.collisions() == []


class TestTheRegisterIsAssignedNotChosen:
    def test_everyone_of_one_gender_is_spread_across_the_band(self):
        cards = [{"id": f"c{i}", "role": "minor", "appearances": i} for i in range(5)]
        given = voice_register.assign(cards, lambda c: "male")
        low, high = voice_register.BANDS["male"]
        assert min(given.values()) == low and max(given.values()) == high
        assert len(set(given.values())) == 5

    def test_the_biggest_part_and_the_second_are_far_apart(self):
        """Taking slots low-to-high would sit the two leads side by side."""
        cards = [{"id": "lead", "role": "protagonist", "appearances": 40},
                 {"id": "second", "role": "protagonist", "appearances": 30},
                 {"id": "third", "role": "major", "appearances": 10}]
        given = voice_register.assign(cards, lambda c: "male")
        assert abs(given["lead"] - given["second"]) > 40

    def test_women_are_cast_in_the_female_band(self):
        cards = [{"id": "she", "role": "major", "appearances": 9}]
        given = voice_register.assign(cards, lambda c: "female")
        low, high = voice_register.BANDS["female"]
        assert low <= given["she"] <= high

    def test_a_crowded_band_reports_who_is_too_close(self):
        given = {"a": 100, "b": 105, "c": 160}
        genders = {"a": "male", "b": "male", "c": "male"}
        assert voice_register.too_close(given, genders) == [("a", "b", 5)]


class TestOneAccentStatedPlainly:
    """Lucy Ferrier rendered as East Asian because her accent field said
    'British English ... moderated by American frontier ... no specific
    regional accent, so avoid a strong local dialect'."""

    def test_the_real_failing_accent_is_refused(self):
        with pytest.raises(ValidationError):
            make(accent="British English pronunciation, moderated by American "
                        "frontier vocabulary and rhythm; no specific regional accent.")

    def test_a_hedged_accent_is_refused(self):
        with pytest.raises(ValidationError, match="hedges with"):
            make(accent="General American English, if required by the production.")

    def test_two_nationalities_are_refused(self):
        with pytest.raises(ValidationError, match="mixes"):
            make(accent="British English with a Japanese lilt.")

    def test_one_plainly_stated_accent_passes(self):
        got = make(accent="British English, Received Pronunciation, educated London.")
        assert got.accent.startswith("British")

    def test_background_may_not_name_a_competing_country(self):
        with pytest.raises(ValidationError, match="FORMED in"):
            make(accent="General American English.",
                 background="Raised in London, England, in 1881, among clerks and "
                            "shopkeepers, her speech shaped entirely by the city and "
                            "the schooling she received there before the family left.")

    def test_background_giving_the_accent_a_reason_passes(self):
        got = make(accent="General American English.",
                   background="Raised on the Utah frontier in the American West of "
                              "1881, among settlers and travellers rather than in any "
                              "schoolroom, her diction plain and her vowels flat.")
        assert got.accent == "General American English."


class TestARefusalIsACorrectionNotAnEnding:
    """The first full cast run raised on character three of twenty-three and
    left twenty uncast."""

    def test_a_refused_instruction_is_asked_again_with_the_reason(self):
        seen = []

        def flaky(tier, prompt, schema):
            seen.append(prompt)
            if len(seen) == 1:
                return schema(**{**GOOD, "accent": "British English, if required."})
            return schema(**GOOD)

        got = voice_persona.write({"id": "x"}, "London", "1881", 100, {}, model=flaky)
        assert got.character == "x"
        assert "REFUSED" in seen[1] and "hedges with" in seen[1]

    def test_it_gives_up_after_the_tries_rather_than_looping(self):
        def always_bad(tier, prompt, schema):
            return schema(**{**GOOD, "accent": "British English, if required."})

        with pytest.raises(voice_persona.NotDirection):
            voice_persona.write({"id": "x"}, "London", "1881", 100, {}, model=always_bad)


class TestTravelIsNotOrigin:
    def test_a_country_merely_travelled_to_is_allowed(self):
        """Jefferson Hope is an American who later drives a cab in London."""
        got = make(accent="General American English.",
                   background="Raised on the American frontier and shaped by years "
                              "hunting in the Nevada mountains; he later followed his "
                              "quarry to London and worked there as a cab driver.")
        assert got.accent.startswith("General")

    def test_a_rival_origin_is_still_refused(self):
        with pytest.raises(ValidationError, match="FORMED in"):
            make(accent="General American English.",
                 background="He was raised in London and educated in England, his "
                            "speech shaped entirely by that city before he ever "
                            "crossed the Atlantic to seek his fortune.")
