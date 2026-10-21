"""scripts/proof/face_replay.py on a stand-in delivered episode (2026-10-21_ep02_proof DESIGN 4.1).

The stand-in "real" episode lives in a tmp folder: its take was displaced by a repair draw (the
first master's bytes sit in attempts/), its refine.json and repair.jsonl are the repair's.  The
replay must build a sandbox with the first master's take, no refine.json and no repair window, arm
the write fence over the stand-in real root, and run the REAL face path with fake detectors against
the REAL engine client (scripts/episode/face_refine.Comfy -> studio.comfy) aimed at package P3's fake
ComfyUI, which answers a crop `canned` until a recording with the same staged `_src` bytes exists,
then `exact`.  Step 10's paste is built by step 10's own spans (face_paste.spans_from over the cut's
layout) and judged against the face rectangle the TRACK RECORD gives, never the Paster's geometry.
The detectors and embedder are fakes; the videos are synthetic frames made by ffmpeg."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

from scripts.proof import face_replay as fx
from studio import compute_device, face_paste as fp
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


def sha8_of(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]


def stand_in_cast(book: Path) -> None:
    """The book's one cast sheet, the plan and the take card that stages it."""
    from PIL import Image
    home, room = book / "episodes" / "ep01", book / "episodes" / "ep01" / "takes" / "r2v"
    sheet = book / "refs" / "characters" / "mr_a" / "sheet_front.png"
    sheet.parent.mkdir(parents=True)
    Image.new("RGB", (64, 64), (120, 120, 120)).save(sheet)
    write(home / "plan.json", {"aspect": "1:1", "shots": [{"index": 0, "size": "wide", "faces": ["mr_a"]}]})
    write(room / "prompts.json", [{"index": 0, "shots": [0], "faces": ["mr_a"], "frames": FRAMES, "seed": 7,
                                   "prompt": PROMPT, "refs": ["refs/characters/mr_a/sheet_front.png"]}])


def stand_in_takes(room: Path, dq_of: str) -> str:
    """The first master's T00 archived at T0+100, the repair's draw at T0+300, and a dq that measured
    `dq_of`'s bytes; the current take's sha8."""
    video(room / "attempts" / "T00_fail1.mp4", "gray", T0 + 100)
    video(room / "T00.mp4", "white", T0 + 300)
    current = sha8_of(room / "T00.mp4")
    measured = current if dq_of == "current" else sha8_of(room / "attempts" / "T00_fail1.mp4")
    gates = [{"name": "face-at-end", "value": 0.04, "ok": True, "hard": False}]
    write(room / "T00.dq.json", {"take_sha8": measured, "passed": True, "gates": gates})
    return current


def stand_in_repair(home: Path, room: Path, current: str) -> None:
    """The counters, the ladder, the repair window and the refine.json the repair wrote."""
    write(home / "attempts.json", {"face_refine.T00": {"rounds": 1, "seconds": 0.0}, "retakes": {"rounds": 2, "seconds": 9.0}})
    write(room / "ladder.json", {"rounds": [{"at": T0 + 150}, {"at": T0 + 255}]})
    write(home / "repair.jsonl", json.dumps({"opened_at": T0 + 250, "closed_at": T0 + 260, "steps": ["09"]}) + "\n")
    write(room / "refine.json", {"T00": {"status": "refined", "take_sha8": current, "people": [],
                                         "decided": datetime.fromtimestamp(T0 + 255).isoformat(timespec="seconds")}})


def stand_in(tmp_path: Path, dq_of: str = "iter1") -> Path:
    """A delivered episode: first master at T0+200, the repair at T0+250-260 drew T00 again at T0+300."""
    book = tmp_path / "real_library" / "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"
    home, room = book / "episodes" / "ep01", book / "episodes" / "ep01" / "takes" / "r2v"
    stand_in_cast(book)
    stand_in_repair(home, room, stand_in_takes(room, dq_of))
    for name, at in (("master_iter1.mp4", T0 + 200), ("master_iter3.mp4", T0 + 400)):
        write(home / "cut" / name, "", at)
    write(home / "review" / "face_labels_0db3d8d9.json", {"labels": ["good", "bad"], "crops": []})
    cut_layout(home / "takes" / "work", room / "T00.mp4")
    return book


def cut_layout(work: Path, take: Path) -> None:
    """The cut's own records step 10 reads: layout.json, gutter.json and the take's segment."""
    write(work / "layout.json", [{"index": 0, "seconds": FRAMES / 24, "head": 0.0, "slow": 1.0, "still": False}])
    write(work / "gutter.json", {})
    shutil.copy2(take, work / "seg00.mp4")


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
def disarmed(monkeypatch):
    monkeypatch.setattr(compute_device, "live_claims", lambda **_: [])     # no GPU claim on a test machine
    yield
    fence.disarm()


def run(book: Path, box: Path) -> dict:
    return fx.replay(book, 1, box, readers=READERS, roots=[book.parent])


def record_crop(book: Path, box: Path, seconds: float = 12.0) -> None:
    """The stand-in's real refine.json and refine/ hold the crop the first replay asked for (bytes kept)."""
    room = book / "episodes/ep01/takes/r2v"
    src = box / "library" / book.name / "episodes/ep01/takes/r2v/refine/T00_p0_src.mp4"
    (room / "refine").mkdir()
    shutil.copy2(src, room / "refine" / "T00_p0_src.mp4")
    shutil.copy2(src.with_name("T00_p0.json"), room / "refine" / "T00_p0.json")
    video(room / "refine" / "T00_p0.mp4", "gray", T0 + 10, ["-vf", "eq=brightness=0.04"])
    doc = json.loads((room / "refine.json").read_text())
    doc["T00"].update(gpu_busy_s=seconds, people=[{"who": "mr_a", "kept": False, "why": "x", "crop": "refine/T00_p0.mp4",
                                                   "track": "refine/T00_p0.json"}])
    write(room / "refine.json", doc)


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


def test_the_real_client_asks_the_fake_comfyui_and_a_crop_is_canned_until_its_src_bytes_are_recorded(tmp_path, disarmed):
    book = stand_in(tmp_path)
    before = tree(book)
    first = run(book, tmp_path / "box1")
    fence.disarm()
    assert first["restored"][0]["dq"] == "measured these bytes"
    assert first["kill"]["requests"] >= 1 and first["kill"]["real_run"]
    assert {e["match"] for e in first["engine_log"]} == {"canned"}
    staged = [p.name for p in (tmp_path / "box1" / "comfy" / "input").iterdir()]
    assert any(re.fullmatch(r"T00_p0_src_[0-9a-f]{8}\.mp4", n) for n in staged)       # stage_image's own name
    log = [json.loads(x) for x in (tmp_path / "box1" / "engine_log.jsonl").read_text().splitlines()]
    assert log[0]["header"] and {r["class"] for r in log if r.get("call") == "prompt"} == {"canned"}
    assert tree(book) == before                                   # the real episode was only read
    record_crop(book, tmp_path / "box1")
    second = run(book, tmp_path / "box2")
    assert second["engine_log"][0]["match"] == "exact" and second["engine_log"][0]["clock"] == "recorded"
    assert not second["kill"]["real_run"]
    row = next(r for r in second["faces"] if r["who"] == "mr_a")
    assert row["match"] == "exact" and row["selected"] and row["refined"]


def test_the_engine_clock_runs_through_the_fakes_history_and_is_never_time_evidence(tmp_path, disarmed):
    book = stand_in(tmp_path)
    run(book, tmp_path / "box1")
    fence.disarm()
    record_crop(book, tmp_path / "box1", seconds=12.0)
    said = run(book, tmp_path / "box2")
    assert said["engine_clock"]["gpu_busy_s"] == 12.0         # take_phases.window over the fake's /history
    assert said["engine_clock"]["clock"] == "recorded" and said["engine_clock"]["time_evidence"] is False
    assert said["sr1"]["measured_s"] == 0.0                    # the sandbox's clock never enters SR-1


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


def paste_room(tmp_path: Path) -> tuple[Path, Path]:
    """A cut whose one take has one kept, current refine: the records step 10 pastes from."""
    room, work = tmp_path / "takes" / "r2v", tmp_path / "takes" / "work"
    take = video(room / "T00.mp4", "white", T0)
    video(room / "refine" / "T00_p0.mp4", "black", T0)
    write(room / "refine" / "T00_p0.json", {"windows": [[300, 260, 160]] * FRAMES, "life": [0, FRAMES - 1],
                                            "start": 0, "frames": FRAMES, "face_px": 66.0, "side": 160})
    person = {"who": "mr_a", "kept": True, "crop": "refine/T00_p0.mp4", "track": "refine/T00_p0.json", "face_px": 66.0}
    write(room / "refine.json", {"T00": {"status": "refined", "take_sha8": fp.sha8(take), "people": [person]}})
    cut_layout(work, take)
    return work, room


def test_step_10s_own_paste_moves_nothing_outside_the_face_the_track_records(tmp_path):
    work, room = paste_room(tmp_path)
    said = fx.step10_outside(work, room, "1:1")
    assert list(said) == [("T00", "mr_a")] and said[("T00", "mr_a")] == 0.0
    track = fp.kept_tracks(json.loads((room / "refine.json").read_text())["T00"], room)[0]
    rect = fx.face_rect((768, 768), track, 5, None)
    assert 0 < rect.sum() < 160 * 160                                   # the face, not the whole window


def test_a_misplaced_paste_is_seen_because_the_rectangle_is_not_the_pasters_geometry(tmp_path, monkeypatch):
    work, room = paste_room(tmp_path)
    placed = fp.box_at

    def moved(win, guard, w, h, f):
        x, y, side = placed(win, guard, w, h, f)
        return x + 60, y, side
    monkeypatch.setattr(fp, "box_at", moved)
    assert fx.step10_outside(work, room, "1:1")[("T00", "mr_a")] > 0


def test_a_track_recorded_before_its_faces_is_read_where_the_windows_put_the_face():
    """ep01's track files hold no per-frame `faces`: the eye is read at face_track.windows' centre."""
    rng = np.random.default_rng(3)
    frames = [rng.integers(0, 255, (768, 768, 3), dtype=np.uint8) for _ in range(12)]
    doc = {"start": 0, "life": [0, 11], "windows": [[0, 0, 300]] * 12, "face_px": 120.0, "side": 300}
    assert sorted(fx.crop_eyes(frames, doc, [2, 5, 8])) == [2, 5, 8]          # keyed by crop frame


def test_recorded_refine_crops_are_staged_as_owner_label_rows_and_a_staged_file_is_never_rewritten(tmp_path):
    work, room = paste_room(tmp_path)
    shutil.copy2(room / "T00.mp4", room / "refine" / "T00_p0_src.mp4")
    review = tmp_path / "proof" / "review"
    path = fx.stage_labels(room, review)
    doc = json.loads(path.read_text())
    assert path.parent == review and re.fullmatch(r"face_labels_[0-9a-f]{8}\.json", path.name)
    assert [(c["take"], c["who"], c["kind"], c["owner"]) for c in doc["crops"]] == [
        ("T00", "mr_a", "refine_src", ""), ("T00", "mr_a", "refine_render", "")]
    assert all((review / c["crop"]).is_file() for c in doc["crops"])
    doc["crops"][0]["owner"] = "good"
    path.write_text(json.dumps(doc))
    assert fx.stage_labels(room, review) == path and json.loads(path.read_text())["crops"][0]["owner"] == "good"


def test_the_instrument_reads_the_episodes_labels_and_the_staged_ones_and_says_whether_n_can_reach_the_gate(tmp_path):
    book = stand_in(tmp_path)
    work, room = paste_room(tmp_path / "other")
    shutil.copy2(room / "T00.mp4", room / "refine" / "T00_p0_src.mp4")
    review = tmp_path / "proof" / "review"
    fx.stage_labels(room, review)
    said = fx.instrument(book / "episodes" / "ep01", review)
    assert len(said["label_files"]) == 2 and said["crops_staged"] == 2
    assert said["gate_reachable"] is False and said["candidates"]["face_eye.cel"]["n"] == 0


def test_the_sr1_line_says_what_was_measured_and_what_is_only_priced():
    said = fx.sr1_line({"measured_s": 0.0, "measured_takes": 0, "priced_s": 1483.2, "priced_takes": 12, "unknown_takes": []})
    assert "0.0 GPU s measured on 0 takes" in said and "1483.2 s PRICED" in said and "not a measurement" in said


def test_a_canned_render_is_the_size_the_graph_asked_for(tmp_path):
    """The real engine renders the graph's width x height; a canned grey of another size crashes the face
    gate (face_gate.change) where it must refuse.  P3's fake, its own fill."""
    import cv2
    from studio.rehearsal import fake_comfy
    fake = fake_comfy.FakeComfy(tmp_path, workflows=Path(__file__).parent / "fixtures" / "proof" / "fake_comfy" / "workflows")
    job = fake_comfy.Job("p", 1, {}, None, {"width": 768, "height": 512, "frames": 5}, 0, 0.0)
    fake.fill(tmp_path / "out.mp4", None, fake_comfy.Match("canned", "refine_crop"), job)
    ok, frame = cv2.VideoCapture(str(tmp_path / "out.mp4")).read()
    assert ok and frame.shape[:2] == (512, 768) and fake_comfy.grey(tmp_path / "out.mp4")
