"""The music must be asked for the book it is scoring, in a form a trailer has.

Two measured findings drive this file.

1.  THE MODEL SINGS THE LYRICS FIELD.  Three delivered cues were separated
    with demucs and transcribed with whisper: every one has a vocal stem 3-4 LU
    ABOVE the rest of the mix, and the words are the studio's own stage
    directions -- "the lead states its figure plainly and alone, unhurried, no
    accompaniment".  The "bland lyrics" the owner heard were the arrangement
    notes being sung.  So the sheet carries tags and sung words only, and the
    section prose moves into the caption's Arrangement timeline.
2.  A SONG IS A PLATEAU; A TRAILER CUE IS A STAIRCASE.  The shipped cue reached
    -15 LUFS at 8 s and held it to 97 s, peaked at 52%, and ended in a fade.
    The caption now asks for three waves, a hole before every step, and a stop
    before the title hit.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from studio.affirm import negations
from studio.music_tone import (CAPTION_CHARS, CAPTION_WORDS, EXECUTABLE_TAGS,
                               HOSTED_CHARS, LYRICS_MODES, SHEET_TAGS, Tone,
                               caption, caption_stamp, load_tone, lyrics_plan)

SCARLET_DIR = Path("library/20260822113400_a-study-in-scarlet")


def scarlet() -> Tone:
    return load_tone(SCARLET_DIR)


class TestTone:
    def test_the_shipped_tone_loads(self):
        tone = scarlet()
        assert tone.tonal_centre == "G" and tone.mode == "aeolian"
        assert tone.lyrics_mode == "instrumental"

    def test_key_and_scale_are_derived_from_the_centre_and_the_mode(self):
        """`Basic Attributes: key is G, and scale is minor` is the grammar the
        vendor's own caption-rewriter emits, so it stays -- but one centre and
        one mode are what the composer decides, and the pair is read off it."""
        tone = scarlet()
        assert tone.key == "G" and tone.scale == "minor"
        assert replace(tone, mode="mixolydian").scale == "major"

    def test_a_negation_in_any_field_is_refused(self):
        """"no drum kit and no taiko at any point" asks for a drum kit and a
        taiko: the tokens are in the prompt either way."""
        with pytest.raises(ValueError, match="mix_space"):
            replace(scarlet(), mix_space="close and dry, no reverb tail")

    def test_a_negation_inside_a_tuple_field_is_refused(self):
        with pytest.raises(ValueError, match="pulse_carriers"):
            replace(scarlet(), pulse_carriers=("a pocket watch", "never a snare"))

    def test_the_mode_must_be_one_the_table_names(self):
        with pytest.raises(ValueError, match="mode"):
            replace(scarlet(), mode="sad")

    def test_a_refrain_is_required_exactly_when_one_is_sung(self):
        with pytest.raises(ValueError, match="refrain"):
            replace(scarlet(), lyrics_mode="refrain", refrain=None)
        with pytest.raises(ValueError, match="refrain"):
            replace(scarlet(), lyrics_mode="instrumental", refrain="a line")
        assert replace(scarlet(), lyrics_mode="refrain",
                       refrain="Follow the scarlet thread").refrain

    def test_the_pulse_needs_a_carrier_the_model_can_play_in_time(self):
        """A pocket watch alone gave neither the model nor the tracker a metre
        to hold: 84 asked, 89-189 delivered over eight seeds.  At least one
        carrier must be an instrument with a strong rhythmic prior."""
        with pytest.raises(ValueError, match="pulse_carriers"):
            replace(scarlet(), pulse_carriers=("a knuckle on wood", "a struck wine glass"))

    def test_a_v1_tone_file_says_what_it_is_missing(self, tmp_path):
        (tmp_path / "trailer/music").mkdir(parents=True)
        (tmp_path / "trailer/music/tone.json").write_text(
            json.dumps({"genre": "g", "bpm": 84, "key": "G", "scale": "minor"}),
            encoding="utf-8")
        with pytest.raises(ValueError, match="tonal_centre"):
            load_tone(tmp_path)

    def test_a_book_with_no_tone_file_says_so(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_tone(tmp_path)


class TestCaption:
    def test_the_lead_instrument_is_named_in_the_first_sentence(self):
        """The vendor's own instrumental examples all do this, and the caption
        library the rewriter routes to has no instrumental entries at all --
        so the lead has to be stated where the model reads the genre."""
        first = caption(scarlet()).split("### Global Metadata\n")[1].split(". ")[0]
        assert "solo violin" in first

    def test_it_says_the_piece_is_instrumental(self):
        assert "instrumental" in caption(scarlet()).lower()

    def test_the_tempo_is_asked_for_once_and_qualitatively(self):
        """MEASURED: one caption asking `bpm is 84` three times delivered
        89-189 across eight seeds.  Repetition is more tokens, not more
        control, and the vendor's skill asks for a range unless an exact
        number is justified."""
        text = caption(scarlet())
        assert "around 100 BPM" in text
        assert text.count("BPM") == 1

    def test_the_key_is_asked_for_once(self):
        assert caption(scarlet()).count("key is") == 1

    def test_it_carries_the_three_headings(self):
        for heading in ("Global Metadata", "Vocal Details", "Arrangement"):
            assert heading in caption(scarlet())

    def test_the_arrangement_names_the_sections_in_sheet_order(self):
        """`clean_caption` strips the `### `, so the timeline is plain prose --
        it lines up with the sheet only because it names the same tags in the
        same order."""
        timeline = caption(scarlet()).split("Structure: ")[1]
        found = [part.split(":")[0] for part in timeline.split(". ")
                 if part.split(":")[0] in EXECUTABLE_TAGS]
        assert found == list(SHEET_TAGS)

    def test_it_asks_for_every_excitement_mechanic(self):
        """The shipped cue followed exactly one of the twelve (rising
        register).  Nothing in the old caption asked for anything propulsive:
        it asked for a chamber piece to get louder."""
        text = caption(scarlet())
        for asked in ("repeating", "every four bars", "sixteenth", "higher",
                      "rising sweep", "half-time", "answering", "densest",
                      "two full bars of total silence", "loudest",
                      "decaying alone", "hard stop"):
            assert asked in text, asked

    def test_it_asks_the_tempo_to_hold_while_the_subdivision_doubles(self):
        """Three of five Scarlet seeds read 175-201 BPM against 84 asked when
        the caption said "the pulse doubles".  Density may double; the beat the
        tracker counts holds."""
        text = caption(scarlet())
        assert "held from the first bar to the last" in text
        assert "over the same beat" in text

    def test_the_percussion_is_a_closed_roster_read_off_the_carriers(self):
        """A closed list occupies the slot a drum kit would fill, and reading
        it off `pulse_carriers` keeps the roster and the pulse one fact."""
        tone = scarlet()
        assert "the complete percussion section is" in caption(tone)
        for carrier in tone.pulse_carriers:
            assert carrier in caption(tone)

    def test_the_caption_size_is_recorded_and_capped(self):
        """The number itself is the point of this test.

        MEASURED on 2026-09-05: 3199 characters, 539 words.  The hosted API
        caps a prompt at 2000 characters and does not apply here; the local
        node caps caption plus lyrics at 5000 TOKENS
        (`comfy_extras/nodes_minimax_music.py`), roughly 20 000 characters;
        the vendor's caption skill defaults to 250-450 words for a SONG
        caption.  This one also carries the nine-section trailer form.
        """
        text = caption(scarlet())
        assert (len(text), len(text.split())) == (3199, 539), (len(text), len(text.split()))
        assert CAPTION_WORDS[0] <= len(text.split()) <= CAPTION_WORDS[1]
        assert len(text) <= CAPTION_CHARS
        assert HOSTED_CHARS == 2000

    def test_it_is_affirmative_throughout(self):
        assert negations(caption(scarlet())) == []

    def test_two_books_do_not_get_the_same_caption(self):
        other = replace(scarlet(), genre="Victorian gothic horror score",
                        tonal_centre="E", mode="phrygian")
        assert caption(scarlet()) != caption(other)


class TestLyricsPlan:
    def test_an_instrumental_sheet_is_tags_and_the_documented_marker(self):
        """The vendor's own reference instrumental render is exactly this:
        `[Intro]\\n(instrumental)\\n[Outro]\\n(instrumental)`."""
        sheet = lyrics_plan(scarlet())
        assert sheet.count("(instrumental)") == len(SHEET_TAGS)
        assert sheet.startswith("[Intro]\n(instrumental)")

    def test_the_sheet_uses_the_nine_documented_tags_only(self):
        for block in lyrics_plan(scarlet()).split("\n\n"):
            assert block.split("]")[0].lstrip("[") in EXECUTABLE_TAGS

    def test_the_chorus_appears_twice_so_the_second_can_be_the_drop(self):
        """The model was trained on songs: one `[Chorus]` at 44% became the
        peak and `[Post-Chorus]` at 78% an afterthought (MEASURED: loudest
        tenth 40-50%, 60-80% six dB down).  A-B-A-B-A, each bigger."""
        assert SHEET_TAGS.count("Chorus") == 2 and SHEET_TAGS.count("Pre-Chorus") == 2

    def test_the_sections_that_thin_the_texture_are_left_out(self):
        """`[Solo]` and `[Instrumental]` mean thin and moderate to this model,
        and act three must be neither: the shipped cue's HF/mid ratio dipped
        19 dB in the `[Solo]` tenth, exactly where the cut wants density."""
        assert "Solo" not in SHEET_TAGS and "Instrumental" not in SHEET_TAGS

    @pytest.mark.parametrize("mode", LYRICS_MODES)
    def test_no_stage_direction_survives_in_any_mode(self, mode):
        """This is the whole finding: a parenthetical is a SUNG backing line in
        the training corpus, and the only documented exception is the single
        word `(instrumental)`."""
        tone = replace(scarlet(), lyrics_mode=mode,
                       refrain="Follow the scarlet thread" if mode == "refrain" else None,
                       vocalise=("Ra-che", "vindicta"))
        found = [part.split(")")[0] for part in lyrics_plan(tone).split("(")[1:]]
        assert set(found) <= {"instrumental"}, found

    def test_a_refrain_is_sung_in_both_choruses_and_the_final_wave(self):
        tone = replace(scarlet(), lyrics_mode="refrain",
                       refrain="Follow the scarlet thread")
        assert lyrics_plan(tone).count("Follow the scarlet thread") >= 3

    def test_a_vocalise_sings_the_book_s_own_words(self):
        tone = replace(scarlet(), lyrics_mode="vocalise",
                       vocalise=("Ra-che", "vindicta"))
        sheet = lyrics_plan(tone)
        assert "Ra-che" in sheet and "vindicta" in sheet
        assert sheet.split("\n\n")[0] == "[Intro]\n(instrumental)"

    def test_the_sheet_is_affirmative(self):
        assert negations(lyrics_plan(scarlet())) == []


class TestCueStaleness:
    """A cue rendered from a different recipe is not this book's cue.

    The stamp covers the LYRICS as well as the caption now: the two are one
    CFG block in the node (`build_prompt` puts both between `<|im_start|>` and
    `<|audio_start|>`, and the unconditioned branch replaces the lot), so two
    renders with the same caption and different sheets are different recipes.
    """

    def test_the_same_recipe_gives_the_same_stamp(self):
        tone = scarlet()
        assert caption_stamp(caption(tone), lyrics_plan(tone)) == \
            caption_stamp(caption(tone), lyrics_plan(tone))

    def test_a_rewritten_caption_gives_a_different_stamp(self):
        tone = scarlet()
        other = replace(tone, lead_instrument="a cor anglais, close-miked")
        assert caption_stamp(caption(tone)) != caption_stamp(caption(other))

    def test_a_rewritten_sheet_gives_a_different_stamp(self):
        tone = scarlet()
        vocal = replace(tone, lyrics_mode="refrain", refrain="Follow the scarlet thread")
        assert caption_stamp(caption(tone), lyrics_plan(tone)) != \
            caption_stamp(caption(tone), lyrics_plan(vocal))

    def test_a_cue_with_no_stamp_is_not_current(self, tmp_path):
        from studio.music_tone import cue_is_current
        assert not cue_is_current(tmp_path / "cue-1.flac", "abc")

    def test_a_cue_whose_stamp_matches_is_current(self, tmp_path):
        from studio.music_tone import cue_is_current, stamp_cue
        cue = tmp_path / "cue-1.flac"
        cue.write_bytes(b"x")
        stamp_cue(cue, "abc", "a caption", "[Intro]\n(instrumental)")
        assert cue_is_current(cue, "abc")
        assert not cue_is_current(cue, "def")

    def test_the_recipe_that_was_sent_is_written_beside_the_cue(self, tmp_path):
        """cue-3002's stamp matches no committed caption times any committed
        tone.json, so the text that produced the shipped cue is unrecoverable
        from git.  What was sent is now recorded where the audio is."""
        from studio.music_tone import stamp_cue
        cue = tmp_path / "cue-3002.flac"
        cue.write_bytes(b"x")
        stamp_cue(cue, "abc", "a caption", "[Intro]\n(instrumental)")
        recorded = json.loads((tmp_path / "cue-3002.caption.json").read_text(encoding="utf-8"))
        assert recorded["caption"] == "a caption"
        assert recorded["lyrics"] == "[Intro]\n(instrumental)"
        assert recorded["stamp"] == "abc"
