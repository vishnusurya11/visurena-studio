"""scripts/episode/face_refine.py end to end on a fake ComfyUI and a fake take room:
select the takes, track their faces, match each track to the staged cast, render
each crop with ONLY that person's sheet, gate it, and record the decision per take
in takes/r2v/refine.json.  The engine, the detector and the embedder are fakes; the
videos are a few synthetic frames made by ffmpeg.  Nothing reaches ComfyUI."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from scripts.episode import face_refine as cli
from studio import episode_home, face_detect as fd, face_refine as fr

FRAMES = 22   # on H3's grid (22 % 17 == 5)


def video(path: Path, colour="gray", frames=FRAMES, size=768, boil=False, redraw=False):
    src = f"color=c={colour}:s={size}x{size}:r=24:d={frames / 24}"
    vf = ["-vf", "noise=alls=90:allf=t"] if boil else (["-vf", "eq=brightness=0.04"] if redraw else [])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", src, *vf, "-frames:v", str(frames),
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(path)], check=True)
    return path


PROMPT = ("subject_definitions:\n<Subject 1> is Mr. A in <Picture 1>: Grey hair. <Picture 1> defines this man alone.\n\n"
          "detailed_description:\nHand-drawn 2D gothic anime.\n[Shot 1] <Subject 1> stands at the LEFT third.")


class Room:
    def __init__(self, tmp_path: Path, size="wide", passed=True):
        self.book = tmp_path / "book"
        self.home = episode_home.home(self.book, 1)
        self.room = self.home / "takes" / "r2v"
        self.room.mkdir(parents=True)
        sheet = self.book / "refs" / "characters" / "mr_a" / "sheet_front.png"
        sheet.parent.mkdir(parents=True)
        Image.new("RGB", (64, 64), (120, 120, 120)).save(sheet)
        (self.home / "plan.json").write_text(json.dumps({"aspect": "1:1", "shots": [{"index": 0, "size": size}]}))
        card = {"index": 0, "shots": [0], "faces": ["mr_a"], "frames": FRAMES, "seed": 7, "prompt": PROMPT,
                "refs": ["refs/characters/mr_a/sheet_front.png", "episodes/ep01/storyboard/h3/shot_00.png"]}
        (self.room / "prompts.json").write_text(json.dumps([card]))
        video(self.room / "T00.mp4")
        gates = [{"name": "face-at-end", "value": 0.04, "ok": True, "hard": False}]
        (self.room / "T00.dq.json").write_text(json.dumps({"passed": passed, "gates": gates}))


def detect_one(rgb):
    h = rgb.shape[0]
    s = h * 0.04
    return [{"box": [0.2 * h, 0.4 * h, 0.2 * h + s, 0.4 * h + s], "score": 0.99}]


def embed(rgb, box):
    return np.array([1.0, 0.0])


class Engine:
    """ComfyUI's stand-in, reporting as v0.41.2 does: the LoadVideo's input crop
    first (node 30), then the SaveVideo's render (node 17) -- a faithful redraw of
    the crop, a boiling one, or (echo) the input itself."""

    def __init__(self, tmp_path: Path, boil=False, echo=False):
        self.dir, self.boil, self.echo, self.graphs, self.staged, self.queued = tmp_path / "out", boil, echo, [], {}, {}
        self.dir.mkdir()

    def stage(self, path: Path) -> str:
        self.staged[path.name] = path
        return path.name

    def submit(self, graph: dict) -> str:
        import time
        self.graphs.append(graph)
        self.queued[f"job{len(self.graphs)}"] = time.time()
        return f"job{len(self.graphs)}"

    def span(self, job: str) -> tuple[float, float]:
        """The engine's execution_start / execution_success stamps for the job: 0.1 s of GPU, soon after its queueing."""
        at = self.queued[job]
        return at + 0.02, at + 0.12

    def wait(self, job: str) -> dict[str, list[Path]]:
        graph = self.graphs[int(job[3:]) - 1]
        crop = self.staged[graph["30"]["inputs"]["file"]]
        out = self.dir / f"{job}.mp4"
        render = Path(shutil.copy(crop, out)) if self.echo else video(out, boil=self.boil, redraw=not self.boil)
        return {"30": [crop], "17": [render]}


def run(world: Room, engine: Engine, indices=None):
    return cli.refine(world.book, 1, indices, engine=engine, detect=detect_one, loose=detect_one, embed=embed,
                      within="")


def test_a_wide_take_is_pending_until_refined(tmp_path):
    w = Room(tmp_path)
    assert cli.pending(w.book, 1) == [0]


def test_a_take_the_warp_gate_tracked_readable_is_not(tmp_path):
    w = Room(tmp_path, size="wide")
    dq = json.loads((w.room / "T00.dq.json").read_text())
    dq["measures"] = {"warp": {"S": 0.1, "Se": 0.1, "share": 1.0, "tracks": [{"median_px": 150.0, "min_px": 150.0, "life": 22}]}}
    (w.room / "T00.dq.json").write_text(json.dumps(dq))
    assert cli.pending(w.book, 1) == []


def test_a_closer_take_is_pending_too_the_tracker_decides(tmp_path):
    assert cli.pending(Room(tmp_path, size="medium_close").book, 1) == [0]


def test_a_take_that_failed_a_hard_row_outside_the_bars_is_never_refined(tmp_path):
    w = Room(tmp_path, passed=False)
    dq = json.loads((w.room / "T00.dq.json").read_text())
    dq["gates"].append({"name": "identity", "value": 0.1, "ok": False, "hard": True})
    (w.room / "T00.dq.json").write_text(json.dumps(dq))
    assert cli.pending(w.book, 1) == []


def test_every_face_is_tracked_and_matched_to_the_staged_person(tmp_path):
    w = Room(tmp_path)
    frames = cli.read_frames(w.room / "T00.mp4")
    tracks = cli.tracks_of(frames, fd.by_frames(frames, detect_one))
    assert len(tracks) == 1
    cast = fr.cast_of(PROMPT, ["refs/characters/mr_a/sheet_front.png"])
    got = cli.match(PROMPT, cast, tracks, frames, w.book, detect_one, embed)
    assert {k: p.who for k, p in got.items()} == {0: "mr_a"}


def test_the_crop_renders_with_only_its_persons_sheet_at_its_faces_denoise(tmp_path):
    w, engine = Room(tmp_path), Engine(tmp_path)
    run(w, engine)
    g = engine.graphs[0]
    assert g["9"]["inputs"]["denoise"] == pytest.approx(fr.denoise_for(0.04 * 768), abs=0.002)
    person = json.loads((w.room / "refine.json").read_text())["T00"]["people"][0]
    assert person["denoise"] == g["9"]["inputs"]["denoise"] and person["face_px"] == pytest.approx(30.7, abs=0.1)
    assert g["18"]["inputs"]["image"] == "sheet_front.png" and g["8"]["inputs"]["length"] == FRAMES
    assert "Mr. A" in g["8"]["inputs"]["prompt"] and g["12"]["inputs"]["noise_seed"] == 8


def test_every_person_row_carries_its_smallest_tracked_face(tmp_path):
    """The tiny-face rung reads `min_px` (face_track.track_px), the face at its smallest."""
    w, engine = Room(tmp_path), Engine(tmp_path)
    run(w, engine)
    person = json.loads((w.room / "refine.json").read_text())["T00"]["people"][0]
    assert 0 < person["min_px"] <= person["face_px"] + 0.5


def test_a_faithful_refine_is_kept_and_recorded_beside_the_takes(tmp_path):
    w = Room(tmp_path)
    run(w, Engine(tmp_path))
    doc = json.loads((w.room / "refine.json").read_text())
    entry = doc["T00"]
    assert entry["status"] == "refined" and entry["take_sha8"] == cli.sha8(w.room / "T00.mp4")
    person = entry["people"][0]
    assert person["kept"] and person["who"] == "mr_a" and (w.room / person["crop"]).exists()
    track = json.loads((w.room / person["track"]).read_text())
    assert len(track["windows"]) == FRAMES and track["life"][0] <= track["life"][1]
    assert cli.pending(w.book, 1) == []


def test_a_boiling_refine_falls_back_to_the_unrefined_take(tmp_path):
    w = Room(tmp_path)
    run(w, Engine(tmp_path, boil=True))
    entry = json.loads((w.room / "refine.json").read_text())["T00"]
    assert entry["status"] == "unrefined" and not entry["people"][0]["kept"]
    assert "flicker" in entry["people"][0]["why"]


def test_a_refine_that_returns_its_input_falls_back(tmp_path):
    w = Room(tmp_path)
    run(w, Engine(tmp_path, echo=True))
    entry = json.loads((w.room / "refine.json").read_text())["T00"]
    assert entry["status"] == "unrefined" and "its source" in entry["people"][0]["why"]


def test_the_input_echo_is_never_filed_as_the_refine(tmp_path):
    w = Room(tmp_path)
    run(w, Engine(tmp_path))
    person = json.loads((w.room / "refine.json").read_text())["T00"]["people"][0]
    assert person["measures"]["change"] >= fr.SAME_MAX


def test_a_take_with_no_face_found_is_recorded_and_not_rendered(tmp_path):
    w, engine = Room(tmp_path), Engine(tmp_path)
    cli.refine(w.book, 1, None, engine=engine, detect=lambda rgb: [], loose=lambda rgb: [], embed=embed, within="")
    assert engine.graphs == []
    assert json.loads((w.room / "refine.json").read_text())["T00"]["status"] == "none_found"


def test_a_take_whose_every_face_reads_is_recorded_and_not_rendered(tmp_path):
    w, engine = Room(tmp_path), Engine(tmp_path)
    big = lambda rgb: [{"box": [300.0, 200.0, 460.0, 360.0], "score": 0.9}]
    cli.refine(w.book, 1, None, engine=engine, detect=big, loose=big, embed=embed, within="")
    assert engine.graphs == []
    assert json.loads((w.room / "refine.json").read_text())["T00"]["status"] == "all_readable"


def test_the_finder_is_asked_for_the_take_and_closed_after(tmp_path):
    w, seen = Room(tmp_path), []

    class Find:
        def __call__(self, take, frames):
            seen.append(take.name)
            return fd.by_frames(frames, detect_one)

        def close(self):
            seen.append("closed")
    cli.refine(w.book, 1, None, engine=Engine(tmp_path), detect=detect_one, loose=detect_one, embed=embed,
               find=Find(), within="")
    assert seen == ["T00.mp4", "closed"]


def test_a_cut_is_recorded_with_its_price(tmp_path):
    w = Room(tmp_path)
    cli.record_cut(w.room, [0], 220.0, w.book, 1)
    entry = json.loads((w.room / "refine.json").read_text())["T00"]
    assert entry["status"] == "cut" and "220" in entry["why"]
    assert cli.pending(w.book, 1) == [0], "a cut take is still owed a refine when time allows"


def test_the_refine_is_stamped_on_the_episode_clock(tmp_path):
    w = Room(tmp_path)
    cli.refine(w.book, 1, None, engine=Engine(tmp_path), detect=detect_one, loose=detect_one, embed=embed,
               within="takes")
    rows = [json.loads(l) for l in (w.home / "timing.jsonl").read_text().splitlines()]
    assert [(r["stage"], r.get("within")) for r in rows] == [("face_refine", "takes")]


# ---- A25 (face debate 2026-10-21): the row's clock columns are measured, never a price --------------

def test_every_take_row_carries_its_queue_wait_and_gpu_busy_seconds(tmp_path):
    """ep01's `seconds` was a per-take wall under overlapped lanes (5.4x the stage); `gpu_s_priced`
    repeated to the 0.1 s on different takes.  The row now says when the take was queued, when the
    engine started it, how long it waited and how long the GPU was busy for it, from the engine's record."""
    w, engine = Room(tmp_path), Engine(tmp_path)
    run(w, engine)
    entry = json.loads((w.room / "refine.json").read_text())["T00"]
    assert "seconds" not in entry
    assert entry["span_s"] >= 0 and entry["queued_at"] <= entry["started_at"]
    assert entry["gpu_wait_s"] == pytest.approx(entry["started_at"] - entry["queued_at"], abs=0.06)   # the column is 0.1 s
    assert entry["gpu_busy_s"] > 0 and entry["gpu_busy_s"] == pytest.approx(sum(p["gpu_s"] for p in entry["people"]), abs=0.01)


def test_the_stage_row_carries_the_gpu_busy_seconds_of_its_takes(tmp_path):
    w = Room(tmp_path)
    cli.refine(w.book, 1, None, engine=Engine(tmp_path), detect=detect_one, loose=detect_one, embed=embed, within="takes")
    row = [json.loads(l) for l in (w.home / "timing.jsonl").read_text().splitlines()][0]
    assert row["gpu_busy_s"] > 0 and row["gpu_busy_s"] <= row["wall_s"] + 0.01


# ---- A26: why the tracker ran, and the two smallest faces the record holds ---------------------------

def test_every_take_row_names_the_readable_clause_that_sent_it_to_the_tracker(tmp_path):
    w = Room(tmp_path)
    run(w, Engine(tmp_path))
    entry = json.loads((w.room / "refine.json").read_text())["T00"]
    assert entry["readable_clause"] == "no_tracks" and entry["warp_min_px"] is None
    assert entry["yolo_min_px"] == pytest.approx(30.7, abs=0.5)
