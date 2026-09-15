r"""A generated bed has silence at its ends, and `compose` laid it anyway.

MEASURED on episode 6's five delivered tone files (1-second RMS, dead = under
-60 dBFS):

    plain      26.56s   dead at 24, 25                      (2 s tail)
    light      41.12s   dead at 35-40                       (6 s tail)
    uneasy     31.24s   dead at 0-4 and 18-21               (5 s HEAD, 4 s middle)
    grave      31.16s   dead at 26-30                       (5 s tail)
    thrilling  23.36s   dead at 18                          (1 s middle)

`compose` laid each file from sample 0 for the length of its span. `uneasy` is
used TWICE in episode 6, so both of its spans open with five seconds of nothing.
The delivered `bed.wav` is under -60 dBFS at 57-66 s, 80-83 s, 117-125 s and
154 s -- **24 of 159.6 seconds, 15 % of the episode, with no music at all** --
and two of the five "crossfades" are one file's silent tail fading into
another's silent head.

`is_dead` does not see this: it measures the WHOLE generation against its
target, and a file with a six-second silent tail still integrates on target.
A per-file loudness check cannot find a hole inside the file.

AND THE SECOND BUG, in the same four lines. `compose` did
`audio.mean(axis=1)` -- mono-summing a STEREO source. The loss is unequal
because it depends on each take's L/R correlation:

    plain      -30.92 stereo -> -36.06 mono   (-5.14, corr 0.119)
    light      -30.47 -> -34.11               (-3.65, corr 0.757)
    uneasy     -28.82 -> -32.20               (-3.38, corr 0.873)
    grave      -28.95 -> -32.89               (-3.95, corr 0.655)
    thrilling  -27.25 -> -30.56               (-3.30, corr 0.796)

So every tone shipped 3.3-5.1 dB under the level it was verified at, the
designed 3.5 LU arc from `plain` to `thrilling` became 5.5 LU, and episode 6 is
the only one of the six with a mono bed (L-R vs mid: -37.0 dB against -8.7 to
-19.2 for episodes 1-5).
"""
import numpy as np
import pytest
import soundfile as sf

from studio.episode_bed import DEAD_DBFS, Span, compose, trim_to_music


def a_tone(path, seconds: float, head: float = 0.0, tail: float = 0.0,
           rate: int = 48000, channels: int = 2):
    """A stereo sine with `head` and `tail` seconds of digital silence."""
    n = int(seconds * rate)
    t = np.arange(n) / rate
    one = (0.2 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    one[:int(head * rate)] = 0.0
    if tail:
        one[-int(tail * rate):] = 0.0
    sf.write(str(path), np.stack([one, one * 0.9], axis=1)[:, :channels], rate)
    return path


def test_a_silent_head_is_trimmed(tmp_path):
    got = trim_to_music(a_tone(tmp_path / "a.wav", 20.0, head=5.0), DEAD_DBFS)
    assert 14.5 < len(got[0]) / got[1] < 15.5


def test_a_silent_tail_is_trimmed(tmp_path):
    got = trim_to_music(a_tone(tmp_path / "b.wav", 20.0, tail=6.0), DEAD_DBFS)
    assert 13.5 < len(got[0]) / got[1] < 14.5


def test_a_file_that_is_all_music_is_untouched(tmp_path):
    got = trim_to_music(a_tone(tmp_path / "c.wav", 12.0), DEAD_DBFS)
    assert 11.8 < len(got[0]) / got[1] < 12.2


def test_the_stereo_image_survives(tmp_path):
    got = trim_to_music(a_tone(tmp_path / "d.wav", 10.0), DEAD_DBFS)
    assert got[0].ndim == 2 and got[0].shape[1] == 2


def test_a_mono_source_stays_mono(tmp_path):
    got = trim_to_music(a_tone(tmp_path / "e.wav", 10.0, channels=1), DEAD_DBFS)
    assert got[0].shape[1] == 1


# ---- and the laid bed has no hole in it -------------------------------------

def loudest_gap(path, window: float = 1.0) -> float:
    audio, rate = sf.read(str(path), dtype="float32", always_2d=True)
    mono = audio.mean(axis=1)
    worst = 0.0
    for i in range(int(len(mono) / rate / window)):
        block = mono[int(i * window * rate):int((i + 1) * window * rate)]
        worst = min(worst, 20 * np.log10(max(1e-9, float(np.sqrt((block ** 2).mean())))))
    return worst


def test_a_bed_laid_from_a_silent_headed_tone_has_no_hole(tmp_path):
    """`uneasy` opens with five seconds of nothing and is used twice."""
    files = {"uneasy": a_tone(tmp_path / "uneasy.wav", 31.0, head=5.0),
             "plain": a_tone(tmp_path / "plain.wav", 27.0, tail=2.0)}
    cut = [Span(0.0, 20.0, "plain"), Span(20.0, 45.0, "uneasy")]
    out = compose(cut, files, tmp_path / "bed.wav")
    assert loudest_gap(out) > DEAD_DBFS


def test_the_laid_bed_keeps_two_channels(tmp_path):
    files = {"plain": a_tone(tmp_path / "p.wav", 20.0)}
    out = compose([Span(0.0, 12.0, "plain")], files, tmp_path / "bed.wav")
    assert sf.read(str(out), always_2d=True)[0].shape[1] == 2


def test_the_dead_floor_is_the_measured_one():
    """A 1 s window under this is a hole a listener hears as a dropout."""
    assert DEAD_DBFS == -60.0
