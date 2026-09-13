"""Two pictures per character: an identity BUST and a wardrobe CARD per state.

Pure string building.  Nothing here draws, uploads or prices an image.
"""
import pytest

from studio import cast_refs, trailer_refs as tr
from studio.affirm import negations

ROW = {"ref_id": "char-john_watson", "entity_id": "john_watson", "kind": "character",
       "name": "Dr. John Watson",
       "physical": "A man in his late twenties, as thin as a lath.",
       "wardrobe": {"outdoor": "wears the brown bowler hat squarely on his head",
                    "indoor": "is bare-headed and carries the brown bowler by the brim "
                              "in his left hand, down at his side"},
       "sheet": {"same": "the same thin waxed moustache",
                 "head": "His dark hair is swept back and his skin is sunburnt the colour "
                         "of a nut, darker than his white collar.",
                 "garments": "He wears a fawn brown herringbone tweed overcoat open over a "
                             "matching tweed waistcoat with a gold watch chain across it.",
                 "hands": "Both his hands are bare skin to the wrist and the coat cuff ends "
                          "above a bare wrist.",
                 "props": "His right hand closes round the polished silver ball knob of a "
                          "black walking stick, the knob at the height of his hip."}}


class TestTheIdentityBust:
    def test_the_bust_is_bare_headed_and_shows_the_whole_hairline(self):
        said = tr.bust_prompt("His dark hair is swept back.")
        assert "bare-headed" in said and "hairline" in said
        assert "His dark hair is swept back." in said

    def test_the_bust_states_the_backdrop_as_the_only_thing_behind_him(self):
        said = tr.bust_prompt("")
        assert "runs off all four edges" in said
        assert "The frame holds this one man alone." in said

    def test_the_bust_edits_a_reference_and_says_which_man_it_is(self):
        said = tr.bust_prompt("", same="the same thin waxed moustache")
        assert said.startswith("The same man as in the reference image")
        assert "the same thin waxed moustache" in said

    def test_every_sentence_the_sheet_sends_names_something_present(self):
        assert negations(tr.bust_prompt("His dark hair is swept back.")) == []


class TestTheWardrobeCard:
    def test_the_card_is_three_quarter_length_with_both_hands_inside_the_frame(self):
        said = tr.card_prompt("He wears a fawn overcoat.", hands="Both his hands are bare.")
        assert "three-quarter-length" in said and "head to mid-thigh" in said
        assert "both arms and both hands entirely inside the frame" in said
        assert "Both his hands are bare." in said

    def test_everything_the_contract_names_is_held_facing_the_camera(self):
        said = tr.card_prompt("He wears a coat.", props="His right hand holds a silver knob.")
        assert "His right hand holds a silver knob." in said
        assert "turned toward the camera" in said

    def test_the_card_shares_the_busts_backdrop_light_and_stock(self):
        card, bust = tr.card_prompt("He wears a coat."), tr.bust_prompt("")
        for tail in (tr.PLAIN_STUDIO, tr.NEUTRAL, tr.FILM):
            assert tail in card and tail in bust

    def test_every_sentence_the_card_sends_names_something_present(self):
        assert negations(tr.card_prompt("He wears a coat.", hands="Bare hands.",
                                        props="A silver knob.")) == []


class TestTheFrameBlockTheTrailerStillUses:
    def test_character_prompt_keeps_its_signature_and_frames_a_bare_head(self):
        said = tr.character_prompt("A lean man.", "Muted London grey.")
        assert said.startswith("A lean man.") and "bare-headed" in said
        assert tr.STYLE in said

    def test_a_caller_may_hand_it_another_frame_block(self):
        said = tr.character_prompt("A lean man.", "Grey.", frame="Wide.")
        assert "Wide." in said and "bare-headed" not in said

    def test_the_frame_block_stays_affirmative(self):
        assert negations(tr.character_prompt("A lean man.", tr.palette_for("detective"))) == []


class TestTheEightPrompts:
    def test_one_bust_plus_one_card_per_declared_state(self):
        made = cast_refs.sheet_prompts(ROW)
        assert sorted(made) == ["char-john_watson", "char-john_watson_indoor",
                                "char-john_watson_outdoor"]

    def test_the_bust_carries_the_head_text_and_no_hat(self):
        made = cast_refs.sheet_prompts(ROW)["char-john_watson"]
        assert "sunburnt the colour of a nut" in made
        assert "bowler" not in made

    def test_each_card_carries_its_own_state_and_the_invariant_wardrobe(self):
        made = cast_refs.sheet_prompts(ROW)
        assert "He wears the brown bowler hat squarely on his head." in made["char-john_watson_outdoor"]
        assert "He is bare-headed and carries the brown bowler" in made["char-john_watson_indoor"]
        for state in ("indoor", "outdoor"):
            assert "herringbone tweed overcoat" in made[f"char-john_watson_{state}"]
            assert "silver ball knob" in made[f"char-john_watson_{state}"]

    def test_a_state_the_character_is_never_in_gets_no_card(self):
        indoor_only = dict(ROW, wardrobe={"indoor": "is bare-headed"})
        assert sorted(cast_refs.sheet_prompts(indoor_only)) == \
               ["char-john_watson", "char-john_watson_indoor"]

    def test_no_prompt_asks_for_an_absence(self):
        for name, said in cast_refs.sheet_prompts(ROW).items():
            assert negations(said) == [], name


class TestTheCardsCostWhatTheLedgerSays:
    def test_a_portrait_card_is_priced_and_matches_the_take_canvas_ratio(self):
        from studio import image_spend as spend
        assert spend.estimate_usd("gpt-image-2.5-sunburst", cast_refs.SIZE, "high") == 0.08
        assert cast_refs.SIZE == "1024x1536"

    def test_the_whole_cast_set_is_eight_pictures(self):
        rows = [dict(ROW, ref_id="char-a", entity_id="a"),
                dict(ROW, ref_id="char-b", entity_id="b"),
                dict(ROW, ref_id="char-c", entity_id="c",
                     wardrobe={"indoor": "is bare-headed"})]
        assert sum(len(cast_refs.sheet_prompts(row)) for row in rows) == 8
