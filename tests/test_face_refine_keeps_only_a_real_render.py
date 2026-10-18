"""A face refine is kept only when it is a real render (Jekyll Kawajiri POC, 2026-10-18).

On ComfyUI v0.41.2 the F2 graph's LoadVideo (node 30) reports its INPUT crop in the
job's history, first.  `collect` copied the first output, so step 09_07 filed the
unrefined source crop as "refined" -- 0.0 per pixel from its source -- and the gate
passed it, being the same video.  Now collect takes the SaveVideo node's output by
node id, and a refined crop identical to its source is a refusal, never a pass.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from scripts.episode import face_refine as cli
from studio import comfy, face_gate as fg, face_refine as fr

RECORD = {"outputs": {
    "30": {"images": [{"filename": "T87_p0_src.mp4", "subfolder": "", "type": "input"}]},
    "17": {"images": [{"filename": "T87_p0_33fa1a71_00001_.mp4", "subfolder": "face_refine", "type": "output"}]},
}}
"""The shape of the POC W job's history on v0.41.2: the LoadVideo echo first."""


def test_the_outputs_are_kept_by_the_node_that_wrote_them():
    got = comfy.outputs_by_node(RECORD)
    assert got["17"] == [comfy.COMFY_ROOT / "output" / "face_refine" / "T87_p0_33fa1a71_00001_.mp4"]
    assert got["30"][0].parts[-2] == "input"


def test_the_saved_node_is_the_graphs_save_video():
    graph = {"30": {"class_type": "LoadVideo"}, "16": {"class_type": "CreateVideo"}, "17": {"class_type": "SaveVideo"}}
    assert fr.saved_node(graph) == "17"


def test_a_graph_without_a_save_node_is_refused():
    with pytest.raises(ValueError):
        fr.saved_node({"30": {"class_type": "LoadVideo"}})


def test_the_f2_workflow_saves_through_node_17():
    template, _ = comfy.load_workflow(fr.WORKFLOW)
    assert fr.saved_node(template) == "17"


class EchoEngine:
    """v0.41.2's history: the LoadVideo input first, the SaveVideo output second."""

    def __init__(self, src: Path, out: Path):
        self.src, self.out = src, out

    def wait(self, prompt_id: str) -> dict[str, list[Path]]:
        return {"30": [self.src], "17": [self.out]}


def job(tmp_path: Path) -> tuple:
    room = tmp_path / "room"
    (room / cli.OUT).mkdir(parents=True)
    src, out = tmp_path / "src.mp4", tmp_path / "out.mp4"
    src.write_bytes(b"source crop")
    out.write_bytes(b"refined render")
    work = cli.TakeWork(3, "abcd1234", [])
    return room, work, cli.Job(0, None, [], [], 0, 22, "pid", save="17"), EchoEngine(src, out)


def test_collect_copies_the_save_video_output_not_the_input_echo(tmp_path):
    room, work, j, engine = job(tmp_path)
    cli.collect(room, work, j, engine)
    assert j.out.read_bytes() == b"refined render"


def test_collect_refuses_a_job_with_no_saved_output(tmp_path):
    room, work, j, engine = job(tmp_path)
    j.save = "99"
    with pytest.raises(RuntimeError):
        cli.collect(room, work, j, engine)


def test_a_refined_crop_identical_to_its_source_changed_nothing():
    a = [np.full((16, 16, 3), 80, np.uint8)] * 4
    assert fg.change(a, a) == 0.0
    assert fg.change(a, [f + 12 for f in a]) == pytest.approx(12.0)


def test_a_refine_that_returns_its_input_is_a_failure_never_a_pass():
    m = fr.Measures(id_src=0.6, id_ref=0.6, seam=1.4, flick_src=16.6, flick_ref=16.6, faces_src=1, faces_ref=1,
                    change=0.0)
    kept, why = fr.decide(m)
    assert not kept and "its source" in why


def test_a_real_refine_is_not_refused_for_changing_the_crop():
    m = fr.Measures(id_src=0.6, id_ref=0.6, seam=9.8, flick_src=16.6, flick_ref=14.4, faces_src=1, faces_ref=1,
                    change=11.4)
    assert fr.decide(m) == (True, "kept")
