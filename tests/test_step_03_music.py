"""Step 03 of the trailer stage: seeds are MEASURED and ranked, never trusted.

Eight seeds of one caption ranged 0.31-0.97 bars-in-mode, so the step renders
a batch, measures every seed's metre, and gates on the best: fitness above the
floor, a metric grid, and at least one slot.  Every fake here is the seam the
contract names: `build_music.run` (ComfyUI), `llm.structured`, and the beat
tracker -- no test renders, calls a model, or loads Beat This.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from scripts.trailer import build_music
from scripts.trailer import step_03_music as step
from studio import beatmap, db, llm
from studio.beatmap import RATE, track_autocorrelation
from studio.learnings import load
from studio.affirm import negations
from studio.music_tone import Tone, caption, lyrics_plan
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

    def test_verdict_needs_a_metric_grid_on_the_asked_tempo(self, tmp_path):
        """Fitness had a floor of 6.0 no real seed ever met (run 9's best was
        4.4; earlier 0.3-2.5), and the slot the gate wanted is now MADE from
        the grid by 04-lines.  What the gate grades is what the cut needs
        and no seed can fake: a countable grid at the asked pace."""
        two = beatmap.metre(write_wav(tmp_path / "a.wav", cue(**KINDS["two"])), seed=1,
                            rel_path="a.wav", track=track_autocorrelation)
        assert step.verdict(two, 120)[0]
        assert step.verdict(two.model_copy(update={"slots": [], "fitness": 0.5}), 120)[0]
        assert not step.verdict(two, 84)[0] and "against 84 asked" in step.verdict(two, 84)[1]
        assert not step.verdict(two.model_copy(update={"grid": "onsets"}), 120)[0]
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


class TestStep:
    def test_step_ranks_seeds_on_fitness(self, ctx, tmp_path, monkeypatch):
        seeds = step.seeds_for(0)
        kinds = {seeds[0]: "flat", seeds[1]: "two", seeds[2]: "one", seeds[3]: "flat"}
        comfy_calls, llm_calls = [], []
        monkeypatch.setattr(build_music, "run", fake_comfy(tmp_path, kinds, comfy_calls))
        monkeypatch.setattr(llm, "structured", fake_llm(llm_calls))
        step.run(ctx.codex_id, ctx)
        chosen = chosen_of(ctx)
        assert chosen.seed == seeds[1] and chosen.grid == "metre" and len(chosen.slots) == 2
        assert chosen.rel_path == f"trailer/main/music/cue-{seeds[1]}.wav"
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
