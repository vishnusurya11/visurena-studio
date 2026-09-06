"""The cut-opportunity map is measured on synthetic signals whose events are
KNOWN, so every detector is graded against an answer key rather than an ear.

A tone that changes timbre once has one section boundary; a level that
jumps 8 dB has one lift; a click has its accents on the clicks.  If a
detector finds more, it is inventing structure; if it finds less, it will
miss the real cue's.  Nothing here reads library/, loads a model or spends.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from studio import music_events as me
from studio.beatmap import RATE, envelope_of
from studio.music_events import CutMap
from studio.trailer_stage_spec import Metre
from test_metre import click_track

HOP_S = me.HOP / RATE
TOL = 0.06
"""One and a half onset frames: the tolerance `test_metre` grades beats at."""


# --- synthetic signals -------------------------------------------------------

def warm(seconds: float, amp: float = 0.1, freq: float = 220.0) -> np.ndarray:
    """Timbre A: a fundamental with two soft harmonics."""
    t = np.arange(int(RATE * seconds)) / RATE
    wave = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(4 * np.pi * freq * t)
            + 0.25 * np.sin(6 * np.pi * freq * t))
    return (amp * wave / 1.75).astype(np.float32)


def bright(seconds: float, amp: float = 0.1, freq: float = 311.0) -> np.ndarray:
    """Timbre B: a square wave, every odd harmonic present."""
    t = np.arange(int(RATE * seconds)) / RATE
    return (amp * np.sign(np.sin(2 * np.pi * freq * t))).astype(np.float32)


def with_noise(samples: np.ndarray, level: float = 0.002, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return samples + level * rng.standard_normal(len(samples)).astype(np.float32)


def stepped(seconds: float, at: float, step_db: float, amp: float = 0.1) -> np.ndarray:
    """A tone whose level jumps by `step_db` at `at` seconds."""
    tone = warm(seconds, amp)
    gain = np.ones(len(tone), dtype=np.float32)
    gain[int(at * RATE):] = 10 ** (step_db / 20)
    return tone * gain


def ramped(seconds: float, start: float, end: float, rise_db: float,
           amp: float = 0.03) -> np.ndarray:
    """A tone that climbs `rise_db` linearly between `start` and `end`."""
    tone = warm(seconds, amp)
    t = np.arange(len(tone)) / RATE
    db = np.clip((t - start) / (end - start), 0.0, 1.0) * rise_db
    return tone * (10 ** (db / 20)).astype(np.float32)


@pytest.fixture(scope="module")
def join():
    """15 s of timbre A, then 15 s of timbre B: one section boundary at 15."""
    samples = with_noise(np.concatenate([warm(15.0), bright(15.0)]))
    return samples, me.structure_features(samples)


@pytest.fixture(scope="module")
def click():
    samples, beats, downbeats = click_track(120, 30.0)
    return samples, beats, downbeats, me.onset_curve(samples)


def metre_of(beats, downbeats, seconds=30.0) -> Metre:
    return Metre(seed=1, rel_path="trailer/music/cue-1.flac", seconds=seconds, bpm=120.0,
                 bar=2.0, beats_per_bar=4, beats=beats, downbeats=downbeats,
                 bars_in_mode=1.0, grid="metre", fitness=1.0)


def near(t: float, targets, tol: float) -> bool:
    return any(abs(t - x) <= tol for x in targets)


# --- features ----------------------------------------------------------------

class TestFeatures:
    def test_coarse_pools_a_ramp_to_its_block_means(self):
        ramp = np.arange(12, dtype=float)[None, :]
        pooled = me.coarse(ramp, hop_s=0.05, frame=0.25)
        assert pooled.shape == (1, 2)
        assert pooled[0].tolist() == [2.0, 7.0]

    def test_coarse_length_is_the_floor_of_the_frame_count(self):
        assert me.coarse(np.ones((3, 23)), hop_s=0.05, frame=0.25).shape == (3, 4)

    def test_zscore_leaves_a_dead_dimension_small(self):
        """An empty chroma bin is numerical dust; blown up to unit variance it
        would outvote the dimensions that actually move."""
        feat = np.vstack([np.linspace(0, 10, 40), np.full(40, 1e-7) * np.arange(40)])
        z = me.zscore(feat)
        assert abs(z[0].std() - 1.0) < 1e-6
        assert np.abs(z[1]).max() < 0.05

    def test_structure_features_are_frames_of_the_cue(self, join):
        samples, feat = join
        assert feat.shape[0] == 19 + 12
        assert abs(feat.shape[1] - 30.0 / me.FRAME) <= 1

    def test_onset_curve_has_one_frame_per_hop(self, click):
        samples, _, _, strength = click
        assert abs(len(strength) - len(samples) / me.HOP) <= 2


# --- novelty -----------------------------------------------------------------

def block_features(sizes, seed=0):
    """Homogeneous blocks of a random unit vector each: an SSM of squares."""
    rng = np.random.default_rng(seed)
    cols = []
    for n in sizes:
        v = rng.standard_normal(8)
        cols.append(np.tile(v[:, None], (1, n)) + 0.01 * rng.standard_normal((8, n)))
    return np.hstack(cols)


class TestNovelty:
    def test_self_similarity_is_one_on_the_diagonal(self):
        s = me.self_similarity(block_features([10, 10]))
        assert s.shape == (20, 20)
        assert np.allclose(np.diag(s), 1.0)

    def test_two_repeated_blocks_give_a_two_by_two_structure(self):
        s = me.self_similarity(block_features([10, 10]))
        assert s[:10, :10].mean() > 0.95 and s[10:, 10:].mean() > 0.95
        assert abs(s[:10, 10:].mean()) < 0.7

    def test_checkerboard_quadrants_are_signed_and_sum_to_zero(self):
        k = me.checkerboard(4)
        assert k.shape == (8, 8)
        assert k[:4, :4].sum() > 0 and k[4:, 4:].sum() > 0
        assert k[:4, 4:].sum() < 0 and k[4:, :4].sum() < 0
        assert abs(k.sum()) < 1e-9

    def test_novelty_peaks_at_the_join_and_nowhere_else(self):
        nov = me.novelty(me.self_similarity(block_features([40, 40])), size=8)
        assert nov.shape == (80,) and 0.0 <= nov.min() and nov.max() == pytest.approx(1.0)
        assert abs(int(nov.argmax()) - 40) <= 1
        assert (nov > 0.5).sum() <= 3

    def test_boundaries_thin_two_peaks_inside_the_gap_to_one(self):
        curve = np.zeros(100)
        curve[[30, 42]] = [1.0, 0.8]
        assert [t for t, _ in me.boundaries(curve, 0.25, min_gap=5.0, prominence=0.15)] == [7.5]

    def test_boundaries_below_the_prominence_floor_are_none(self):
        curve = np.zeros(100)
        curve[30] = 0.1
        assert me.boundaries(curve, 0.25, min_gap=5.0, prominence=0.15) == []


class TestSections:
    def test_a_timbre_join_is_exactly_one_section_boundary(self, join):
        _, feat = join
        found = me.sections(feat, seconds=30.0)
        assert len(found) == 1
        assert abs(found[0][0] - 15.0) <= 0.5

    def test_the_kernel_scales_with_the_cue_inside_its_clip(self):
        assert me.section_kernel(30.0) == 12.0
        assert me.section_kernel(102.0) == 17.0
        assert me.section_kernel(240.0) == 24.0

    def test_phrases_find_the_join_too(self, join):
        _, feat = join
        assert any(abs(t - 15.0) <= 0.5 for t, _ in me.phrases(feat))


# --- envelope events ---------------------------------------------------------

class TestLevelSteps:
    def test_an_eight_db_step_up_is_one_lift(self):
        times, db = envelope_of(stepped(20.0, at=10.0, step_db=8.0))
        lifts, drops = me.level_steps(db)
        assert len(lifts) == 1 and drops == []
        assert abs(lifts[0][0] - 10.0) <= 0.1
        assert lifts[0][1] == pytest.approx(8.0, abs=0.5)

    def test_an_eight_db_step_down_is_one_drop(self):
        times, db = envelope_of(stepped(20.0, at=10.0, step_db=-8.0))
        lifts, drops = me.level_steps(db)
        assert lifts == [] and len(drops) == 1
        assert abs(drops[0][0] - 10.0) <= 0.1

    def test_a_four_db_step_is_neither(self):
        _, db = envelope_of(stepped(20.0, at=10.0, step_db=4.0))
        assert me.level_steps(db) == ([], [])


class TestDropouts:
    def test_three_seconds_of_silence_is_one_span(self):
        tone = warm(20.0)
        tone[int(8.0 * RATE):int(11.0 * RATE)] = 0.0
        times, db = envelope_of(tone)
        spans = me.dropout_spans(times, db)
        assert len(spans) == 1
        start, end = spans[0]
        assert abs(start - 8.0) <= 0.05 and abs((end - start) - 3.0) <= 0.05

    def test_a_steady_tone_has_none(self):
        times, db = envelope_of(warm(10.0))
        assert me.dropout_spans(times, db) == []


class TestSwells:
    def test_a_linear_ramp_is_one_swell(self):
        _, db = envelope_of(ramped(20.0, start=6.0, end=14.0, rise_db=18.0))
        found = me.swells(db)
        assert len(found) == 1
        start, end, rise = found[0]
        assert abs(start - 6.0) <= 1.0 and abs(end - 14.0) <= 1.0
        assert rise == pytest.approx(18.0, abs=2.0)

    def test_a_level_step_is_a_lift_and_no_swell(self):
        """A 6 dB step has flat floors either side; trough-to-peak spans 20 s
        but the climb itself is a second long."""
        _, db = envelope_of(stepped(20.0, at=10.0, step_db=8.0))
        assert me.swells(db) == []

    def test_trimmed_keeps_the_climb_and_drops_the_floors(self):
        level = np.concatenate([np.zeros(40), np.linspace(0, 10, 20), np.full(40, 10.0)])
        start, end = me.trimmed(level, 0, 99, margin=1.0)
        assert 40 <= start <= 42 and 57 <= end <= 60

    def test_a_flat_tone_has_no_swell(self):
        _, db = envelope_of(warm(20.0))
        assert me.swells(db) == []

    def test_smoothed_keeps_the_length_and_flattens_a_spike(self):
        db = np.zeros(200)
        db[100] = 20.0
        sm = me.smoothed(db)
        assert len(sm) == 200 and sm.max() <= 1.0 + 1e-9


class TestAccents:
    def test_onset_peaks_land_on_the_clicks(self, click):
        _, beats, _, strength = click
        peaks = me.onset_peaks(strength, HOP_S)
        assert 0.9 * len(beats) <= len(peaks) <= 1.1 * len(beats)
        # the audio switching on at 0 is an onset too; every later one is a click
        assert all(near(t, beats, TOL) for t, _ in peaks if t > 0.2)

    def test_accents_are_the_strongest_clicks_and_on_the_beat(self, click):
        _, beats, downbeats, strength = click
        found = me.accents(strength, HOP_S)
        on_beat = sum(near(t, beats, TOL) for t, _ in found) / len(found)
        assert on_beat >= 0.85
        assert all(near(t, downbeats, TOL) for t, _ in found)

    def test_accents_within_a_frame_of_a_beat_sit_on_the_beat(self):
        """librosa's onset frame lags the click by ~30 ms; the tracker's beat
        is the truer time when one is that close."""
        beats = [0.5, 1.0, 1.5]
        assert me.beat_accents([(1.028, 9.0), (1.3, 4.0)], beats) == [(1.0, 9.0), (1.3, 4.0)]

    def test_accents_are_the_top_tenth_with_a_floor(self):
        strength = np.zeros(4000)
        idx = np.arange(20, 4000, 40)
        strength[idx] = np.arange(1, len(idx) + 1, dtype=float)
        found = me.accents(strength, HOP_S)
        assert len(found) == max(me.ACCENT_FLOOR, len(idx) // 10)
        assert min(s for _, s in found) > len(idx) - len(found)


# --- housekeeping ------------------------------------------------------------

def ev(t, rank=2, kind="phrase", **kw):
    return dict(t=t, rank=rank, kind=kind, evidence=[kind], **kw)


class TestSnap:
    def test_an_event_inside_reach_moves_to_the_grid(self):
        out = me.snap([ev(46.25)], grid=[40.0, 46.20, 50.0])
        assert out[0]["t"] == 46.2
        assert any(e.startswith("snap") for e in out[0]["evidence"])

    def test_an_event_out_of_reach_stays(self):
        out = me.snap([ev(46.25)], grid=[45.35, 47.15])
        assert out[0]["t"] == 46.25

    def test_a_dropout_start_is_a_fact_of_the_envelope_and_stays(self):
        out = me.snap([ev(46.25, rank=3, kind="dropout", end=47.0)], grid=[46.20])
        assert out[0]["t"] == 46.25


class TestMerge:
    def test_two_events_within_reach_fold_into_the_higher_rank(self):
        out = me.merge([ev(52.40, rank=3, kind="hit"), ev(52.60, rank=2, kind="lift")])
        assert len(out) == 1
        assert out[0]["t"] == 52.4 and out[0]["kind"] == "hit"
        assert set(out[0]["evidence"]) >= {"hit", "lift"}

    def test_two_events_apart_stay_two(self):
        assert len(me.merge([ev(52.40), ev(53.00)])) == 2

    def test_the_higher_rank_keeps_its_time_even_when_later(self):
        out = me.merge([ev(52.40, rank=2, kind="lift"), ev(52.60, rank=3, kind="hit")])
        assert out[0]["t"] == 52.6

    def test_weight_orders_by_rank_then_structure_then_earliness(self):
        assert me.weight(ev(5.0, 3, "hit")) > me.weight(ev(1.0, 2, "section"))
        assert me.weight(ev(5.0, 3, "section")) > me.weight(ev(1.0, 3, "hit"))
        assert me.weight(ev(1.0, 3, "hit")) > me.weight(ev(5.0, 3, "hit"))

    def test_a_section_outranks_a_hit_at_the_same_rank(self):
        """The hit IS the section landing; folded the other way the plan
        would lose the movement door and keep an accent."""
        out = me.merge([ev(52.40, rank=3, kind="hit"), ev(52.60, rank=3, kind="section")])
        assert out[0]["kind"] == "section" and out[0]["t"] == 52.6
        out = me.merge([ev(52.40, rank=3, kind="section"), ev(52.60, rank=3, kind="dropout")])
        assert out[0]["kind"] == "section"


class TestAffordances:
    def test_an_event_affords_the_time_to_its_next_equal_or_higher(self):
        events = [ev(0.0, 3, "section"), ev(5.0, 2), ev(10.0, 3, "section")]
        out = me.affordances(events, seconds=30.0)
        assert [e["affords"] for e in out] == [10.0, 5.0, 20.0]


class TestHolds:
    def test_a_steady_gap_between_events_is_a_hold(self):
        times, db = envelope_of(warm(12.0))
        events = [ev(5.0), ev(10.0)]
        assert (5.0, 10.0) in me.hold_spans(events, times, db, seconds=12.0)

    def test_a_hump_inside_the_gap_is_no_hold(self):
        """A 6 dB hump two seconds long; one second of it smooths to 1.8 dB
        std and the shot can hold through it."""
        tone = warm(12.0)
        tone[int(6.5 * RATE):int(8.5 * RATE)] *= 10 ** (6 / 20)
        times, db = envelope_of(tone)
        assert (5.0, 10.0) not in me.hold_spans([ev(5.0), ev(10.0)], times, db, seconds=12.0)

    def test_span_stats_measure_level_rise_and_density(self):
        times, db = envelope_of(ramped(20.0, 6.0, 14.0, 18.0))
        stats = me.span_stats(6.0, 14.0, times, db, onset_times=[7.0, 9.0, 11.0, 13.0])
        assert stats["rises_db"] == pytest.approx(18.0, abs=2.5)
        assert stats["onset_density"] == pytest.approx(0.5)
        assert -40 < stats["level_db"] < 0


class TestHardOuts:
    def test_a_loud_bar_ending_on_an_accented_grid_point_ranks_first(self):
        tone = warm(12.0, amp=0.01)
        tone[int(8.0 * RATE):int(10.0 * RATE)] *= 20.0
        times, db = envelope_of(tone)
        strength = np.zeros(int(12.0 / HOP_S))
        strength[int(10.0 / HOP_S)] = 5.0
        found = me.hard_outs([4.0, 10.0], times, db, strength, HOP_S)
        assert found[0][0] == 10.0
        assert all(t != 4.0 for t, _ in found)

    def test_the_hard_out_is_the_best_candidate_before_the_title(self):
        candidates = [(130.35, 9.0), (126.2, 8.0), (48.9, 7.0)]
        assert me.hard_out_of(candidates, title_hit=128.95, seconds=144.5, grid=[]) == 126.2

    def test_without_a_candidate_the_tail_is_the_default_on_the_grid(self):
        grid = [0.5 + 2.0 * k for k in range(15)]
        assert me.hard_out_of([], title_hit=None, seconds=30.0, grid=grid) == 24.5


class TestKnownEvents:
    def test_a_known_event_keeps_its_time_and_kind_and_takes_the_detectors_as_witnesses(self):
        """MEASURED (run 14, cutmap-1001): the arc's stop at 76.399 s merged
        under a detected 'section' (equal rank, more structural), so the ask's
        stop -- a dropout -- went unmeasured.  The arc's event wins: it is the
        cut, the detector only saw it."""
        known = [me.event(15.0, "dropout", "arc:stop", end=20.0)]
        found = [me.event(15.1, "section", "novelty"), me.event(3.0, "hit", "onset")]
        out = me.with_known(found, known)
        assert [(e["t"], e["kind"]) for e in out] == [(3.0, "hit"), (15.0, "dropout")]
        assert out[1]["evidence"] == ["arc:stop", "novelty"] and out[1]["end"] == 20.0
        assert found[0]["evidence"] == ["novelty"] and known[0]["evidence"] == ["arc:stop"]

    def test_the_known_stop_is_the_hard_out(self):
        samples, beats, downbeats = click_track(120, 30.0)
        known = [me.event(downbeats[9], "dropout", "arc:stop", end=downbeats[12]),
                 me.event(downbeats[12], "hit", "arc:title_hit")]
        raw = me.cut_map(samples, RATE, metre_of(beats, downbeats), known=known)
        assert raw["hard_out"] == round(downbeats[9], 3)
        stop = [e for e in raw["events"] if e["evidence"][0] == "arc:stop"]
        assert len(stop) == 1 and stop[0]["kind"] == "dropout" and stop[0]["end"] == downbeats[12]
        assert me.known_hard_out([]) is None


# --- the map -----------------------------------------------------------------

class TestCutMap:
    @pytest.fixture(scope="class")
    def cue(self):
        samples, beats, downbeats = click_track(120, 30.0)
        samples = samples + np.concatenate([warm(15.0, 0.05), bright(15.0, 0.05)])
        return me.cut_map(samples, RATE, metre_of(beats, downbeats)), downbeats

    def test_the_map_round_trips_through_the_contract(self, cue):
        raw, _ = cue
        text = json.dumps(raw)
        model = CutMap.model_validate_json(text)
        assert model.model_dump() == raw
        assert model.seconds == pytest.approx(30.0, abs=0.01)

    def test_events_are_sorted_and_ranked(self, cue):
        raw, _ = cue
        ts = [e["t"] for e in raw["events"]]
        assert ts == sorted(ts)
        assert {e["rank"] for e in raw["events"]} <= {1, 2, 3}
        assert all(e["evidence"] for e in raw["events"])

    def test_the_join_is_a_section_event_on_a_downbeat(self, cue):
        raw, downbeats = cue
        sections = [e for e in raw["events"] if e["kind"] == "section"]
        assert len(sections) == 1
        assert abs(sections[0]["t"] - 15.0) <= 0.75
        assert near(sections[0]["t"], downbeats, 1e-6)

    def test_the_hard_out_sits_inside_the_cue_on_the_grid(self, cue):
        raw, downbeats = cue
        assert 0.6 * raw["seconds"] <= raw["hard_out"] < raw["seconds"]
        assert near(raw["hard_out"], downbeats + [e["t"] for e in raw["events"]], 1e-6)

    def test_every_event_sits_on_a_beat(self, cue):
        """Clicks every half second: with accents on the beat, no event is
        left between two grid points."""
        raw, _ = cue
        beats = [0.5 + 0.5 * k for k in range(59)]
        assert all(near(e["t"], beats, 1e-6) for e in raw["events"])

    def test_a_level_step_at_the_join_is_no_swell_span(self, cue):
        raw, _ = cue
        assert [s for s in raw["spans"] if s["kind"] == "swell"] == []

    def test_a_map_with_unsorted_events_is_refused(self):
        with pytest.raises(ValueError, match="sorted"):
            CutMap(events=[me.CutEvent(t=5.0, rank=2, kind="phrase", evidence=["x"]),
                           me.CutEvent(t=1.0, rank=2, kind="phrase", evidence=["x"])],
                   spans=[], hard_out=8.0, title_hit=None, seconds=10.0)

    def test_a_hard_out_past_the_end_is_refused(self):
        with pytest.raises(ValueError, match="hard_out"):
            CutMap(events=[], spans=[], hard_out=12.0, title_hit=None, seconds=10.0)
