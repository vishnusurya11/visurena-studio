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
from studio.music_tone import Tone, caption
from studio.trailer_run import RunContext
from studio.trailer_stage_spec import Metre
from test_metre import click_track, write_wav

TONE = Tone(genre="Chamber noir", bpm=120, key="G", scale="minor",
            lead_instrument="a solo violin", percussion="a walking double bass and a pocket watch",
            sonics="dry and close", progression="curious, then a pursuit",
            imagery="a gaslit room", instruments="cello and double bass")


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
        return schema(percussion="a taiko under a ticking hi-hat, struck on every beat",
                      instruments="cello and a bass drum holding the grid")
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
        first = build_music.render_cue(tmp_path, "caption A", 5, dest, 60.0)
        again = build_music.render_cue(tmp_path, "caption A", 5, dest, 60.0)
        moved = build_music.render_cue(tmp_path, "caption B", 5, dest, 60.0)
        assert first == again == moved == dest / "cue-5.wav" and len(calls) == 2

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

    def test_reauthor_keeps_the_register_and_the_tempo_and_swaps_the_pulse(self, monkeypatch):
        """The asked bpm is the tone's, not the reauthor's: a sheet that could
        choose 80-140 would move the goal the gate measures against."""
        calls: list[str] = []
        monkeypatch.setattr(llm, "structured", fake_llm(calls))
        tone = step.reauthor(TONE, None)
        assert tone.genre == TONE.genre and tone.lead_instrument == TONE.lead_instrument
        assert tone.bpm == TONE.bpm and tone.percussion != TONE.percussion
        assert "bars in mode" in calls[0] and "hold 120 BPM" in calls[0]
        assert "bpm" not in step.CaptionSheet.model_fields


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
