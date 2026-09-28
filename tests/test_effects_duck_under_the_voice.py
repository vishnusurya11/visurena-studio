"""Effects and ambience duck under every line, as the bed does.

OWNER 2026-09-27, on ep13 master_iter8: "the sound effects are good but too
loud."  Measured (debate10 sound reports): the mix ducked only the bed; 5 of
the 8 effects and every ambience played at full level under narration, and
speech sat 9.8 LU over the gaps against 11.3-16.5 on WotW ep10-12 and
Sherlock.  The duck is done at MIX time on the cached cue files, so no cue is
rendered again.
"""
from pathlib import Path

from studio import episode_sound


def test_a_line_window_is_shifted_into_the_cue_own_clock():
    got = episode_sound.cue_windows([(10.0, 12.0)], when=8.0, depth=6.0)
    assert got == [(2.0, 4.0, 6.0)]


def test_an_effect_ducks_deeper_than_an_ambience():
    assert episode_sound.duck_depth(Path("shot03_b709a542.wav")) == episode_sound.EFFECT_DUCK_DB
    assert episode_sound.duck_depth(Path("amb_1b73d72c_0028.58.wav")) == episode_sound.AMBIENCE_DUCK_DB
    assert episode_sound.EFFECT_DUCK_DB > episode_sound.AMBIENCE_DUCK_DB > 0


def test_every_cue_is_written_ducked_and_keeps_its_time(tmp_path):
    ran = []
    cues = [(8.0, tmp_path / "shot03_x.wav"), (0.0, tmp_path / "amb_y.loop.wav")]
    got = episode_sound.ducked(cues, [(10.0, 12.0)], tmp_path, run=lambda args: ran.append(args))
    assert [w for w, _ in got] == [8.0, 0.0]
    assert all(p.name.endswith(".ducked.wav") for _, p in got)
    assert len(ran) == 2 and "volume=" in " ".join(ran[0])


def test_a_cue_no_line_touches_is_laid_as_it_is(tmp_path):
    cues = [(100.0, tmp_path / "shot24_z.wav")]
    got = episode_sound.ducked(cues, [(10.0, 12.0)], tmp_path, run=lambda args: None)
    assert got == cues
