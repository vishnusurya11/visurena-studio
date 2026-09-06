"""Step 03 of the trailer stage: seeds are MEASURED and ranked, never trusted.

Eight seeds of one caption ranged 0.31-0.97 bars-in-mode, so the step renders
a batch, measures every seed's metre, and gates on the best: fitness above the
floor, a metric grid, and at least one slot.  Every fake here is the seam the
contract names: `build_music.run` (ComfyUI), `llm.structured`, and the beat
tracker -- no test renders, calls a model, or loads Beat This.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pytest

from scripts.trailer import build_music
from scripts.trailer import step_03_music as step
from studio import beatmap, cue_arc, db, llm
from studio.beatmap import RATE, track_autocorrelation
from studio import cue_ask, frame_budget
from studio.cue_plan import MIN_FORM_BARS, CuePlan
from studio import cue_conform, cue_settle, frame_budget
from studio.cue_settle import Settled
from studio.cue_spans import ShorterCue
from studio.learnings import load
from studio.affirm import negations
from studio.music_tone import Tone, caption, lyrics_plan, recipe_path, stamp_cue
from studio.trailer_run import RunContext
from studio.trailer_stage_spec import Metre
from test_metre import click_track, write_wav

TONE = Tone(
    genre="Period chamber score", tonal_centre="G", mode="aeolian",
    mood=("curious", "relentless", "grieving"), bpm=120, time_signature="4/4",
    tempo_plan="quarter notes, then eighths, then sixteenths over the same beat",
    chord_plan="one centre throughout, brightening to the fourth degree at the pursuit",
    pulse_carriers=("a ticking pocket watch", "pizzicato cello and double bass"),
    signature_sound="a detuned upright piano playing the figure",
    lead_instrument="a solo violin, close-miked",
    supporting_instruments="cello and double bass",
    register_arc="violin above, piano bass octaves below",
    dynamics_arc="curious, then a pursuit", mix_space="dry and close",
    era_reference="one ribbon microphone, an 1890s parlour session",
    imagery="a gaslit room", hit="one low bare open fifth in unison")


def cue(troughs=((20.0, 24.0),), stop=(49.0, 51.5), seconds=60.0, seed=0) -> np.ndarray:
    """A 120 BPM click over a bed: troughs are slots, the stop and burst are the title."""
    rng = np.random.default_rng(seed)
    samples, _, _ = click_track(120, seconds, seed=seed)
    t = np.arange(len(samples)) / RATE
    samples = samples + 0.1 * np.sin(2 * np.pi * 110 * t).astype(np.float32)
    for a, b in troughs:
        samples[int(a * RATE):int(b * RATE)] *= 0.2
    if stop:
        samples[int(stop[0] * RATE):int(stop[1] * RATE)] = 0
        n, s = int(0.3 * RATE), int(stop[1] * RATE)
        burst = 0.6 * rng.standard_normal(n) * np.exp(-np.arange(n) / (0.1 * RATE))
        samples[s:s + n] += burst.astype(np.float32)
    return samples


KINDS = {"two": dict(troughs=((20.0, 24.0), (34.0, 38.0))), "one": dict(),
         "flat": dict(troughs=(), stop=None)}


@pytest.fixture()
def ctx(tmp_path, monkeypatch):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex_id = db.insert_codex(conn, "Scarlet", codex_id="20260901000003")
    book = tmp_path / "book"
    (book / "trailer/music").mkdir(parents=True)
    (book / "trailer/music/tone.json").write_text(json.dumps(TONE.__dict__), encoding="utf-8")
    context = RunContext(conn, codex_id, book, logs_root=tmp_path / "logs")
    context.open_step("03")
    monkeypatch.setattr(beatmap, "track_beats", track_autocorrelation)
    return context


def fake_comfy(tmp_path, kinds: dict[int, str], calls: list[dict]):
    """`build_music.run` without ComfyUI: one wav per seed, shaped by `kinds`."""
    def run(name, values, timeout=0):
        calls.append(values)
        seed = values["seed"]
        return [write_wav(tmp_path / f"render-{seed}.wav", cue(**KINDS[kinds.get(seed, "flat")]))]
    return run


def fake_llm(calls: list[str]):
    def structured(tier, prompt, schema, **kw):
        calls.append(prompt)
        return schema(pulse_carriers=["a ticking pocket watch", "a field snare on two and four"],
                      supporting_instruments="cello and a bass drum holding the grid")
    return structured


def refusing_llm(calls: list[str]):
    """A model that first answers with an absence, then names what plays."""
    def structured(tier, prompt, schema, **kw):
        calls.append(prompt)
        if len(calls) % 2:
            return schema(pulse_carriers=["a knuckle on wood", "no drum kit at any point"],
                          supporting_instruments="cello and a bass drum holding the grid")
        return schema(pulse_carriers=["a ticking pocket watch", "a field snare on two and four"],
                      supporting_instruments="cello and a bass drum holding the grid")
    return structured


def wobbly(samples, rate):
    """A tracker that hears a pulse but no bar: rubato on every seed."""
    beats = [0.5 + i * 0.5 + (0.12 if i % 3 else -0.1) for i in range(100)]
    return beats, [0.5, 2.6, 4.1, 6.9, 8.2, 10.9, 12.0, 15.1, 16.3, 19.2]


def chosen_of(ctx) -> Metre:
    return Metre.model_validate_json((ctx.out_dir / "music/metre.json").read_text(encoding="utf-8"))


class TestSeeds:
    def test_batches_never_repeat_a_seed(self):
        seeds = [s for b in range(4) for s in step.seeds_for(b)]
        assert len(seeds) == len(set(seeds)) == 4 * step.BATCH

    def test_render_cue_keeps_the_suffix_and_caches_on_the_caption(self, tmp_path, monkeypatch):
        calls: list[dict] = []
        monkeypatch.setattr(build_music, "run", fake_comfy(tmp_path, {}, calls))
        dest = tmp_path / "music"
        dest.mkdir()
        sheet = "[Intro]\n(instrumental)"
        first = build_music.render_cue(tmp_path, "caption A", 5, dest, sheet)
        again = build_music.render_cue(tmp_path, "caption A", 5, dest, sheet)
        moved = build_music.render_cue(tmp_path, "caption B", 5, dest, sheet)
        resung = build_music.render_cue(tmp_path, "caption B", 5, dest, "[Intro]\nAh...")
        assert first == again == moved == resung == dest / "cue-5.wav" and len(calls) == 3

    def test_render_cue_asks_for_the_seconds_the_frames_afford(self, tmp_path, monkeypatch):
        """The cue length is derived from the frame budget, never pinned: a
        different length is a different cue, so the stamp covers it too."""
        calls: list[dict] = []
        monkeypatch.setattr(build_music, "run", fake_comfy(tmp_path, {}, calls))
        dest = tmp_path / "music"
        dest.mkdir()
        build_music.render_cue(tmp_path, "caption A", 5, dest, "", duration=64)
        build_music.render_cue(tmp_path, "caption A", 5, dest, "", duration=64)
        build_music.render_cue(tmp_path, "caption A", 5, dest, "", duration=80)
        assert [c["duration"] for c in calls] == [64, 80]

    def test_render_cue_names_the_file_by_its_prefix(self, tmp_path, monkeypatch):
        """The raw render is `raw-<seed>`: the cue the pipeline grades and
        ships is the ARC cut from it, and that one is `cue-<seed>`."""
        monkeypatch.setattr(build_music, "run", fake_comfy(tmp_path, {}, []))
        dest = tmp_path / "music"
        dest.mkdir()
        raw = build_music.render_cue(tmp_path, "caption A", 5, dest, "", prefix="raw")
        assert raw == dest / "raw-5.wav" and build_music.render_cue(tmp_path, "caption A", 5, dest, "", prefix="raw") == raw

    def test_candidate_row_measures_the_rendered_file(self, tmp_path):
        row = build_music.candidate(write_wav(tmp_path / "cue-9.wav", cue(**KINDS["two"])), 9)
        assert row["seed"] == 9 and row["rel_path"] == "trailer/music/cue-9.wav"
        assert row["seconds"] == pytest.approx(60.0, abs=0.1) and row["title_impact"] == 51.5

    def test_a_seed_is_on_tone_within_a_tempo_mark_of_the_asked_bpm(self):
        """The tone asks a bpm for a reason: it is the register's pace, and
        the cut follows the MEASURED pulse at face value.  One tempo mark
        (andante 76-108 is +-17% about 92) is the band; Scarlet run 9's
        177.8 against 84 asked is seven bands out."""
        assert step.tempo_error(84.0, 84) == 0.0
        assert step.tempo_error(177.84, 84) == pytest.approx(1.117, abs=0.001)
        assert step.on_tone(96.0, 84) and step.on_tone(72.0, 84)
        assert not step.on_tone(100.9, 84) and not step.on_tone(177.84, 84)

    def test_verdict_needs_the_ask_delivered_on_a_metric_grid(self, tmp_path):
        """Fitness had a floor of 6.0 no real seed ever met, then the gate
        wanted the asked tempo; run 10 met both and the cut still landed 28%
        of its cuts on an event.  What the cut needs and no seed can fake:
        the events the ask pinned to bars, delivered, on a countable grid.
        Tempo is reported, never gated: the picture cuts to measured events."""
        two = beatmap.metre(write_wav(tmp_path / "a.wav", cue(**KINDS["two"])), seed=1,
                            rel_path="a.wav", track=track_autocorrelation)
        assert step.verdict(two, 120, {1: 0.9})[0]
        assert step.verdict(two.model_copy(update={"slots": [], "fitness": 0.5}), 120, {1: 0.9})[0]
        passed, measured, floor = step.verdict(two, 84, {1: 0.9})
        assert passed and "against 84 asked" in measured and floor == cue_ask.VERDICT_FLOOR
        assert not step.verdict(two, 120, {1: 0.5})[0] and "ask 0.50 delivered" in step.verdict(two, 120, {1: 0.5})[1]
        assert not step.verdict(two, 120)[0]
        assert not step.verdict(two.model_copy(update={"grid": "onsets"}), 120, {1: 0.9})[0]
        assert not step.verdict(None, 120)[0]

    def test_best_of_ranks_on_what_the_gate_grades_before_fitness(self, tmp_path):
        """Scarlet run 7: rubato seed 1002 scored 9.2 on dynamic range alone and
        shipped over nine metric seeds; the cut then landed 0% of cuts on a
        downbeat.  Run 9: seed 1003 at 177.8 BPM in three won on its four
        1.7 s troughs over 3004 at 100.9, and the trailer was 'random music,
        too loud, not the tone'.  A grid the cut can count first, then the
        nearest tempo band to the asked bpm, then fitness."""
        two = beatmap.metre(write_wav(tmp_path / "a.wav", cue(**KINDS["two"])), seed=1,
                            rel_path="a.wav", track=track_autocorrelation)
        rubato = two.model_copy(update={"seed": 2, "grid": "onsets", "fitness": 9.2})
        metric = two.model_copy(update={"seed": 4, "fitness": 2.4})
        better = two.model_copy(update={"seed": 5, "slots": [], "fitness": 3.0})
        fast = two.model_copy(update={"seed": 1003, "bpm": 177.84, "fitness": 4.4})
        near = two.model_copy(update={"seed": 3004, "bpm": 100.9, "slots": [], "fitness": 2.1})
        assert step.best_of([rubato, metric, better, fast], 120).seed == 5
        assert step.best_of([rubato, fast, near], 84).seed == 3004
        assert step.best_of([rubato, fast], 84).seed == 1003
        assert step.best_of([rubato], 120).seed == 2
        assert step.best_of([], 120) is None

    def test_form_outranks_a_steady_grid(self, tmp_path):
        """Run 10's chosen seed had the steadiest grid of its family and was a
        plateau from 8 s that ended in a fade.  A staircase on a wobblier grid
        is the better trailer: the cut can follow onsets, and it cannot invent
        a climax that is missing."""
        two = beatmap.metre(write_wav(tmp_path / "a.wav", cue(**KINDS["two"])), seed=1,
                            rel_path="a.wav", track=track_autocorrelation)
        plateau = two.model_copy(update={"seed": 7, "fitness": 9.0})
        staircase = two.model_copy(update={"seed": 8, "grid": "onsets", "fitness": 1.0})
        assert step.best_of([plateau, staircase], 120, {7: 0, 8: 2}).seed == 8
        assert step.best_of([plateau, staircase], 120).seed == 7

    def test_reauthor_keeps_the_register_and_the_tempo_and_swaps_the_pulse(self, monkeypatch):
        """The asked bpm is the tone's, not the reauthor's: a sheet that could
        choose 80-140 would move the goal the gate measures against."""
        calls: list[str] = []
        monkeypatch.setattr(llm, "structured", fake_llm(calls))
        tone = step.reauthor(TONE, None)
        assert tone.genre == TONE.genre and tone.lead_instrument == TONE.lead_instrument
        assert tone.bpm == TONE.bpm and tone.pulse_carriers != TONE.pulse_carriers
        assert "bars in mode" in calls[0] and "around 120 BPM" in calls[0]
        assert "bpm" not in step.CaptionSheet.model_fields

    def test_the_reauthor_brief_names_what_plays(self):
        """Run 10 asked for "instruments STRUCK on every beat ... not double
        it, not a triple subdivision".  A metronome satisfies every word of
        that sentence, and a click track is what came back."""
        assert negations(step.reauthor_prompt(TONE, None)) == []
        assert "STRUCK on every beat" not in step.reauthor_prompt(TONE, None)

    def test_a_rewrite_that_names_an_absence_is_refused_and_asked_again(self, monkeypatch):
        """The reauthor writes text that becomes conditioning, so its answer
        goes through the same gate the authored tone does."""
        calls: list[str] = []
        monkeypatch.setattr(llm, "structured", refusing_llm(calls))
        tone = step.reauthor(TONE, None)
        assert len(calls) == 2 and "refused" in calls[1]
        assert "a field snare on two and four" in tone.pulse_carriers


class TestForm:
    """The two terms that tell a trailer cue from a song at the same tempo.

    Both are read off the envelope the step already measures, so they cost
    nothing extra, and both are stated as synthetic arrays here because the
    shapes are the whole point: a staircase, and an ending that stops.
    """

    def envelope(self, tenths: list[float], seconds: float = 50.0):
        """(times, dB) whose ten tenths hold the levels given."""
        count = int(seconds / beatmap.WINDOW)
        db = np.concatenate([np.full(count // 10, level) for level in tenths])
        return np.arange(len(db)) * beatmap.WINDOW, db

    def test_a_plateau_is_not_a_staircase(self):
        """The shipped cue: tenths 8-9 sat 1.6 dB over tenths 2-3, and every
        other term in the fitness formula passed it."""
        times, db = self.envelope([-17.9, -19.2, -15.9, -15.4, -11.2,
                                   -14.4, -17.7, -17.0, -14.6, -23.4])
        assert not step.climbs(times, db)

    def test_three_waves_each_louder_than_the_last_is(self):
        times, db = self.envelope([-30, -22, -20, -18, -16, -14, -12, -10, -6, -12])
        assert step.climbs(times, db)

    def test_a_late_climb_whose_peak_comes_early_is_refused(self):
        """Loud early and loud late is two peaks, not a staircase; the cut
        wants its shortest shots where the loudest five seconds are."""
        times, db = self.envelope([-30, -22, -20, -4, -16, -14, -12, -10, -12, -14])
        assert not step.climbs(times, db)

    def test_the_loudest_five_seconds_are_located(self):
        times, db = self.envelope([-30, -22, -20, -18, -16, -14, -12, -10, -6, -12])
        assert 0.75 <= step.loudest_start(times, db) <= 0.92

    def test_every_tenth_is_measured(self):
        times, db = self.envelope([-30, -22, -20, -18, -16, -14, -12, -10, -6, -12])
        assert step.tenth_medians(db) == [-30, -22, -20, -18, -16, -14, -12, -10, -6, -12]

    def test_silence_after_the_title_hit_is_a_stop(self):
        times, db = self.envelope([-30, -20, -20, -20, -20, -20, -20, -20, -6, -40])
        assert step.stops_dead(times, db, title_hit=40.5, bar=2.4)

    def test_a_cue_that_keeps_going_after_the_hit_is_a_fade(self):
        """cue-3002 fell monotonically over five seconds from 97.1 s; a fade
        under the title card reads as a song ending."""
        times, db = self.envelope([-30, -20, -20, -20, -20, -20, -6, -30, -6, -30])
        assert not step.stops_dead(times, db, title_hit=30.0, bar=2.4)

    def test_a_cue_with_no_title_hit_has_nothing_to_stop_after(self):
        times, db = self.envelope([-20] * 10)
        assert not step.stops_dead(times, db, title_hit=None, bar=2.4)

    def test_form_of_scores_a_rendered_seed_out_of_two(self, tmp_path):
        rendered = write_wav(tmp_path / "a.wav", cue(**KINDS["two"]))
        found = beatmap.metre(rendered, seed=1, rel_path="a.wav",
                              track=track_autocorrelation)
        assert 0 <= step.form_of(rendered, found) <= 2


class TestAsk:
    """The cue is as long as the frames afford, never a pinned number."""

    def test_the_ask_is_sized_by_step_07s_share(self, ctx, monkeypatch):
        """210 min less one reader session, at the typed curve, at the corpus
        mix, is 76 s of picture: 38 bars of 2 s, plus the two the tail holds."""
        monkeypatch.setattr(ctx.budget, "allowance", lambda step: 210 * 60.0)
        assert step.bars_of(ctx, TONE) == 40
        assert step.ask_of(ctx, TONE).seconds == 80.0

    def test_a_budget_too_small_for_the_shortest_form_still_asks_for_it(self, ctx, monkeypatch):
        """A trailer without music is worse than one cut to a short cue: the
        shortest form is asked for and the fit rule trims the plan later."""
        monkeypatch.setattr(ctx.budget, "allowance", lambda step: 600.0)
        assert step.bars_of(ctx, TONE) == MIN_FORM_BARS + step.TAIL_BARS

    def test_the_render_is_asked_for_the_ask_plus_headroom(self, ctx, tmp_path, monkeypatch):
        comfy_calls: list[dict] = []
        monkeypatch.setattr(build_music, "run", fake_comfy(tmp_path, {}, comfy_calls))
        monkeypatch.setattr(ctx.budget, "allowance", lambda step: 210 * 60.0)
        step.run(ctx.codex_id, ctx)
        assert {c["duration"] for c in comfy_calls} == {80 + step.TAIL_HEADROOM}

    def test_best_of_prefers_the_seed_that_delivered_its_ask(self):
        a = Metre(seed=1, rel_path="m/a.wav", seconds=60.0, bpm=120.0, bar=2.0, beats_per_bar=4,
                  beats=[0.5], downbeats=[0.5], bars_in_mode=0.9, grid="metre", fitness=9.0)
        b = a.model_copy(update={"seed": 2, "fitness": 1.0})
        assert step.best_of([a, b], 120, {1: 2, 2: 2}, {1: 0.5, 2: 0.9}) is b
        assert step.best_of([a, b], 120, {1: 2, 2: 2}, {1: 0.9, 2: 0.9}) is a

    def test_arc_cue_cuts_the_ask_from_the_raw_render_and_reuses_it(self, ctx, monkeypatch):
        """The raw render's bars, quiet phrases first, the stop and the title
        hit where the ask puts them: a cue-<seed> beside raw-<seed>, its recipe
        carried over, arced once per (render, ask)."""
        from tests.test_cue_arc import SCRAMBLED, metre_of, planted, measured_bar_levels
        music = ctx.out_dir / "music"
        music.mkdir(parents=True, exist_ok=True)
        raw = write_wav(music / "raw-7.wav", planted(SCRAMBLED))
        stamp_cue(raw, "recipe-7", "caption A", "[Intro]")
        monkeypatch.setattr(beatmap, "metre", lambda path, seed, rel_path: metre_of(16))
        ask = cue_ask.CueAsk.for_bars(16, bar=2.0, bpm=120)
        out = step.arc_cue(ctx.book_dir, raw, ask, 7)
        assert out == music / "cue-7.wav" and recipe_path(out).exists()
        grid = json.loads(step.grid_path(out).read_text(encoding="utf-8"))
        assert len(grid["downbeats"]) == ask.bars and len(grid["beats"]) == 4 * ask.bars
        samples = beatmap.decode(out)
        assert abs(len(samples) / RATE - ask.seconds) < 2.0
        levels = measured_bar_levels(samples, ask.bars)
        assert levels[11] < levels[10] - 30 and levels[ask.title_bar] > levels[ask.title_bar - 1] + 20
        assert np.mean(levels[8:11]) > np.mean(levels[0:4]) + 6
        written = out.stat().st_mtime_ns
        assert step.arc_cue(ctx.book_dir, raw, ask, 7) == out and out.stat().st_mtime_ns == written
        longer = cue_ask.CueAsk.for_bars(20, bar=2.0, bpm=120)
        assert step.arc_cue(ctx.book_dir, raw, longer, 7) == out and out.stat().st_mtime_ns != written

    def test_arc_cue_cuts_on_the_measured_bar_when_the_render_came_back_slower(self, ctx, monkeypatch):
        """MEASURED: raw-1001 tracked at 2.69 s bars against 2.4 s asked; cut
        on the ask's bar the arc came out 101.8 s for a 91.2 s ask with beats
        laid 2.4 s apart on 2.69 s bars (bars_in_mode 0.81).  The bars are
        the render's; the ask's COUNT of bars is what is cut, on the length
        the render plays them at, and the grid says so."""
        from tests.test_cue_arc import SCRAMBLED, metre_of, planted
        music = ctx.out_dir / "music"
        music.mkdir(parents=True, exist_ok=True)
        raw = write_wav(music / "raw-8.wav", planted(SCRAMBLED))
        stamp_cue(raw, "recipe-8", "caption A", "[Intro]")
        measured = metre_of(16)                                   # 120 BPM: 2.0 s bars
        monkeypatch.setattr(beatmap, "metre", lambda path, seed, rel_path: measured)
        ask = cue_ask.CueAsk.for_bars(16, bar=1.5, bpm=160)      # asked faster than delivered
        out = step.arc_cue(ctx.book_dir, raw, ask, 8)
        assert abs(len(beatmap.decode(out)) / RATE - ask.bars * measured.bar) < 2.0
        grid = json.loads(step.grid_path(out).read_text(encoding="utf-8"))
        assert np.allclose(np.diff(grid["downbeats"]), measured.bar, atol=0.05)
        assert np.allclose(np.diff(grid["beats"]), measured.bar / 4, atol=0.05)

    def test_measure_reads_the_grid_the_arc_was_cut_on(self, ctx, monkeypatch):
        """An arced cue carries its bar lines beside it; the Metre is read on
        them, because a tracker loses the downbeats inside the asked holes."""
        from tests.test_cue_arc import SCRAMBLED, planted
        music = ctx.out_dir / "music"
        music.mkdir(parents=True, exist_ok=True)
        wav = write_wav(music / "cue-9.wav", planted(SCRAMBLED))
        downbeats = [i * 2.0 for i in range(16)]
        step.grid_path(wav).write_text(json.dumps(
            {"beats": cue_arc.grid_of(downbeats, 2.0)[0], "downbeats": downbeats}), encoding="utf-8")
        monkeypatch.setattr(beatmap, "track_beats", lambda s, r: ([], []))
        found = step.measure(ctx.book_dir, wav, 9)
        assert found.grid == "metre" and np.allclose(found.downbeats, downbeats, atol=0.02)
        assert step.known_grid(music / "cue-10.wav") is None

    def test_arc_cue_ships_a_render_with_no_bar_lines_as_it_is(self, ctx, monkeypatch):
        """Rubato has no bars to re-order: the raw render is the cue, and the
        grade sees the same file the old path graded (degrade, then learn)."""
        from tests.test_cue_arc import SCRAMBLED, metre_of, planted
        music = ctx.out_dir / "music"
        music.mkdir(parents=True, exist_ok=True)
        raw = write_wav(music / "raw-8.wav", planted(SCRAMBLED[:6]))
        stamp_cue(raw, "recipe-8", "caption A", "")
        bare = metre_of(2).model_copy(update={"downbeats": [], "beats": [], "grid": "onsets"})
        monkeypatch.setattr(beatmap, "metre", lambda path, seed, rel_path: bare)
        out = step.arc_cue(ctx.book_dir, raw, cue_ask.CueAsk.for_bars(16, bar=2.0, bpm=120), 8)
        assert out == music / "cue-8.wav" and out.read_bytes() == raw.read_bytes()

    def test_grade_records_metre_form_map_and_score_for_one_seed(self, ctx, tmp_path):
        music = ctx.out_dir / "music"
        music.mkdir(parents=True, exist_ok=True)
        wav = write_wav(music / "cue-7.wav", cue(**KINDS["two"]))
        state = {"ask": step.ask_of(ctx, TONE), "found": [], "form": {}, "maps": {}, "asks": {},
                 "score": {}}
        metre = step.grade(ctx.book_dir, wav, 7, state)
        assert state["found"] == [metre] and metre.seed == 7
        assert set(state["form"]) == set(state["maps"]) == set(state["score"]) == {7}
        assert 0.0 <= state["score"][7] <= 1.0 and (music / "cutmap-7.json").exists()

    def test_warn_short_names_every_shortfall_of_the_shipped_cue(self, ctx, tmp_path, monkeypatch):
        logged = []
        monkeypatch.setattr(ctx.tracker, "log", lambda msg, **kw: logged.append(msg))
        two = beatmap.metre(write_wav(tmp_path / "a.wav", cue(**KINDS["two"])), seed=1,
                            rel_path="a.wav", track=track_autocorrelation)
        step.warn_short(ctx, two.model_copy(update={"grid": "onsets"}), 84, {1: 1}, 0.4)
        assert [m.split(" shipped")[1][:14] for m in logged] == [
            " delivering 0.", " with 1 of 2 f", " on the ONSET ", " OFF TONE: 115"]
        logged.clear()
        step.warn_short(ctx, two, 120, {1: 2}, 0.9)
        assert logged == []

    def test_a_shorter_ask_retires_the_seeds_rendered_at_the_longer_one(self, ctx):
        """The fit rule judged the ASK too long for the frames: every cue cut
        to it is out of the running once a shorter one has been rendered."""
        first = step.ask_of(ctx, TONE)
        shorter = step.shorter_ask(TONE, first, 4)
        a = Metre(seed=1, rel_path="m/a.wav", seconds=60.0, bpm=120.0, bar=2.0, beats_per_bar=4,
                  beats=[0.5], downbeats=[0.5], bars_in_mode=0.9, grid="metre", fitness=20.0)
        b = a.model_copy(update={"seed": 2})
        state = {"found": [a, b], "asks": {1: first, 2: shorter}, "ask": shorter}
        assert step.in_the_running(state) == [b]
        state["ask"] = step.shorter_ask(TONE, first, 8)
        assert step.in_the_running(state) == [a, b]

    def test_a_shorter_ask_loses_the_bars_the_fit_needed_and_keeps_the_form(self, ctx):
        ask = step.ask_of(ctx, TONE)
        assert step.shorter_ask(TONE, ask, 4).bars == ask.bars - 4
        assert step.shorter_ask(TONE, ask, 10_000).bars == MIN_FORM_BARS + step.TAIL_BARS


class TestStep:
    def test_a_cue_that_offers_too_many_spans_is_asked_for_shorter(self, ctx, tmp_path, monkeypatch):
        """A seed that delivers its ask on more spans than the frames afford
        AND that no conform can cut down fails the gate with the bars the
        fit needed; the next batch asks for that many fewer, and the plan
        shipped is the conformed one."""
        seeds = step.seeds_for(0)
        kinds = {s: "two" for b in range(2) for s in step.seeds_for(b)}
        comfy_calls, fits = [], []
        monkeypatch.setattr(build_music, "run", fake_comfy(tmp_path, kinds, comfy_calls))
        monkeypatch.setattr(llm, "structured", fake_llm([]))
        monkeypatch.setattr(step, "score_of", lambda ask, cut, found: 0.9)

        def conformed(ctx_, plan):
            fits.append(plan.asked.bars)
            if len(fits) == 1:
                raise ShorterCue(4)
            return Settled(plan=plan, ids=cue_conform.indices(plan), removed=[])
        monkeypatch.setattr(step, "conformed", conformed)
        step.run(ctx.codex_id, ctx)
        first = step.ask_of(ctx, TONE)
        shorter = step.shorter_ask(TONE, first, 4)
        assert [c["duration"] for c in comfy_calls] ==             [math.ceil(first.seconds) + step.TAIL_HEADROOM] * 4 +             [math.ceil(shorter.seconds) + step.TAIL_HEADROOM] * 4
        assert fits == [first.bars, shorter.bars, shorter.bars]
        rows = load(ctx.learnings_path)
        assert rows[0].action == "first_seeds" and "4 fewer bars" in rows[0].measured
        plan = CuePlan.model_validate_json((ctx.out_dir / "music/plan.json").read_text(encoding="utf-8"))
        assert plan.asked.bars == shorter.bars and plan.seed in step.seeds_for(1)

    def test_a_plan_no_fit_can_afford_ships_untrimmed_and_warns(self, ctx, tmp_path, monkeypatch):
        seeds = step.seeds_for(0)
        kinds = {seeds[0]: "two", seeds[1]: "two", seeds[2]: "two", seeds[3]: "two"}
        monkeypatch.setattr(build_music, "run", fake_comfy(tmp_path, kinds, []))
        monkeypatch.setattr(llm, "structured", fake_llm([]))
        monkeypatch.setattr(ctx.budget, "can_afford", lambda s, secs: False)
        monkeypatch.setattr(step, "score_of", lambda ask, cut, found: 0.9)

        def never(ctx_, plan):
            raise ShorterCue(3)
        monkeypatch.setattr(step, "conformed", never)
        logged = []
        monkeypatch.setattr(ctx.tracker, "log", lambda msg, **kw: logged.append(msg))
        step.run(ctx.codex_id, ctx)
        assert (ctx.out_dir / "music/plan.json").exists()
        assert any("3 fewer bars" in m for m in logged)

    def test_a_cue_over_the_frames_is_conformed_from_the_one_render(self, ctx, tmp_path, monkeypatch):
        """Row 56: a shorter cue is an edit of the verified one, not a second
        render.  The gate passes on the conformed plan, the cue is cut, and
        the plan shipped plays the settled file."""
        seeds = step.seeds_for(0)
        kinds = {s: "two" for s in seeds}
        comfy_calls, cuts = [], []
        monkeypatch.setattr(build_music, "run", fake_comfy(tmp_path, kinds, comfy_calls))
        monkeypatch.setattr(llm, "structured", fake_llm([]))
        monkeypatch.setattr(step, "score_of", lambda ask, cut, found: 0.9)

        def conformed(ctx_, plan):
            out = cue_settle.cut_settled(plan, cue_conform.indices(plan), 1)
            return Settled(plan=out.plan, ids=out.ids, removed=out.removed)

        def cut_files(music, book, cue, removed):
            cuts.append((cue.seed, removed))
            return cue_conform.settled_rel(cue)
        monkeypatch.setattr(step, "conformed", conformed)
        monkeypatch.setattr(cue_conform, "cut_files", cut_files)
        step.run(ctx.codex_id, ctx)
        plan = CuePlan.model_validate_json((ctx.out_dir / "music/plan.json").read_text(encoding="utf-8"))
        assert len(comfy_calls) == 4 and len(cuts) == 1 and cuts[0][0] == plan.seed
        assert plan.rel_path.endswith(f"cue-{plan.seed}-settled.wav")
        gone = cuts[0][1][0]
        assert plan.seconds == pytest.approx(chosen_of(ctx).seconds - (gone[1] - gone[0]), abs=1e-3)
        rows = [r for r in load(ctx.learnings_path) if r.gate == "conform"]
        assert len(rows) == 1 and rows[0].action == "conformed" and "1 range" in rows[0].measured

    def test_conformed_is_the_budgets_cut_of_the_plan(self, ctx, monkeypatch):
        from tests.test_cue_qc import build_plan
        monkeypatch.setattr(step, "picture_budget", lambda ctx_: 10.0)
        monkeypatch.setattr(step, "cycle_of", lambda ctx_: frame_budget.TYPED)
        with pytest.raises(ShorterCue):
            step.conformed(ctx, build_plan())
        monkeypatch.setattr(step, "picture_budget", lambda ctx_: 10_000.0)
        assert step.conformed(ctx, build_plan()).plan == build_plan()

    def test_a_join_the_cue_refuses_ships_the_whole_cue_and_warns(self, ctx, tmp_path, monkeypatch):
        seeds = step.seeds_for(0)
        monkeypatch.setattr(build_music, "run", fake_comfy(tmp_path, {s: "two" for s in seeds}, []))
        monkeypatch.setattr(llm, "structured", fake_llm([]))
        monkeypatch.setattr(step, "score_of", lambda ask, cut, found: 0.9)

        def conformed(ctx_, plan):
            out = cue_settle.cut_settled(plan, cue_conform.indices(plan), 1)
            return Settled(plan=out.plan, ids=out.ids, removed=out.removed)

        def refuse(music, book, cue, removed):
            raise ValueError("levels differ by 4.1 dB at the join")
        monkeypatch.setattr(step, "conformed", conformed)
        monkeypatch.setattr(cue_conform, "cut_files", refuse)
        logged = []
        monkeypatch.setattr(ctx.tracker, "log", lambda msg, **kw: logged.append(msg))
        step.run(ctx.codex_id, ctx)
        plan = CuePlan.model_validate_json((ctx.out_dir / "music/plan.json").read_text(encoding="utf-8"))
        assert plan.rel_path == chosen_of(ctx).rel_path and plan.seconds == chosen_of(ctx).seconds
        assert any("refused a join" in m for m in logged)

    def test_step_writes_the_cue_plan_and_a_cut_map_per_seed(self, ctx, tmp_path, monkeypatch):
        """Downstream steps read spans from `music/plan.json` and invent no cut;
        every seed's cut map is kept beside its metre for the retrospect."""
        seeds = step.seeds_for(0)
        kinds = {seeds[0]: "flat", seeds[1]: "two", seeds[2]: "one", seeds[3]: "flat"}
        monkeypatch.setattr(build_music, "run", fake_comfy(tmp_path, kinds, []))
        monkeypatch.setattr(llm, "structured", fake_llm([]))
        step.run(ctx.codex_id, ctx)
        plan = CuePlan.model_validate_json((ctx.out_dir / "music/plan.json").read_text(encoding="utf-8"))
        chosen = chosen_of(ctx)
        assert plan.seed == chosen.seed and plan.rel_path == chosen.rel_path
        assert plan.asked is not None and plan.asked.bars == step.bars_of(ctx, TONE)
        assert plan.spans[-1].kind == "tail" and len(plan.picture_spans()) >= 2
        rendered = sorted(p.stem.split("-")[1] for p in ctx.out_dir.glob("music/cue-*.wav"))
        mapped = sorted(p.stem.split("-")[1] for p in ctx.out_dir.glob("music/cutmap-*.json"))
        assert mapped == rendered and set(str(s) for s in seeds) <= set(mapped)

    def test_step_stops_climbing_at_the_seed_that_delivers_its_ask(self, ctx, tmp_path, monkeypatch):
        """A seed that delivered its ask on a metric grid ends the ladder on the
        first batch: no second batch, no reauthor, nothing learned.  The shipped
        cue is the ARC of the render, so its slots are where the ask put its holes."""
        seeds = step.seeds_for(0)
        kinds = {seeds[0]: "flat", seeds[1]: "two", seeds[2]: "one", seeds[3]: "flat"}
        comfy_calls, llm_calls = [], []
        monkeypatch.setattr(build_music, "run", fake_comfy(tmp_path, kinds, comfy_calls))
        monkeypatch.setattr(llm, "structured", fake_llm(llm_calls))
        monkeypatch.setattr(step, "score_of",
                            lambda ask, cut, found: 0.9 if found.seed == seeds[1] else 0.2)
        step.run(ctx.codex_id, ctx)
        chosen = chosen_of(ctx)
        assert chosen.seed == seeds[1] and chosen.grid == "metre"
        assert chosen.rel_path == f"trailer/main/music/cue-{seeds[1]}.wav"
        plan = CuePlan.model_validate_json((ctx.out_dir / "music/plan.json").read_text(encoding="utf-8"))
        holes = [e.bar for e in plan.asked.events if e.kind == "hole"]
        assert holes and all(any(abs(slot.start - chosen.downbeats[b]) < chosen.bar / 2
                                 for slot in chosen.slots) for b in holes)
        assert sorted(p.name for p in ctx.out_dir.glob("music/metre-*.json")) == \
            sorted(f"metre-{s}.json" for s in seeds)
        assert [c["seed"] for c in comfy_calls] == seeds and llm_calls == []
        assert not ctx.learnings_path.exists()

    def test_rubato_everywhere_ships_onset_grid_and_learns(self, ctx, tmp_path, monkeypatch):
        monkeypatch.setattr(beatmap, "track_beats", wobbly)
        kinds = {s: "two" for b in range(4) for s in step.seeds_for(b)}
        comfy_calls, llm_calls = [], []
        monkeypatch.setattr(build_music, "run", fake_comfy(tmp_path, kinds, comfy_calls))
        monkeypatch.setattr(llm, "structured", fake_llm(llm_calls))
        step.run(ctx.codex_id, ctx)
        chosen = chosen_of(ctx)
        assert chosen.grid == "onsets" and chosen.downbeats == []
        assert len(comfy_calls) == 4 * step.BATCH and len(llm_calls) == 2
        assert caption(TONE) not in [c["caption"] for c in comfy_calls[-8:]]
        rows = load(ctx.learnings_path)
        assert [r.action for r in rows] == ["first_seeds", "four_more_seeds", "reauthor_caption",
                                            "reauthor_caption", "best_seed"]
        assert rows[-1].terminal and rows[-1].step == "03"

    def test_a_spent_budget_ships_what_was_measured(self, ctx, tmp_path, monkeypatch):
        seeds = step.seeds_for(0)
        kinds = {seeds[0]: "one", seeds[1]: "two"}
        comfy_calls: list[dict] = []
        monkeypatch.setattr(build_music, "run", fake_comfy(tmp_path, kinds, comfy_calls))
        monkeypatch.setattr(ctx.budget, "can_afford", lambda s, secs: len(comfy_calls) < 1)
        step.run(ctx.codex_id, ctx)
        assert chosen_of(ctx).seed == seeds[0] and len(comfy_calls) == 1
