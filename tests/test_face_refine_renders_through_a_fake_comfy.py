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
from studio import episode_home, face_refine as fr

FRAMES = 22   # on H3's grid (22 % 17 == 5)


def video(path: Path, colour="gray", frames=FRAMES, size=768, boil=False):
    src = f"color=c={colour}:s={size}x{size}:r=24:d={frames / 24}"
    vf = ["-vf", "noise=alls=90:allf=t"] if boil else []
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
    """ComfyUI's stand-in: a job 'renders' by handing back its crop (or a boiling one)."""

    def __init__(self, tmp_path: Path, boil=False):
        self.dir, self.boil, self.graphs, self.staged = tmp_path / "out", boil, [], {}
        self.dir.mkdir()

    def stage(self, path: Path) -> str:
        self.staged[path.name] = path
        return path.name

    def submit(self, graph: dict) -> str:
        self.graphs.append(graph)
        return f"job{len(self.graphs)}"

    def wait(self, job: str) -> list[Path]:
        graph = self.graphs[int(job[3:]) - 1]
        crop = self.staged[graph["30"]["inputs"]["file"]]
        out = self.dir / f"{job}.mp4"
        return [video(out, boil=True) if self.boil else Path(shutil.copy(crop, out))]


def run(world: Room, engine: Engine, indices=None):
    return cli.refine(world.book, 1, indices, engine=engine, detect=detect_one, loose=detect_one, embed=embed,
                      within="")


def test_a_wide_take_is_pending_until_refined(tmp_path):
    w = Room(tmp_path)
    assert cli.pending(w.book, 1) == [0]


def test_a_closer_take_with_a_readable_face_is_not(tmp_path):
    w = Room(tmp_path, size="medium_close")
    dq = json.loads((w.room / "T00.dq.json").read_text())
    dq["gates"][0]["value"] = 0.2
    (w.room / "T00.dq.json").write_text(json.dumps(dq))
    assert cli.pending(w.book, 1) == []


def test_a_take_that_failed_its_dq_is_never_refined(tmp_path):
    w = Room(tmp_path, passed=False)
    assert cli.pending(w.book, 1) == []


def test_every_face_is_tracked_and_matched_to_the_staged_person(tmp_path):
    w = Room(tmp_path)
    frames = cli.read_frames(w.room / "T00.mp4")
    tracks = cli.tracks_of(frames, detect_one)
    assert len(tracks) == 1
    cast = fr.cast_of(PROMPT, ["refs/characters/mr_a/sheet_front.png"])
    got = cli.match(PROMPT, cast, tracks, frames, w.book, detect_one, embed)
    assert {k: p.who for k, p in got.items()} == {0: "mr_a"}


def test_the_crop_renders_with_only_its_persons_sheet_at_045(tmp_path):
    w, engine = Room(tmp_path), Engine(tmp_path)
    run(w, engine)
    g = engine.graphs[0]
    assert g["9"]["inputs"]["denoise"] == fr.DENOISE
    assert g["18"]["inputs"]["image"] == "sheet_front.png" and g["8"]["inputs"]["length"] == FRAMES
    assert "Mr. A" in g["8"]["inputs"]["prompt"] and g["12"]["inputs"]["noise_seed"] == 8


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


def test_a_take_with_no_face_found_is_recorded_and_not_rendered(tmp_path):
    w, engine = Room(tmp_path), Engine(tmp_path)
    cli.refine(w.book, 1, None, engine=engine, detect=lambda rgb: [], loose=lambda rgb: [], embed=embed, within="")
    assert engine.graphs == []
    assert json.loads((w.room / "refine.json").read_text())["T00"]["status"] == "no_faces"


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
