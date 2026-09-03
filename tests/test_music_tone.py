"""The music must be asked for the book it is scoring.

The caption was one 109-word paragraph, byte-identical for every book except
for a pasted VISUAL palette -- a list of colour words, in the slot a music
palette belonged.  Genre, period, instrumentation and emotional arc were never
inputs, so Scarlet and Jekyll were the same prompt picked by the same scalar.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio.music_tone import (EXECUTABLE_TAGS, Tone, caption, lyrics_plan,
                               load_tone, sections_for)

SCARLET = Tone(
    genre="Victorian Chamber Noir / Procedural Mystery Score",
    bpm=84, key="G", scale="minor",
    lead_instrument="solo violin, played in the drawing-room manner",
    percussion="no drum kit and no taiko at any point; the pulse is a walking "
               "bass and a pocket watch",
    sonics="mid-forward and close, small dry room, rosin and bow noise audible",
    progression="It begins as a cold intellectual exercise. Through the middle "
                "it hardens into pursuit. At two-thirds the ground changes and "
                "the piece opens into dry sunlit emptiness.",
    imagery="a gaslit London room at three in the morning, a magnifying glass "
            "over blood on plaster, then an alkali plain at noon",
    instruments="cello and double bass as a walking pizzicato pulse; a prepared "
                "piano; a lone open-fifth fiddle drone",
)


class TestSections:
    def test_every_tag_is_one_the_model_executes(self):
        """[Build], [Final Build] and [Hit] are not in the model's vocabulary.
        It falls back to guessing from position, which is why nine sections
        delivered 78.5s, 101.75s, 114.0s and 139.75s."""
        for tag, _ in sections_for(9):
            assert tag in EXECUTABLE_TAGS, tag

    def test_the_count_asked_for_is_the_count_returned(self):
        assert len(sections_for(9)) == 9
        assert len(sections_for(6)) == 6

    def test_it_opens_quiet_and_ends_on_a_decay(self):
        tags = [tag for tag, _ in sections_for(9)]
        assert tags[0] == "Intro" and tags[-1] == "Outro"


class TestCaption:
    def test_it_reaches_the_length_the_model_needs(self):
        """Below 200 words the model is documented to under-use the caption;
        the shipped one was 109."""
        shipped = load_tone(Path("library/20260822113400_a-study-in-scarlet"))
        assert 250 <= len(caption(shipped).split()) <= 500

    def test_it_carries_the_three_headings(self):
        text = caption(SCARLET)
        for heading in ("Global Metadata", "Vocal Details", "Arrangement"):
            assert heading in text

    def test_the_lead_instrument_the_book_names_is_asked_for(self):
        assert "solo violin" in caption(SCARLET)

    def test_it_routes_on_genre_not_on_mood_adjectives(self):
        """'cinematic', 'dark', 'epic' are modifiers, not genre families."""
        opening = caption(SCARLET).split("Global Emotional")[0]
        assert "Victorian Chamber Noir" in opening

    def test_vocals_are_excluded_by_silence_not_by_negation(self):
        """Negation reliably produces humming."""
        assert "no vocals" not in caption(SCARLET).lower()

    def test_two_books_do_not_get_the_same_caption(self):
        gothic = Tone(genre="Victorian Gothic Horror Score", bpm=68, key="E",
                      scale="minor", lead_instrument="upright piano, detuned",
                      percussion="there are no drums; the pulse is footfalls, "
                                 "a cane, glass and an axe against a door",
                      sonics="close, airless, narrowing to near mono",
                      progression="One theme played twice and degrading.",
                      imagery="a locked cabinet door, a bare Soho street",
                      instruments="bowed double bass; a viola a quarter tone flat")
        assert caption(SCARLET) != caption(gothic)
        assert "taiko" not in caption(gothic)


class TestLyricsPlan:
    def test_the_content_fills_the_intended_length(self):
        """Fill is ~2.4 syllables per intended second; the old plan was 0.35x,
        so the model finished the sheet early and noodled."""
        plan = lyrics_plan(sections_for(9), intended_seconds=100.0)
        syllables = sum(len(w) // 3 + 1 for w in plan.split())
        assert syllables >= 0.8 * 2.4 * 100.0


class TestLoadTone:
    def test_a_book_with_no_tone_file_says_so(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_tone(tmp_path)

    def test_the_shipped_books_each_have_one(self):
        for book in ("20260822113400_a-study-in-scarlet",
                     "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"):
            tone = load_tone(Path("library") / book)
            assert tone.genre and tone.lead_instrument


class TestCueStaleness:
    """A cue rendered from a different caption is not this book's cue.

    `build_music` skipped any seed whose .flac already existed, so rewriting
    the caption and re-running would have kept every file made by the old one
    and reported success -- the same defect as the clip cache keyed on beat id.
    """

    def test_the_same_caption_gives_the_same_stamp(self):
        from studio.music_tone import caption_stamp
        assert caption_stamp(caption(SCARLET)) == caption_stamp(caption(SCARLET))

    def test_a_rewritten_caption_gives_a_different_stamp(self):
        from studio.music_tone import caption_stamp
        other = Tone(**{**SCARLET.__dict__, "lead_instrument": "a cor anglais"})
        assert caption_stamp(caption(SCARLET)) != caption_stamp(caption(other))

    def test_a_cue_with_no_stamp_is_not_current(self, tmp_path):
        from studio.music_tone import cue_is_current
        assert not cue_is_current(tmp_path / "cue-1.flac", "abc")

    def test_a_cue_whose_stamp_matches_is_current(self, tmp_path):
        from studio.music_tone import cue_is_current, stamp_cue
        cue = tmp_path / "cue-1.flac"
        cue.write_bytes(b"x")
        stamp_cue(cue, "abc")
        assert cue_is_current(cue, "abc")
        assert not cue_is_current(cue, "def")
