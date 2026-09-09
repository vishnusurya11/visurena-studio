"""The music asked FROM the page, not the page read out of the music."""
from __future__ import annotations

import pytest

from studio import script_cue
from studio.trailer_script import ScriptBeat, TrailerScript


def a_page(**kw) -> TrailerScript:
    beats = ([ScriptBeat(id=f"B{i:02d}", movement="M1", function="question", seconds=3.0,
                         see="blood on plaster", hear="a pocket watch, alone. no music yet",
                         why="the crime") for i in range(5)]
             + [ScriptBeat(id=f"B{10 + i:02d}", movement="M2", function="escalation",
                           seconds=3.0, see="fog", hear="the pulse enters under it",
                           why="the hunt") for i in range(9)]
             + [ScriptBeat(id=f"B{30 + i:02d}", movement="M3", function="escalation",
                           seconds=3.0, see="the arrest", hear="strings surge",
                           why="the answer") for i in range(4)]
             + [ScriptBeat(id="B40", movement="M3", function="title", seconds=3.0,
                           card="A STUDY IN SCARLET", hear="the biggest hit, then silence",
                           why="the logo"),
                ScriptBeat(id="B41", movement="M3", function="button", seconds=3.0,
                           card="EPISODE 1 OUT NOW", hear="one heartbeat",
                           why="the next action")])
    fields = {"title": "A Study in Scarlet", "runtime": 60.0, "beats": beats,
              "genre": "detective mystery"}
    fields.update(kw)
    return TrailerScript(**fields)


class TestTheAsk:
    def test_the_cue_is_asked_long_enough_to_cover_the_page(self):
        """The cue may run past the picture and be cut; it may never come up
        short of it."""
        page = a_page()
        ask = script_cue.ask_for(page)
        assert ask.seconds >= page.seconds

    def test_the_bar_is_close_to_the_page_s_own_beat_length(self):
        """A written beat should land near a bar line, not across one -- the
        cut has to fall where the music does."""
        page = a_page()
        ask = script_cue.ask_for(page)
        mean = page.seconds / len(page.beats)
        assert abs(ask.bar - mean) < mean          # within one beat length
        assert 60 <= ask.bpm <= 160

    def test_the_title_hit_is_asked_where_the_page_puts_the_title(self):
        page = a_page()
        ask = script_cue.ask_for(page)
        title = next(b for b in page.beats if b.function == "title")
        assert ask.title_bar == int(page.at(title) / ask.bar)
        assert any(e.kind == "title_hit" and e.bar == ask.title_bar for e in ask.events)


class TestReadingThePage:
    def test_a_beat_that_says_the_music_stops_asks_for_a_hole(self):
        """The page writes for a player: "everything stops", "drops out",
        "silence".  Those are the arc's holes and stops."""
        quiet = ScriptBeat(id="B00", movement="M1", function="escalation", seconds=3.0,
                           see="RACHE", hear="everything stops. one hit, then silence",
                           why="the turn")
        assert script_cue.event_kind(quiet) == "hole"

    def test_a_turn_that_stops_is_a_full_stop_not_a_hole(self):
        turn = ScriptBeat(id="B00", movement="M2", function="turn", seconds=3.0,
                          see="the pills", hear="the score falls away to nothing",
                          why="the turn")
        assert script_cue.event_kind(turn) == "stop"

    def test_a_beat_that_names_an_impact_asks_for_a_hit(self):
        beat = ScriptBeat(id="B00", movement="M3", function="escalation", seconds=2.0,
                          see="the handcuffs", hear="the biggest impact of the piece",
                          why="the arrest")
        assert script_cue.event_kind(beat) == "hit"

    def test_a_beat_that_says_nothing_about_sound_asks_for_nothing(self):
        beat = ScriptBeat(id="B00", movement="M2", function="escalation", seconds=3.0,
                          see="fog", why="the pursuit")
        assert script_cue.event_kind(beat) is None

    def test_two_landmarks_in_one_bar_are_one_moment(self):
        """A listener hears one event per bar; asking for two is asking for
        neither."""
        page = a_page()
        ask = script_cue.ask_for(page)
        bars = [e.bar for e in ask.events]
        assert len(bars) == len(set(bars))


class TestTheBrief:
    def test_the_brief_carries_the_page_s_own_sound_direction(self):
        """This is the text a trailer house sends when it commissions a cue:
        what the music is doing in each part, plus the outline."""
        text = script_cue.brief(a_page())
        assert "a pocket watch, alone" in text and "the biggest hit, then silence" in text
        assert "three acts" in text and "BPM" in text

    def test_the_windows_are_where_the_trailer_speaks(self):
        """Not for ducking -- for STOPPING.  Run 19 ducked a bed under four
        lines and the owner still heard no dialogue."""
        page = a_page()
        spoken = page.beats[2].model_copy(update={"line": "Rache, revenge.",
                                                  "speaker": "sherlock_holmes"})
        page = a_page(beats=page.beats[:2] + [spoken] + page.beats[3:])
        assert script_cue.spoken_windows(page) == [(6.0, 9.0)]
