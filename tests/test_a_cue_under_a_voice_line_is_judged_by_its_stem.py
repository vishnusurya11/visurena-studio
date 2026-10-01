"""ep15 (2026-10-01): three cues sat wholly under voice lines (the field guns
inside line 0, both shot-3 cues inside line 3).  They are ducked 6 dB under the
voice BY DESIGN (owner: "too loud"), and QC's rise-over-baseline measure reads
voice-vs-voice: a +5 dB lift moved the measured rise by 0.0 dB.  The gate was
accusing correct work -- the ep14 shot-20 class of fault, a broken MEASUREMENT.
A cue a voice line covers is now judged by its leveled stem on disk reaching
the target its sidecar records (the file IS in the mix; the edit gate proves
the mix is the master), and the lift cure skips such rows: no gain can move a
masked measure.  $0: arithmetic and one tiny wav."""
from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from studio import episode_sound as es
from studio import sfx_cues


def test_voiced_over_sees_any_overlap_with_a_line():
    lines = [{"at": 0.25, "seconds": 5.84}, {"at": 26.792, "seconds": 6.02}]
    assert es.voiced_over(lines, 0.8, 2.5) is True       # the field guns, inside line 0
    assert es.voiced_over(lines, 10.0, 2.0) is False     # open air
    assert es.voiced_over(lines, 25.0, 2.0) is True      # tail overlaps line 3's head


def sine_wav(path: Path, amp: float) -> Path:
    import soundfile as sf
    t = np.arange(0, 48000) / 48000.0
    sf.write(str(path), (amp * np.sin(2 * math.pi * 440 * t)).astype("float32"), 48000)
    return path


def test_stem_heard_asks_the_file_for_its_own_target(tmp_path):
    cue = sfx_cues.Cue(shot=0, sound="distant field guns firing", at=0.8, seconds=1.0)
    wav = sine_wav(tmp_path / sfx_cues.file_name(cue), 0.1)
    measured = sfx_cues.peak_momentary(wav)
    wav.with_suffix(".json").write_text(json.dumps({"target": measured}), encoding="utf-8")
    db, ok = es.stem_heard(tmp_path, cue)
    assert ok and abs(db - measured) < 0.11              # at its target = heard
    wav.with_suffix(".json").write_text(json.dumps({"target": measured + 10.0}), encoding="utf-8")
    assert es.stem_heard(tmp_path, cue)[1] is False      # 10 dB shy of its ask = not
    assert es.stem_heard(tmp_path / "void", cue) == (float("-inf"), False)


def test_presence_judges_an_under_line_cue_by_its_stem(tmp_path, monkeypatch):
    cue_row = SimpleNamespace(sound="distant field guns firing", at=0.8, seconds=1.0, gain_db=0.0)
    episode = SimpleNamespace(shots=[SimpleNamespace(index=0, sounds=[cue_row])], omit=[])
    placed = {"shots": [{"index": 0, "t_start": 0.0, "seconds": 8.0}],
              "lines": [{"at": 0.25, "seconds": 5.84}]}
    monkeypatch.setattr(sfx_cues, "event_db", lambda *a, **k: 2.0)   # voice masks the rise
    cue = sfx_cues.Cue(shot=0, sound=cue_row.sound, at=0.8, seconds=1.0)
    (tmp_path / "audio" / "sfx").mkdir(parents=True)
    wav = sine_wav(tmp_path / "audio" / "sfx" / sfx_cues.file_name(cue), 0.1)
    wav.with_suffix(".json").write_text(json.dumps({"target": sfx_cues.peak_momentary(wav)}),
                                        encoding="utf-8")
    master = tmp_path / "cut" / "master_r2v.mp4"
    row = es.presence(master, episode, placed)[0]
    assert row["ok"] is True and row["under_line"] is True and row["db"] == 2.0


def test_the_lift_cure_never_pushes_on_a_masked_measure():
    rows = [{"shot": 0, "sound": "guns", "db": 2.0, "ok": False, "under_line": True}]
    assert es.lift_cures(rows, {}) == {}                 # no gain can move it
