r"""Five tones become one continuous bed, or the viewer hears five edits.

`episode_bed.bed_plan` says WHICH tone plays WHEN. This is the other half: the
generated files laid into one track of exactly the episode's length, each span
at its own level, with `CROSSFADE_S` of overlap at every join.

TWO THINGS A NAIVE CONCATENATION GETS WRONG, and both are audible:

  * a butt-joint between two beds is a click and a sudden change of room, which
    a viewer reads as a mistake rather than as scoring. Two seconds is under a
    violin phrase and well over a click.
  * a tone used twice -- episode 6 uses `uneasy` for shots 10-14 and again for
    20-22 -- must be the SAME generation laid twice. Generating it twice pays
    the GPU twice and returns two different performances, which is heard as two
    unrelated pieces of music arriving for no reason.

The composer takes files that are already at their own tone's level, so it only
places and fades; it never re-normalises. Levels are `episode_bed.TONES`.
"""
import math
import wave

import pytest

from studio.episode_bed import CROSSFADE_S, Span
from studio.episode_bed import compose


RATE = 24000


def a_wav(path, seconds: float, hz: float = 220.0, amp: float = 0.25):
    """A plain sine, so a fade is visible in the samples."""
    frames = int(seconds * RATE)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(b"".join(
            int(amp * 32767 * math.sin(2 * math.pi * hz * n / RATE)).to_bytes(
                2, "little", signed=True) for n in range(frames)))
    return path


def samples(path):
    with wave.open(str(path), "rb") as got:
        raw = got.readframes(got.getnframes())
    return [int.from_bytes(raw[i:i + 2], "little", signed=True)
            for i in range(0, len(raw), 2)]


def test_the_track_is_exactly_the_episode_long(tmp_path):
    files = {"plain": a_wav(tmp_path / "plain.wav", 20.0),
             "grave": a_wav(tmp_path / "grave.wav", 20.0, hz=110.0)}
    cut = [Span(0.0, 10.0, "plain"), Span(10.0, 18.0, "grave")]
    out = compose(cut, files, tmp_path / "bed.wav", rate=RATE)
    with wave.open(str(out), "rb") as got:
        assert abs(got.getnframes() / RATE - 18.0) < 0.05


def test_one_span_is_just_that_tone(tmp_path):
    files = {"plain": a_wav(tmp_path / "plain.wav", 20.0)}
    out = compose([Span(0.0, 12.0, "plain")], files, tmp_path / "bed.wav", rate=RATE)
    with wave.open(str(out), "rb") as got:
        assert abs(got.getnframes() / RATE - 12.0) < 0.05


def test_the_outgoing_tone_fades_across_the_seam(tmp_path):
    """Measured against SILENCE, because two sines at one frequency are
    perfectly correlated and an equal-power crossfade sums them to a bump --
    which is the right behaviour for two real beds and a useless test."""
    files = {"a": a_wav(tmp_path / "a.wav", 30.0, hz=220.0),
             "b": a_wav(tmp_path / "b.wav", 30.0, amp=0.0)}
    cut = [Span(0.0, 10.0, "a"), Span(10.0, 20.0, "b")]
    out = compose(cut, files, tmp_path / "bed.wav", rate=RATE)
    got = samples(out)
    mid = max(abs(v) for v in got[int(4 * RATE):int(4 * RATE) + 2000])
    seam = max(abs(v) for v in got[int(9.9 * RATE):int(10.1 * RATE)])
    after = max(abs(v) for v in got[int(11 * RATE):int(11 * RATE) + 2000])
    assert seam < mid, "no fade: the outgoing tone is still at full level at the seam"
    assert after == 0, "the outgoing tone runs past its own crossfade"


def test_the_fade_is_the_documented_length(tmp_path):
    files = {"a": a_wav(tmp_path / "a.wav", 30.0, hz=220.0),
             "b": a_wav(tmp_path / "b.wav", 30.0, amp=0.0)}
    out = compose([Span(0.0, 10.0, "a"), Span(10.0, 20.0, "b")],
                  files, tmp_path / "bed.wav", rate=RATE)
    got = samples(out)
    # the outgoing tone starts ducking CROSSFADE_S BEFORE the seam
    before = max(abs(v) for v in got[int((10 - CROSSFADE_S - 0.3) * RATE):
                                     int((10 - CROSSFADE_S - 0.1) * RATE)])
    inside = max(abs(v) for v in got[int((10 - CROSSFADE_S / 2) * RATE):
                                     int((10 - CROSSFADE_S / 2 + 0.2) * RATE)])
    assert inside < before


def test_a_tone_used_twice_is_read_from_one_file(tmp_path):
    """Episode 6's `uneasy` covers shots 10-14 and 20-22."""
    files = {"a": a_wav(tmp_path / "a.wav", 40.0), "b": a_wav(tmp_path / "b.wav", 40.0)}
    cut = [Span(0.0, 10.0, "a"), Span(10.0, 20.0, "b"), Span(20.0, 30.0, "a")]
    out = compose(cut, files, tmp_path / "bed.wav", rate=RATE)
    with wave.open(str(out), "rb") as got:
        assert abs(got.getnframes() / RATE - 30.0) < 0.05


def test_a_span_longer_than_its_file_is_filled(tmp_path):
    """`bed_plan` asks for enough seconds, but a short generation must not
    leave a hole of digital silence in the middle of an episode."""
    files = {"a": a_wav(tmp_path / "a.wav", 5.0)}
    out = compose([Span(0.0, 20.0, "a")], files, tmp_path / "bed.wav", rate=RATE)
    got = samples(out)
    middle = got[int(12 * RATE):int(12 * RATE) + 2000]
    assert max(abs(v) for v in middle) > 0, "a hole of silence in the bed"


# ---- refusals ---------------------------------------------------------------

def test_a_missing_tone_file_is_refused(tmp_path):
    files = {"a": a_wav(tmp_path / "a.wav", 20.0)}
    with pytest.raises(ValueError, match="grave"):
        compose([Span(0.0, 10.0, "grave")], files, tmp_path / "bed.wav", rate=RATE)


def test_no_spans_at_all_is_refused(tmp_path):
    with pytest.raises(ValueError, match="span"):
        compose([], {}, tmp_path / "bed.wav", rate=RATE)


def test_the_crossfade_is_the_documented_one():
    assert CROSSFADE_S == 2.0
