"""The take-prompt garbles the Jekyll ep01 iter4 audit found (02_prompts.md T1-T19),
each pinned on the plan's own words."""
import pytest

from studio import episode_ref_official as ro


@pytest.fixture(autouse=True)
def jekyll_names():
    saved = dict(ro.DISPLAY), {k: list(v) for k, v in ro.ALIASES.items()}, ro.DRAWN
    ro.DISPLAY.clear()
    ro.DISPLAY.update({"gabriel_john_utterson": "Mr. Utterson", "richard_enfield": "Mr. Enfield",
                       "edward_hyde": "Edward Hyde", "child_of_hyde_incident": "the child"})
    ro.ALIASES.clear()
    ro.ALIASES.update({"gabriel_john_utterson": ["the lawyer"], "edward_hyde": ["the little man"],
                       "child_of_hyde_incident": ["the girl"]})
    yield
    ro.DISPLAY.clear(); ro.DISPLAY.update(saved[0])
    ro.ALIASES.clear(); ro.ALIASES.update(saved[1])
    ro.DRAWN = saved[2]


# ---- T1 / T2: capitals ------------------------------------------------------

def test_an_all_capitals_lead_is_lowered_whole_never_to_tHE():
    got = ro.lower_lead("THE FOCUS OF THE PICTURE IS the door at the CENTRE")
    assert got == "the focus of the picture is the door at the CENTRE"


def test_a_lead_word_still_lowers_and_a_name_keeps_its_capital():
    assert ro.lower_lead("The right hand lifts") == "the right hand lifts"
    assert ro.lower_lead("Watson's hand turns") == "Watson's hand turns"


def test_the_camera_position_opens_lower_case():
    out = ro.detail({"camera": "Over Enfield's shoulder, a yard behind him. The light comes from the LEFT.",
                     "at_rest": ""}, 40)
    assert out[0] == "The camera is over Enfield's shoulder, a yard behind him."


def test_a_named_camera_position_keeps_its_capital():
    out = ro.detail({"camera": "Enfield's eye line, a yard off.", "at_rest": ""}, 40)
    assert out[0] == "The camera is Enfield's eye line, a yard off."


# ---- T15: a drawn book has no lens -----------------------------------------

def test_a_drawn_book_drops_the_lens_length():
    ro.DRAWN = True
    out = ro.detail({"camera": "On the near pavement at eye height, a 50mm lens; the light from the LEFT.",
                     "at_rest": ""}, 40)
    assert "50mm" not in out[0] and out[0].startswith("The camera is on the near pavement at eye height")


def test_a_photoreal_book_keeps_the_lens():
    ro.DRAWN = False
    out = ro.detail({"camera": "On the near pavement at eye height, a 50mm lens.", "at_rest": ""}, 40)
    assert "50mm lens" in out[0]


# ---- T3: a panel cure never reaches the take --------------------------------

def test_a_cure_lead_is_dropped_from_the_take_frame():
    frame = ("Only the named people stand in the picture and everything else is the place. Medium close of "
             "Mr. Enfield on the near pavement")
    assert ro.without_cures(frame) == "Medium close of Mr. Enfield on the near pavement"


def test_two_cure_leads_and_a_templated_one_are_dropped():
    frame = ("The frame is cut as a medium shot. The named subject stands large at the CENTRE of the frame. "
             "Medium beside the little man as he walks")
    assert ro.without_cures(frame) == "Medium beside the little man as he walks"


def test_a_frame_with_no_cure_is_untouched():
    assert ro.without_cures("Wide of the by-street. The door is black.") == "Wide of the by-street. The door is black."


# ---- T4: an epithet binds to its staged Subject, described once -------------

def test_tagged_binds_an_epithet_and_drops_its_parenthetical():
    text = "the little man (clean-shaven, pale smooth cheeks) on the door steps"
    assert ro.tagged(text, ["edward_hyde", "richard_enfield"]) == "<Subject 1> on the door steps"


def test_tagged_drops_the_parenthetical_after_a_bound_name():
    text = "Mr. Enfield (light-brown top hat, fashionable dark frock coat) and the lawyer (black bowler hat)"
    got = ro.tagged(text, ["richard_enfield", "gabriel_john_utterson"])
    assert got == "<Subject 1> and <Subject 2>"


def test_an_unstaged_epithet_keeps_its_words():
    assert ro.tagged("toward the girl (fair hair)", ["edward_hyde"]) == "toward the girl (fair hair)"


def test_people_in_reads_an_epithet():
    assert ro.people_in("onto the little man on the steps", ["richard_enfield", "edward_hyde"]) == ["edward_hyde"]


# ---- T9: the closed mouth is the man the frame names ------------------------

def test_mouth_of_names_the_epithet_person_not_the_listener():
    seg = {"size": "medium", "frame": "over Mr. Enfield's near shoulder onto the little man on the steps",
           "faces": ["edward_hyde", "richard_enfield"], "still": False}
    assert ro.mouth_of(seg, ["edward_hyde", "richard_enfield"], ["edward_hyde", "richard_enfield"]) == "<Subject 1>"


# ---- T5: the speaker is not described again ---------------------------------

def test_a_staged_speaker_carries_no_second_description():
    got = ro.speaker_intro("richard_enfield", "S1", "Receding brown hair; clean-shaven. A compact man of about forty.",
                           set(), ["richard_enfield"])
    assert got == "<Subject 1> (S1), on screen, with a clipped English voice at an even pace, says:"


def test_an_unstaged_speakers_identity_is_his_age_sentence_never_a_stub():
    phys = "Lank grey hair, white at the sides; clean-shaven. A lean, long, bony, dry man of about forty, narrow-chested."
    assert ro.voice_of(phys).startswith("a lean, long, bony, dry man of about forty, with a clipped")


def test_voice_of_without_an_age_sentence_says_a_person():
    assert ro.voice_of("Receding brown hair; clean-shaven; light-brown top hat.").startswith("a person, with")


# ---- T6: the line has ended; nobody still speaks -----------------------------

def test_as_the_line_ends_drops_a_trailing_as_he_speaks():
    out = ro.beat_sentences("The camera pans across; he turns; his free hand opens toward the door as he speaks",
                            0, 6, line_end=4)
    assert "as he speaks" not in " ".join(out)
    assert out[0].startswith("At 00:04, as the line ends, his free hand opens toward the door")


# ---- T7: an adjective is not a verb ------------------------------------------

def test_motion_noun_reads_lean_as_an_adjective_after_his():
    assert ro.motion_noun("his lean hands swing at his sides") == "the swing"


def test_motion_noun_reads_leans_as_a_verb():
    assert ro.motion_noun("he leans in close") == "the lean"


def test_motion_noun_an_open_hand_is_a_gesture():
    assert ro.motion_noun("his lean hand opens toward <Subject 2>") == "the gesture"


# ---- T8: the end noun ---------------------------------------------------------

def test_end_noun_keeps_a_hyphenated_word_whole():
    end = "The by-street seen from above, the blistered door at the CENTRE"
    assert ro.end_noun(end) not in ("", "the", "The")
    assert "by-street" in ro.end_noun(end)


def test_end_noun_keeps_face_to_face_whole():
    assert ro.end_noun("The two men face to face at the CENTRE, the lamp at the LEFT edge") == "the two men face to face"


def test_end_noun_refuses_a_clause_with_a_finite_verb():
    assert ro.end_noun("The knuckly hand turns the key in the lock at the CENTRE") == ""


def test_arrival_end_says_nothing_for_an_empty_noun():
    assert ro.arrival_end("The knuckly hand turns the key in the lock at the CENTRE edge") == ("", "")


# ---- T16 / T13: an unstaged person named in a motion -------------------------

def test_offscreen_aims_at_the_frame_edge_not_a_person():
    assert ro.offscreen("his free hand opens toward the lawyer as he speaks", ["richard_enfield"]) == \
        "his free hand opens toward the edge of the frame as he speaks"


def test_offscreen_leaves_a_staged_person_alone():
    text = "his free hand opens toward the lawyer"
    assert ro.offscreen(text, ["gabriel_john_utterson"]) == text


# ---- T19: density --------------------------------------------------------------

def test_a_short_segment_keeps_one_action_per_1_2_seconds():
    clauses = ["he pulls back", "he lifts his cane and turns", "the lawyer nods and falls into step"]
    assert ro.paced_clauses(clauses, 1.6) == clauses[:1]
    assert ro.paced_clauses(clauses, 4.0) == clauses


# ---- T14: no lettering ---------------------------------------------------------

def test_the_summary_carries_the_unlettered_sentence():
    assert ro.UNLETTERED.endswith("unlettered.")
    assert not ro.negations(ro.UNLETTERED)


def test_an_all_capitals_lead_before_a_name_is_lowered_whole():
    got = ro.lower_lead("THE FOCUS OF THE PICTURE IS Mr. Enfield's face")
    assert got == "the focus of the picture is Mr. Enfield's face"


def test_end_noun_stops_at_a_participle():
    assert ro.end_noun("The by-street seen from above, the door at the CENTRE") == "the by-street"


def test_a_dry_build_of_a_panel_book_is_judged_on_the_panel_band():
    """plan_check's G-TAKELINT dry build stages nothing (refs=None), yet a sheets book stages a
    panel on every take: the block floor is the panel band's 150, never the bare-refs 240."""
    assert ro.describes_panel(True, None) is True
    assert ro.describes_panel(True, 4) is True
    assert ro.describes_panel(False, None) is False
