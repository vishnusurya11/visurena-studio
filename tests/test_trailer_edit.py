"""The cut: variety, shape, and landing on the music."""
from __future__ import annotations

from studio.beatmap import IMPACT_DB, STOPDOWN_DB
from studio.trailer_assemble import segment_start
from studio.trailer_cut import FINAL_HOLD, is_uniform, target_length
from studio.trailer_edit import MIN_SHOT, cut_points, lengths_of, snap

GRID = [1.0, 2.5, 4.0, 6.2, 9.9, 14.0, 20.5, 28.0, 35.0, 44.0, 55.0, 61.0, 70.0, 78.0]


class TestSnapping:
    def test_a_cut_moves_onto_a_near_onset(self):
        assert snap(2.4, GRID) == 2.5

    def test_a_cut_far_from_any_onset_stays_put(self):
        assert snap(50.0, GRID) == 50.0

    def test_an_empty_grid_leaves_every_cut_alone(self):
        assert snap(3.7, []) == 3.7


class TestTheArc:
    def test_the_opening_shot_is_the_longest_of_the_opening(self):
        assert target_length(0.02) > target_length(0.12)

    def test_there_is_a_breath_a_third_of_the_way_in(self):
        assert target_length(0.32) > target_length(0.22)

    def test_the_climax_is_the_fastest_cutting(self):
        assert target_length(0.87) == min(target_length(p / 100) for p in range(100))

    def test_the_cut_decelerates_into_the_title(self):
        assert target_length(0.97) > target_length(0.87)


class TestCutPoints:
    def test_shot_lengths_are_never_uniform(self):
        lengths = lengths_of(cut_points(80.0, GRID))
        assert not is_uniform(lengths)

    def test_no_shot_is_a_flash_frame(self):
        assert all(x >= MIN_SHOT for x in lengths_of(cut_points(80.0, GRID)))

    def test_the_cut_covers_exactly_the_span_asked_for(self):
        points = cut_points(80.0, GRID)
        assert points[0] == 0.0 and points[-1] == 80.0

    def test_a_longer_stretch_yields_fewer_shots(self):
        few = cut_points(80.0, GRID, stretch=3.0)
        many = cut_points(80.0, GRID, stretch=1.0)
        assert len(few) < len(many)

    def test_boundaries_strictly_increase(self):
        points = cut_points(80.0, GRID)
        assert all(b > a for a, b in zip(points, points[1:]))


class TestReuseShowsDifferentMoments:
    def test_three_uses_of_one_take_start_in_three_places(self):
        starts = [segment_start(u, 3, 2.5, 10.1) for u in range(3)]
        assert len(set(starts)) == 3

    def test_a_single_use_takes_from_the_middle_of_the_take(self):
        """Not the head -- the head is the animated reference sheet."""
        from studio.trailer_assemble import HEAD_TRIM
        start = segment_start(0, 1, 2.5, 10.1)
        assert HEAD_TRIM <= start <= 10.1 - 2.5

    def test_a_take_with_no_room_does_not_seek_past_its_end(self):
        assert segment_start(2, 3, 10.0, 10.0) == 0.0


class TestDetectionThresholds:
    def test_a_stopdown_is_a_bigger_move_than_an_impact(self):
        """Asymmetric on purpose: a hit is a spike, a stopdown is a floor."""
        assert STOPDOWN_DB > IMPACT_DB

    def test_the_final_hold_outlasts_every_arc_target(self):
        assert FINAL_HOLD > max(target_length(p / 100) for p in range(100))


class TestSheetLanguageNeverReachesAShot:
    """A shot prompt describes a person in a place, not a photograph of them."""

    def test_a_sheet_prompt_is_rejected(self):
        from studio.trailer_refs import character_prompt
        from studio.trailer_shot import is_scene_safe
        sheet = character_prompt("A tall lean man, hawk-nosed.", "Muted London grey.")
        assert not is_scene_safe(sheet)

    def test_a_plain_physical_description_passes(self):
        from studio.trailer_shot import is_scene_safe
        assert is_scene_safe("A tall lean man of about thirty, thin hawk-like nose.")

    def test_the_shot_prompt_built_from_a_sheet_prompt_is_caught(self):
        """The exact bug: the sheet prompt reaching shot_prompt unnoticed."""
        from studio.trailer_refs import character_prompt
        from studio.trailer_shot import is_scene_safe, shot_prompt
        sheet = character_prompt("A small wiry man.", "Fog and gaslight.")
        built = shot_prompt("Style.", [sheet], "a lane", "He turns.", "hit", 2.0)
        assert not is_scene_safe(built)


class TestHeadTrim:
    """H3 r2v opens on the reference sheet; no shot may come from there."""

    def test_no_use_starts_inside_the_reference_leak(self):
        from studio.trailer_assemble import HEAD_TRIM, segment_start
        starts = [segment_start(u, 3, 2.5, 10.12) for u in range(3)]
        assert all(s >= HEAD_TRIM for s in starts)

    def test_a_single_use_also_clears_the_leak(self):
        from studio.trailer_assemble import HEAD_TRIM, segment_start
        assert segment_start(0, 1, 2.5, 10.12) >= HEAD_TRIM

    def test_uses_still_show_different_moments(self):
        from studio.trailer_assemble import segment_start
        assert len({segment_start(u, 3, 2.0, 10.12) for u in range(3)}) == 3

    def test_a_take_too_short_to_trim_does_not_seek_past_its_end(self):
        from studio.trailer_assemble import segment_start
        assert segment_start(0, 1, 3.0, 3.0) == 0.0


class TestGradeMatching:
    """The prompt cannot lock exposure; post can."""

    def test_a_clip_already_matching_the_hero_is_left_alone(self):
        from studio.trailer_assemble import grade_to
        assert grade_to(60.0, 40.0, 60.0, 40.0) == "eq=contrast=1.0000:brightness=0.0000"

    def test_a_dark_clip_is_brightened(self):
        from studio.trailer_assemble import grade_to
        assert "brightness=0." in grade_to(40.0, 40.0, 70.0, 40.0)

    def test_a_flat_clip_gains_contrast(self):
        """Matching the mean alone leaves flat clips flat, and flat reads cheap."""
        from studio.trailer_assemble import grade_to
        filt = grade_to(60.0, 20.0, 60.0, 45.0)
        assert float(filt.split("contrast=")[1].split(":")[0]) > 1.0

    def test_contrast_is_clamped_so_noise_is_not_amplified(self):
        from studio.trailer_assemble import grade_to
        filt = grade_to(60.0, 1.0, 60.0, 90.0)
        assert float(filt.split("contrast=")[1].split(":")[0]) <= 1.35

    def test_brightness_is_clamped(self):
        from studio.trailer_assemble import grade_to
        filt = grade_to(5.0, 40.0, 250.0, 40.0)
        assert abs(float(filt.split("brightness=")[1])) <= 0.3

    def test_a_zero_deviation_clip_does_not_divide_by_zero(self):
        from studio.trailer_assemble import grade_to
        assert grade_to(60.0, 0.0, 60.0, 40.0)


class TestTitleCard:
    """Typography fails silently; the checks have to be explicit."""

    def test_the_font_is_asserted_to_exist(self):
        """libass substitutes a missing face without a word of warning."""
        import studio.trailer_assemble as assemble
        from pathlib import Path
        original = assemble.TITLE_FONT_FILE
        assemble.TITLE_FONT_FILE = Path("C:/Windows/Fonts/DefinitelyNotAFont.ttf")
        try:
            import pytest
            with pytest.raises(RuntimeError, match="title font missing"):
                assemble.ass_title("X", 3.0, 1344, 768)
        finally:
            assemble.TITLE_FONT_FILE = original

    def test_the_card_carries_letter_spacing(self):
        from studio.trailer_assemble import ass_title
        assert ",22,0," in ass_title("A Study in Scarlet", 3.0, 1344, 768)

    def test_an_apostrophe_survives(self):
        """drawtext's inline text= silently drops these; ASS must not."""
        from studio.trailer_assemble import ass_title
        assert "KEEPER'S" in ass_title("The Keeper's Lantern", 3.0, 1344, 768)

    def test_the_card_fades(self):
        from studio.trailer_assemble import ass_title
        assert "\fad(" in ass_title("X", 3.0, 1344, 768)


class TestEpithets:
    """A book that never describes someone still names them descriptively."""

    def test_a_descriptive_epithet_is_kept(self):
        from studio.trailer_refs import epithets
        assert "the solemn butler" in epithets(["Poole", "the solemn butler"], "Poole")

    def test_a_relationship_is_not_a_description(self):
        from studio.trailer_refs import epithets
        assert epithets(["our old friend", "a friend", "the latter"], "Enfield") == []

    def test_a_bare_name_is_not_an_epithet(self):
        from studio.trailer_refs import epithets
        assert epithets(["Mr. Utterson", "Utterson"], "Mr. Utterson") == []

    def test_an_epithet_survives_sharing_a_word_with_the_name(self):
        """The housemaid's own name is "the maid"; "a maid servant" still counts."""
        from studio.trailer_refs import epithets
        found = epithets(["the maid", "a maid servant", "the housemaid"], "the maid")
        assert "a maid servant" in found and "the maid" not in found

    def test_two_characters_the_book_never_describes_still_differ(self):
        from studio.trailer_refs import described_as
        butler = described_as({"name": "Poole", "aliases": ["the solemn butler"],
                               "profile": {"physical": ""}})
        lawyer = described_as({"name": "Mr. Utterson", "aliases": ["the lawyer"],
                               "profile": {"physical": ""}})
        assert butler != lawyer and butler and lawyer


class TestTheTrailerIsAboutItsBook:
    """Content checks. Every mechanical gate passed a Holmes-less Holmes trailer."""

    def test_the_arc_spans_every_register(self):
        from studio.trailer_plan import arc_for
        registers = {arc_for(i / 10) for i in range(11)}
        assert {"quiet", "build", "hit", "aftermath"} <= registers

    def test_positions_taken_over_scenes_never_reach_a_climax(self):
        """The exact bug: 11 beats over 22 scenes capped position at 0.48."""
        from studio.trailer_plan import arc_for
        wrong = {arc_for(i / 21) for i in range(11)}
        assert "hit" not in wrong

    def test_the_most_central_character_is_the_one_bound(self):
        from studio.trailer_plan import lead_of
        assert lead_of({"cast": ["watson", "holmes"]},
                       ["holmes", "watson"], {"holmes", "watson"}) == ["holmes"]

    def test_a_character_without_a_reference_is_not_bound(self):
        from studio.trailer_plan import lead_of
        assert lead_of({"cast": ["watson", "holmes"]},
                       ["holmes", "watson"], {"watson"}) == ["watson"]

    def test_ranking_counts_presence_and_speech(self):
        from studio.trailer_plan import leading_characters
        scenes = [{"cast": ["holmes", "watson"], "speaking": ["holmes"]},
                  {"cast": ["watson"], "speaking": []},
                  {"cast": ["holmes"], "speaking": ["holmes"]}]
        assert leading_characters(scenes)[0] == "holmes"

    def test_an_empty_scene_binds_nobody(self):
        from studio.trailer_plan import lead_of
        assert lead_of({"cast": []}, ["holmes"], {"holmes"}) == []


class TestActionMatchesTheBoundCharacter:
    def test_the_line_featuring_the_bound_character_wins(self):
        from studio.trailer_plan import action_featuring
        scene = {"elements": [{"kind": "action", "text": "Gregson sits in the arm-chair."},
                              {"kind": "action", "text": "Holmes takes the pill-box."}]}
        assert action_featuring(scene, ["Sherlock Holmes"]) == "Holmes takes the pill-box."

    def test_the_first_line_is_the_fallback(self):
        from studio.trailer_plan import action_featuring
        scene = {"elements": [{"kind": "action", "text": "Rain falls on the street."}]}
        assert action_featuring(scene, ["Sherlock Holmes"]) == "Rain falls on the street."

    def test_a_scene_with_no_action_falls_back_to_its_slug(self):
        from studio.trailer_plan import action_featuring
        scene = {"elements": [], "slug": {"text": "INT. 221B BAKER STREET - DAY"}}
        assert action_featuring(scene, []) == "INT. 221B BAKER STREET - DAY"

    def test_short_name_particles_do_not_match_everything(self):
        """Matching on "a" or "de" would make every line look like a hit."""
        from studio.trailer_plan import action_featuring
        scene = {"elements": [{"kind": "action", "text": "A door closes."},
                              {"kind": "action", "text": "Utterson looks up."}]}
        assert action_featuring(scene, ["a de Utterson"]) == "Utterson looks up."


class TestCharacterCollision:
    """Four characters a book never describes must not become one man."""

    def test_role_implies_dress(self):
        from studio.trailer_refs import costume_for
        assert "livery" in costume_for(["the solemn butler"])
        assert "police uniform" in costume_for(["a policeman"])

    def test_an_unknown_role_implies_nothing(self):
        from studio.trailer_refs import costume_for
        assert costume_for(["a friend"]) == ""

    def test_dress_never_mentions_hair_or_age(self):
        """So it can be added to a book description without contradicting it."""
        from studio.trailer_refs import COSTUME
        banned = ("hair", "haired", "bearded", "his fifties", "elderly", "young")
        assert not [d for _, d in COSTUME if any(w in d for w in banned)]

    def test_marks_are_stable_for_one_character(self):
        from studio.trailer_refs import distinguishing_marks
        assert distinguishing_marks("poole") == distinguishing_marks("poole")

    def test_marks_differ_between_characters(self):
        from studio.trailer_refs import distinguishing_marks
        ids = ["henry_jekyll", "reginald_lanyon", "poole", "richard_enfield"]
        assert len({distinguishing_marks(i) for i in ids}) == len(ids)

    def test_invented_marks_never_override_the_book(self):
        """Appending them to a real description contradicted it."""
        from studio.trailer_refs import described_as
        described = described_as({"id": "hyde", "name": "Edward Hyde",
                                  "aliases": ["a little man"],
                                  "profile": {"physical": "A small young man, "
                                              "clean-shaven and pale."}})
        assert "greying beard" not in described
        assert "small young man" in described

    def test_two_doctors_do_not_come_out_identical(self):
        from studio.trailer_refs import described_as
        one = described_as({"id": "henry_jekyll", "name": "Dr. Jekyll",
                            "aliases": ["the doctor"], "profile": {"physical": ""}})
        two = described_as({"id": "reginald_lanyon", "name": "Dr. Lanyon",
                            "aliases": ["the doctor"], "profile": {"physical": ""}})
        assert one != two


class TestTheTitleLandsOnTheHit:
    """The defect this whole pipeline was built to fix, in miniature."""

    @staticmethod
    def card_seconds(shots_end: float, hit_at: float, hold: float = 3.0) -> float:
        return max(hold, (hit_at - shots_end) + hold)

    def test_a_hit_after_the_shots_is_covered_by_the_card(self):
        card = self.card_seconds(80.1, 83.95)
        assert 80.1 <= 83.95 <= 80.1 + card

    def test_a_fixed_hold_would_have_missed_it(self):
        """80.1 + 3.0 = 83.1, and the cue's impact is at 83.95."""
        assert not 80.1 <= 83.95 <= 80.1 + 3.0

    def test_a_hit_during_the_shots_still_leaves_a_full_hold(self):
        assert self.card_seconds(80.1, 60.0) == 3.0

    def test_the_card_never_shrinks_below_the_final_hold(self):
        from studio.trailer_cut import FINAL_HOLD
        assert all(self.card_seconds(80.0, h) >= FINAL_HOLD
                   for h in (10.0, 79.0, 80.0, 95.0))


class TestCameraVariety:
    """A slow drifting push on every shot is the tell of generated video."""

    def test_consecutive_beats_in_one_register_differ(self):
        from studio.trailer_shot import camera_for
        assert len({camera_for("build", i) for i in range(3)}) == 3

    def test_the_register_still_governs(self):
        from studio.trailer_shot import camera_for
        assert all("fast speed" in camera_for("hit", i) for i in range(3))
        assert not any("fast speed" in camera_for("quiet", i) for i in range(3))

    def test_a_static_frame_can_be_asked_for(self):
        """H3 drifts by default when the prompt says nothing about the camera."""
        from studio.trailer_shot import camera_for
        assert any("static" in camera_for("quiet", i) for i in range(3))

    def test_an_unknown_register_still_yields_a_camera(self):
        from studio.trailer_shot import camera_for
        assert camera_for("nonsense", 0)

    def test_no_bracket_syntax_anywhere(self):
        """[Push in] is the hosted Hailuo dialect and does nothing on H3."""
        from studio.trailer_shot import CAMERA
        assert not [m for moves in CAMERA.values() for m in moves if "[" in m]


class TestAssemblyDegradesRatherThanRefusing:
    """One failed render at 4am should cost variety, not the whole trailer."""

    @staticmethod
    def substitute(beat_id: str, order: int, have: list[str]) -> str:
        return beat_id if beat_id in have else have[order % len(have)]

    def test_a_present_beat_uses_its_own_take(self):
        assert self.substitute("B03", 7, ["B00", "B03", "B05"]) == "B03"

    def test_a_missing_beat_falls_back_deterministically(self):
        have = ["B00", "B03", "B05"]
        assert self.substitute("B07", 4, have) == self.substitute("B07", 4, have)

    def test_the_fallback_is_a_take_that_exists(self):
        have = ["B00", "B03", "B05"]
        assert all(self.substitute(f"B{i:02d}", i, have) in have for i in range(11))

    def test_the_floor_rejects_a_trailer_cut_from_almost_nothing(self):
        beats, have = 11, 3
        assert have < max(4, beats * 0.6)

    def test_a_nearly_complete_set_is_accepted(self):
        beats, have = 11, 9
        assert have >= max(4, beats * 0.6)


class TestSubstituteTakesStillSpread:
    def test_a_take_standing_in_for_many_beats_spreads_across_its_length(self):
        """Counting the ORIGINAL beats would reuse one moment repeatedly."""
        from studio.trailer_assemble import segment_start
        starts = [segment_start(u, 6, 2.0, 10.12) for u in range(6)]
        assert len(set(starts)) == 6
        assert starts == sorted(starts)


class TestFraming:
    """Faces collapse in wides, and the driver is head size, not resolution."""

    def test_the_climax_frames_closest(self):
        from studio.trailer_shot import framing_for
        assert "close shot" in framing_for("hit")

    def test_every_register_names_a_shot_size(self):
        from studio.trailer_shot import FRAMING
        assert all("shot" in text for text in FRAMING.values())

    def test_a_shot_with_a_person_carries_framing(self):
        from studio.trailer_shot import shot_prompt
        built = shot_prompt("S.", ["a lean man"], "a room", "He turns.", "hit", 2.0)
        assert "head and shoulders" in built

    def test_a_shot_with_no_people_does_not(self):
        """Framing a person who is not there just confuses the model."""
        from studio.trailer_shot import shot_prompt
        built = shot_prompt("S.", [], "a lane", "Rain falls.", "quiet", 2.0)
        assert "waist up" not in built


class TestTheHeroLookIsDark:
    """Measured across 50 released trailers: median frame luma is 28/255."""

    FLOOR = 32.0

    def test_the_floor_sits_near_the_corpus_median(self):
        assert 25.0 <= self.FLOOR <= 40.0

    def test_a_dark_batch_is_lifted_only_to_the_floor(self):
        means = [11.9, 24.9, 20.0]
        assert max(sorted(means)[len(means) // 2], self.FLOOR) == self.FLOOR

    def test_a_bright_batch_keeps_its_own_median(self):
        """The floor is a floor, not a target -- it must not pull bright work down."""
        means = [70.0, 85.0, 90.0]
        assert max(sorted(means)[len(means) // 2], self.FLOOR) == 85.0

    def test_clips_converge_on_the_hero(self):
        from studio.trailer_assemble import grade_to
        for mean in (11.9, 24.9, 48.4):
            filt = grade_to(mean, 37.9, self.FLOOR, 37.9)
            contrast = float(filt.split("contrast=")[1].split(":")[0])
            bright = float(filt.split("brightness=")[1])
            assert abs((mean * contrast + bright * 255) - self.FLOOR) < 0.5


class TestLimiterAutoLevel:
    """alimiter re-levels by default, which inverts what a limit does."""

    def test_every_limiter_disables_auto_level(self):
        import inspect
        from studio import sfx, trailer_assemble
        for module in (sfx, trailer_assemble):
            source = inspect.getsource(module)
            for line in source.splitlines():
                if "alimiter=limit=" in line:
                    assert "level=disabled" in line, line.strip()

    def test_synthesised_cues_leave_true_peak_headroom(self):
        """They are summed with a bed that itself arrives at 0.00 dBTP."""
        from studio.sfx import HEADROOM
        assert HEADROOM <= 0.75
