"""The ask is a bar-indexed event list; the caption reads it aloud; verify reads it back.

Every fixture here is synthesised from the ask itself (`synth_from_ask`), so
the verifier is proved on audio whose landmarks are known to the sample, and
the cut map handed to `verify` is built from `beatmap`'s own primitives in the
dict shape `studio/music_events.py` will produce.  Nothing renders, nothing is
spent.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

from studio import cue_ask as ca
from studio.affirm import negations
from studio.beatmap import RATE, envelope_of, onsets, stopdowns, structural_impacts
from studio.cue_plan import EVENT_ORDER, CueAsk
from studio.music_tone import CAPTION_WORDS, Tone, load_tone
from synth_ask import synth_from_ask

BARS = 32


def tone_of(genre: str = "Period orchestral chamber score", mood=("curious", "relentless", "grieving"),
            bpm: int = 100, time_signature: str = "4/4") -> Tone:
    """A Tone in the Scarlet shape, every field affirmative, built inline."""
    return Tone(
        genre=genre, tonal_centre="G", mode="aeolian", mood=mood, bpm=bpm,
        time_signature=time_signature,
        tempo_plan="the pulse moves in quarter notes and doubles to eighths at the first rise",
        chord_plan="one centre throughout, the verse sinking a step at a time in minor",
        pulse_carriers=("a ticking pocket watch", "pizzicato cello and double bass in eighths",
                        "a field snare on two and four"),
        signature_sound="a detuned upright piano playing the four-note figure",
        lead_instrument="a solo violin in the drawing-room manner, close-miked",
        supporting_instruments="string quartet and foot-pumped harmonium, a cimbalom",
        register_arc="violin and horns above, piano bass octaves below",
        dynamics_arc="A cold intellectual exercise that hardens into a pursuit, then grief.",
        mix_space="close in one small dry room with a short tail",
        era_reference="one ribbon microphone a hand's width away",
        imagery="a gaslit London room at three in the morning",
        hit="one low bare open fifth struck in unison by horns, bass drum and piano")


def cut_map_of(samples: np.ndarray, ask: CueAsk) -> dict:
    """The cut map `music_events` will write, built here from beatmap primitives."""
    times, db = envelope_of(samples)
    grid = onsets(times, db)
    beat = ask.bar / ca.beats_per_bar_of(ask)
    events = [{"t": t, "rank": 3, "kind": "hit"} for t in structural_impacts(times, db, count=6)]
    events += [{"t": t, "rank": 3, "kind": "dropout"} for t in stopdowns(times, db)]
    for bar in range(1, ask.bars):
        start = bar * ask.bar
        now = ca.pulse_present(grid, start, start + ask.bar, beat)
        before = ca.pulse_present(grid, start - ask.bar, start, beat)
        if now and not before:
            events.append({"t": start, "rank": 2, "kind": "entry"})
    return {"events": sorted(events, key=lambda e: e["t"]), "spans": []}


@pytest.fixture(scope="module")
def ask() -> CueAsk:
    return ca.ask_for(tone_of(), BARS)


@pytest.fixture(scope="module")
def synth(ask) -> np.ndarray:
    return synth_from_ask(ask, RATE)


class TestRegister:
    def test_a_thriller_gets_the_thriller_register_and_a_romance_gets_late_pulse(self):
        thriller = ca.form_for(tone_of(genre="Thriller score for a small string ensemble"))
        romance = ca.form_for(tone_of(genre="Romance for harp and strings", time_signature="3/4"))
        assert thriller.name == "procedural"
        assert romance.name == "romance"
        assert romance.pulse_entry > thriller.pulse_entry

    def test_nine_registers_each_open_pulse_free_and_end_on_a_stop(self):
        assert len(ca.REGISTERS) == 9
        for register in ca.REGISTERS.values():
            assert register.intro_bars >= 1 and register.pulse_entry == register.intro_bars / 32
            assert register.ending.endswith("stop") and register.tail_seconds > 0

    def test_an_unnamed_genre_gets_the_documented_default(self):
        assert ca.form_for(tone_of()).name == ca.DEFAULT_REGISTER == "detective"
        assert ca.form_for(tone_of(mood=("comic", "brisk", "warm"))).name == "comedy"


class TestAsk:
    def test_the_ask_lands_its_events_on_the_registers_bars(self, ask):
        register = ca.form_for(tone_of())
        by_kind = {}
        for e in ask.events:
            by_kind.setdefault(e.kind, []).append(e.bar)
        assert by_kind["pulse_in"] == [round(register.pulse_entry * BARS)]
        assert by_kind["hole"] == [round(f * BARS) for f in register.holes]
        assert by_kind["stop"] == [ask.title_bar - register.silence_bars]
        assert by_kind["title_hit"] == [ask.title_bar]
        assert ask.title_bar == BARS - max(2, int(np.ceil(register.tail_seconds / ask.bar)))

    def test_the_bar_is_read_from_the_tempo_and_the_time_signature(self):
        assert ca.ask_for(tone_of(bpm=120), BARS).bar == pytest.approx(2.0)
        waltz = ca.ask_for(tone_of(genre="Romance", bpm=120, time_signature="3/4"), BARS)
        assert waltz.bar == pytest.approx(1.5)

    def test_events_arrive_in_bar_order_and_the_contract_defaults_are_untouched(self, ask):
        bars = [e.bar for e in ask.events]
        assert bars == sorted(bars) and bars[-1] == ask.title_bar
        base = CueAsk.for_bars(BARS, bar=ask.bar, bpm=ask.bpm)
        assert [e.kind for e in base.events] == list(EVENT_ORDER) + ["title_hit"]

    def test_too_few_bars_for_the_registers_tail_is_refused(self):
        with pytest.raises(ValueError, match="bars"):
            ca.ask_for(tone_of(genre="Elegy", bpm=200), 8)


class TestCaption:
    def test_the_caption_names_every_section_in_order(self, ask):
        text = ca.caption_from(ask, tone_of())
        at = [text.index(f"{tag}:") for tag in ca.FORM_TAGS]
        assert at == sorted(at)
        assert all(len(re.findall(rf"(?<![\w-]){tag}:", text)) == 1 for tag in ca.FORM_TAGS)

    def test_the_caption_is_affirmative_only(self, ask):
        text = ca.caption_from(ask, tone_of())
        assert negations(text) == []
        for constant in ca.MODEL_TEXT:
            for value in (constant.values() if isinstance(constant, dict) else constant):
                assert negations(value) == [], value

    def test_the_caption_stays_inside_the_word_budget(self, ask):
        """Both the inline tone and the shipped Scarlet tone, the wordiest one authored."""
        for tone in (tone_of(), load_tone(Path("library/20260822113400_a-study-in-scarlet"))):
            words = len(ca.caption_from(ask, tone).split())
            assert CAPTION_WORDS[0] <= words <= CAPTION_WORDS[1], words

    def test_the_verse_speaks_the_pulse_through_its_entry_and_the_intro_holds_it_still(self, ask):
        text = ca.form_text(ask, tone_of())
        verse = text[text.index("Verse:"):text.index("Pre-Chorus:")]
        assert ca.EVENT_TEXT["pulse_in"].split("{")[0] in verse
        assert ca.PULSE_TEXT[True] not in verse
        assert ca.PULSE_TEXT[True] in text[text.index("Chorus:"):]

    def test_the_caption_ends_on_the_hit(self, ask):
        tone = tone_of()
        assert ca.caption_from(ask, tone).rstrip(". ").endswith(tone.hit)

    def test_the_textures_ask_for_a_whisper_and_for_maximum_intensity(self, ask):
        """The arc is an EDIT: it sorts the render's phrases by measured
        level, so what the caption must deliver is MATERIAL at both extremes.
        "At speaking level" asked for the middle and the renders were flat
        (see `test_music_tone`); the epic caption's "huge and loud" and
        "maximum intensity" came back 13-18 dB apart."""
        text = ca.form_text(ask, tone_of())
        verse = text[text.index("Verse:"):text.index("Pre-Chorus:")]
        chorus = text[text.index("Chorus:"):text.index("Bridge:")]
        post = text[text.index("Post-Chorus:"):text.index("Outro:")]
        assert "whisper" in verse and "quiet" in verse
        assert "enormous impact" in chorus and "huge and loud" in chorus
        assert "maximum intensity" in post and "loudest" in post

    def test_the_caption_carries_every_asked_event_once(self, ask):
        text = ca.form_text(ask, tone_of())
        assert text.count(ca.EVENT_TEXT["hole"].split("{")[0]) == 1
        assert ca.COUNT_WORDS[len([e for e in ask.events if e.kind == "hole"])] in text
        assert ca.EVENT_TEXT["stop"] in text and ca.EVENT_TEXT["hit"] in text


class TestMeasure:
    def test_section_level_is_the_window_median_against_the_cue_median(self):
        times = np.arange(0, 10, 0.05)
        db = np.where(times < 5, -30.0, -20.0)
        assert ca.section_level(times, db, 0.0, 5.0) == pytest.approx(-5.0)
        assert ca.section_level(times, db, 5.0, 10.0) == pytest.approx(5.0)

    def test_pulse_is_present_when_most_beats_carry_an_onset(self):
        assert ca.pulse_present([0.0, 0.5, 1.0, 1.5], 0.0, 2.0, 0.5)
        assert not ca.pulse_present([0.0], 0.0, 2.0, 0.5)
        assert not ca.pulse_present([], 0.0, 2.0, 0.5)

    def test_onset_density_is_onsets_per_bar(self):
        assert ca.onset_density([0.1, 0.5, 1.2, 3.9, 5.0], 0.0, 4.0, 2.0) == pytest.approx(2.0)

    def test_ending_kind_tells_a_stop_from_a_fade_from_a_run_on(self):
        t = np.arange(0, 6 * RATE) / RATE
        tone = 0.3 * np.sin(2 * np.pi * 220 * t)
        stop = tone * (t < 3.0)
        fade = tone * np.clip((6.0 - t) / 3.0, 0.0, 1.0)
        assert ca.ending_kind(*envelope_of(stop), 3.0) == "stop"
        assert ca.ending_kind(*envelope_of(fade), 3.0) == "fade"
        assert ca.ending_kind(*envelope_of(tone), 3.0) == "run_on"


class TestVerify:
    def test_verify_fills_measured_from_the_synth(self, ask, synth):
        found = ca.verify(ask, cut_map_of(synth, ask), None)
        missing = [e.kind for e in found.events if e.measured is None]
        assert missing == [], missing
        for e in found.events:
            assert abs(e.measured - e.bar * ask.bar) <= ca.SECTION_TOL * ask.bar

    def test_an_event_a_bar_late_still_matches_and_two_bars_late_does_not(self, ask):
        title = ask.title_bar * ask.bar
        late = {"events": [{"t": title + 0.99 * ask.bar, "rank": 3, "kind": "hit"}], "spans": []}
        later = {"events": [{"t": title + 2.0 * ask.bar, "rank": 3, "kind": "hit"}], "spans": []}
        assert ca.verify(ask, late, None).events[-1].measured == pytest.approx(title + 0.99 * ask.bar)
        assert ca.verify(ask, later, None).events[-1].measured is None

    def test_measured_downbeats_say_where_a_bar_is(self, ask):
        class Grid:
            downbeats = [i * ask.bar * 1.02 for i in range(ask.bars)]
        title = ask.title_bar * ask.bar * 1.02
        cut_map = {"events": [{"t": title, "rank": 3, "kind": "hit"}], "spans": []}
        assert ca.verify(ask, cut_map, Grid()).events[-1].measured == pytest.approx(title)

    def test_an_event_matches_only_its_own_kinds(self, ask):
        stop = next(e.bar for e in ask.events if e.kind == "stop") * ask.bar
        wrong = {"events": [{"t": stop, "rank": 3, "kind": "hit"}], "spans": []}
        assert next(e for e in ca.verify(ask, wrong, None).events if e.kind == "stop").measured is None


class TestScore:
    def test_plan_score_weights_the_stop_and_the_title(self, ask):
        kinds = [e.kind for e in ask.events]
        landed = lambda missing: ca.plan_score(ask.model_copy(update={"events": [
            e.model_copy(update={"measured": None if e.kind == missing else e.bar * ask.bar})
            for e in ask.events]}))
        weight = len(kinds) + 2
        assert landed(None) == 1.0
        assert landed("title_hit") == pytest.approx((weight - 2) / weight)
        assert landed("stop") == pytest.approx((weight - 2) / weight)
        assert landed("hit") == pytest.approx((weight - 1) / weight)
        assert landed("hit") > landed("stop")

    def test_the_verdict_is_the_floor_applied(self):
        assert ca.verdict(1.0) and ca.verdict(ca.VERDICT_FLOOR)
        assert not ca.verdict(ca.VERDICT_FLOOR - 0.01)


class TestSynth:
    def test_the_synth_has_a_hole_where_the_ask_says(self, ask, synth):
        times, db = envelope_of(synth)
        for hole in (e for e in ask.events if e.kind == "hole"):
            start = hole.bar * ask.bar
            assert ca.section_level(times, db, start + 0.1, start + ca.HOLE_BARS * ask.bar - 0.1) < -40
            assert ca.section_level(times, db, start - ask.bar, start - 0.1) > -20

    def test_the_synth_steps_up_at_each_section_and_is_pulse_free_before_the_entry(self, ask, synth):
        times, db = envelope_of(synth)
        grid = onsets(times, db)
        beat = ask.bar / ca.beats_per_bar_of(ask)
        levels = [ca.section_level(times, db, s.bar * ask.bar + 0.1, (s.bar + 2) * ask.bar)
                  for s in ask.sections]
        assert levels == sorted(levels) and levels[-1] - levels[0] >= 12
        pulse_in = next(e.bar for e in ask.events if e.kind == "pulse_in") * ask.bar
        assert not ca.pulse_present(grid, 0.0, pulse_in, beat)
        assert ca.pulse_present(grid, pulse_in, pulse_in + 2 * ask.bar, beat)

    def test_the_synth_stops_dead_and_hits_once_at_the_title(self, ask, synth):
        times, db = envelope_of(synth)
        stop = next(e.bar for e in ask.events if e.kind == "stop") * ask.bar
        assert ca.ending_kind(times, db, stop) == "stop"
        hits = [t for t in structural_impacts(times, db, count=2) if t > stop]
        assert len(hits) == 1 and abs(hits[0] - ask.title_bar * ask.bar) < 0.1
        assert len(synth) == int(ask.seconds * RATE)
