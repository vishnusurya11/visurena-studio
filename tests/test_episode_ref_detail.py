"""The per-shot DETAIL of a take prompt: the six per-setup authors write
`camera`, `at_rest`, `end` and `changed` into every panel of the plan, and the
block spends them until it lands in the owner's 150-240 word band (spec §1.4
D2-D6, L14).

Free and offline: every fixture here is a string.  Nothing renders, nothing is
measured, no GPU and no credit.
"""
from studio import episode_ref_official as ro
from studio.episode_spec import Setup, Shot


# ---- the stillness vocabulary the authors write for a DRAWER ---------------

def test_the_drawers_stillness_words_become_positions_the_camera_can_see():
    """The plan's prose is written for a storyboard artist, who is drawing ONE
    frame, so it says `held`, `stays` and `waits`.  L2 measures those words at
    0.77 frozen in the render, so each becomes the position it describes."""
    assert ro.calm("the brown bowler held against his chest") == \
        "the brown bowler against his chest"
    assert ro.calm("his lips stay closed") == "his lips are closed"
    assert ro.calm("his face stays in frame") == "his face is in frame"
    assert ro.calm("the brown bowler still on") == "the brown bowler on"
    assert ro.calm("a cab waits at the corner") == "a cab stands at the corner"
    assert ro.calm("a drinker holds a newspaper open") == "a drinker keeps a newspaper open"
    assert ro.calm("the reflections hold steady") == "the reflections keep steady"
    assert ro.calm("the flagstone floor holds the bottom of frame") == \
        "the flagstone floor keeps the bottom of frame"


def test_calm_leaves_prose_that_already_moves_alone():
    assert ro.calm("the hand lifts off the knob and reaches across the bench") == \
        "the hand lifts off the knob and reaches across the bench"
    assert ro.lint("The camera holds a static shot as he drinks.", {}) == []


# ---- how much of a field a block may spend ---------------------------------

def test_a_field_is_cut_at_a_clause_boundary_never_mid_phrase():
    text = "on the drinkers' side of the counter, at standing eye height, a normal lens, turned along it"
    assert ro.trim(text, 12) == "on the drinkers' side of the counter, at standing eye height"
    assert ro.trim(text, 4) == "on the drinkers' side of the counter"   # the first clause always lands
    assert ro.trim("", 20) == ""


def test_a_block_asks_for_only_the_detail_it_is_short_of():
    """The gate is per block (OWNER 5.17), so a heavy block takes no padding at
    all and a light one takes just enough to clear the floor."""
    assert ro.budget(120) == 45          # 165 is the floor plus a margin
    assert ro.budget(165) == 0 and ro.budget(231) == 0
    assert ro.budget(0) == 165


def test_the_detail_spends_the_camera_first_and_then_what_is_at_rest():
    seg = {"camera": "on the drinkers' side of the counter, at standing eye height",
           "at_rest": "the brown bowler rests flat against his chest, his head level"}
    assert ro.detail(seg, 0) == []
    assert ro.detail(seg, 10) == ["The camera is on the drinkers' side of the counter."]
    assert ro.detail(seg, 40) == ["The camera is on the drinkers' side of the counter, at standing eye height.",
                                  "At the first frame the brown bowler rests flat against his chest, "
                                  "his head level."]


def test_the_detail_is_calm_before_it_is_spent():
    seg = {"camera": "set low with the tray held level", "at_rest": "his lips stay closed"}
    assert ro.detail(seg, 40) == ["The camera is set low with the tray level.",
                                  "At the first frame his lips are closed."]


# ---- the two block-level guarantees (L8, L9) -------------------------------

def test_a_gait_carries_its_pace_at_the_end_of_its_own_clause():
    """D11, owner: the motion runs at normal speed, and the pace is named.  It lands
    at the end of the clause, never stacked on the verb (base-en §4.3)."""
    assert ro.paced("He walks down the corridor.") == "He walks down the corridor at a normal walking pace."
    assert ro.paced("He steps back from the doorway, then turns.") == \
        "He steps back from the doorway at a normal walking pace, then turns."
    assert ro.paced("The camera is one step farther along the counter.") == \
        "The camera is one step farther along the counter."      # a step is a noun here
    assert ro.paced("He walks at a normal pace.") == "He walks at a normal pace."
    assert ro.paced("The horse trots ahead.") == "The horse trots ahead at a normal trot."
    assert ro.paced("The hand lifts off the knob.") == "The hand lifts off the knob."


def test_the_limp_names_the_stick_once():
    """Measured in iteration 5: `takes a full step limping on his stick back from the
    doorway on his stick` -- the plan had already said which stick."""
    assert ro.limp("a close shot of <Subject 1> walking the pavement") == \
        "a close shot of <Subject 1> walking limping on his stick the pavement"
    assert ro.limp("<Subject 1> steps down on his stick") == "<Subject 1> steps limping down on his stick"
    assert ro.limp("the glass goes down on the mahogany") == "the glass goes down on the mahogany"


def test_the_pace_and_the_limp_are_block_promises_and_spare_the_spoken_line():
    """D12, owner verbatim.  The walk is as often in the frame text as in the motion
    (`Watson seen from behind, his boot on the third step`), and the dialogue is
    verbatim by grammar, so the block writes into neither it nor the life clause."""
    parts = [("a close shot of <Subject 1> climbing the third step", True),
             ("<Subject 1> (S1) says: <d>[English] I stepped out.</d>", False),
             ("At 00:02 he steps up to the door.", True),
             ("Behind him two porters step in through the gates, from 00:00 to 00:05.", False)]
    out = ro.guarantee(parts, "<Subject 1>")
    assert out[1] == parts[1][0] and out[3] == parts[3][0]
    assert out[0] == ("a close shot of <Subject 1> climbing limping on his stick the third step "
                      "at a normal walking pace")
    assert ro.guarantee([("Stamford walks at a normal pace", True)], "<Subject 1>") == \
        ["Stamford walks at a normal pace"]


# ---- the gates that measure the finished block -----------------------------

def test_a_body_scale_action_counts_in_every_inflection_the_plan_writes():
    """OWNER 5.18.  The plan writes `both men advance`, `the hands pump` and `his
    shoulders turn round`; the gate is the verb's CLASS, never its ending."""
    for body in ("he walks on", "both men advance three strides", "his shoulders turn round",
                 "the two hands pump up and down", "he stands up to his full height",
                 "the horse trots ahead", "he bends over the table", "the hand reaching across"):
        assert ro.ACTION.search(body), body
    for micro in ("his eyes narrow slightly", "his brows draw together", "he blinks once",
                  "his jaw sets", "a single breath"):
        assert not ro.ACTION.search(micro), micro


def test_the_builder_owns_the_clock_so_the_authors_seconds_come_out():
    """D1/D4: the block states whole seconds that cover the take, so the plan's own
    `by 3.5 seconds` inside a clause gave one beat two different times."""
    assert ro.untimed("the hand lifts it out of frame over 2 seconds") == "the hand lifts it out of frame"
    assert ro.untimed("by 3.5 seconds the knob stands alone on the rail") == \
        "the knob stands alone on the rail"
    assert ro.untimed("his head turns to the hat and back by 3 seconds") == \
        "his head turns to the hat and back"
    assert ro.untimed("they walk on for the whole shot") == "they walk on for the whole shot"


def test_a_clause_that_only_says_the_mouth_is_closed_is_not_a_beat():
    """D7 and D9 state the mouth once, bound to an action.  Measured: two or more
    stillness sentences in a segment ran 0.77 frozen against 0.47."""
    head, rest = ro.clauses_of("Static shot; he lifts the glass; his lips stay closed")
    assert (head, rest) == ("Static shot", ["he lifts the glass"])
    assert ro.clauses_of("Static shot; both mouths are closed")[1] == []
    assert ro.clauses_of("Static shot; he closes the door")[1] == ["he closes the door"]


def test_a_denied_verb_is_not_an_action():
    """T6 of the spec's calibration table: `His head does not turn away and the framing
    does not change` is the measured freeze, and it must still fail L4."""
    assert ro.affirmative("The smile stays on him. His head does not turn away.") == \
        "The smile stays on him "
    assert not ro.ACTION.search(ro.affirmative("His head does not turn away"))
    assert ro.ACTION.search(ro.affirmative("His head turns away"))


def test_the_take_floor_is_the_sum_of_its_blocks_when_350_cannot_be_reached():
    """ref-en §5.2 asks 350-500 words a take; a ONE-shot take cannot reach 350
    without breaking the owner's 240-word block ceiling, so the floor is the
    blocks' own floor until the take has the shots to carry the guide's."""
    assert ro.take_floor(1) == 150 and ro.take_floor(2) == 300 and ro.take_floor(3) == 350
    one = "detailed_description:\n" + ro.STYLE + "\n[Shot 1] From 00:00 to 00:08. " + "word " * 200
    assert [f for f in ro.l14_length(one, {}) if "detailed_description is" in f] == []


def test_the_closed_mouth_names_what_the_PERSON_does_not_what_the_street_does():
    """D7: `<Subject 1>'s mouth is closed ... while he {action}` -- measured, the
    clause was taking the first motion clause even when its subject was the
    scenery ('while the street and shopfronts stream past the side window')."""
    motion = ("Static shot; the street streams past the side window; a jolt throws him toward the "
              "camera and his hand comes up to the knob")
    assert ro.mouth_action(motion, "<Subject 1>") == "a jolt throws him toward the camera"
    assert ro.mouth_action("Static shot; he lifts the glass and drinks", "<Subject 1>") == \
        "he lifts the glass and drinks"
    walk = ("Tracking ahead of him; the railings stream past behind him; <Subject 1>'s head turns "
            "from Stamford to the street ahead")
    assert ro.mouth_action(walk, "<Subject 1>") == "his head turns from Stamford to the street ahead"


def test_a_clause_keeps_its_punctuation_when_the_seconds_come_out():
    assert ro.untimed("he points the stick back at the arch by 5 seconds.") == \
        "he points the stick back at the arch."
    assert ro.untimed("then his head and shoulders turn round") == "his head and shoulders turn round"


# ---- the whole block -------------------------------------------------------

SHOT = Shot(index=4, section="setup", setup="criterion", size="close", faces=["john_watson"],
            frame="Close on Watson turned from the counter, the brown bowler held against his chest.",
            motion="Static shot; he lifts the wine glass and drinks; he sets it down on the mahogany",
            camera="on the drinkers' side of the counter at its crowded near end, at standing eye "
                   "height, a normal lens, turned along the mahogany toward the far end",
            at_rest="the brown bowler rests flat against his chest, both edges of its brim level, "
                    "his fingers closed on the crown; the mahogany beside his elbow lies bare")
SETUP = Setup(described="The Criterion Bar, Piccadilly, 1881.",
              crowd="eight or nine men two deep at the counter, a barman drawing a cork")


def test_a_light_block_is_filled_to_the_band_from_the_panels_own_prose():
    from studio.episode_spec import Line
    text = ro.build([SHOT], [{"index": 4, "t_start": 0.0, "seconds": 7.0}],
                    [Line(index=0, kind="narration", speaker="john_watson", text="A word.", shot=4)],
                    {0: (0.25, 4.0)}, 175, ["john_watson"], {"john_watson": "A man of thirty."},
                    SETUP.described, "john_watson", setup=SETUP, check_lint=False)
    body = ro.blocks(text)[0][3]
    assert 150 <= ro.words(body) <= 240
    assert "The camera is on the drinkers' side of the counter at its crowded near end" in body
    assert "At the first frame the brown bowler rests flat against his chest" in body
    assert ro.lint(text, {}) == []
