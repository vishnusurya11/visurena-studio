r"""A bed shorter than its span is LOOPED, and a loop has a seam.

MEASURED on episode 10's master (analyst F).  Four of six spans loop because
ACE-Step stops early and pads silence.  `compose` looped with `np.tile` -- a
butt joint, no fade.  Five seams hid under speech; the sixth sat at 167.83 s in
the only eleven seconds of the episode with nobody talking: `uneasy`'s trimmed
end is its eight-second decrescendo, the tile restarts it at its opening bar,
and the master steps from -36.1 to -27.1 LUFS across the joint (spectral flux
eleven times the local median).  The listener hears a violin fade to nothing,
restart, and fade again, over three pictures.

So every tile boundary gets the same equal-power crossfade the spans get.

AND THE SECOND FAULT: `light` came back as a 27.7 s file with 10.4 s of music in
it (-76 dBFS from 11 s on) and integrated -30.5 LUFS against a -30.5 target --
`is_dead` measures the whole file and cannot see a silent tail.  Laid three
times over shots 23-27.  A tone whose LIVE music is under LIVE_SHARE of what
the span wants is a failed generation, and re-rolled like an empty one.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from studio import episode_bed
from studio.episode_bed import CROSSFADE_S, Span, compose, looped

RATE = 48000


def decaying_tone(path: Path, seconds: float = 5.0, top: float = 0.5, bottom: float = 0.05, hz: float = 220.0):
    """A sine that fades 20 dB across the file: loop it and the joint is a cliff."""
    t = np.arange(int(seconds * RATE)) / RATE
    env = top * (bottom / top) ** (t / seconds)
    one = (env * np.sin(2 * np.pi * hz * t)).astype(np.float32)
    sf.write(str(path), np.stack([one, one], axis=1), RATE)
    return path


def rms_steps_db(mono: np.ndarray, window_s: float = 0.05) -> list[float]:
    """The dB change between every pair of consecutive 50 ms windows."""
    step = int(window_s * RATE)
    levels = [20 * np.log10(max(1e-9, float(np.sqrt((mono[i:i + step] ** 2).mean()))))
              for i in range(0, len(mono) - step, step)]
    return [abs(b - a) for a, b in zip(levels, levels[1:])]


def test_a_tile_boundary_has_no_step(tmp_path):
    files = {"uneasy": decaying_tone(tmp_path / "u.wav")}
    out = compose([Span(0.0, 20.0, "uneasy")], files, tmp_path / "bed.wav", rate=RATE)
    audio, _ = sf.read(str(out), dtype="float32", always_2d=True)
    assert max(rms_steps_db(audio.mean(axis=1))) < 3.0


def test_np_tile_would_have_stepped_twenty_db(tmp_path):
    """The control: the fault this test exists for is real at the joint."""
    audio, _ = sf.read(str(decaying_tone(tmp_path / "u.wav")), dtype="float32", always_2d=True)
    tiled = np.tile(audio, (4, 1))[:20 * RATE].mean(axis=1)
    assert max(rms_steps_db(tiled)) > 15.0


def test_looped_returns_exactly_what_was_asked_for():
    audio = np.ones((3 * RATE, 2), dtype=np.float32)
    assert len(looped(audio, 10 * RATE, int(CROSSFADE_S * RATE))) == 10 * RATE
    assert len(looped(audio, RATE, int(CROSSFADE_S * RATE))) == RATE


def test_a_file_long_enough_is_not_looped():
    audio = np.arange(5 * RATE, dtype=np.float32).reshape(-1, 1)
    got = looped(audio, 4 * RATE, int(CROSSFADE_S * RATE))
    assert np.array_equal(got, audio[:4 * RATE])


def test_the_loop_is_at_full_level_across_the_joint():
    """Equal-power: a constant tone looped stays within a dB of itself everywhere."""
    audio = np.full((3 * RATE, 1), 0.5, dtype=np.float32)
    got = looped(audio, 10 * RATE, int(CROSSFADE_S * RATE))
    assert float(got.min()) > 0.5 * 0.7 and float(got.max()) <= 0.5 * 1.42


# ---- a mostly-silent tone is a failed generation ------------------------------

def half_silent(path: Path, seconds: float = 27.7, live: float = 6.0):   # under LIVE_SHARE: an empty, not a short loop
    t = np.arange(int(seconds * RATE)) / RATE
    one = (0.2 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    one[int(live * RATE):] = 0.0
    sf.write(str(path), np.stack([one, one], axis=1), RATE)
    return path


def test_live_seconds_is_the_music_not_the_file(tmp_path):
    assert 10.0 < episode_bed.live_seconds(half_silent(tmp_path / "light.wav", live=10.4)) < 10.8


def test_the_measured_light_tone_is_short():
    from scripts.episode import assemble

    # ep11: ACE-Step gave 8.6-11.2 s for a 26 s ask on six seeds; with crossfaded
    # loops a tone a third as long as its span is laid, an emptier one is refused
    assert not assemble.is_short(10.4, want=27.7)
    assert assemble.is_short(6.0, want=27.7)
    assert not assemble.is_short(23.4, want=26.7), "uneasy delivered 88 % and is fine"
    assert assemble.LIVE_SHARE == 0.30
    assert not assemble.is_short(assemble.LIVE_SHARE * 20.0, want=20.0) and assemble.is_short(assemble.LIVE_SHARE * 20.0 - 0.01, want=20.0)


def test_a_short_tone_is_re_rolled_under_the_same_bound(tmp_path, monkeypatch):
    from scripts.episode import assemble

    served = [half_silent(tmp_path / "roll1.wav"), half_silent(tmp_path / "roll2.wav", live=27.0)]
    seeds = []

    def fake_run(workflow, values, timeout=0):
        seeds.append(values["seed"])
        return [served.pop(0)]

    monkeypatch.setattr(assemble, "run", fake_run)
    monkeypatch.setattr(assemble, "integrated", lambda p: -30.5)
    monkeypatch.setattr(assemble, "level", lambda p, t: p)
    room = tmp_path / "audio"; room.mkdir()
    got = assemble.one_tone(room, 10, "light", 27.7, "acestep")
    assert got == room / "bed_light.wav" and episode_bed.live_seconds(got) > 26.0
    assert len(seeds) == 2 and seeds[0] != seeds[1]
    assert (room / "bed_light.short1.wav").exists(), "the refused roll is kept, named for why"


def test_a_tone_short_every_time_stops_the_assemble(tmp_path, monkeypatch):
    import pytest

    from scripts.episode import assemble

    monkeypatch.setattr(assemble, "run", lambda w, v, timeout=0: [half_silent(tmp_path / f"r{v['seed']}.wav")])
    monkeypatch.setattr(assemble, "integrated", lambda p: -30.5)
    monkeypatch.setattr(assemble, "level", lambda p, t: p)
    room = tmp_path / "audio"; room.mkdir()
    with pytest.raises(SystemExit, match="light"):
        assemble.one_tone(room, 10, "light", 27.7, "acestep")
    assert len(list(room.glob("bed_light.short*.wav"))) == assemble.BED_ROLLS
