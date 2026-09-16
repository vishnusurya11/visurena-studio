"""The take prompt in MiniMax's own ref2va grammar (references/ref-en.txt):
subject_definitions, summary, retention_analysis, detailed_description,
overall_soundscape, non_diegetic_music.

Spec: `scratchpad/review9/ref2v_prompt_spec.md`, approved 2026-09-11.  Where
the official guide and the owner disagree the owner's form is kept and marked
OWNER in the module, so the A/B can flip it with a one-line change."""
import pytest

from studio import episode_ref_official as ro
from studio.episode_spec import Line, Setup, Shot, SubShot

SHOTS = [Shot(index=11, section="spike", setup="lab", size="close", faces=[],
              frame="Close on Watson's sunburnt hand on the silver knob of the black stick at the bench edge, "
                    "the tall arched window behind it.",
              motion="Static shot; the hand lifts off the knob and reaches across the bench for the "
                     "test-tube; the thumb comes back over the ball of the knob; he leans his weight onto it"),
         Shot(index=12, section="spike", setup="lab", size="medium_close", faces=["sherlock_holmes"],
              frame="Medium close-up of Holmes facing Watson across the bench, the blue flame under the "
                    "retort at his elbow.",
              motion="Static shot; Holmes lifts the test-tube to the window and turns it in his fingers; "
                     "he sets it down on the bench")]
PLACED = [{"index": 11, "t_start": 92.96, "seconds": 4.25}, {"index": 12, "t_start": 97.21, "seconds": 3.71}]
LINES = [Line(index=17, kind="narration", speaker="john_watson", text="He looked at my hands.", shot=11),
         Line(index=18, kind="dialogue", speaker="sherlock_holmes", text="You have been in Afghanistan.", shot=12)]
AT = {17: (93.21, 3.75), 18: (97.46, 3.19)}
PHYS = {"sherlock_holmes": "A man in his late twenties, excessively lean, a pale indoor complexion."}
FRAMES = 199  # 8.29 s of latent; the take's PLACED length is 7.96 (5.6: the rendered length is the truth)
LAB = "The chemical laboratory of Saint Bartholomew's Hospital, 1881."


def build(**kw):
    """The fixture take is two short segments, so it cannot reach L14's 150 words a
    block; the lint gate is exercised by its own test below."""
    kw = {"faces": ["sherlock_holmes"], "physical": PHYS, "described": LAB,
          "narrator": "john_watson", "check_lint": False, **kw}
    return ro.build(SHOTS, PLACED, LINES, AT, FRAMES, **kw)


def segs():
    return ro.segments(SHOTS, PLACED, PLACED[0]["t_start"], FRAMES)


# ---- 3.1 / 3.2 / 3.3  the owner's clock ------------------------------------

def test_every_time_is_a_whole_second():
    """Owner 2026-09-11: whole seconds only; the pin, not the text, is what cuts."""
    assert ro.stamp(3.2083) == "00:03" and ro.stamp(0.25) == "00:00"
    assert ro.stamp(65.6) == "01:06" and ro.stamp(0.0) == "00:00"


def test_a_shot_is_a_range_that_starts_at_zero_and_meets_the_next():
    assert ro.span(0.0, 4.25) == "From 00:00 to 00:04"
    assert ro.span(4.25, 7.96) == "From 00:04 to 00:08"
    assert ro.span(2.2, 2.6) == "From 00:02 to 00:03"  # a short segment still spans a second
    assert ro.during(8.0, 10.4) == "from 00:08 to 00:10"  # the same range, mid-sentence


def test_the_last_range_ends_on_the_ceiling_of_the_latent():
    """Owner: the ranges account for ALL the time of the video, so 7.29 s ends at 00:08."""
    assert ro.take_end(175) == 8 and ro.take_end(294) == 13
    assert ro.take_end(192) == 8 and ro.take_end(193) == 9


def test_beats_spread_whole_seconds_strictly_inside_the_range():
    assert ro.beats(0, 3, 2) == [1, 2]
    assert ro.beats(3, 8, 2) == [5, 6]
    assert ro.beats(8, 13, 2) == [10, 11]


def test_beats_never_collide_and_stop_when_the_seconds_run_out():
    assert ro.beats(0, 4, 3) == [1, 2, 3]
    assert ro.beats(4, 5, 1) == []          # no whole second lies strictly inside
    assert ro.beats(0, 3, 5) == [1, 2]      # the surplus clauses share the last stamp


# ---- 3.5  subject_definitions ----------------------------------------------

def test_pictures_are_numbered_sheets_then_plate_then_cells_then_ends():
    text, pics, strip = ro.subjects(["sherlock_holmes"], PHYS, "The laboratory.", segs(), ends=[2])
    assert pics == {0: 3, 1: 4} and strip == 6      # 1 sheet, 2 plate, 3-4 cells, 5 END; 6 is the slot after
    assert "<Subject 1> is Sherlock Holmes in <Picture 1>:" in text
    assert "<Subject 2> is the location in <Picture 2>: The laboratory." in text
    assert "<Picture 3> is the first frame of [Shot 1]," in text
    assert "<Picture 4> is the first frame of [Shot 2]," in text
    assert "<Picture 5> is the last frame of [Shot 2]," in text
    assert "<Picture 6>" not in text  # nothing is staged after the END cells


def test_the_plate_is_a_definition_and_never_a_framing():
    """review7 headline: the plate rendered AS a shot at 0.88-0.996 similarity."""
    text, _, _ = ro.subjects(["sherlock_holmes"], PHYS, "The laboratory of the hospital.", segs(), [])
    assert "<Picture 2> defines this room alone; each shot keeps the framing of its own first-frame picture." in text
    text, _, _ = ro.subjects([], {}, "The street front of the hospital, 1881.", segs(), [])
    assert "<Picture 1> defines this place alone" in text


def test_no_strip_is_declared_because_every_cell_has_its_own_picture():
    """Owner 2026-09-11, on take 00: "picture 3 and 4 are literally the same".  On a
    one-segment take the strip WAS the cell, similarity 1.000; its only unique content
    was shot order, and each cell's own line already carries that, at full resolution.
    The strip had also done harm: the model read its trailing panels as later shots."""
    text, cells, after = ro.subjects(["sherlock_holmes"], PHYS, "The laboratory.", segs(), ends=[])
    assert "storyboard reference" not in text
    assert "<Picture 3> is the first frame of [Shot 1]" in text
    assert "<Picture 4> is the first frame of [Shot 2]" in text
    assert cells == {0: 3, 1: 4} and after == 5  # the slot after the last picture; nothing is staged there

def test_a_narration_take_says_its_audio_runs_silent():
    """OWNER 2026-09-11: only dialogue is in <Audio 1>; claiming speech that is not in
    the file is the contradiction the model resolves by inventing a speaker."""
    text, _, _ = ro.subjects([], {}, "The lab.", segs(), [], spoken=[])
    assert "<Audio 1> is the take's complete audio track and runs silent for its whole length." in text
    text, _, _ = ro.subjects([], {}, "The lab.", segs(), [], spoken=[(LINES[1], 0.25)])
    assert "<Audio 1> is the take's complete audio track: the one line spoken on camera at 00:00," in text


def test_shot_list_joins_the_official_way():
    assert ro.shot_list([1]) == "[Shot 1]"
    assert ro.shot_list([1, 2]) == "[Shot 1] and [Shot 2]"
    assert ro.shot_list([1, 2, 3]) == "[Shot 1], [Shot 2] and [Shot 3]"


# ---- 3.6 / 3.7  retention_analysis -----------------------------------------

def test_ends_sentence_is_gone():
    """3.6: its job is now S5 + R4, which name the picture instead of its position."""
    assert not hasattr(ro, "ends_sentence")


def test_the_location_is_partially_preserved_and_never_appears_in_a_shot():
    _, pics, strip = ro.subjects(["sherlock_holmes"], PHYS, "The laboratory.", segs(), [])
    ret = ro.retention(["sherlock_holmes"], segs(), pics, strip, [], "The laboratory.").split("\n")
    assert ret[1].startswith("<Subject 2> (the location behind [Shot 1] and [Shot 2]): partially_preserved - ")
    assert "appears in" not in ret[1]


def test_retention_marks_every_cell_a_first_frame_and_cites_no_strip():
    """A citation of a picture the graph does not stage is exactly what L11 catches,
    and it caught the strip's own retention line the moment the strip was dropped."""
    text = ro.retention(["sherlock_holmes"], segs(), {}, 0, [], "The laboratory.")
    assert "weak_reference" not in text and "storyboard reference" not in text
    assert "<Picture 3> ([Shot 1] first frame): fully_preserved" in text
    assert "<Picture 4> ([Shot 2] first frame): fully_preserved" in text
    assert "<Audio 1>: fully_copy" in text

def test_the_cast_subject_is_scoped_to_the_shots_that_show_him():
    _, pics, strip = ro.subjects(["sherlock_holmes"], PHYS, "The laboratory.", segs(), [])
    ret = ro.retention(["sherlock_holmes"], segs(), pics, strip, [], "The laboratory.")
    # FIX A 2026-09-13: a cast sheet is a DEFINITION, not a framing -- OWNER 5.16's
    # plate cure, owed to people. `appears in` + `fully_preserved` on a whole-frame
    # portrait is what re-rendered the studio pose into the room (ep03 T02 at 4.0 s).
    assert "<Subject 1> (the man in [Shot 2]): partially_preserved" in ret
    assert "appears in" not in ret


def test_no_speaker_id_ever_reaches_the_retention_analysis():
    """ref-en §5.4: 'Do not write (Sx) in retention_analysis.'"""
    text = build()
    ret = text[text.index("retention_analysis:"):text.index("detailed_description:")]
    assert "(S1)" not in ret and "(S2)" not in ret


# ---- 3.8 / 3.9 / 3.10  voices ----------------------------------------------

def test_speaker_ids_count_dialogue_voices_only():
    ids = ro.voice_id(LINES, "john_watson")
    assert ids.get("sherlock_holmes") == "S1" and "john_watson" not in ids


def test_a_speaker_is_described_the_first_time_and_only_the_first_time():
    first = ro.speaker_intro("sherlock_holmes", "S1", PHYS["sherlock_holmes"], set(), ["sherlock_holmes"])
    assert first == ("<Subject 1> (S1), on screen, a man in his late twenties, with a clipped English "
                     "voice at an even pace, says:")
    later = ro.speaker_intro("sherlock_holmes", "S1", PHYS["sherlock_holmes"], {"sherlock_holmes"},
                             ["sherlock_holmes"])
    assert later == "<Subject 1> (S1) says:"


def test_a_narration_line_is_clipped_to_the_segment_it_plays_under():
    """Measured: voice_events emitted span(t0, t0 + duration), so T01 said 'From 00:00
    to 00:05' inside a shot that ends at 00:03."""
    line = Line(index=1, kind="narration", speaker="john_watson", text="Young Stamford.", shot=1)
    out = ro.voice_events([line], {1: (0.25, 4.77)}, 0.0, {}, ["john_watson"], {}, "<Subject 1>",
                          "he lifts the glass", 0, 3, set())
    assert out == "<Subject 1>'s mouth is closed from 00:00 to 00:03 while he lifts the glass."


def test_an_insert_gets_no_lips_sentence_at_all():
    """review7 #1: a hand insert has no corresponding character."""
    line = Line(index=1, kind="narration", speaker="john_watson", text="Young Stamford.", shot=1)
    assert ro.voice_events([line], {1: (0.25, 4.77)}, 0.0, {}, ["john_watson"], {}, "", "", 0, 3, set()) == ""


def test_a_dialogue_line_is_introduced_then_driven_and_never_paced():
    out = ro.voice_events([LINES[1]], AT, 92.96, {"sherlock_holmes": "S1"}, ["sherlock_holmes"],
                          PHYS, "<Subject 1>", "lifts the test-tube", 4, 9, set())
    assert "<Subject 1> (S1), on screen," in out
    assert "says: <d>[English] You have been in Afghanistan.</d>" in out
    assert "His mouth shapes every syllable as the line is heard and closes on the last word." in out
    assert "at the pace of a spoken line" not in out


# ---- 3.11 / 3.12  the owner's two content rules ----------------------------

def test_a_public_setup_puts_people_to_work_behind_the_shot():
    """Owner verbatim: 'i liked you added some background folks in public shots'.  The
    clause is the contract's own `Framed.crowd`, falling back to `Setup.crowd`.

    Who the crowd is BEHIND is the block's staged faces: `them` for two or more,
    the one face's own label, and `Beyond the foreground` when nobody's face is
    staged -- episode 9 said "Behind him" over twelve shots with no him."""
    assert ro.life_sentence("the drinkers lift their glasses", 0, 3, "<Subject 1>") == \
        "Behind <Subject 1> the drinkers lift their glasses, from 00:00 to 00:03."
    assert ro.life_sentence("the drinkers lift their glasses", 0, 3, "them").startswith("Behind them ")
    assert ro.life_sentence("the drinkers lift their glasses", 0, 3, "").startswith("Beyond the foreground ")
    assert ro.life_sentence("", 0, 3, "them") == ""


def test_an_insert_takes_no_background_life_and_a_segment_inherits_its_setups():
    """`Setup.crowd`: it 'reaches every panel that is not an insert'."""
    setup = Setup(described="The Criterion Bar.", crowd="The drinkers lift their glasses.")
    assert ro.crowd_of({"size": "close", "crowd": "", "setup": setup}) == "the drinkers lift their glasses"
    assert ro.crowd_of({"size": "close", "crowd": "a barman draws a cork", "setup": setup}) == \
        "a barman draws a cork"
    assert ro.crowd_of({"size": "insert", "crowd": "", "setup": setup}) == ""


def test_watson_limps_whenever_he_walks_and_the_plan_may_never_say_slow():
    """Owner verbatim: the word 'slowly' never reaches the prompt; the limp carries it."""
    assert ro.limp_clause("Watson walks down the corridor") == \
        "Watson walks limping on his stick down the corridor"
    assert ro.limp_clause("Watson limps along on his stick") == "Watson limps along on his stick"
    assert ro.limp_clause("Stamford walks at a normal pace") == "Stamford walks at a normal pace"
    with pytest.raises(ValueError, match="slow"):
        ro.limp_clause("Watson limps and walks slowly on his stick")


# ---- 3.13  the camera ------------------------------------------------------

def test_a_static_shot_is_bound_to_an_action_never_asserted_over_the_whole_shot():
    """base-en §4.3's own example: 'The camera holds a static shot as the runner exits the frame.'"""
    out = ro.camera_sentence(SHOTS[0].motion, 0, 4)
    assert out == ("The camera holds a static shot as the hand lifts off the knob and reaches across "
                   "the bench for the test-tube, from 00:00 to 00:01.")
    assert "remain still throughout" not in out


def test_a_named_move_states_its_type_and_leaves_medium_amplitude_unsaid():
    motion = "Tracking beside them at a normal walking pace for the whole shot; the railings stream past"
    out = ro.camera_sentence(motion, 5, 8)
    assert out == ("The camera tracks beside them at a normal walking pace for the whole shot as the "
                   "railings stream past, from 00:05 to 00:08.")
    assert "slowly" not in out and "in one continuous motion in one direction" not in out


def test_the_remaining_clauses_get_their_own_stamps_and_the_last_one_runs_on():
    out = ro.beat_sentences(SHOTS[0].motion, 0, 4)
    assert out == ["At 00:01 the thumb comes back over the ball of the knob.",
                   "At 00:03 he leans his weight onto it, and the lean continues to the last frame of the shot."]


def test_a_dialogue_shots_follow_on_beat_is_timed_from_the_line_end():
    """Measured: T14 froze at 9.50 s (line end 9.50), T22 at 3.00 s (line end 2.92)."""
    motion = ("Static shot; Watson puts the question to the man beside him; "
              "he lifts the stick and plants it a pace forward")
    assert ro.camera_sentence(motion, 0, 5, line_end=4).endswith(", from 00:00 to 00:04.")
    assert ro.beat_sentences(motion, 0, 5, line_end=4) == [
        "At 00:04, as the line ends, he lifts the stick and plants it a pace forward, and the lift "
        "continues to the last frame of the shot."]


# ---- 3.14 / 3.15  the segments and their description ------------------------

def test_a_segment_carries_its_own_end_and_its_lastness():
    out = segs()
    assert [s["t"] for s in out] == [0.0, ro.grid_seconds(4.25)]
    # FIX D: the last range ends on the second the latent REACHES, not its ceiling
    assert [s["end"] for s in out] == [4, 8] and [s["last"] for s in out] == [False, True]
    assert out[0]["size"] == "close" and out[1]["faces"] == ["sherlock_holmes"]


def test_the_first_shot_begins_from_its_picture_and_later_shots_cut_to_theirs():
    body = build()
    body = body[body.index("detailed_description:"):]
    assert "[Shot 1] From 00:00 to 00:04. The shot begins from <Picture 3>: a close shot of" in body
    assert "[Shot 2] From 00:04 to 00:08. At 00:04 the shot cuts to a medium close-up of <Subject 1>" in body
    assert "beginning from <Picture 4>:" in body
    assert "the shot shows" not in body


def test_the_hidden_heuristic_and_its_plate_composition_sentence_are_gone():
    """5.10: 'The people are seen from behind, in profile or far off.' is the PLATE's
    own composition, and it is in no grammar."""
    text = build()
    assert "The people are seen from behind" not in text and "in profile or far off" not in text


def test_an_insert_says_what_is_in_frame_instead_of_naming_a_character():
    shot = Shot(index=1, section="setup", setup="c", size="close", faces=["john_watson"],
                frame="Close on Watson at the counter.", motion="Static shot; he lifts the glass",
                cuts=[SubShot(at_s=3.5, size="insert", frame="Insert at the foot-rail of the hand on the knob.",
                              motion="Static shot; the fingers loosen on the knob and close again")])
    text = ro.build([shot], [{"index": 1, "t_start": 0.0, "seconds": 7.0}],
                    [Line(index=0, kind="narration", speaker="john_watson", text="A word.", shot=1)],
                    {0: (0.25, 4.0)}, 175, ["john_watson"], {"john_watson": "A man in his late twenties."},
                    "A bar.", "john_watson", check_lint=False)
    second = text[text.index("detailed_description:"):]
    second = second[second.index("[Shot 2]"):]
    assert "only what <Picture 4> shows is in frame." in second
    assert "mouth is closed" not in second


# ---- 3.16 / 3.17  the whole prompt -----------------------------------------

def test_the_six_sections_come_in_the_official_order():
    text = build()
    order = [text.index(k) for k in ("subject_definitions:", "summary:", "retention_analysis:",
                                     "detailed_description:", "overall_soundscape:", "non_diegetic_music:")]
    assert order == sorted(order)


def test_the_summary_names_every_task_type_in_play_and_the_rendered_length():
    text = build()
    assert "[reference generation + keyframe completion + audio reuse] One 8.29-second take of 2 shots" in text
    assert "[Shot 1] begins from <Picture 3> and runs from 00:00 to 00:04" in text
    assert "[Shot 2] begins from <Picture 4> and runs from 00:04 to 00:08" in text


def test_the_soundscape_carries_ambience_only():
    """base-en §4.6: dialogue 'already belongs in the multimodal description'."""
    sound = build().split("overall_soundscape: ")[1].split("\n")[0]
    assert "voice" not in sound and "narration" not in sound and "<d>" not in sound


def test_the_builder_refuses_negation_and_its_own_output_carries_none():
    """Owner 2026-09-11 15:35: MiniMax does not read negation; say what IS."""
    assert ro.negations("The camera holds one position.") == []
    assert ro.negations("Do not move; nobody speaks; never reversing; <Subject 1> without a hat") == \
        ["never", "nobody", "not", "without"]
    assert ro.negations("He is barely there and none of it lands, neither one nor the other") == \
        ["barely", "neither", "none", "nor"]
    assert ro.negations(build()) == []


def test_a_dialogue_line_may_carry_a_negation_because_it_is_verbatim():
    """ref-en §5.4 requires the line byte for byte; the scan stops at <d>."""
    assert ro.negations("<Subject 1> says: <d>[English] I do not know.</d> His mouth shapes it.") == []


def test_the_builder_refuses_a_prompt_that_fails_the_lint():
    with pytest.raises(ValueError, match=r"L\d"):
        ro.build(SHOTS, PLACED, LINES, AT, FRAMES, faces=["sherlock_holmes"], physical=PHYS,
                 described=LAB, narrator="john_watson")


def test_a_place_word_is_matched_whole_never_inside_another_word():
    """`bar` inside `Saint Bartholomew's` called the hospital's street front a room."""
    assert ro.place_word("The Criterion Bar, Piccadilly, 1881.") == "room"
    assert ro.place_word("The street front of Saint Bartholomew's Hospital, 1881.") == "place"
    assert ro.place_word("A long stone corridor inside the hospital.") == "room"
    assert ro.short_place("A bar off Piccadilly, 1881.") == "a bar off Piccadilly"
    assert ro.short_place("The Criterion Bar, Piccadilly.") == "the Criterion Bar"
