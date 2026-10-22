r"""Every tone of the toned bed is LISTENED to before it is laid, and one that sings is re-rolled.

`bed()` -- the old single bed -- runs `bed_gate.refuse` on what it made.  The
production path is `toned_bed` -> `one_tone`, and it only re-rolled a tone that
came back empty or short: nothing on it ever listened for words (fleet A
skeptic M1, 2026-10-22, `scripts/episode/assemble.py:397-428`).  The module's
own docstring promised `bed_sings()` "VERIFIED per bed", and no such function
existed.

MEASURED on the fleet A bench B1 (2026-10-22), the same `bed_gate.sings_text`
with the clip's own seconds: production ACE-Step 1.5 tones refused 0 of 8, ACE
XL turbo 0 of 8, YuE2 native no-ABC 1 of 10 (`C_S1t_s101`).  So the ear costs
no false refusal on the engine that ships, and it catches the one that sings.

A sung tone is a failed generation like an empty one: kept on disk named for
why (`bed_<tone>.sings<roll>.wav`, which `bed_seed` already counts), re-rolled
under the same `BED_ROLLS` bound, and the assemble stops if every roll sings.
An ear that cannot be reached is UNVERIFIED and said out loud, as `bed()` says it.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

RATE = 48000
VERSE = ("oh my love the river runs so cold tonight and every light along the shore "
         "is calling out your name")


def tone(path: Path, seconds: float = 27.7) -> Path:
    """A tone with music end to end: never empty, never short."""
    t = np.arange(int(seconds * RATE)) / RATE
    one = (0.2 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    sf.write(str(path), np.stack([one, one], axis=1), RATE)
    return path


def quiet_ear(_path: Path) -> str:
    return "Thank you."


def singing_ear(_path: Path) -> str:
    return VERSE


def deaf_ear(_path: Path) -> str:
    raise RuntimeError("no transcriber reachable")


def test_a_tone_that_sings_is_a_fault(tmp_path):
    from scripts.episode import assemble

    out = tone(tmp_path / "bed_light.wav")
    assert assemble.tone_fault(out, -30.5, -30.5, 27.7, ear=singing_ear) == "sings"


def test_an_instrumental_tone_is_no_fault(tmp_path):
    from scripts.episode import assemble

    out = tone(tmp_path / "bed_light.wav")
    assert assemble.tone_fault(out, -30.5, -30.5, 27.7, ear=quiet_ear) == ""


def test_an_unheard_tone_is_laid_but_said_to_be_unverified(tmp_path, capsys):
    """Being unable to listen is not a pass and not a refusal: it is said."""
    from scripts.episode import assemble

    out = tone(tmp_path / "bed_light.wav")
    assert assemble.tone_fault(out, -30.5, -30.5, 27.7, ear=deaf_ear) == ""
    assert "UNVERIFIED" in capsys.readouterr().out


def fake_engine(monkeypatch, tmp_path, seeds: list[int]):
    from scripts.episode import assemble

    def fake_run(workflow, values, timeout=0):
        seeds.append(values["seed"])
        return [tone(tmp_path / f"r{values['seed']}.wav")]

    monkeypatch.setattr(assemble, "run", fake_run)
    monkeypatch.setattr(assemble, "integrated", lambda p: -30.5)
    monkeypatch.setattr(assemble, "level", lambda p, t: p)


def test_a_singing_tone_is_re_rolled_and_kept_named_for_why(tmp_path, monkeypatch):
    from scripts.episode import assemble

    seeds: list[int] = []
    fake_engine(monkeypatch, tmp_path, seeds)
    heard = [VERSE, "Thank you."]
    room = tmp_path / "audio"; room.mkdir()
    got = assemble.one_tone(room, 10, "light", 27.7, "acestep", ear=lambda p: heard.pop(0))
    assert got == room / "bed_light.wav"
    assert len(seeds) == 2 and seeds[0] != seeds[1]
    assert (room / "bed_light.sings1.wav").exists()


def test_a_tone_that_sings_every_roll_stops_the_assemble(tmp_path, monkeypatch):
    from scripts.episode import assemble

    fake_engine(monkeypatch, tmp_path, [])
    room = tmp_path / "audio"; room.mkdir()
    with pytest.raises(SystemExit, match="sing"):
        assemble.one_tone(room, 10, "light", 27.7, "acestep", ear=singing_ear)
    assert len(list(room.glob("bed_light.sings*.wav"))) == assemble.BED_ROLLS


def test_a_re_run_after_a_sung_tone_moves_the_seed(tmp_path):
    """`bed_seed` reads refusals off the disk; a sung tone's name must be one it counts."""
    from scripts.episode import assemble

    room = tmp_path / "audio"; room.mkdir()
    before = assemble.bed_seed(room / "bed_light.wav", 10)
    (room / "bed_light.sings1.wav").write_bytes(b"")
    assert assemble.bed_seed(room / "bed_light.wav", 10) != before
