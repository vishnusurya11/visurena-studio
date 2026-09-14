"""A staged picture is named by its BYTES, so a render can never be given a
different picture than the one it asked for.

TWO FAULTS, one cause: `stage_image` copied into a single global
`ComfyUI/input/` under the file's BARE NAME, and skipped the copy on an mtime
comparison.

  S1 A REDRAW MASQUERADES AS THE RENDER'S INPUT.  MEASURED on episode 3,
     2026-09-13: fifteen cells on disk no longer match the bytes that were
     staged when their take rendered (`Q08_0`, `Q09_0`, `Q09_1`, `Q10_0`,
     `Q13_0`, `Q13_1`, `Q15_0`, `Q16_0`, `Q16_1`, `Q17_0`, `Q18_0`, `Q05_0E`,
     `Q08_0E`, `Q12_0E`, `Q13_0E`).  T13 scores 100/100 only because its record
     predates the redraw; re-run its DQ and it hard-fails against a picture it
     was never shown.  The gate and the render are reading different files and
     nothing says so.

  S2 EPISODES COLLIDE SILENTLY.  Cell names carry no book and no episode, and
     ep02 and ep03 of this one book share more than twenty of them (`Q00_0.png`,
     `Q02_1.png`, `Q08_0.png`, ...).  Stage ep02 after ep03 and ep03's next
     render quietly uses ep02's picture -- no error, no log line, no way to see
     it afterwards.

Naming the staged copy by a digest of its content makes both impossible: the
same bytes always land on the same name, different bytes never share one, and
`shots.json` then records exactly which bytes rendered.
"""
from pathlib import Path

import pytest

from studio import comfy


@pytest.fixture()
def staging(tmp_path, monkeypatch):
    monkeypatch.setattr(comfy, "COMFY_ROOT", tmp_path / "comfy")
    return tmp_path / "comfy" / "input"


def cell(where: Path, name: str, body: bytes) -> Path:
    where.mkdir(parents=True, exist_ok=True)
    out = where / name
    out.write_bytes(body)
    return out


def test_the_staged_name_carries_a_digest_of_the_bytes(tmp_path, staging):
    got = comfy.stage_image(cell(tmp_path, "Q13_0.png", b"the panel"))
    assert got.startswith("Q13_0_") and got.endswith(".png") and got != "Q13_0.png"
    assert (staging / got).read_bytes() == b"the panel"


def test_the_same_bytes_always_stage_to_the_same_name(tmp_path, staging):
    first = comfy.stage_image(cell(tmp_path, "Q13_0.png", b"the panel"))
    again = comfy.stage_image(cell(tmp_path / "elsewhere", "Q13_0.png", b"the panel"))
    assert first == again


def test_a_redraw_gets_its_own_name_and_cannot_displace_the_first(tmp_path, staging):
    """S1: the take that already rendered keeps its picture on disk."""
    path = cell(tmp_path, "Q13_0.png", b"the panel")
    was = comfy.stage_image(path)
    path.write_bytes(b"the redrawn panel")
    now = comfy.stage_image(path)
    assert was != now
    assert (staging / was).read_bytes() == b"the panel"
    assert (staging / now).read_bytes() == b"the redrawn panel"


def test_two_episodes_sharing_a_cell_name_do_not_collide(tmp_path, staging):
    """S2: `Q00_0.png` in ep02 and in ep03 are different pictures."""
    ep02 = comfy.stage_image(cell(tmp_path / "ep02", "Q00_0.png", b"sitting room, episode two"))
    ep03 = comfy.stage_image(cell(tmp_path / "ep03", "Q00_0.png", b"sitting room, episode three"))
    assert ep02 != ep03
    assert (staging / ep02).read_bytes() == b"sitting room, episode two"
    assert (staging / ep03).read_bytes() == b"sitting room, episode three"


def test_a_second_stage_of_unchanged_bytes_does_not_rewrite_the_file(tmp_path, staging):
    """Cheap: the digest already proves the content, so the copy is skipped."""
    path = cell(tmp_path, "Q13_0.png", b"the panel")
    name = comfy.stage_image(path)
    before = (staging / name).stat().st_mtime_ns
    assert comfy.stage_image(path) == name
    assert (staging / name).stat().st_mtime_ns == before


def test_a_missing_file_still_raises(tmp_path, staging):
    with pytest.raises(FileNotFoundError):
        comfy.stage_image(tmp_path / "nope.png")


def test_a_wav_is_staged_the_same_way(tmp_path, staging):
    """`voice`, `voice_qc` and the take audio all go through this door too."""
    got = comfy.stage_image(cell(tmp_path, "silence_02.wav", b"RIFF...."))
    assert got.startswith("silence_02_") and got.endswith(".wav")
