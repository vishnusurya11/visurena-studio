"""Generated sound effects: the contract, the level, the placing, the QC measure.

Nothing here reaches ComfyUI.  The workflow is replaced by a fake `run` that
writes a small synthetic FLAC with numpy + soundfile, the
way the engine would hand one back, so every level assertion reads a real
file through the same ebur128 the mix uses.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from pydantic import ValidationError

from studio import sfx_cues
from studio.sfx_cues import Cue
from studio.trailer_assemble import integrated

RATE = 44100


def burst(path: Path, seconds: float = 2.0, level: float = 0.05, onset: float = 0.3) -> Path:
    """Silence, then a decaying noise burst: the shape of a gunshot."""
    rng = np.random.default_rng(7)
    n, start = int(seconds * RATE), int(onset * RATE)
    audio = np.zeros((n, 2), dtype=np.float32)
    tail = np.exp(-np.arange(n - start) / (0.25 * RATE))[:, None]
    audio[start:] = (rng.standard_normal((n - start, 2)) * tail * level).astype(np.float32)
    sf.write(str(path), audio, RATE, format="FLAC")
    return path


def steady(path: Path, seconds: float = 11.0, level: float = 0.02) -> Path:
    """Steady noise: the shape of an ambience bed."""
    rng = np.random.default_rng(3)
    audio = (rng.standard_normal((int(seconds * RATE), 2)) * level).astype(np.float32)
    sf.write(str(path), audio, RATE, format="FLAC")
    return path


class FakeRun:
    """Stands in for `comfy.run`: records each call, returns one made file."""

    def __init__(self, folder: Path, make=burst):
        self.folder, self.make, self.calls = folder, make, []

    def __call__(self, name, values, timeout=0.0):
        self.calls.append((name, values))
        return [self.make(self.folder / f"fake_{len(self.calls)}.flac", values["seconds"])]


def gun(**over) -> Cue:
    fields = {"shot": 3, "sound": "a single heavy field gun firing, distant", "seconds": 2.0}
    return Cue(**{**fields, **over})


# ---------------------------------------------------------------- the contract

class TestCue:
    def test_defaults_place_it_at_the_head_of_its_shot_at_the_default_level(self):
        cue = gun()
        assert (cue.at, cue.gain_db) == (0.0, 0.0)

    @pytest.mark.parametrize("seconds", [0.5, 10.5])
    def test_the_workflow_cannot_make_under_one_or_over_ten_seconds(self, seconds):
        with pytest.raises(ValidationError):
            gun(seconds=seconds)

    def test_a_negative_offset_is_refused(self):
        with pytest.raises(ValidationError):
            gun(at=-0.1)

    def test_an_empty_sound_is_refused(self):
        with pytest.raises(ValidationError):
            gun(sound="  ")


class TestPromptFor:
    def test_it_begins_with_the_prefix_the_model_was_trained_on(self):
        assert sfx_cues.prompt_for(gun()).startswith("TrackType: SFX, a single heavy field gun")

    def test_it_asks_for_no_music_and_no_dialogue(self):
        prompt = sfx_cues.prompt_for(gun())
        assert "no music" in prompt and "no dialogue" in prompt

    def test_the_place_rides_after_the_sound(self):
        prompt = sfx_cues.prompt_for(gun(), where="1890s Surrey common")
        assert prompt.index("field gun") < prompt.index("1890s Surrey common")

    def test_it_is_deterministic(self):
        assert sfx_cues.prompt_for(gun(), "x") == sfx_cues.prompt_for(gun(), "x")


class TestValuesFor:
    def test_the_trim_is_as_long_as_the_generation(self):
        values = sfx_cues.values_for("p", 4.0, 11, "pre")
        assert values["seconds"] == values["trim_duration"] == 4.0

    def test_it_runs_the_manifest_sampler(self):
        values = sfx_cues.values_for("p", 4.0, 11, "pre")
        assert (values["steps"], values["cfg"], values["seed"]) == (8, 1.0, 11)


class TestFileName:
    def test_it_names_the_shot_and_is_stable(self):
        name = sfx_cues.file_name(gun())
        assert name.startswith("shot03_") and name.endswith(".wav")
        assert name == sfx_cues.file_name(gun())

    def test_two_sounds_on_one_shot_do_not_collide(self):
        assert sfx_cues.file_name(gun()) != sfx_cues.file_name(gun(sound="a crowd"))


# ---------------------------------------------------------------- the level

def peak_momentary(path: Path) -> float:
    return sfx_cues.peak_momentary(path)


class TestRender:
    def test_it_writes_a_48k_wav_at_the_cue_level(self, tmp_path):
        out = sfx_cues.render(gun(), tmp_path / "gun.wav", 5, run=FakeRun(tmp_path))
        info = sf.info(str(out))
        assert (info.samplerate, info.format) == (48000, "WAV")
        assert peak_momentary(out) == pytest.approx(sfx_cues.CUE_LUFS, abs=1.0)

    def test_gain_moves_the_level_by_that_many_decibels(self, tmp_path):
        out = sfx_cues.render(gun(gain_db=-6.0), tmp_path / "g.wav", 5, run=FakeRun(tmp_path))
        assert peak_momentary(out) == pytest.approx(sfx_cues.CUE_LUFS - 6.0, abs=1.0)

    def test_it_never_exceeds_the_true_peak_ceiling(self, tmp_path):
        fake = FakeRun(tmp_path, make=lambda p, s: burst(p, s, level=0.9))
        out = sfx_cues.render(gun(gain_db=12.0), tmp_path / "g.wav", 5, run=fake)
        assert np.abs(sf.read(str(out))[0]).max() <= 10 ** (sfx_cues.CUE_TP / 20)

    def test_the_sidecar_records_what_made_it_and_no_path(self, tmp_path):
        out = sfx_cues.render(gun(), tmp_path / "gun.wav", 5, run=FakeRun(tmp_path))
        side = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
        assert side["seed"] == 5 and side["prompt"].startswith("TrackType: SFX,")
        assert str(tmp_path) not in json.dumps(side)

    def test_a_second_call_with_the_same_ask_does_not_render(self, tmp_path):
        fake = FakeRun(tmp_path)
        sfx_cues.render(gun(), tmp_path / "gun.wav", 5, run=fake)
        sfx_cues.render(gun(), tmp_path / "gun.wav", 5, run=fake)
        assert len(fake.calls) == 1

    def test_a_new_seed_renders_again(self, tmp_path):
        fake = FakeRun(tmp_path)
        sfx_cues.render(gun(), tmp_path / "gun.wav", 5, run=fake)
        sfx_cues.render(gun(), tmp_path / "gun.wav", 6, run=fake)
        assert len(fake.calls) == 2

    def test_a_silent_generation_is_refused_not_levelled(self, tmp_path):
        fake = FakeRun(tmp_path, make=lambda p, s: burst(p, s, level=0.0))
        with pytest.raises(RuntimeError, match="silent"):
            sfx_cues.render(gun(), tmp_path / "gun.wav", 5, run=fake)


def early_end(path: Path, content: float = 1.0, seconds: float = 3.0) -> Path:
    """Noise for `content` seconds, then the -88 dB floor SA3 pads with."""
    rng = np.random.default_rng(5)
    audio = (rng.standard_normal((int(seconds * RATE), 2)) * 4e-5).astype(np.float32)
    audio[:int(content * RATE)] = rng.standard_normal((int(content * RATE), 2)) * 0.1
    sf.write(str(path), audio, RATE, format="FLAC")
    return path


class TestContentEnd:
    def test_it_finds_where_the_generation_stopped(self, tmp_path):
        assert sfx_cues.content_end(early_end(tmp_path / "e.flac")) == pytest.approx(1.0, abs=0.02)

    def test_a_sound_that_fills_the_file_is_not_trimmed(self, tmp_path):
        assert sfx_cues.content_end(steady(tmp_path / "s.flac", 3.0)) is None

    def test_render_cuts_the_padding_off(self, tmp_path):
        fake = FakeRun(tmp_path, make=lambda p, s: early_end(p, 1.0, s))
        out = sfx_cues.render(gun(seconds=3.0), tmp_path / "g.wav", 5, run=fake)
        assert sf.info(str(out)).duration == pytest.approx(1.0, abs=0.02)


class TestRenderAll:
    def test_each_cue_gets_its_own_seed_and_file(self, tmp_path):
        fake = FakeRun(tmp_path)
        pairs = sfx_cues.render_all([gun(), gun(sound="a crowd")], tmp_path, 10, run=fake)
        assert [v["seed"] for _, v in fake.calls] == [10, 11]
        assert len({path for _, path in pairs}) == 2


# ---------------------------------------------------------------- placing

SHOTS = [{"index": 3, "t_start": 10.0, "t_end": 14.0, "seconds": 4.0},
         {"index": 4, "t_start": 14.0, "t_end": 20.0, "seconds": 6.0},
         {"index": 7, "t_start": 30.0, "t_end": 32.0, "seconds": 2.0}]


class TestPlaced:
    def test_a_cue_starts_at_its_shot_plus_its_offset(self):
        assert sfx_cues.placed([(gun(at=1.0), Path("g.wav"))], SHOTS) == [(11.0, Path("g.wav"))]

    def test_a_late_cue_is_pulled_back_to_end_inside_its_shot(self):
        got = sfx_cues.placed([(gun(at=3.5, seconds=2.0), Path("g.wav"))], SHOTS)
        assert got[0][0] == pytest.approx(12.0)

    def test_a_cue_longer_than_its_shot_is_a_plan_fault(self):
        with pytest.raises(ValueError, match="shot 3"):
            sfx_cues.placed([(gun(seconds=5.0), Path("g.wav"))], SHOTS)

    def test_a_cue_on_a_shot_the_cut_does_not_have_is_named(self):
        with pytest.raises(KeyError, match="99"):
            sfx_cues.placed([(gun(shot=99), Path("g.wav"))], SHOTS)


# ---------------------------------------------------------------- ambience

class TestSpans:
    def test_adjacent_shots_become_one_span(self):
        assert sfx_cues.spans(SHOTS[:2]) == [(10.0, 10.0)]

    def test_a_gap_starts_a_new_span(self):
        assert sfx_cues.spans([SHOTS[0], SHOTS[2]]) == [(10.0, 4.0), (30.0, 2.0)]


class TestLoopable:
    def test_the_seam_is_continuous(self, tmp_path):
        clip = sfx_cues.loopable(steady(tmp_path / "a.flac"), tmp_path / "loop.wav")
        audio, rate = sf.read(str(clip))
        joined = np.concatenate([audio[-rate // 20:], audio[:rate // 20]])
        assert np.abs(np.diff(joined, axis=0)).max() < 0.2

    def test_it_is_one_fade_shorter_than_the_render(self, tmp_path):
        clip = sfx_cues.loopable(steady(tmp_path / "a.flac"), tmp_path / "loop.wav")
        assert sf.info(str(clip)).duration == pytest.approx(11.0 - sfx_cues.LOOP_FADE, abs=0.01)


class TestAmbience:
    def test_it_lays_one_cue_per_span_as_long_as_the_span(self, tmp_path):
        fake = FakeRun(tmp_path, make=lambda p, s: steady(p, s))
        cues = sfx_cues.ambience("summer meadow, larks", SHOTS, tmp_path / "amb", 9, run=fake)
        assert [at for at, _ in cues] == [10.0, 30.0]
        assert sf.info(str(cues[0][1])).duration == pytest.approx(10.0, abs=0.05)

    def test_it_sits_at_the_ambience_level(self, tmp_path):
        fake = FakeRun(tmp_path, make=lambda p, s: steady(p, s))
        cues = sfx_cues.ambience("summer meadow", SHOTS[:2], tmp_path / "amb", 9, run=fake)
        assert integrated(cues[0][1]) == pytest.approx(sfx_cues.AMBIENCE_LUFS, abs=1.5)

    def test_it_renders_the_bed_once_for_every_span(self, tmp_path):
        fake = FakeRun(tmp_path, make=lambda p, s: steady(p, s))
        sfx_cues.ambience("summer meadow", SHOTS, tmp_path / "amb", 9, run=fake)
        assert len(fake.calls) == 1 and fake.calls[0][1]["seconds"] == sfx_cues.AMBIENCE_RENDER


# ---------------------------------------------------------------- QC

def master_with_hit(path: Path, hit_at: float | None) -> Path:
    """Six seconds of quiet noise, with a loud burst at `hit_at` if given."""
    rng = np.random.default_rng(1)
    audio = (rng.standard_normal(6 * 48000) * 0.005).astype(np.float32)
    if hit_at is not None:
        start = int(hit_at * 48000)
        audio[start:start + 24000] += (rng.standard_normal(24000) * 0.3).astype(np.float32)
    sf.write(str(path), audio, 48000)
    return path


class TestWindowDb:
    def test_full_scale_square_reads_zero(self):
        assert sfx_cues.window_db(np.ones(4800, dtype=np.float32), 48000)[0] == pytest.approx(0.0)

    def test_it_makes_one_reading_per_50_ms(self):
        assert len(sfx_cues.window_db(np.zeros(48000, dtype=np.float32), 48000)) == 20


class TestEventDb:
    def test_a_present_hit_stands_well_above_the_second_before(self, tmp_path):
        master = master_with_hit(tmp_path / "m.wav", 3.0)
        assert sfx_cues.event_db(master, 3.0, 1.0) > 20.0

    def test_a_missing_hit_reads_near_zero(self, tmp_path):
        master = master_with_hit(tmp_path / "m.wav", None)
        assert abs(sfx_cues.event_db(master, 3.0, 1.0)) < 3.0

    def test_a_cue_with_nothing_before_it_is_refused(self, tmp_path):
        with pytest.raises(ValueError):
            sfx_cues.event_db(master_with_hit(tmp_path / "m.wav", 0.0), 0.0, 1.0)
