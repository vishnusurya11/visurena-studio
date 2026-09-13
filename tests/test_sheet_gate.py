"""The PRE-SPEND gate: the last free moment before a paid draw.

Owner, 2026-09-11: "dq check before generating images".  Everything here runs
on the TEXT of a sheet prompt, so a fault that can be read in words is refused
in words, for $0, instead of being discovered on a $0.13-$0.20 sheet and then
animated for GPU-hours.

Every threshold in this file is measured on the six real sheets of
`library/20260822113400_a-study-in-scarlet/episodes/ep01` (45 panels, 153
within-sheet pairs) -- the numbers are in `studio/sheet_gate.py`'s docstrings.
No test here draws, decodes an image, calls an API or spends a cent.
"""
from studio import sheet_gate as gate
from studio.episode_spec import Setup

CORRIDOR = Setup(described="A whitewashed hospital corridor, 1881.", cast=["john_watson"],
                 landmark="the pale barred window at the far end", route="from the near end to the far door",
                 crowd="a porter in a leather apron carrying a covered tray away down the corridor, "
                       "two students in black coats standing at a doorway")
LAB = Setup(described="A chemical laboratory.", cast=["sherlock_holmes"],
            crowd="one student in shirtsleeves at a far bench with his back turned, working")


def seg(shot=0, sub=0, **kw):
    base = {"shot": shot, "sub": sub, "size": "medium", "path": 0.1, "faces": [], "camera": "",
            "frame": "Two men on the flagstones.", "motion": "he walks on", "at_rest": "",
            "end_frame": "", "changed": "", "crowd": "two porters halted at the wall, unloading a trolley"}
    return base | kw


# ---- naming ---------------------------------------------------------------

def test_a_finding_names_the_panel_the_owner_reads_on_the_contact_sheet():
    assert gate.panel_key(seg(9, 1)) == "Q09_1"
    assert gate.panel_key(dict(seg(2), end=True)) == "Q02_0E"


# ---- AFFIRMATIVE ----------------------------------------------------------

def test_a_negation_anywhere_in_the_built_prompt_is_a_hard_finding():
    panels = [seg(9, frame="No gloves on the hand on the stick.")]
    found = gate.affirmative("PANELS\nPanel 1 - MEDIUM. In frame: No gloves on the hand on the stick.", panels)
    assert [(f.check, f.panel, f.hard) for f in found] == [("AFFIRMATIVE", "Q09_0", True)]


def test_a_negation_in_a_sheet_wide_block_is_owned_by_the_sheet():
    found = gate.affirmative("CONSTRAINTS\nNo text on any surface.", [seg(9)])
    assert found[0].panel == "sheet" and found[0].text.lower() == "no"


def test_an_affirmative_prompt_reports_nothing():
    assert gate.affirmative("In frame: a bare sunburnt hand on the silver knob.", [seg(9)]) == []


# ---- TWINS ----------------------------------------------------------------

def test_two_panels_that_ask_for_one_picture_are_twins():
    """Reviewer 3, 2026-09-11: corridor S09 / S11 measured 0.731 on frame+camera
    before the fix -- same axis, same walking height, same normal lens square down
    the corridor.  That pair is the positive case the floor is set against."""
    a = seg(9, frame="Medium shot from behind at the corridor's near end: Stamford a pace ahead, "
                     "Watson's brown tweed back, bars of window light on the flagstones ahead.",
            camera="in the middle of the corridor at walking height, a normal lens, square down the "
                   "corridor, Watson's brown tweed back in the LEFT half and the barred windows down "
                   "the RIGHT side of frame")
    b = seg(11, frame="Medium shot from behind at the corridor's far end: Stamford a pace ahead, "
                      "Watson's brown tweed back, bars of window light on the flagstones ahead.",
            camera="in the middle of the corridor at walking height, a normal lens, square down the "
                   "corridor, Watson's brown tweed back in the LEFT half and the barred windows down "
                   "the RIGHT side of frame")
    found = gate.twins([a, b])
    assert [(f.check, f.panel, f.hard) for f in found] == [("TWINS", "Q11_0", True)]


def test_two_panels_of_the_same_place_at_different_sizes_are_not_twins():
    a = seg(9, frame="Medium shot from behind: Stamford a pace ahead on the flagstones.",
            camera="in the middle of the corridor at walking height, a normal lens")
    b = seg(10, frame="Insert through the dissecting-room doorway: a plain wooden stick on a slab "
                      "beside a body under a grey sheet, cold light from a high window.",
            camera="low at the slab's near edge, a macro lens")
    assert gate.twins([a, b]) == []


def test_the_twin_floor_is_the_measured_one():
    assert (gate.TWIN, gate.WATCH) == (0.72, 0.62)


def test_a_pair_just_under_the_floor_is_a_watch_not_a_refusal():
    a, b = seg(9, frame="alpha beta gamma delta epsilon zeta"), seg(11, frame="alpha beta gamma delta epsilon eta")
    found = gate.twins([a, b], floor=0.99, watch=0.5)
    assert [(f.check, f.hard) for f in found] == [("TWINS", False)]


def test_overlap_is_one_for_one_text_and_zero_for_two_subjects():
    assert round(gate.overlap("a bare sunburnt hand", "a bare sunburnt hand"), 6) == 1.0
    assert gate.overlap("a bare sunburnt hand", "the wet cobbled street") == 0.0


# ---- INSTANT BEFORE -------------------------------------------------------

def test_a_start_panel_whose_own_action_has_already_happened_is_refused():
    panel = seg(8, frame="Full shot up the flight: Watson has climbed to the threshold sill.",
                motion="Watson climbs all five steps on his stick")
    found = gate.instant_before(panel)
    assert [(f.check, f.panel, f.hard) for f in found] == [("INSTANT BEFORE", "Q08_0", True)]
    assert "has climbed" in found[0].text


def test_has_just_is_the_fault_whatever_the_motion_says():
    panel = seg(2, frame="Stamford has just set the glass down in its own wet ring.", motion="he looks away")
    assert [f.hard for f in gate.instant_before(panel)] == [True]


def test_a_background_figure_at_rest_is_not_the_panels_own_action():
    """S20 on the live plan: "a porter HAS SET his barrow down against the railings"
    is the crowd standing still, and the panel's own motion is Watson turning.  A
    finished verb the motion never names is a watch, not a refusal."""
    panel = seg(20, at_rest="a porter has set his barrow down against the railings and stands beside it",
                motion="Static shot; Watson turns his whole upper body toward Stamford over 2 seconds")
    assert [f.hard for f in gate.instant_before(panel)] == [False]


def test_a_line_already_spoken_is_a_watch_because_no_rule_separates_the_two_cases():
    """Reviewer 3 called S18's "lips just closed on the last word" a fault and
    S22's identical phrasing correct.  No text rule tells them apart, so the gate
    prints it and lets the eye decide rather than refusing a good sheet."""
    panel = seg(22, at_rest="his lips just closed on the wry smile with the last word held on them")
    assert [f.hard for f in gate.instant_before(panel)] == [False]


def test_the_word_already_alone_is_only_a_watch():
    """'his weight already down on the stick' is a REST state, not a finished
    action; measured on the live plan it is the difference between a true fault
    (S22, the line already spoken) and a correctly written start panel (S12.1)."""
    panel = seg(12, sub=1, at_rest="Watson stands with his weight already down on the black stick")
    assert [f.hard for f in gate.instant_before(panel)] == [False]


def test_an_end_panel_is_allowed_to_show_its_action_finished():
    panel = dict(seg(2), end=True, frame="Watson's glass has risen to his mouth.")
    assert gate.instant_before(panel) == []


# ---- END PANEL ------------------------------------------------------------

def test_an_end_picture_without_a_named_change_is_refused():
    panel = seg(2, end_frame="Stamford's glass is at his lips.", changed="")
    found = gate.end_findings(panel)
    assert [(f.check, f.panel, f.hard) for f in found] == [("END PANEL", "Q02_0", True)]


def test_a_changed_sentence_of_the_measured_shape_passes():
    panel = seg(2, end_frame="Stamford's glass is at his lips.",
                changed="Watson's glass has risen to his mouth in the LEFT third of frame, a hand tall.")
    assert gate.end_findings(panel) == []


def test_a_changed_sentence_that_names_no_frame_edge_or_size_only_warns():
    panel = seg(19, sub=1, end_frame="The two men are up the aisle.",
                changed="The two men have come three paces up the aisle and fill the frame from the knees.")
    found = gate.end_findings(panel)
    assert [(f.check, f.hard) for f in found] == [("END PANEL", False)]
    assert "frame edge" in found[0].note


def test_a_changed_paragraph_only_warns_and_says_its_length():
    panel = seg(3, end_frame="The cab is gone.",
                changed="The hansom has crossed to the RIGHT of frame, a sixth of the frame's height, and "
                        "the boy on the kerb has turned, and two pedestrians have passed, and the water "
                        "has fallen back into the broken puddle behind the wheel.")
    found = gate.end_findings(panel)
    assert [(f.check, f.hard) for f in found] == [("END PANEL", False)]
    assert "41 words" in found[0].note


def test_the_changed_band_is_the_reviewers_twelve_to_seventeen():
    assert gate.CHANGED_WORDS == (12, 17)


# ---- CAMERA ---------------------------------------------------------------

def test_a_camera_move_word_in_a_still_panel_is_refused():
    panel = seg(8, camera="at the foot of the steps, tilted up the flight, a normal lens")
    found = gate.camera_still(panel)
    assert [(f.check, f.panel, f.hard) for f in found] == [("CAMERA", "Q08_0", True)]
    assert found[0].text.lower() == "tilted"


def test_a_camera_that_only_stands_somewhere_passes():
    assert gate.camera_still(seg(8, camera="at the foot of the worn stone steps, set low at the height "
                                           "of the second step and looking up the flight, a normal lens")) == []


def test_an_end_panel_is_read_as_the_sheet_reads_it_and_no_further():
    """`end_text()` prints the END panel's picture and its crowd; it never prints
    the `camera` or `at_rest` of the panel it closes -- it says "the same camera
    position as panel j".  A gate that read those would fail a panel on words the
    drawer is never shown."""
    panel = dict(seg(8), end=True, frame="Watson stands on the threshold sill, the bowler in his left hand.",
                 camera="at the foot of the steps, tilted up the flight", at_rest="his hand rising to the brim")
    assert gate.camera_still(panel) == [] and gate.drawn_text(panel) == panel["frame"]


def test_a_move_word_in_the_motion_is_not_the_cameras_business():
    """`motion` is written FOR MiniMax; the sheet never sees it (`still()` strips
    the camera clause), so the gate reads the `camera` field alone."""
    assert gate.camera_still(seg(3, motion="Tracking beside the hansom for the whole shot")) == []


# ---- GEOMETRY -------------------------------------------------------------

def test_a_relation_between_two_parts_of_a_vehicle_is_refused():
    """Q03_1 came back with the wheel and the horse's legs side by side: "ahead of"
    is the documented weak spot, "which edge at what size" is the strength."""
    panel = seg(3, sub=1, frame="Insert low beside the moving hansom: the horse's hind legs ahead of "
                                "the wheel, the wet street receding.")
    found = gate.geometry(panel)
    assert [(f.check, f.panel, f.hard) for f in found][0] == ("GEOMETRY", "Q03_1", True)
    assert any("ahead of the wheel" in f.text for f in found)


def test_a_relation_to_a_wall_is_how_a_room_is_described():
    panel = seg(0, frame="Medium two-shot at the counter: the gilt mirror behind the counter "
                         "reflecting their backs, a hansom waiting at the kerb beyond the doors.")
    assert gate.geometry(panel) == []


def test_a_frame_edge_named_in_lower_case_is_still_a_frame_edge():
    """S07 on the live plan places the whole wall "from the gateway arch at the left
    of frame to the corner at the right of frame" and then says the cabman sits up
    behind the hood: the panel has done the work the check asks for."""
    panel = seg(7, frame="Wide from across the street: the hansom at the kerb, the cabman up behind the hood.",
                camera="across the street on the far pavement, the soot-dark wall running from the gateway "
                       "arch at the left of frame to the corner at the right of frame")
    assert gate.geometry(panel) == []


def test_a_vehicle_part_placed_at_a_frame_edge_passes():
    panel = seg(3, sub=1, frame="Insert low at the kerb: one tall spoked wheel filling the LEFT two "
                                "thirds of frame, the horse's hind hooves small at the TOP RIGHT, "
                                "two cab-lengths ahead of the wheel.")
    assert gate.geometry(panel) == []


# ---- CROWD ----------------------------------------------------------------

def test_a_public_setup_is_the_one_whose_own_crowd_names_more_than_one_person():
    assert gate.public(CORRIDOR) is True and gate.public(LAB) is False


def test_a_public_panel_with_no_crowd_of_its_own_warns():
    found = gate.crowd_findings(seg(9, crowd=""), CORRIDOR)
    assert [(f.check, f.panel, f.hard) for f in found] == [("CROWD", "Q09_0", False)]


def test_a_crowd_with_a_count_and_an_activity_passes():
    assert gate.crowd_findings(seg(9, crowd="two porters halted at the wall with a covered trolley "
                                            "between them"), CORRIDOR) == []


def test_a_crowd_with_no_activity_warns():
    found = gate.crowd_findings(seg(9, crowd="two porters and a nurse"), CORRIDOR)
    assert [f.hard for f in found] == [False] and "activity" in found[0].note


def test_an_insert_carries_no_crowd_and_that_is_right():
    assert gate.crowd_findings(seg(9, size="insert", crowd=""), CORRIDOR) == []


def test_a_private_setup_that_grows_a_crowd_warns():
    found = gate.crowd_findings(seg(13, crowd="eight or nine students working at the far benches"), LAB)
    assert [(f.check, f.hard) for f in found] == [("CROWD", False)]
    assert "private" in found[0].note


# ---- WARDROBE -------------------------------------------------------------

def test_a_hand_in_frame_without_the_contract_warns():
    found = gate.wardrobe(seg(0, frame="his hand closed on the silver ball knob of the stick"))
    assert [(f.check, f.panel, f.hard) for f in found] == [("WARDROBE", "Q00_0", False)]
    assert found[0].note.startswith("hand")


def test_the_named_contract_passes():
    assert gate.wardrobe(seg(0, frame="his bare sunburnt hand closed on the silver ball knob")) == []
    assert gate.wardrobe(seg(4, frame="Watson in his brown bowler, the hat square on his head")) == []


def test_a_jacket_without_its_colour_warns():
    found = gate.wardrobe(seg(17, frame="Medium shot from behind Holmes's velvet shoulder at his table"))
    assert [f.note.split(":")[0] for f in found] == ["jacket"]


# ---- PROPS ----------------------------------------------------------------

def test_a_prop_the_motion_moves_that_the_frame_never_drew_warns():
    panel = seg(17, sub=1, frame="Insert on the bench: the litre vessel and one red thread in the water.",
                motion="his hand lowers the pipette to the water over 2 seconds")
    found = gate.props(panel)
    assert [(f.check, f.panel, f.hard) for f in found] == [("PROPS", "Q17_1", False)]
    assert found[0].text == "pipette"


def test_a_prop_named_by_its_other_name_is_still_in_frame():
    panel = seg(6, frame="Medium close inside the hansom: Stamford in profile past the brass lamp.",
                motion="the cab sways and he looks out of the side")
    assert gate.props(panel) == []


# ---- GRID -----------------------------------------------------------------

def test_a_panel_count_that_disagrees_with_the_grid_is_refused():
    prompt = "SHEET\nA film storyboard sheet: a 3 by 2 grid of 6 equal vertical 9:16 panels"
    found = gate.grid_findings([seg(0), seg(1)], prompt, (3, 2, (2048, 2048)))
    assert [(f.check, f.panel, f.hard) for f in found] == [("GRID", "sheet", True)]
    assert "6" in found[0].note and "2" in found[0].note


def test_the_sheet_that_names_its_own_cell_count_passes():
    prompt = "SHEET\nA film storyboard sheet: a 3 by 2 grid of 6 equal vertical 9:16 panels"
    assert gate.grid_findings([seg(k) for k in range(6)], prompt, (3, 2, (2048, 2048))) == []


def test_a_sheet_whose_sentence_says_another_number_is_refused():
    prompt = "SHEET\nA film storyboard sheet: a 3 by 3 grid of 9 equal vertical 9:16 panels"
    found = gate.grid_findings([seg(k) for k in range(6)], prompt, (3, 2, (2048, 2048)))
    assert [f.hard for f in found] == [True]


# ---- the verdict ----------------------------------------------------------

def test_one_hard_finding_refuses_the_draw_and_a_watch_does_not():
    hard = [gate.Finding("TWINS", "Q11_0", "x", True)]
    watch = [gate.Finding("CROWD", "Q11_0", "x", False)]
    assert gate.verdict(hard)["passed"] is False
    assert gate.verdict(watch)["passed"] is True
    assert gate.verdict(hard + watch) == {"passed": False, "hard": 1, "watch": 1,
                                          "checks": {"TWINS": 1, "CROWD": 1}}


def test_the_whole_sheet_runs_every_check_on_every_panel():
    panels = [seg(0), seg(1, frame="his hand on the knob", camera="tracking beside him")]
    prompt = "SHEET\nA film storyboard sheet: a 3 by 1 grid of 3 equal vertical 9:16 panels"
    found = gate.sheet_findings(panels, CORRIDOR, prompt, (3, 1, (1536, 1024)))
    names = {f.check for f in found}
    assert {"CAMERA", "WARDROBE", "GRID"} <= names
    assert all(f.panel for f in found)


def test_a_contract_trimmed_by_the_limit_is_a_hard_fault():
    """Owner 2026-09-11: the stick's length never reached a drawer because the
    contract was silently cut at 220 characters.  Silence is what made it cost 23
    panels, so the gate says it out loud."""
    from studio import sheet_gate
    long = ("A man in his late twenties, as thin as a lath, as brown as a nut, dark hair swept back, "
            "a thin waxed moustache, a brown bowler hat, a brown tweed overcoat over a tweed "
            "waistcoat with a watch chain and a white cravat pinned with a stud, both hands bare to "
            "the wrist and sunburnt. The stick stands hip high, its shaft as thick as one finger.")
    assert sheet_gate.contract_faults({"john_watson": long})
    assert not sheet_gate.contract_faults({"john_watson": "A short man in a grey coat."})
