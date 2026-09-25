"""Every rubric field is answered by a number beside a wall, in the judge's
pen: shadow from take_look's floor, faces from the box height at the closes,
board from frame_match against the panel, repeats from near-duplicate pairs
across setups, story from the reader's listed action against the plan's verb.
Synthetic pictures, an injected reader and an injected embedder; no video is
decoded and nothing reaches ComfyUI."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.episode import eye_review as er
from studio.judges import master_eye as me

READS = json.loads((Path(__file__).parent / "fixtures" / "vlm" / "master_reads.json").read_text("utf-8"))["reads"]
PLAN = {"setups": {"yard": {"described": "a yard at noon", "crowd": ""},
                   "road": {"described": "a road at noon", "crowd": ""}},
        "shots": [{"index": 1, "setup": "yard", "size": "wide", "section": "hook", "faces": ["a"],
                   "frame": "a man in a yard", "motion": "the camera holds; he walks the yard"},
                  {"index": 2, "setup": "road", "size": "close", "section": "turn", "faces": ["a"],
                   "frame": "a man at a curb", "motion": "he catches the bridle at the curb"},
                  {"index": 3, "setup": "road", "size": "medium", "section": "button", "faces": ["a"],
                   "frame": "a man on a road", "motion": "he walks off"}]}
PLACED = {"duration_s": 30.0, "lines": [],
          "shots": [{"index": 1, "t_start": 0.0, "t_end": 10.0}, {"index": 2, "t_start": 10.0, "t_end": 20.0},
                    {"index": 3, "t_start": 20.0, "t_end": 30.0}]}
VEC = np.ones(8) / np.sqrt(8)


def picture(seed: int, floor: bool) -> np.ndarray:
    """A random picture; with `floor`, its left quarter is true black."""
    pic = np.random.default_rng(seed).integers(60, 255, (64, 64, 3)).astype(np.uint8)
    if floor:
        pic[:, :16] = 0
    return pic


def build(home: Path, floor: bool, face_h: float, reader):
    pics = [picture(shot, floor) for shot in (1, 1, 2, 2, 3, 3)]
    for shot in (1, 2, 3):
        (home / "storyboard").mkdir(parents=True, exist_ok=True)
        Image.fromarray(pics[2 * shot - 1]).save(home / "storyboard" / f"shot_{shot:02d}.png")
    frames = lambda _master, times: pics[:len(times)]  # noqa: E731
    embed = lambda _pic: [{"h": face_h, "vec": VEC}]  # noqa: E731
    return me.read(home, home / "master.mp4", PLAN, PLACED, frames=frames, reader=reader, embed=embed, count=6)


def reader_by_shot(pics_seen: list, catch_on: tuple[int, ...] = (2,)):
    def reader(pic: np.ndarray) -> str:
        pics_seen.append(pic)
        return READS["catch"] if len(pics_seen) in (3, 4) else READS["walk"]
    return reader


def test_a_clean_master_answers_y_on_every_field_with_its_numbers(tmp_path):
    verdict, measures = build(tmp_path, floor=True, face_h=0.4, reader=reader_by_shot([]))
    assert verdict.passed and verdict.faults == [] and verdict.reads == 6 and verdict.confidence == 1.0
    doc = me.rubric(verdict, "abc12345", measures=measures)
    assert [doc["rubric"][f]["answer"] for f, _q in er.RUBRIC] == ["y"] * 5
    shadow = doc["rubric"]["shadow"]["evidence"]
    assert shadow["p5"] == 0.0 and shadow["near_black"] >= 0.25 and shadow["wall"]["p5"] == 20.0
    faces = doc["rubric"]["faces"]["evidence"]
    assert faces["closes"] == [{"shot": 2, "size": "close", "h": 0.4, "wall": me.FACE_AT_CLOSE}]
    assert faces["wall"] == {"close": me.FACE_AT_CLOSE, "medium_close": me.FACE_AT_MEDIUM_CLOSE}
    board = doc["rubric"]["board"]["evidence"]
    assert set(board["last_vs_cell"]) == {1, 2, 3} and all(v >= me.ON_BOARD for v in board["last_vs_cell"].values())
    assert doc["rubric"]["repeats"]["evidence"]["count"] == 0
    assert "catch" in doc["rubric"]["story"]["evidence"]["matched"]
    assert doc["reviewed_by"] == "judge:master_eye@1" and doc["notes"]
    assert er.refusals(doc, "abc12345", Path("review/eye_abc12345.json")) == []


def test_a_lifted_master_with_small_faces_answers_n_from_the_same_measures(tmp_path):
    verdict, measures = build(tmp_path, floor=False, face_h=0.1, reader=reader_by_shot([]))
    assert not verdict.passed
    assert set(me.faults_by_field(verdict)) == {"shadow", "faces"}
    doc = me.rubric(verdict, "abc12345", measures=measures)
    for name in ("shadow", "faces"):
        cell = doc["rubric"][name]
        assert cell["answer"] == "n" and cell["flagged_by"] == "judge:master_eye@1" and cell["evidence"]
    assert doc["rubric"]["shadow"]["evidence"]["p5"] > 20.0
    assert doc["rubric"]["faces"]["evidence"]["under"] == [2]
    assert [doc["rubric"][f]["answer"] for f in ("board", "repeats", "story")] == ["y", "y", "y"]


def test_an_unreadable_answer_lowers_the_confidence_and_names_no_fault(tmp_path):
    seen = []

    def reader(pic):
        seen.append(pic)
        return READS["unread"] if len(seen) == 1 else READS["walk"]
    verdict, _m = build(tmp_path, floor=True, face_h=0.4, reader=reader)
    assert verdict.reads == 6 and verdict.confidence == round(5 / 6, 16)
    assert [f.kind for f in verdict.faults] == ["story"]
