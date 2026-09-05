"""The metre is MEASURED from the audio, never read off the caption.

Eight seeds of one byte-identical caption ranged 0.31-0.97 bars-in-mode and
89-189 BPM against 84 asked, so the tracker is the only witness to the grid
the cut can use.  The default suite proves the numpy tracker and the Metre
derivation on a synthetic click; the model-backed path (Beat This!) runs the
same clicks under `local`, because a neural tracker needs its checkpoint on
disk and a bare sine click is outside anything it was trained on.
"""
from __future__ import annotations

import json
import os
import wave
from pathlib import Path

import numpy as np
import pytest

from studio import beatmap
from studio.beatmap import (RATE, Grid, bars_in_mode, beats_in_mode, metre, phrases, tempo_of,
                            track_autocorrelation)
from studio.trailer_stage_spec import Metre

TEMPOS = (60, 90, 120, 180)
TOLERANCE = 0.06
LOCAL = pytest.mark.skipif(not os.environ.get("VISURENA_LOCAL"),
                           reason="model-backed tracker; set VISURENA_LOCAL=1")


def click_track(bpm: float, seconds: float = 30.0, rate: int = RATE,
                seed: int = 0) -> tuple[np.ndarray, list[float], list[float]]:
    """A 4/4 click with the downbeat accented: (samples, beats, downbeats)."""
    rng = np.random.default_rng(seed)
    samples = np.zeros(int(rate * seconds), dtype=np.float32)
    length = int(0.03 * rate)
    decay = np.exp(-np.arange(length) / (0.004 * rate))
    beats, downbeats = [], []
    for i in range(int((seconds - 0.1) * bpm / 60)):
        when = 0.5 + i * 60.0 / bpm
        start = int(when * rate)
        freq, amp = (880.0, 1.0) if i % 4 == 0 else (440.0, 0.5)
        samples[start:start + length] += amp * decay * np.sin(
            2 * np.pi * freq * np.arange(length) / rate)
        beats.append(round(when, 4))
        if i % 4 == 0:
            downbeats.append(round(when, 4))
    samples += 0.005 * rng.standard_normal(len(samples)).astype(np.float32)
    return samples, beats, downbeats


def write_wav(path: Path, samples: np.ndarray, rate: int = RATE) -> Path:
    with wave.open(str(path), "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(rate)
        fh.writeframes((np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes())
    return path


def recall(reference: list[float], found: list[float], tol: float = TOLERANCE) -> float:
    if not reference:
        return 0.0
    return sum(any(abs(r - f) <= tol for f in found) for r in reference) / len(reference)


class TestAutocorrelationTracker:
    @pytest.mark.parametrize("bpm", TEMPOS)
    def test_click_track_recovers_beats_and_downbeats(self, bpm):
        samples, beats, downbeats = click_track(bpm)
        got_beats, got_downbeats = track_autocorrelation(samples, RATE)
        assert recall(beats, got_beats) >= 0.9, (bpm, len(got_beats))
        assert recall(downbeats, got_downbeats) >= 0.9, (bpm, got_downbeats[:5])

    @pytest.mark.parametrize("bpm", TEMPOS)
    def test_tempo_has_no_octave_double(self, bpm):
        samples, _, _ = click_track(bpm)
        got_beats, _ = track_autocorrelation(samples, RATE)
        assert abs(tempo_of(got_beats) / bpm - 1.0) <= 0.03


class TestTempo:
    def test_tempo_is_the_span_not_the_median_interval(self):
        """Median IBI on a 20 ms grid is 3000/n and carries octave doubles."""
        beats = [0.5 + i * 0.677 for i in range(40)]
        assert abs(tempo_of(beats) - 60 / 0.677) < 0.01

    def test_bars_in_mode_counts_bars_within_five_percent_of_the_mode(self):
        downbeats = [0.0, 2.0, 4.0, 6.0, 8.05, 10.0, 13.0]
        assert bars_in_mode(downbeats) == pytest.approx(5 / 6)

    def test_phrases_are_every_fourth_downbeat(self):
        assert phrases([float(i) for i in range(10)]) == [0.0, 4.0, 8.0]


class TestMetreOfAFile:
    def test_a_click_file_yields_a_metric_grid(self, tmp_path):
        samples, beats, downbeats = click_track(120, seconds=20.0)
        wav = write_wav(tmp_path / "cue-7.wav", samples)
        found = metre(wav, seed=7, rel_path="trailer/music/cue-7.wav",
                      track=track_autocorrelation)
        assert isinstance(found, Metre) and found.grid == "metre"
        assert found.bars_in_mode >= 0.95 and abs(found.bpm - 120) < 2
        assert recall(downbeats, found.downbeats) >= 0.9
        assert found.phrase_starts == phrases(found.downbeats)

    def test_a_tracker_that_finds_nothing_is_replaced_by_the_fallback(self, tmp_path):
        samples, beats, _ = click_track(90, seconds=20.0)
        wav = write_wav(tmp_path / "cue-1.wav", samples)
        found = metre(wav, seed=1, rel_path="cue-1.wav", track=lambda s, r: ([], []))
        assert recall(beats, found.beats) >= 0.9

    def test_a_rubato_grid_falls_back_to_onsets(self, tmp_path):
        samples, _, _ = click_track(120, seconds=20.0)
        wav = write_wav(tmp_path / "cue-2.wav", samples)
        wobble = [0.5, 2.0, 4.6, 5.3, 8.0, 8.9, 11.5, 12.1, 14.0, 16.9]
        found = metre(wav, seed=2, rel_path="cue-2.wav",
                      track=lambda s, r: ([w for w in wobble], wobble[::2]))
        assert found.grid == "onsets" and found.downbeats == []


class TestGrid:
    def test_beats_per_bar_is_counted_between_downbeats(self):
        beats = [i * 0.5 for i in range(24)]
        grid = Grid.of(beats, beats[::3])
        assert grid.beats_per_bar == 3 and grid.bar == pytest.approx(1.5)


class TestRebar:
    """Scarlet run 6, re-tracked: seeds 2002, 2004, 3001 and 3003 held a
    steady beat for 40-58 s (beats_in_mode 0.89-0.96) and were graded rubato
    (bars_in_mode 0.45-0.65) because the downbeat tracker alternated bars of
    two and four beats -- {2: 29, 4: 31}.  A steady beat determines its bar;
    the downbeats are re-voted every modal count of beats along the beat."""
    BEATS = [i * 0.5 for i in range(64)]

    def test_beats_in_mode_is_the_share_of_intervals_within_five_percent(self):
        assert beats_in_mode(self.BEATS) == 1.0
        assert beats_in_mode([0.0, 0.5, 1.0, 1.8, 2.3]) == pytest.approx(3 / 4)
        assert beats_in_mode([0.0]) == 0.0

    def test_a_phase_flipping_tracker_is_rebarred_on_the_beat(self):
        flipped = [self.BEATS[i] for i in (0, 4, 6, 10, 12, 16, 20, 22, 26, 28, 32, 36, 40, 44)]
        grid = Grid.of(self.BEATS, flipped)
        assert grid.bars_in_mode >= 0.95 and grid.beats_per_bar == 4
        assert grid.downbeats == self.BEATS[::4][:len(grid.downbeats)]

    def test_the_vote_keeps_the_phase_the_tracker_mostly_heard(self):
        offbeat = [self.BEATS[i] for i in (1, 5, 9, 11, 13, 17, 21, 25, 29)]
        assert Grid.of(self.BEATS, offbeat).downbeats[0] == self.BEATS[1]

    def test_an_unsteady_beat_keeps_the_trackers_bars(self):
        rubato = [0.0, 0.5, 1.0, 1.7, 2.1, 2.9, 3.3, 4.2, 4.6, 5.5, 5.9, 6.8]
        grid = Grid.of(rubato, rubato[::4])
        assert grid.downbeats == rubato[::4]


@LOCAL
@pytest.mark.local
class TestBeatThis:
    @pytest.mark.parametrize("bpm", (120, 180))
    def test_click_track_recovers_beats_and_downbeats(self, bpm):
        samples, beats, _ = click_track(bpm)
        got_beats, _ = beatmap.track_beat_this(samples, RATE)
        assert recall(beats, got_beats) >= 0.9
        assert abs(tempo_of(got_beats) / bpm - 1.0) <= 0.03

    def test_tracker_agrees_with_hand_taps_within_60ms(self):
        """Needs a human: tests/fixtures/metre_taps.json = {rel_path, beats, downbeats}."""
        fixture = Path("tests/fixtures/metre_taps.json")
        if not fixture.exists():
            pytest.skip("no hand-tapped fixture yet (BUILD.md item 6)")
        taps = json.loads(fixture.read_text(encoding="utf-8"))
        found = metre(Path(taps["rel_path"]), seed=0, rel_path=taps["rel_path"])
        assert recall(taps["beats"], found.beats) >= 0.8
        assert recall(taps["downbeats"], found.downbeats) >= 0.8


class TestMetreReport:
    def test_report_writes_one_metre_json_per_seed(self, tmp_path):
        from scripts.trailer import metre_report
        book = tmp_path / "1_book"
        music = book / "trailer" / "music"
        music.mkdir(parents=True)
        for seed in (7, 8):
            write_wav(music / f"cue-{seed}.wav", click_track(120, seconds=12.0)[0])
        (music / "cues.json").write_text("{}", encoding="utf-8")
        found = metre_report.report(music, book, track=track_autocorrelation)
        assert [m.seed for m in found] == [7, 8]
        loaded = Metre.model_validate_json((music / "metre-7.json").read_text(encoding="utf-8"))
        assert loaded.rel_path == "trailer/music/cue-7.wav"
        assert metre_report.music_dirs(book) == [music]
        assert "bars_in_mode" in metre_report.line_for(loaded)
