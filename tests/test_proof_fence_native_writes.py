"""The fence on writes made in C (2026-10-21_ep02_proof P1 fix round).

libsndfile and OpenCV open their target path in C, so no Python `open` audit event fires and
the audit hook alone never sees soundfile.write or cv2.imwrite.  The fence wraps those entry
points; a planted write under a stand-in real root trips before the file exists.  The
inventory test fails the day studio/ or scripts/ use a native writer the fence does not wrap."""
from __future__ import annotations

import json
import re
import sys
import types
from pathlib import Path

import numpy as np
import pytest

from studio.rehearsal import fence

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def armed(tmp_path):
    real, box = tmp_path / "real", tmp_path / "box"
    for d in (real / "book" / "episodes" / "ep01" / "audio" / "lines", box):
        d.mkdir(parents=True)
    fence.install(fence.Fence.of(roots=(real,), sandbox=box, repo=REPO))
    yield real, box
    fence.disarm()


def trips(box: Path) -> list[dict]:
    path = box / "tripwire.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def test_soundfile_write_under_a_real_root_trips_before_the_file_exists(armed):
    import soundfile as sf
    real, box = armed
    target = real / "book" / "episodes" / "ep01" / "audio" / "lines" / "x.wav"
    with pytest.raises(fence.RehearsalTripwire, match="soundfile"):
        sf.write(str(target), np.zeros(100, dtype="float32"), 16000)
    assert not target.exists() and trips(box)[-1]["event"] == "soundfile"


@pytest.mark.parametrize("mode", ["w", "x", "r+", "w+"])
def test_a_write_capable_soundfile_trips_and_a_read_passes(armed, mode):
    import soundfile as sf
    real, box = armed
    fence.disarm()
    sf.write(str(real / "book" / "kept.wav"), np.zeros(10, dtype="float32"), 16000)
    fence.install(fence.Fence.of(roots=(real,), sandbox=box, repo=REPO))
    with pytest.raises(fence.RehearsalTripwire):
        sf.SoundFile(str(real / "book" / ("kept.wav" if "r" in mode else "new.wav")), mode=mode,
                     samplerate=16000, channels=1)
    with sf.SoundFile(str(real / "book" / "kept.wav")) as read:
        assert read.frames == 10


def test_cv2_imwrite_under_a_real_root_trips(armed):
    import cv2
    real, box = armed
    with pytest.raises(fence.RehearsalTripwire, match="cv2.imwrite"):
        cv2.imwrite(str(real / "book" / "strip.png"), np.zeros((4, 4, 3), dtype="uint8"))
    assert not (real / "book" / "strip.png").exists()


def test_native_writes_in_the_sandbox_pass(armed):
    import cv2
    import soundfile as sf
    _, box = armed
    sf.write(str(box / "ok.wav"), np.zeros(10, dtype="float32"), 16000)
    assert cv2.imwrite(str(box / "ok.png"), np.zeros((4, 4, 3), dtype="uint8"))
    assert (box / "ok.wav").exists() and (box / "ok.png").exists() and trips(box) == []


NATIVE = {"soundfile.SoundFile": re.compile(r"\b(sf|soundfile)\.(write|SoundFile)\(|\bSoundFile\("),
          "cv2.imwrite": re.compile(r"\bimwrite\("), "cv2.VideoWriter": re.compile(r"\bVideoWriter\("),
          "torch.save": re.compile(r"\btorch\.save\("), "torchaudio.save": re.compile(r"\btorchaudio\.save\(")}
"""Native writer call -> the call shapes that write a path from C (no `open` audit event)."""
SCANNED = ("studio", "scripts")


def native_uses() -> dict[str, list[str]]:
    """call -> `file:line` of every native writer call in the scanned code."""
    found: dict[str, list[str]] = {}
    for top in SCANNED:
        for path in sorted((REPO / top).rglob("*.py")):
            for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                for call in (c for c, rx in NATIVE.items() if rx.search(line)):
                    found.setdefault(call, []).append(f"{path.relative_to(REPO).as_posix()}:{n}")
    return found


def test_every_native_writer_the_code_uses_is_wrapped_by_the_fence():
    uses = native_uses()
    assert "soundfile.SoundFile" in uses and "cv2.imwrite" in uses
    assert {call: where for call, where in uses.items() if call not in fence.NATIVE_GUARDS} == {}


def test_a_module_imported_after_arming_is_patched_on_import(tmp_path, monkeypatch):
    (tmp_path / "late_native_mod.py").write_text("def save(p):\n    return p\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    seen = []
    fence.patch_on_import("late_native_mod", lambda mod: seen.append(mod.__name__))
    import late_native_mod  # noqa: F401
    assert seen == ["late_native_mod"]
    sys.modules.pop("late_native_mod", None)


def test_a_module_already_imported_is_patched_at_once():
    seen = []
    mod = types.ModuleType("already_here_mod")
    sys.modules["already_here_mod"] = mod
    try:
        fence.patch_on_import("already_here_mod", lambda m: seen.append(m))
    finally:
        sys.modules.pop("already_here_mod", None)
    assert seen == [mod]
