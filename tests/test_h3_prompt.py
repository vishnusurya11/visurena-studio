"""The six-section Ref2VA document H3 actually asks for.

We were sending one flat ~120-word paragraph built from two lookup tables keyed
on the dramatic register, so every beat in a register got the same framing and
the same camera sentence.
"""
from __future__ import annotations

from studio.h3_prompt import SECTIONS, build, detailed_description, word_count

TAKE = dict(
    style="Muted gaslit Victorian London, heavy chiaroscuro.",
    character="a tall spare man of about forty with a hawk-like nose",
    place="a cramped sitting room at 221B Baker Street",
    action="Holmes stoops over the body and lifts a small glass phial.",
    open_framing="A medium shot cut at the waist; the head fills about a fifth "
                 "of the picture height.",
    close_framing="The object fills the middle half of the frame, lit by a "
                  "single source, the background soft and out of focus.",
    camera="As Holmes stoops over the body, the camera pushes in with small "
           "amplitude at slow speed toward a small glass phial.",
    seconds=10.1,
)


class TestBuild:
    def test_every_section_is_present_and_in_order(self):
        document = build(**TAKE)
        found = [s for s in SECTIONS if s in document]
        assert found == list(SECTIONS)
        positions = [document.index(s) for s in SECTIONS]
        assert positions == sorted(positions)

    def test_the_summary_declares_the_task_type(self):
        assert "[Reference to Video]" in build(**TAKE)

    def test_the_subject_label_binds_the_character(self):
        assert "<Subject 1>" in build(**TAKE)

    def test_the_retention_marker_is_from_the_closed_set(self):
        assert "fully_preserved" in build(**TAKE)

    def test_the_camera_sentence_reaches_the_document(self):
        assert "toward a small glass phial" in build(**TAKE)

    def test_both_framings_reach_the_document(self):
        document = build(**TAKE)
        assert "cut at the waist" in document and "middle half of the frame" in document

    def test_it_never_carries_reference_sheet_language(self):
        from studio.trailer_shot import is_scene_safe
        assert is_scene_safe(build(**TAKE))

    def test_a_take_with_no_character_omits_the_subject_description(self):
        document = build(**{**TAKE, "character": ""})
        assert "hawk-like nose" not in document


class TestDetailedDescription:
    def test_it_reaches_the_length_the_spec_asks_for(self):
        """H3's guide asks for 350-500 words in this section."""
        body = detailed_description(**{k: TAKE[k] for k in
                                       ("character", "place", "action", "open_framing",
                                        "close_framing", "camera", "seconds", "style")})
        assert 350 <= word_count(body) <= 500, word_count(body)

    def test_it_opens_on_the_wider_framing_and_ends_on_the_tighter(self):
        body = detailed_description(**{k: TAKE[k] for k in
                                       ("character", "place", "action", "open_framing",
                                        "close_framing", "camera", "seconds", "style")})
        assert body.index("cut at the waist") < body.index("middle half of the frame")

    def test_it_states_the_take_is_continuous(self):
        body = detailed_description(**{k: TAKE[k] for k in
                                       ("character", "place", "action", "open_framing",
                                        "close_framing", "camera", "seconds", "style")})
        assert "no cuts" in body or "continuous" in body


class TestTwoSubjects:
    """A two-shot binds two faces: the second person takes the second slot and
    the place goes by prompt.  Not the blind path yet -- the A/B decides."""
    WATSON = "a stocky moustached man of thirty with a weathered face"

    def test_the_second_person_takes_the_second_slot(self):
        document = build(**TAKE, second=self.WATSON)
        assert "<Subject 2>: The second person" in document
        assert "weathered face" in document and "hawk-like nose" in document

    def test_both_people_are_fully_preserved_and_the_place_is_not_a_subject(self):
        from studio.h3_prompt import retention_analysis
        text = retention_analysis(True, has_second=True)
        assert text.count("fully_preserved") == 2 and "attribute_transfer" not in text
        assert "221B" not in build(**TAKE, second=self.WATSON).split("summary:")[0]

    def test_the_body_says_they_are_two_different_people(self):
        document = build(**TAKE, second=self.WATSON)
        assert "two different people" in document
        assert "identities of the people in <Subject 1> and <Subject 2>" in document

    def test_without_a_second_person_nothing_changes(self):
        assert build(**TAKE, second="") == build(**TAKE)
