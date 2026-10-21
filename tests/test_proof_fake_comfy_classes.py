"""The fake ComfyUI replays every job class the REAL engine was recorded running, and must answer
in the real engine's shape, status and kind of timing (2026-10-21_ep02_proof DESIGN 2.2, R12).

`tests/fixtures/proof/comfy_classes/` holds one real job per class, copied from the GPU transcript
(docs/audit/2026-10-21_ep02_proof/gpu/transcript, ComfyUI 0.41.2 on the RTX 4090): its submitted
graph, the /prompt reply and the /history record, or the client's error.  Each test submits the
SAME graph to the fake through the real client, with a recording of that job (media made in tmp
at the recorded size and frame count, the recorded seconds), and compares:
  shape   the /history record key for key, type for type (record_comfy_transcript.shape_diff)
  status  status_str, completed and the message kinds in order
  timing  execution_start -> execution_success in integer ms equal to the recorded seconds, and the
          fake labels the clock `recorded` (never evidence for a time question, R15)
  errors  the client raises the class and words the real engine made it raise."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pytest

from scripts.proof import record_comfy_transcript as rct
from studio import comfy
from studio.rehearsal import fake_comfy
from studio.rehearsal import workflow_fingerprint as wf
from tests.test_proof_fake_comfy_routes import needs_ffmpeg, rig  # noqa: F401

CLASSES = Path(__file__).resolve().parent / "fixtures" / "proof" / "comfy_classes"
SUCCESS = ("krea2_sheet", "qwen_grid_1x1", "qwen_grid_2x2", "qwen3vl_read_cold", "qwen3vl_read_warm",
           "qwen3vl_read_after_restart", "h3_take", "h3_tiny_face_1024", "h3_face_refine")
KIND = {"krea2_sheet": "picture", "qwen_grid_1x1": "grid", "qwen_grid_2x2": "grid", "h3_take": "take",
        "h3_tiny_face_1024": "take", "h3_face_refine": "take"}
"""The kind the fake infers for each class with no template to name it (a video output is a take)."""


def recorded(name: str) -> dict:
    return json.loads((CLASSES / f"{name}.json").read_text(encoding="utf-8"))


def graph_of(rec: dict) -> dict:
    return rec["history_entry"]["prompt"][2] if rec.get("history_entry") else rec["submitted_graph"]


def first_media(he: dict) -> dict | None:
    """The first item a media output node of the real record reported (type output)."""
    items = [i for node in he["outputs"].values() for i in node.get("images", []) if i.get("type") == "output"]
    return items[0] if items else None


def make_media(path: Path, meta: dict) -> Path:
    """A file at the real output's size (and frame count for a video), made in tmp."""
    size = (int(meta["width"]), int(meta["height"]))
    if meta["kind"] == "video":
        fake_comfy.grey_video(path, int(meta["frame_count"]), size=size)
    else:
        import cv2
        import numpy as np
        cv2.imwrite(str(path), np.full((size[1], size[0], 3), 90, dtype=np.uint8))
    return path


def text_of(he: dict) -> str:
    return next(t for node in he["outputs"].values() for t in node.get("text", []))


def recording_for(name: str, rec: dict, media: Path) -> dict:
    """An exact recording of the class's job: its graph, its output, its recorded seconds."""
    graph, he = graph_of(rec), rec["history_entry"]
    gpath = media / f"{name}.graph.json"
    gpath.write_text(json.dumps(graph), encoding="utf-8")
    item = first_media(he)
    if item:
        out = make_media(media / f"{name}{Path(item['filename']).suffix}", item["metadata"])
    else:
        out = media / f"{name}.txt"
        out.write_text(text_of(he), encoding="utf-8")
    return {"kind": KIND.get(name, "vl_text"), "workflow_fp": wf.multiset_fp(graph), "graph": str(gpath),
            "path": str(out), "seconds": rec["execution_s"], "source": f"comfy_classes/{name}.json"}


def stage_inputs(r, graph: dict, media: Path) -> None:
    """Every LoadVideo's file in the fake engine's input folder, as the stage would have copied it."""
    for node in graph.values():
        if node.get("class_type") == "LoadVideo":
            make_media(r.fake.root / "input" / node["inputs"]["file"],
                       {"kind": "video", "width": 768, "height": 768, "frame_count": 73})


def replay(r, name: str) -> tuple[dict, dict]:
    """(the real record, the fake's record) of one class submitted through the real client."""
    rec = recorded(name)
    r.fake.add_recordings([recording_for(name, rec, r.media)])
    stage_inputs(r, graph_of(rec), r.media)
    pid = comfy.submit(graph_of(rec))
    return rec, comfy.wait_record(pid, timeout=30, poll=0.02)


def post_prompt(host: str, graph: dict) -> dict:
    """The raw /prompt reply, read as the engine wrote it (submit keeps only the prompt id)."""
    request = urllib.request.Request(f"{host}/prompt", data=json.dumps({"prompt": graph}).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read())


def kinds(record: dict) -> list[str]:
    return [m[0] for m in record["status"]["messages"]]


def span_ms(record: dict) -> int:
    ts = {m[0]: m[1]["timestamp"] for m in record["status"]["messages"]}
    return ts["execution_success"] - ts["execution_start"]


def every_timestamp_is_int_ms(record: dict) -> bool:
    return all(isinstance(m[1].get("timestamp"), int) for m in record["status"]["messages"])


# ---- the successful classes ----------------------------------------------------------------

@needs_ffmpeg
@pytest.mark.parametrize("name", SUCCESS)
def test_each_recorded_class_replays_in_the_real_engines_shape(rig, name):
    rec, got = replay(rig(), name)
    assert rct.shape_diff(rct.shape(rec["history_entry"]), rct.shape(got), name) == []
    assert set(got["outputs"]) == set(rec["history_entry"]["outputs"])
    assert got["prompt"][4] and set(got["prompt"][4]) == set(rec["history_entry"]["prompt"][4])


@needs_ffmpeg
@pytest.mark.parametrize("name", SUCCESS)
def test_each_recorded_class_ends_with_the_real_status_and_message_kinds(rig, name):
    rec, got = replay(rig(), name)
    real = rec["history_entry"]["status"]
    assert (got["status"]["status_str"], got["status"]["completed"]) == (real["status_str"], real["completed"])
    assert kinds(got) == [m[0] for m in real["messages"]]


@needs_ffmpeg
@pytest.mark.parametrize("name", SUCCESS)
def test_each_recorded_class_carries_its_recorded_seconds_as_the_engine_does(rig, name):
    rec, got = replay(rig(), name)
    assert every_timestamp_is_int_ms(rec["history_entry"]) and every_timestamp_is_int_ms(got)
    assert abs(span_ms(rec["history_entry"]) - round(rec["execution_s"] * 1000)) <= 10
    assert abs(span_ms(got) - span_ms(rec["history_entry"])) <= 10
    assert got["rehearsal"]["clock"] == "recorded"


@needs_ffmpeg
@pytest.mark.parametrize("name", ("krea2_sheet", "qwen_grid_2x2", "h3_take", "h3_tiny_face_1024", "h3_face_refine"))
def test_a_media_output_says_its_size_and_frames_as_the_engine_does(rig, name):
    rec, got = replay(rig(), name)
    real = first_media(rec["history_entry"])["metadata"]
    mine = first_media(got)["metadata"]
    keep = ("kind", "width", "height", "frame_count")
    assert {k: mine.get(k) for k in keep if k in real} == {k: real[k] for k in keep if k in real}


@needs_ffmpeg
def test_a_load_video_echoes_its_input_ahead_of_the_save_as_the_engine_does(rig):
    r = rig()
    rec, got = replay(r, "h3_face_refine")
    echoed = [i for node in got["outputs"].values() for i in node.get("images", []) if i["type"] == "input"]
    assert [i["filename"] for i in echoed] == ["T26_p0_src_d1648a3a.mp4"]
    by_node = comfy.outputs_by_node(got)
    assert [p.name for p in by_node["17"]] == ["h3_face_refine_T26_p0_00001_.mp4"]
    logged = r.answers()[-1]["outputs"]
    assert logged == ["comfy/output/proof_gpu/h3_face_refine_T26_p0_00001_.mp4"]


# ---- the error classes ----------------------------------------------------------------------

@needs_ffmpeg
def test_an_interrupted_take_ends_as_the_engine_ends_it_and_the_client_says_unknown_error(rig):
    r, rec = rig(), recorded("error_interrupt")
    r.fake.add_recordings([{**recording_for("h3_take", recorded("h3_take"), r.media), "graph": None}])
    r.fake.hold(True)
    pid = comfy.submit(graph_of(rec))
    comfy.interrupt()
    with pytest.raises(RuntimeError) as got:
        comfy.wait_record(pid, timeout=5, poll=0.02)
    assert str(got.value) == f"{pid} failed: unknown error"
    assert rec["studio_client_error"].endswith("failed: unknown error")
    record = comfy.history(pid)
    assert rct.shape_diff(rct.shape(rec["history_entry"]), rct.shape(record), "interrupt") == []
    assert kinds(record) == kinds(rec["history_entry"]) and record["outputs"] == {} and record["meta"] == {}


def test_an_interrupt_naming_another_prompt_leaves_the_running_job_alone(rig):
    r = rig()
    r.fake.hold(True)
    pid = comfy.submit({"1": {"class_type": "EmptyImage", "inputs": {"width": 8, "height": 8}},
                        "2": {"class_type": "SaveImage", "inputs": {"images": ["1", 0], "filename_prefix": "x"}}})
    comfy._post("/interrupt", {"prompt_id": "not-running"})
    assert comfy.running(pid)
    assert any("is not currently running, skipping interrupt" in e["m"] for e in r.fake.ring)


def test_an_engine_that_dies_under_a_read_raises_engine_lost_with_the_real_words(rig):
    rec = recorded("qwen3vl_read_engine_crash")
    rig(faults=[{"kind": "crash", "on": "submit#1", "detail": "0.3"}])
    pid = comfy.submit(graph_of(rec))
    with pytest.raises(comfy.EngineLost) as got:
        comfy.wait_record(pid, timeout=5, poll=0.02)
    real_cls, real_said = rec["studio_client_error"].split(": ", 1)
    assert type(got.value).__name__ == real_cls
    assert str(got.value).replace(pid, "<id>") == real_said.replace(rec["prompt_response"]["prompt_id"], "<id>")
    assert comfy.history(pid) == rec["history_entry"] == {}


def test_a_graph_whose_every_output_fails_validation_is_refused_with_the_real_400(rig):
    case = recorded("error_invalid_graph")["full_reject"]
    rig(faults=[{"kind": "rejected", "on": "submit#1", "detail": "2.text"}])
    graph = graph_of(recorded("qwen3vl_read_warm"))
    with pytest.raises(RuntimeError) as got:
        comfy.submit(graph)
    said = json.loads(str(got.value).split("ComfyUI rejected the workflow: ", 1)[1])
    assert rct.shape_diff(rct.shape(case["prompt_response"]), rct.shape(said), "full_reject") == []
    assert said["error"]["type"] == case["prompt_response"]["error"]["type"] == "prompt_outputs_failed_validation"
    assert case["studio_comfy_submit_raised"].startswith("RuntimeError: ComfyUI rejected the workflow")


@needs_ffmpeg
def test_a_graph_with_one_valid_output_is_accepted_and_ends_success_with_no_picture(rig):
    case = recorded("error_invalid_graph")["partial_accept"]
    r = rig(faults=[{"kind": "partial_accept", "on": "submit#1", "detail": "30:3.seed"}])
    r.fake.add_recordings([recording_for("krea2_sheet", recorded("krea2_sheet"), r.media)])
    reply = post_prompt(r.host, case["submitted_graph"])
    assert rct.shape_diff(rct.shape(case["prompt_response"]), rct.shape(reply), "partial_accept") == []
    got = comfy.wait_record(reply["prompt_id"], timeout=5, poll=0.02)
    assert rct.shape_diff(rct.shape(case["history_entry"]), rct.shape(got), "partial_accept") == []
    assert comfy.outputs_of(got) == [] and got["status"]["status_str"] == "success"
