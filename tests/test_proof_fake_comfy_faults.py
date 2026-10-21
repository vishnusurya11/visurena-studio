"""Every fault the fake ComfyUI injects, pinned through the REAL studio.comfy client
(2026-10-21_ep02_proof DESIGN 2.2, package P3): a transient exec error is resubmitted exactly
once, a fatal one never, a crash costs one resubmission, a lost engine and a hang end in the
client's own StillRunning, an unreadable reply is never cached, and each corrupt output is the
file a gate downstream has to refuse."""
from __future__ import annotations

import subprocess

import pytest

from studio import comfy, engine_ops
from studio.rehearsal import comfy_faults, fake_comfy
from tests.test_proof_fake_comfy_routes import (FFMPEG, TAKE, filled, needs_ffmpeg, rig,  # noqa: F401
                                                take_recording)

CAPTION = {"image_1": "frame_aa.png", "prompt": "list the people", "seed": 1}


def fault(kind: str, at: int = 1, workflow: str = "fx_take", **kw) -> dict:
    return {"kind": kind, "on": f"submit#{at}", "workflow": workflow, **kw}


def has_audio(path) -> bool:
    said = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    return "Audio:" in said


# ---- the fault table --------------------------------------------------------------------

def test_a_fault_parses_from_the_designs_sentence_and_from_a_row():
    said = comfy_faults.parse("exec_error on submit#3 of workflow fx_take")
    assert said == comfy_faults.Fault("exec_error", 3, "fx_take")
    assert comfy_faults.parse(fault("corrupt", 2, detail="no_audio")).detail == "no_audio"
    with pytest.raises(ValueError):
        comfy_faults.parse({"kind": "meteor", "on": "submit#1"})
    with pytest.raises(ValueError):
        comfy_faults.parse({"kind": "corrupt", "on": "submit#1", "detail": "sideways"})


def test_the_counter_is_per_workflow_and_a_global_fault_counts_every_submit():
    faults = comfy_faults.Faults([fault("hang", 2), {"kind": "crash", "on": "submit#4"}])
    seen = [faults.on_submit(w) for w in ("fx_take", "fx_caption", "fx_take", "fx_caption", "fx_take")]
    assert [f.kind if f else None for f in seen] == [None, None, "hang", "crash", None]


def test_the_transient_text_is_the_clients_retry_class_and_the_fatal_text_is_not():
    assert comfy.transient(comfy_faults.message_text(comfy_faults.TRANSIENT_ERROR))
    assert not comfy.transient(comfy_faults.message_text(comfy_faults.FATAL_ERROR))


# ---- execution errors -------------------------------------------------------------------

@needs_ffmpeg
def test_a_transient_exec_error_is_resubmitted_exactly_once(rig):
    r = rig(faults=[fault("exec_error")])
    r.fake.add_recordings([take_recording(r.media)])
    out = comfy.run("fx_take", TAKE)
    rows = r.answers()
    assert len(rows) == 2 and rows[0]["fault"] == "exec_error" and rows[1]["fault"] is None
    assert out[0].exists() and rows[1]["class"] == "exact"


def test_two_transient_errors_in_a_row_propagate_after_two_submits(rig):
    r = rig(faults=[fault("exec_error", 1, "fx_grid"), fault("exec_error", 2, "fx_grid")])
    with pytest.raises(RuntimeError, match="HostBuffer"):
        comfy.run("fx_grid", {"prompt": "a", "seed": 1, "filename_prefix": "g"})
    assert len(r.answers()) == 2


def test_a_fatal_exec_error_is_never_resubmitted(rig):
    r = rig(faults=[fault("exec_fatal", 1, "fx_grid")])
    with pytest.raises(RuntimeError, match="out of memory"):
        comfy.run("fx_grid", {"prompt": "a", "seed": 1, "filename_prefix": "g"})
    assert [row["fault"] for row in r.answers()] == ["exec_fatal"]


def test_an_exec_error_record_has_the_engines_error_shape(rig):
    rig(faults=[fault("exec_error", 1, "fx_grid")])
    pid = comfy.submit(filled("fx_grid", {"prompt": "a", "seed": 1, "filename_prefix": "g"}))
    record = comfy.history(pid)
    assert record["status"]["status_str"] == "error" and record["status"]["completed"] is False
    kinds = [m[0] for m in record["status"]["messages"]]
    assert kinds == ["execution_start", "execution_cached", "execution_error"]
    assert {"node_id", "node_type", "exception_message", "exception_type", "traceback"} <= set(
        record["status"]["messages"][-1][1])


# ---- the engine going away --------------------------------------------------------------

def test_a_crash_forgets_the_job_and_the_client_resubmits_it_once(rig):
    r = rig(faults=[fault("crash", 1, "fx_grid", detail="0.3")])
    out = comfy.run("fx_grid", {"prompt": "a", "seed": 1, "filename_prefix": "g"})
    assert out[0].exists() and [row["fault"] for row in r.answers()] == ["crash", None]


def test_a_lost_engine_never_answers_again_and_a_restart_cannot_bring_it_back(rig, monkeypatch):
    for name, value in {"RESTART_SECONDS": 0.3, "QUEUE_SECONDS": 0.3}.items():
        monkeypatch.setattr(comfy, name, value)
    r = rig(faults=[fault("lost", 1, "fx_grid")])
    pid = comfy.submit(filled("fx_grid", {"prompt": "a", "seed": 1, "filename_prefix": "g"}))
    with pytest.raises(comfy.StillRunning):
        comfy.wait_record(pid, timeout=0.4, poll=0.05)
    assert engine_ops.alive(base_url=r.host) is False and r.fake.restart() is False
    assert [row.get("call") for row in r.log()].count("restart") == 1


def test_a_hang_ignores_the_interrupt_until_a_restart_empties_the_engine(rig):
    r = rig(faults=[fault("hang", 1, "fx_grid")])
    pid = comfy.submit(filled("fx_grid", {"prompt": "a", "seed": 1, "filename_prefix": "g"}))
    with pytest.raises(comfy.StillRunning):
        comfy.wait_record(pid, timeout=0.3, poll=0.05)
    comfy.interrupt()
    assert comfy.stuck(pid, patience=0.3, poll=0.05) is True
    assert r.fake.restart() is True and comfy.lost(pid) is True
    assert comfy.queue_counts() == (0, 0)


# ---- unreadable and corrupt answers -----------------------------------------------------

def test_an_unreadable_reply_is_refused_by_the_reader_and_never_cached(rig):
    from studio.judges import panel_eye
    r = rig(faults=[fault("unreadable", 1, "fx_caption")])
    said = r.media / "reply.txt"
    said.write_text('{"people": 2}', encoding="utf-8")
    r.fake.add_recordings([{"kind": "vl_text", "workflow_fp": r.fake.fingerprint("fx_caption"),
                            "values": CAPTION, "path": str(said), "seconds": 13.0, "source": "fx"}])
    assert comfy.cached_text("fx_caption", CAPTION, readable=panel_eye.is_json) == comfy_faults.UNREADABLE_TEXT
    assert not list((r.box / "library" / ".vlm_cache").rglob("*.txt"))
    assert comfy.cached_text("fx_caption", CAPTION, readable=panel_eye.is_json) == '{"people": 2}'


@needs_ffmpeg
@pytest.mark.parametrize("how", comfy_faults.CORRUPTIONS)
def test_each_corrupt_output_is_the_broken_file_it_names(rig, how):
    r = rig(faults=[fault("corrupt", detail=how)])
    rec = take_recording(r.media)
    r.fake.add_recordings([rec])
    out = comfy.run("fx_take", TAKE)[0]
    size, whole = out.stat().st_size, (r.media / "T05_try0.mp4").stat().st_size
    if how == "zero_byte":
        assert size == 0
    elif how == "truncated":
        assert 0 < size < whole and fake_comfy.video_info(out)[1] < 24
    elif how == "no_audio":
        assert not has_audio(out) and fake_comfy.video_info(out)[1] == 24
    else:
        assert has_audio(out) and fake_comfy.video_info(out)[1] not in (0, 24)
    assert r.answers()[-1]["fault"] == "corrupt" and r.answers()[-1]["corrupt"] == how


def test_a_video_corruption_on_a_picture_is_refused_when_the_fault_fires(rig):
    rig(faults=[fault("corrupt", 1, "fx_grid", detail="no_audio")])
    with pytest.raises(RuntimeError, match="no_audio"):
        comfy.run("fx_grid", {"prompt": "a", "seed": 1, "filename_prefix": "g"})


# ---- engine_ops.restart in a rehearsal (P4's fake_publish calls fake_comfy.restart()) ----

def test_the_module_restart_reaches_the_fake_in_this_process(rig):
    r = rig(faults=[fault("hang", 1, "fx_grid")])
    pid = comfy.submit(filled("fx_grid", {"prompt": "a", "seed": 1, "filename_prefix": "g"}))
    assert fake_comfy.restart(r.host) is True and comfy.lost(pid)


def test_from_a_child_process_the_module_restart_goes_over_http_even_to_a_lost_engine(rig):
    r = rig(faults=[fault("lost", 1, "fx_grid")])
    fake_comfy._LIVE.pop(r.fake.port)                       # as a drive child sees it: no instance here
    comfy.submit(filled("fx_grid", {"prompt": "a", "seed": 1, "filename_prefix": "g"}))
    assert engine_ops.alive(base_url=r.host) is False
    assert fake_comfy.restart(r.host) is False              # the admin route answers; the engine stays lost
    assert [row.get("call") for row in r.log()].count("restart") == 1


def test_the_module_restart_never_aims_at_the_real_engine():
    with pytest.raises(RuntimeError, match="8188"):
        fake_comfy.restart("http://127.0.0.1:8188")
