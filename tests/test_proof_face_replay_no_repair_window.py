"""scripts/proof/face_replay.py on a stand-in delivered episode (2026-10-21_ep02_proof DESIGN 4.1).

The stand-in "real" episode lives in a tmp folder: its take was displaced by a repair draw (the
first master's bytes sit in attempts/), its refine.json and repair.jsonl are the repair's.  The
replay must build a sandbox with the first master's take, no refine.json and no repair window, arm
the write fence over the stand-in real root, run the REAL face path with fake detectors, and label a
crop request `unrecorded` until a recording with the same `_src` bytes exists, then `exact`.  The
detectors, embedder and engine are fakes; the videos are synthetic frames made by ffmpeg."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

from scripts.proof import face_replay as fx
from studio.rehearsal import fence

FRAMES = 22
T0 = 1_790_000_000.0
"""2026-09: every stand-in time is T0 + seconds (Windows reads no local time before 1970)."""
PROMPT = ("subject_definitions:\n<Subject 1> is Mr. A in <Picture 1>: Grey hair. <Picture 1> defines this man alone.\n\n"
          "detailed_description:\nHand-drawn 2D gothic anime.\n[Shot 1] <Subject 1> stands at the LEFT third.")


def video(path: Path, colour: str, mtime: float, extra=()) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c={colour}:s=768x768:r=24:d=1",
                    *extra, "-frames:v", str(FRAMES), "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                    str(path)], check=True)
    os.utime(path, (mtime, mtime))
    return path


def write(path: Path, doc, mtime: float | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc if isinstance(doc, str) else json.dumps(doc), encoding="utf-8")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def stand_in(tmp_path: Path, dq_of: str = "iter1") -> Path:
    """A delivered episode: first master at T0+200, the repair at T0+250-260 drew T00 again at T0+300."""
    from PIL import Image
    book = tmp_path / "real_library" / "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"
    home, room = book / "episodes" / "ep01", book / "episodes" / "ep01" / "takes" / "r2v"
    sheet = book / "refs" / "characters" / "mr_a" / "sheet_front.png"
    sheet.parent.mkdir(parents=True)
    Image.new("RGB", (64, 64), (120, 120, 120)).save(sheet)
    write(home / "plan.json", {"aspect": "1:1", "shots": [{"index": 0, "size": "wide", "faces": ["mr_a"]}]})
    write(room / "prompts.json", [{"index": 0, "shots": [0], "faces": ["mr_a"], "frames": FRAMES, "seed": 7,
                                   "prompt": PROMPT, "refs": ["refs/characters/mr_a/sheet_front.png"]}])
    video(room / "attempts" / "T00_fail1.mp4", "gray", T0 + 100)
    video(room / "T00.mp4", "white", T0 + 300)
    current = hashlib.sha256((room / "T00.mp4").read_bytes()).hexdigest()[:8]
    measured = current if dq_of == "current" else hashlib.sha256((room / "attempts" / "T00_fail1.mp4").read_bytes()).hexdigest()[:8]
    gates = [{"name": "face-at-end", "value": 0.04, "ok": True, "hard": False}]
    write(room / "T00.dq.json", {"take_sha8": measured, "passed": True, "gates": gates})
    write(home / "attempts.json", {"face_refine.T00": {"rounds": 1, "seconds": 0.0}, "retakes": {"rounds": 2, "seconds": 9.0}})
    write(room / "ladder.json", {"rounds": [{"at": T0 + 150}, {"at": T0 + 255}]})
    write(home / "repair.jsonl", json.dumps({"opened_at": T0 + 250, "closed_at": T0 + 260, "steps": ["09"]}) + "\n")
    write(room / "refine.json", {"T00": {"status": "refined", "take_sha8": current, "people": [],
                                         "decided": datetime.fromtimestamp(T0 + 255).isoformat(timespec="seconds")}})
    for name, at in (("master_iter1.mp4", T0 + 200), ("master_iter3.mp4", T0 + 400)):
        write(home / "cut" / name, "", at)
    write(home / "review" / "face_labels_0db3d8d9.json", {"labels": ["good", "bad"], "crops": []})
    return book


def detect_one(rgb):
    h = rgb.shape[0]
    s = h * 0.04
    return [{"box": [0.2 * h, 0.4 * h, 0.2 * h + s, 0.4 * h + s], "score": 0.99}]


def embed(rgb, box):
    return np.array([1.0, 0.0])


READERS = (detect_one, detect_one, embed, lambda take, frames: {t: detect_one(frames[t]) for t in range(0, len(frames), 3)})


def tree(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


@pytest.fixture
def disarmed():
    yield
    fence.disarm()


def run(book: Path, box: Path) -> dict:
    return fx.replay(book, 1, box, readers=READERS, roots=[book.parent])


def test_the_sandbox_holds_the_first_masters_take_and_no_repair(tmp_path):
    book = stand_in(tmp_path, dq_of="current")
    box_book, restored = fx.build(book, 1, tmp_path / "box")
    home = box_book / "episodes" / "ep01"
    room = home / "takes" / "r2v"
    assert restored[0]["source"] == "attempts/T00_fail1.mp4" and restored[0]["attempts"] == 0
    assert (room / "T00.mp4").read_bytes() == (book / "episodes/ep01/takes/r2v/attempts/T00_fail1.mp4").read_bytes()
    assert "other bytes" in restored[0]["dq"] and not (room / "T00.dq.json").exists()
    assert not (room / "refine.json").exists() and not (home / "repair.jsonl").exists()
    attempts = json.loads((home / "attempts.json").read_text())
    assert "face_refine.T00" not in attempts and attempts["retakes"]["rounds"] == 1
    assert json.loads((room / "ladder.json").read_text()) == {"rounds": [{"at": T0 + 150}]}


def test_an_unrecorded_crop_is_counted_and_a_recorded_one_is_exact(tmp_path, disarmed):
    book = stand_in(tmp_path)
    before = tree(book)
    first = run(book, tmp_path / "box1")
    fence.disarm()
    assert first["restored"][0]["dq"] == "measured these bytes"
    assert first["kill"]["requests"] >= 1 and first["kill"]["real_run"]
    assert {e["match"] for e in first["engine_log"]} == {"unrecorded"}
    assert tree(book) == before                                   # the real episode was only read
    src = tmp_path / "box1" / "library" / book.name / "episodes/ep01/takes/r2v/refine/T00_p0_src.mp4"
    recorded = book / "episodes/ep01/takes/r2v/refine"
    recorded.mkdir()
    shutil.copy2(src, recorded / "T00_p0_src.mp4")
    video(recorded / "T00_p0.mp4", "gray", T0 + 10, ["-vf", "eq=brightness=0.04"])
    second = run(book, tmp_path / "box2")
    assert second["engine_log"][0]["match"] == "exact" and not second["kill"]["real_run"]
    row = next(r for r in second["faces"] if r["who"] == "mr_a")
    assert row["match"] == "exact" and row["selected"] and row["refined"]


def test_the_fence_is_armed_over_the_real_root_while_it_runs(tmp_path, disarmed):
    book = stand_in(tmp_path)
    run(book, tmp_path / "box")
    with pytest.raises(fence.RehearsalTripwire):
        (book / "planted.txt").write_text("x")
    assert not (book / "planted.txt").exists()


def test_every_paste_keeps_the_take_outside_the_face_core_and_the_instrument_has_no_labels(tmp_path, disarmed):
    book = stand_in(tmp_path)
    said = run(book, tmp_path / "box")
    assert said["outside"]["moved"] == 0
    assert said["instrument"]["n"] == 0 and said["instrument"]["state"] == "INSTRUMENT FAILED"
    assert all(r["instrument_state"] == "INSTRUMENT FAILED" for r in said["faces"])
    assert {r["check"] for r in said["proof_rows"]} >= {"unrecorded_le_half", "outside_invariant", "refine_decision_recall",
                                                        "face_first_pass_vs_iter1", "face_first_pass_vs_iter3",
                                                        "face_mid_tier", "tiny_face_path", "face_replay.selection_agreement"}
    assert "rows" not in said            # the report reads `rows` as proof rows: the per-face table is `faces`


def test_the_agreement_names_the_take_the_repair_decided_on_other_bytes(tmp_path, disarmed):
    book = stand_in(tmp_path)
    said = run(book, tmp_path / "box")
    assert said["agreement"]["n"] == 1 and said["agreement"]["rows"][0]["take"] == "T00"
    assert said["agreement"]["rows"][0]["same_bytes"] is False


def test_a_take_whose_dq_measured_other_bytes_is_not_selected_by_the_real_code(tmp_path, disarmed):
    """ep01 T01: the first master's bytes kept no dq of their own, and face_refine.eligible needs one."""
    said = run(stand_in(tmp_path, dq_of="current"), tmp_path / "box")
    assert said["kill"]["requests"] == 0 and said["kill"]["real_run"]
    assert said["faces"][0]["why"] == "not_selected" and not said["faces"][0]["selected"]


def test_the_step_10_paste_moves_nothing_outside_the_face_core_and_the_measure_sees_the_paste(tmp_path):
    from studio import face_paste as fp
    from studio.rehearsal import face_rows
    crop = video(tmp_path / "crop.mp4", "white", T0)
    rng = np.random.default_rng(7)
    frames = [rng.integers(40, 120, (256, 256, 3), dtype=np.uint8) for _ in range(FRAMES)]
    track = fp.Track([(64, 64, 96)] * FRAMES, (0, FRAMES - 1), 0, str(crop), 0.4, None)
    assert fx.paste_outside(frames, track) == 0.0
    assert fx.allowed_core(frames[0].shape, track, 5).sum() > 0
    paster = fp.Paster(lambda f: f, [fp.Span(0, 0, FRAMES, 0, 1.0, None, (track,))], 256, 256, 1)
    pasted = [paster(f) for f in frames]
    assert face_rows.outside_moved(frames[8], pasted[8], np.zeros((256, 256), bool)) > 0   # the paste is seen


def test_a_track_recorded_before_its_faces_is_read_where_the_windows_put_the_face():
    """ep01's track files hold no per-frame `faces`: the eye is read at face_track.windows' centre."""
    rng = np.random.default_rng(3)
    frames = [rng.integers(0, 255, (768, 768, 3), dtype=np.uint8) for _ in range(12)]
    doc = {"start": 0, "life": [0, 11], "windows": [[0, 0, 300]] * 12, "face_px": 120.0, "side": 300}
    assert len(fx.crop_eyes(frames, doc, [2, 5, 8])) == 3
