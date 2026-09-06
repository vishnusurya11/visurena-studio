"""Trailer punctuation, synthesised and deterministic: a sub impact on the
ask's landmarks, a noise riser into every hole, a soft ceiling on the sum.
Every test measures the synthesised sound itself; nothing is decoded or spent."""
from __future__ import annotations

import numpy as np

from studio import cue_punct
from studio.beatmap import RATE, envelope_of
from studio.cue_ask import HOLE_BARS
from studio.cue_plan import AskedEvent, CueAsk

BAR = 2.0


def rms_db(x: np.ndarray) -> float:
    return 20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-12)


def centroid_hz(x: np.ndarray, rate: int) -> float:
    spectrum = np.abs(np.fft.rfft(x))
    freqs = np.fft.rfftfreq(len(x), 1 / rate)
    return float((spectrum * freqs).sum() / spectrum.sum())


def sub_share(x: np.ndarray, rate: int, below_hz: float = 120.0) -> float:
    power = np.abs(np.fft.rfft(x)) ** 2
    freqs = np.fft.rfftfreq(len(x), 1 / rate)
    return float(power[freqs < below_hz].sum() / power.sum())


def test_impact_is_a_short_decaying_sub_hit():
    hit = cue_punct.impact(RATE)
    assert len(hit) == int(cue_punct.IMPACT_SECONDS * RATE)
    assert np.abs(hit).max() <= 1.0
    assert sub_share(hit, RATE) > 0.6
    assert rms_db(hit[: RATE // 4]) > rms_db(hit[-RATE // 4:]) + 12


def test_impact_is_deterministic():
    assert np.array_equal(cue_punct.impact(RATE), cue_punct.impact(RATE))


def test_riser_swells_and_brightens_to_its_end():
    rise = cue_punct.riser(RATE, 2.0)
    assert len(rise) == 2 * RATE
    quarters = [rms_db(part) for part in np.array_split(rise, 4)]
    assert all(b > a for a, b in zip(quarters, quarters[1:]))
    assert centroid_hz(rise[-RATE // 2:], RATE) > centroid_hz(rise[RATE // 4: RATE // 2], RATE)


def test_soft_knee_leaves_the_bed_alone_and_bends_the_peaks():
    x = np.array([0.0, 0.5, -0.8, 1.6, -2.0], dtype=np.float32)
    y = cue_punct.soft_knee(x)
    assert np.allclose(y[:3], x[:3])
    assert 0.85 < y[3] <= 1.0 and -1.0 <= y[4] < -0.85
    assert np.all(np.abs(y) <= 1.0)


def test_mix_at_adds_at_the_second_and_clips_to_the_bed():
    bed = np.zeros(RATE, dtype=np.float32)
    out = cue_punct.mix_at(bed, RATE, np.ones(100, dtype=np.float32), 0.5)
    at = RATE // 2
    assert out[at - 1] == 0.0 and out[at] == 1.0 and out[at + 99] == 1.0 and out[at + 100] == 0.0
    tail = cue_punct.mix_at(np.zeros(RATE, dtype=np.float32), RATE, np.ones(RATE, dtype=np.float32), 0.75)
    assert len(tail) == RATE and tail[-1] == 1.0


def test_mix_at_reaches_both_channels_of_a_stereo_bed():
    bed = np.zeros((RATE, 2), dtype=np.float32)
    out = cue_punct.mix_at(bed, RATE, np.ones(10, dtype=np.float32), 0.0)
    assert out[0].tolist() == [1.0, 1.0]


def test_punctuate_lands_an_impact_on_the_hit_and_title_bars_and_a_riser_into_the_hole():
    ask = CueAsk.for_bars(16, bar=BAR, bpm=120)
    ask = ask.model_copy(update={"events": ask.events + [AskedEvent(kind="hole", bar=8)]})
    downbeats = [i * BAR for i in range(16)]
    bed = np.zeros(int(16 * BAR * RATE), dtype=np.float32)
    out = cue_punct.punctuate(bed, RATE, downbeats, ask)
    times, db = envelope_of(out)
    def level(bar, span=0.5):
        return float(np.max(db[(times >= bar * BAR) & (times < bar * BAR + span)]))
    hit, title, hole = 4, ask.title_bar, 8
    assert level(hit) > -20 and level(title) > -20 and level(hole + HOLE_BARS) > -20
    assert level(hole - 0.25) > level(hole - 1.5) + 10        # the riser swells into the hole
    assert level(2) < -60                                    # an ordinary bar is untouched


def test_punctuate_keeps_the_bed_under_the_ceiling():
    ask = CueAsk.for_bars(16, bar=BAR, bpm=120)
    downbeats = [i * BAR for i in range(16)]
    bed = 0.95 * np.sign(np.sin(np.arange(int(16 * BAR * RATE)) * 0.3)).astype(np.float32)
    out = cue_punct.punctuate(bed, RATE, downbeats, ask)
    assert np.abs(out).max() <= 1.0
    assert abs(rms_db(out[: RATE]) - (rms_db(bed[: RATE]) - cue_punct.BED_TRIM_DB)) < 0.5
