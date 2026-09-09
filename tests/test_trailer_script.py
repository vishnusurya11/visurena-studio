"""The trailer's own screenplay: the spine everything downstream is built on.

Written before a note of music or a frame of picture exists.  A film trailer
house cannot write one -- "you wouldn't want to write a script calling for
scenes and settings that aren't in the negative" (Fred Greene, entertainment
copywriter, UCLA TFT) -- because their picture is searched for in footage that
already exists.  Ours is rendered to order, which is the one case where the
picture column can be authored: the same reason game trailers and commercials
are scripted in advance and theatrical trailers are not.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from studio import trailer_script as script
from studio.trailer_script import ScriptBeat, TrailerScript
from studio.trailer_edit import MAX_SHOT


def beat(index: int, movement: str, seconds: float, **kw) -> ScriptBeat:
    fields = {"see": "Holmes at the window, back to us", "hear": "one low string",
              "why": "the world before anything happens", "function": "escalation"}
    fields.update(kw)
    return ScriptBeat(id=f"B{index:02d}", movement=movement, seconds=seconds, **fields)


def a_script(**kw) -> TrailerScript:
    """25/45/30 of 60 s, in beats no longer than the editor may hold one."""
    beats = ([beat(i, "M1", 3.0, function="question") for i in range(5)]
             + [beat(10 + i, "M2", 3.0) for i in range(9)]
             + [beat(30 + i, "M3", 3.0) for i in range(4)]
             + [beat(40, "M3", 3.0, function="title", card="A STUDY IN SCARLET", see=None)]
             + [beat(41, "M3", 3.0, function="button", card="EPISODE 1 OUT NOW", see=None)])
    fields = {"title": "A Study in Scarlet", "runtime": 60.0, "beats": beats}
    fields.update(kw)
    return TrailerScript(**fields)


class TestTheSpine:
    def test_a_script_is_the_beats_and_what_each_one_is_for(self):
        found = a_script()
        assert found.seconds == pytest.approx(60.0, abs=0.5)
        assert [b.id for b in found.beats][:2] == ["B00", "B01"]
        assert found.beats[0].why and found.beats[0].see

    def test_a_page_is_a_sixty_second_page(self):
        """The owner's format, 2026-09-07: 60 s, +-10.  Not the 106 s run 19
        shipped and not the 130-148 s of theatrical practice -- this is a
        social trailer whose job is to make someone watch the episode, and the
        YouTube Shorts feed plays only the first 60 s of any upload."""
        assert script.RUNTIME == 60.0 and script.RUNTIME_SLACK == 10.0
        long = ([beat(i, "M1", 2.125, function="question") for i in range(10)]
                + [beat(20 + i, "M2", 2.125) for i in range(18)]
                + [beat(40 + i, "M3", 2.125) for i in range(10)]
                + [beat(60, "M3", 2.125, function="title", card="TITLE", see=None),
                   beat(61, "M3", 2.125, function="button", card="EPISODE 1", see=None)])
        with pytest.raises(ValidationError, match="60"):
            TrailerScript(title="T", runtime=85.0, beats=long)

    def test_a_page_carries_the_frame_it_is_composed_for(self):
        """9:16 by default -- the feed the audience is in.  A square sits
        letterboxed there, and full-frame 9:16 measured +91% against it."""
        assert a_script().aspect == "9:16"
        assert a_script(aspect="1:1").aspect == "1:1"

    def test_the_last_beat_hands_the_viewer_somewhere_to_go(self):
        """The named fatal flaw of book trailers is ending on a cover with no
        next action.  Every analogue -- podcast, channel trailer, anime PV --
        ends on an explicit one."""
        assert a_script().beats[-1].card == "EPISODE 1 OUT NOW"
        with pytest.raises(ValidationError, match="next action"):
            a_script(beats=a_script().beats[:-1] + [beat(41, "M3", 3.0, function="button")])

    def test_the_movements_are_spent_in_SECONDS_not_in_shot_counts(self):
        """MEASURED, run 19: the quota was enforced on COUNTS -- one section of
        six went to M1 -- and M1 got 0.7 s of a 106 s trailer, 1% against its
        25% share.  A trailer with no first act cannot be rescued by music."""
        found = a_script()
        assert found.movement_seconds() == pytest.approx({"M1": 15.0, "M2": 27.0, "M3": 18.0},
                                                         abs=0.6)
        assert found.movement_shares()["M1"] == pytest.approx(0.25, abs=0.02)

    def test_a_movement_starved_of_seconds_is_refused(self):
        """The exact shape of run 19, as a contract violation."""
        beats = [beat(0, "M1", 0.7, function="question")]
        beats += [beat(10 + i, "M2", 4.0) for i in range(7)]
        beats += [beat(30 + i, "M3", 4.0) for i in range(7)]
        beats += [beat(41, "M3", 2.5, function="title", card="TITLE", see=None),
                  beat(42, "M3", 0.8, function="button", card="EPISODE 1", see=None)]
        with pytest.raises(ValidationError, match="M1"):
            TrailerScript(title="T", runtime=60.0, beats=beats)

    def test_no_act_may_hold_a_shot_longer_than_the_editor_would(self):
        """REVERSED from an earlier draft.  Theatrical craft allows an
        atmospheric opening to hold one shot 6-10 s (BEAT, arXiv 2605.27067).
        Social does not: ~70% of short-form sessions end before 20% of the
        video, and multi-scene cuts measured +38% conversion, 5+ scenes +171%.
        The first frame is the hook, not a slow build."""
        assert script.hold_ceiling("M1") == script.hold_ceiling("M3") == MAX_SHOT
        with pytest.raises(ValidationError, match="may hold"):
            ScriptBeat(id="B00", movement="M1", function="question", seconds=7.0,
                       see="an empty gaslit street", why="the world before anything")

    def test_a_card_may_hold_longer_than_a_shot(self):
        """The title card is the one held frame the cut is built around."""
        held = a_script().beats[-1].model_copy(update={"seconds": 6.5})
        assert held.holds and held.seconds > MAX_SHOT

    def test_every_beat_shows_something_or_says_something(self):
        with pytest.raises(ValidationError, match="see"):
            beat(0, "M1", 3.0, see=None)


class TestWhatItPromises:
    def test_the_script_says_how_many_times_the_trailer_speaks(self):
        kept = a_script().beats
        spoken = kept[3].model_copy(update={"line": "Rache, revenge.",
                                            "speaker": "sherlock_holmes"})
        found = a_script(beats=kept[:3] + [spoken] + kept[4:])
        assert found.spoken() == ["Rache, revenge."]
        assert found.speech_seconds() == pytest.approx(3.0)

    def test_a_page_that_talks_the_whole_way_through_is_refused(self):
        """MEASURED on the first two Scarlet drafts: 72% then 68% of the runtime
        carried a line, against the 41-45% real trailers run.  Asking for less
        in the brief did not work twice, so the page is REFUSED and re-asked --
        the model's own retry ladder then fixes it.  A trailer that never stops
        talking is a radio play with pictures."""
        talky = [b.model_copy(update={"line": "Rache, revenge.",
                                      "speaker": "sherlock_holmes"})
                 if b.function != "title" and not b.card else b
                 for b in a_script().beats]
        with pytest.raises(ValidationError, match="speaks for"):
            a_script(beats=talky)

    def test_a_spoken_beat_names_who_speaks(self):
        with pytest.raises(ValidationError, match="speaker"):
            beat(0, "M1", 3.0, line="Rache, revenge.")

    def test_the_title_card_is_in_the_last_movement_and_there_is_one(self):
        with pytest.raises(ValidationError, match="title"):
            TrailerScript(title="T", runtime=12.0,
                          beats=[beat(0, "M1", 3.0, function="question"),
                                 beat(1, "M2", 2.7), beat(2, "M2", 2.7),
                                 beat(3, "M3", 3.6)])


class TestTheMusicOwnsTheClock:
    def test_the_page_owns_proportions_and_the_cue_owns_seconds(self):
        """Two independent practitioner accounts name the AUDIO BED as the
        structure -- "it all starts with the audio bed... we end up filling in
        picture last" (Doug Brandt) -- and the fine cut's music "may or may not
        adhere to the timing of your rough cut" (Derek Lieu).  So the written
        seconds are a TARGET: when the cue comes back 92.4 s instead of 100,
        every beat is rescaled and the act shares survive untouched."""
        found = a_script()
        retimed = found.retimed(55.4)
        assert retimed.seconds == pytest.approx(55.4, abs=0.2)
        assert retimed.movement_shares() == pytest.approx(found.movement_shares(), abs=0.01)
        assert [b.id for b in retimed.beats] == [b.id for b in found.beats]

    def test_a_beat_knows_where_it_falls_in_the_runtime(self):
        """Position is what the structure literature can actually check -- and
        what our own QC could not see when act one came out 0.7 s long."""
        found = a_script()
        assert found.at(found.beats[0]) == pytest.approx(0.0)
        assert found.share_at(found.beats[5]) == pytest.approx(0.25, abs=0.02)

    def test_retiming_past_what_an_act_may_hold_is_refused(self):
        """A cue so long that its beats outrun their act's ceiling is a cue the
        cut cannot honour: the contract says so rather than shipping held
        frames.  The opening has the most give, so the last act fails first."""
        with pytest.raises(ValidationError, match="may hold"):
            a_script().retimed(82.0)


class TestReading:
    def test_it_renders_as_a_page_a_person_can_read_and_argue_with(self):
        page = script.render(a_script())
        assert "A STUDY IN SCARLET" in page and "ACT I" in page
        assert "B00" in page and "0:00" in page
        assert "25%" in page or "24%" in page
