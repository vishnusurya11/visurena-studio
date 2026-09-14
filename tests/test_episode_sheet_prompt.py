"""The sheet prompt is LABELLED BLOCKS, and every sentence on it says what IS.

Owner and reviewers, 2026-09-11, on the six sheets on disk: the drawer copied
four of five END cells because it was told "identical"; it drew three
different hansoms because "the horse ahead of the wheel" is a relation and a
drawer can only place nouns at edges; it left a London bar empty because the
crowd was named once for nine panels; and "Static shot;" -- a video
instruction -- reached a still prompt and put a Bunsen flame on a cravat stud.

So the prompt gains a GEOMETRY block (every relation restated as which frame
edge at what apparent size, plus the 180-degree line), a flat WARDROBE block,
a per-panel BACKGROUND LIFE clause, a start panel that names what is still at
rest and an END panel written as a complete picture -- and it loses every
negation, because a negated noun is still that noun in the prompt
(`studio/affirm.py`).
"""
from studio import episode_seq_board as sq
from studio.affirm import negations
from studio.episode_spec import Setup

PHYSICAL = {
    "john_watson": ("A man in his late twenties, as thin as a lath, as brown as a nut, dark hair swept "
                    "back, a thin waxed moustache, wearing a fawn tweed overcoat and a white cravat "
                    "pinned with a stud; a brown bowler hat, on his head outdoors and in his left hand "
                    "indoors; no gloves; a bare sunburnt right hand on the silver ball knob of a black "
                    "walking stick."),
    "stamford": ("A stout young man in his mid-twenties, round clean-shaven face, dark hair parted at "
                 "the side, small bright eyes, wearing a black frock coat over a grey waistcoat, white "
                 "shirt and dark cravat; a black bowler hat outdoors, in his hand indoors."),
}

STREET = Setup(
    described="A wet cobbled street off Piccadilly, 1881, under a grey afternoon sky.",
    cast=["john_watson", "stamford"], landmark="the stone arch", outdoors=True, props=["cab"],
    route="from the Criterion kerb along the wet street to the hospital gateway",
    geometry=("ONE pair of tall spoked wheels, one wheel on each side of the body, their axle passing "
              "UNDER THE MIDDLE of the passenger box; the bay horse stands in the shafts two "
              "horse-lengths clear of the wheel, level with the top of frame. The cab travels from the "
              "LEFT edge of frame toward the RIGHT edge, horse leading, so the horse is nearer the "
              "RIGHT edge and the driver nearer the LEFT edge in every panel."),
    crowd="four pedestrians under umbrellas on the far pavement and a boy with a broom at the crossing")

BAR = Setup(described="The Criterion Bar, Piccadilly, 1881, early evening.", cast=["john_watson"],
            landmark="the great gilt-framed mirror", crowd="eight or nine men in top hats two deep at the counter")


def seg(shot, sub=0, size="medium", path=0.2, **kw):
    base = {"shot": shot, "sub": sub, "size": size, "path": path, "faces": [], "motion": "Static shot; he walks on",
            "frame": "Two men on the wet cobbles.", "camera": "", "at_rest": "", "end_frame": "", "changed": "",
            "crowd": ""}
    return base | kw


def sheet(segs=None, setup=STREET, physical=None):
    segs = segs if segs is not None else [seg(0), seg(1, size="insert", path=None)]
    return sq.prompt(segs, setup, physical if physical is not None else PHYSICAL,
                     previous=False, first=True, geography=[1])


class TestTheShape:
    def test_the_prompt_is_labelled_blocks_in_the_spec_order(self):
        """One 5 kB paragraph became short labelled blocks, scene to constraints:
        both OpenAI guides say so for a complex request (research 2026-09-11)."""
        text = sheet()
        heads = [line for line in text.splitlines() if line and line == line.upper() and not line.startswith("Panel")]
        assert heads == ["SHEET", "DIFFERENT PICTURES", "ORDER", "REFERENCES", "LOCATION", "GEOMETRY",
                         "WARDROBE", "BACKGROUND LIFE", "PANELS", "STYLE", "CONSTRAINTS"]
        assert "\n\n" in text

    def test_every_sentence_of_a_sheet_prompt_says_what_is(self):
        """Owner 2026-09-11: no negation reaches the drawer either.  A negated noun
        is still that noun -- "no signage" drew CRISTERION on a board."""
        assert negations(sheet()) == []
        assert negations(sheet([seg(0), sq.end_panel(seg(0), 1)])) == []

    def test_the_sheet_states_the_different_picture_law_before_the_panels(self):
        text = sheet()
        assert sq.DIFFERENT in text
        assert text.index(sq.DIFFERENT) < text.index("PANELS")


class TestGeometry:
    def test_the_geometry_block_carries_the_setup_s_own_chain_of_parts(self):
        assert "UNDER THE MIDDLE of the passenger box" in sheet()

    def test_the_geometry_block_fixes_the_180_degree_line_as_two_frame_edges(self):
        """Q03_0 was a lateral pass and Q03_1 receded down the street: a 90 degree
        mismatch, because nothing said which side of the street the camera stands on."""
        text = sq.geometry_block(STREET)
        assert "keeps to ONE side of the line" in text and "stays on that side for every panel" in text
        assert "LEFT edge" in text and "RIGHT edge" in text  # the setup's own edges, panel by panel
        assert negations(text) == []

    def test_a_setup_with_no_route_states_no_camera_line(self):
        assert "keeps to ONE side of the line" not in sq.geometry_block(BAR)


class TestWardrobe:
    def test_the_hat_rule_is_flat_and_positive_for_this_sheet(self):
        """The rule was a conditional ("on his head outdoors and in his left hand
        indoors") and the drawer half-obeyed it: Q08_0E kept the bowler on although
        its own text said the hat had come off."""
        assert "brown bowler hat is on his head in every panel" in sq.wardrobe_block(STREET, PHYSICAL)
        indoors = sq.wardrobe_block(BAR, PHYSICAL)
        assert "brown bowler hat is in his hand in every panel" in indoors
        assert "outdoors" not in indoors and "indoors" not in indoors

    def test_the_glove_rule_is_stated_as_bare_skin(self):
        assert "bare skin" in sq.wardrobe_block(STREET, PHYSICAL)

    def test_the_steady_half_of_a_description_drops_the_conditional_clauses(self):
        steady = sq.steady(PHYSICAL["john_watson"])
        assert "as thin as a lath" in steady and "fawn tweed overcoat" in steady
        assert negations(steady) == [] and "indoors" not in steady

    def test_a_character_who_owns_no_hat_is_stated_bareheaded(self):
        """`steady()` drops "bareheaded indoors" with the other conditionals, so the
        flat fact has to be restated here or the drawer is told nothing about his head."""
        line = sq.hat_line("Sherlock Holmes", "A lean man, bareheaded indoors, in a velvet jacket.", False)
        assert line.strip() == "Sherlock Holmes is bareheaded in every panel of this sheet."
        assert negations(line) == []

    def test_the_hat_of_a_description_is_the_headgear_phrase(self):
        assert sq.hat_of(PHYSICAL["stamford"]) == "a black bowler hat"
        assert sq.hat_of("A bareheaded man in a velvet jacket.") == ""


class TestBackgroundLife:
    def test_a_public_panel_names_its_own_crowd_with_a_count_and_an_activity(self):
        """A location-level crowd sentence does not survive nine panels: the bar's
        own text says "drinkers two deep" and two panels drew an empty bar."""
        text = sheet([seg(0)], setup=BAR)
        assert "Behind them, eight or nine men in top hats two deep at the counter, out of focus." in text

    def test_an_insert_carries_no_crowd_clause(self):
        text = sq.panels_block([seg(0, size="insert", path=None)], [], BAR)
        assert "Behind them" not in text

    def test_a_panel_s_own_crowd_beats_the_setup_s(self):
        text = sq.panels_block([seg(0, crowd="a barman drawing a cork")], [], BAR)
        assert "Behind them, a barman drawing a cork, out of focus." in text


class TestThePanels:
    def test_a_start_panel_names_the_size_the_camera_and_what_is_still_at_rest(self):
        """"The instant before: <verb phrase>" was drawn as the finished action:
        Q02_0 came back with the glass already raised."""
        text = sq.panels_block([seg(0, size="medium_close", camera="at the crowded near end of the counter",
                                    at_rest="Stamford's glass stands on the mahogany, his hand beside it.")],
                               [], BAR)
        assert text.startswith("Panel 1 - MEDIUM CLOSE-UP, camera at the crowded near end of the counter.")
        assert "In frame: Two men on the wet cobbles." in text
        assert "the instant BEFORE the action: Stamford's glass stands on the mahogany" in text

    def test_no_panel_text_carries_a_camera_move(self):
        """"Static shot;" is an instruction to MiniMax, and it reached the drawer."""
        text = sheet([seg(0, motion="Static shot; the glass goes up"), seg(1, motion="Tracking beside him; he walks")])
        assert "Static" not in text and "Tracking" not in text

    def test_an_end_panel_leads_with_where_the_change_arrived(self):
        """The prompt used to say "same" EIGHT times and carry a six-noun
        "Unchanged since panel J" list against one change stated LAST, while every
        start panel on the same sheet said "same" zero times.  Sameness is now
        SHOWN by the inherited inventory, not asserted; the words go on the one
        thing that moved and where it moved to.
        See tests/test_an_end_panel_inherits_a_picture.py."""
        start = seg(2, size="medium", end_frame="Stamford's glass is at his lips and his eyes are on Watson.",
                    changed="one glass has travelled to his mouth")
        text = sq.panels_block([start, sq.end_panel(start, 1)], [], BAR)
        assert "Panel 2 - PANEL 1 ONE ACTION LATER" in text
        assert "one glass has travelled to his mouth" in text
        assert "In frame: Stamford's glass is at his lips" in text
        assert text.index("travelled to his mouth") < text.index("In frame: Stamford")
        assert "Unchanged since panel 1:" not in text
        assert "identical" not in text and "Static" not in text

    def test_an_end_panel_without_a_written_picture_inherits_the_start_panels_nouns(self):
        """The plan still carries no `end` pictures, and until it does the END
        panel CARRIES the start panel's own nouns rather than pointing at them.
        It used to say "the same place, the same camera and the same light as
        panel N, drawn afresh with <verb>" -- a delta with no base, whose only
        base was the panel six inches away on the same canvas."""
        text = sq.panels_block([seg(3), sq.end_panel(seg(3), 1)], [], BAR)
        assert "PANEL 1 ONE ACTION LATER" in text
        assert "the same place, the same camera" not in text
        assert "Two men on the wet cobbles" in text
        assert negations(text) == []

    def test_the_size_ladder_fires_only_on_a_route_panel(self):
        """'the gilt mirror behind them' is not the far landmark: the ladder used to
        fire on the substring 'behind' anywhere in a panel's text."""
        close = seg(2, size="close", path=None, frame="Close on Stamford, the gilt mirror behind them.")
        assert "height of" not in sq.panels_block([close], [], BAR)
        walk = seg(3, size="medium", path=0.3, frame="Over Watson's shoulder, the door far off.")
        assert "The stone arch is the height of a finger." in sq.panels_block([walk], [1], STREET)


class TestReferences:
    def test_every_attached_image_is_named_by_index_and_role(self):
        text = sq.references_block(STREET, PHYSICAL)
        assert text.startswith("Image 1 is the empty location")
        assert "Image 2 is the cab: this exact vehicle" in text
        assert "Image 3 is John Watson:" in text and "Image 4 is Stamford:" in text

    def test_a_setup_with_no_prop_plate_names_the_cast_straight_after_the_location(self):
        assert "Image 2 is John Watson:" in sq.references_block(BAR, PHYSICAL)


class TestTheRetry:
    def test_the_strict_retry_names_the_panels_that_came_back_the_same(self):
        """The retry used to be one of two fixed strings: it told the drawer that
        some panel was a copy and never which one."""
        text = sq.strict_prefix([("Q02_0", "Q02_0E")], [], BAR)
        assert "panels Q02_0 and Q02_0E" in text and "Draw Q02_0E afresh" in text
        assert negations(text) == []

    def test_the_strict_retry_restates_the_one_walk_when_the_ladder_went_backwards(self):
        text = sq.strict_prefix([], [2], STREET)
        assert "The stone arch is larger in every route panel" in text
        assert negations(text) == []

    def test_a_sheet_that_passed_needs_no_prefix(self):
        assert sq.strict_prefix([], [], BAR) == ""


def test_one_panel_can_be_redrawn_alone_with_the_sheet_s_own_laws():
    """A single bad cell costs $0.08 to redraw alone against $0.20 for its whole
    sheet, and redrawing the sheet throws away the panels that came back right
    (owner 2026-09-11, S14.1: "legs are small, proportions are off")."""
    panel = seg(14, 1, camera="two paces in front at knee height, a normal lens", at_rest="the hand lies slack")
    text = sq.single(panel, STREET, PHYSICAL)
    assert "one single vertical 9:16 photograph" in text and "grid" not in text
    assert "GEOMETRY" in text and "WARDROBE" in text and "LOCATION" in text
    assert "Panel 1" not in text and "panel 2" not in text  # one picture, so no panel numbering
    assert "two paces in front at knee height" in text and "the hand lies slack" in text
