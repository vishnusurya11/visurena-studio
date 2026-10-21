"""The fake ComfyUI answers the REAL studio.comfy client on every route it uses, and labels each
answer exact, substituted or canned (2026-10-21_ep02_proof DESIGN 2.2, package P3).

Every test drives the real `comfy.run`, `run_text`, `cached_text`, `submit` + `wait_record`,
`free_models`, `interrupt`, `engine_ops` and `take_phases.ring` against a real HTTP server on
127.0.0.1:<free port>.  The client is pointed at it through `settings.comfy_host` of a sandbox
manifest (P1), never at :8188.  Recorded media are made in tmp by ffmpeg, never committed."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import pytest

from studio import comfy, compute_device, engine_ops, settings, take_phases
from studio.rehearsal import fake_comfy
from studio.rehearsal import workflow_fingerprint as wf

FIX = Path(__file__).resolve().parent / "fixtures" / "proof" / "fake_comfy"
WORKFLOWS = FIX / "workflows"
FFMPEG = shutil.which("ffmpeg")
needs_ffmpeg = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg is not on PATH")
TAKE = {"prompt": "Utterson walks the lane at night", "width": 512, "height": 512, "frames": 24,
        "seed": 1005, "ref_image_1": "utterson_ab12cd34.png", "filename_prefix": "ep_take_05"}


# ---- the rig: a sandbox manifest, the fake, the real client pointed at it ----------------

@dataclass
class Rig:
    box: Path
    fake: fake_comfy.FakeComfy
    host: str
    media: Path

    def log(self) -> list[dict]:
        return [json.loads(x) for x in (self.box / "engine_log.jsonl").read_text(encoding="utf-8").splitlines()]

    def answers(self) -> list[dict]:
        return [r for r in self.log() if r.get("call") == "prompt"]


def manifest_box(root: Path, port: int) -> Path:
    """The smallest sandbox settings accepts: library/ and rehearsal.json naming the fake's port."""
    box = root / f"sandbox_{port}"
    (box / "library").mkdir(parents=True)
    manifest = {"run_id": "fx", "comfy_host": f"http://127.0.0.1:{port}", "fakes": False,
                "real_library": str(root / "real_library")}
    (box / "rehearsal.json").write_text(json.dumps(manifest), encoding="utf-8")
    return box


def point_client(monkeypatch, box: Path) -> str:
    """The real client's constants as a rehearsal process binds them (settings, P1)."""
    env = {"VISURENA_LIBRARY": str(box / "library")}
    host = settings.comfy_host(env=env)
    for name, value in {"HOST": host, "COMFY_ROOT": settings.comfy_root(env=env), "WORKFLOWS": WORKFLOWS,
                        "VLM_CALLS": None, "TEXT_CACHE": box / "library" / ".vlm_cache",
                        "RESTART_POLL": 0.02}.items():
        monkeypatch.setattr(comfy, name, value)
    monkeypatch.setattr(compute_device, "live_claims", lambda **_: [])
    return host


@pytest.fixture
def rig(tmp_path, monkeypatch, real_comfy):
    """The real run/run_text/free_models (conftest's `real_comfy`), aimed at a fake on a free port."""
    started: list[fake_comfy.FakeComfy] = []

    def make(recordings=(), faults=(), **kw) -> Rig:
        port = fake_comfy.free_port()
        box = manifest_box(tmp_path, port)
        fake = fake_comfy.FakeComfy(box, recordings=recordings, workflows=WORKFLOWS, faults=faults,
                                    port=port, **kw).start()
        started.append(fake)
        media = tmp_path / "real_library" / "ep01"
        media.mkdir(parents=True, exist_ok=True)
        return Rig(box, fake, point_client(monkeypatch, box), media)

    yield make
    for fake in started:
        fake.stop()


# ---- recorded media, made by ffmpeg in tmp ----------------------------------------------

def make_video(path: Path, frames: int = 24, fps: int = 24) -> Path:
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=size=64x64:rate={fps}",
                    "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000", "-frames:v", str(frames),
                    "-t", f"{frames / fps:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    str(path)], check=True, capture_output=True)
    return path


def make_wav(path: Path, seconds: float, rate: int = 16000) -> Path:
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1), out.setsampwidth(2), out.setframerate(rate)
        out.writeframes((b"\x10\x00" * int(seconds * rate)))
    return path


def wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as got:
        return got.getnframes() / got.getframerate()


def fp(name: str) -> str:
    return wf.index(WORKFLOWS)[name]["fp"]


def filled(name: str, values: dict) -> dict:
    template, inject = comfy.load_workflow(name)
    return comfy.apply_inject(template, inject, values)


def take_recording(media: Path, values: dict = TAKE, tries: int = 0, seconds: float = 412.5) -> dict:
    graph = media / f"T05_try{tries}.graph.json"
    graph.write_text(json.dumps(filled("fx_take", values)), encoding="utf-8")
    video = make_video(media / f"T05_try{tries}.mp4")
    return {"kind": "take", "workflow_fp": fp("fx_take"), "key": {"index": 5}, "tries": tries,
            "graph": str(graph), "path": str(video), "seconds": seconds, "source": "fixture T05"}


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---- the workflow fingerprint -----------------------------------------------------------

def test_fingerprint_is_the_class_multiset_plus_the_inject_map():
    template, inject = wf.read_template(WORKFLOWS / "image" / "fx_caption.json")
    assert wf.fingerprint(template, inject) == wf.fingerprint(json.loads(json.dumps(template)), dict(inject))
    moved = {**inject, "seed": {"node": "1", "field": "seed"}}
    assert wf.fingerprint(template, moved) != wf.fingerprint(template, inject)
    assert wf.classes(template) == [["LoadImage", 1], ["PreviewAny", 1], ["Qwen3_VQA", 1]]


def test_identify_names_the_template_even_when_classes_tie_on_a_literal(monkeypatch):
    monkeypatch.setattr(comfy, "WORKFLOWS", WORKFLOWS)
    idx = wf.index(WORKFLOWS)
    assert idx["fx_caption"]["fp"] == idx["fx_caption_alt"]["fp"]      # same classes, same inject map
    for name in ("fx_caption", "fx_caption_alt", "fx_take", "fx_tts", "fx_grid"):
        graph = filled(name, {"seed": 7}) if name != "fx_take" else filled(name, TAKE)
        assert wf.identify(graph, idx) == name


def test_identify_survives_added_nodes_a_take_graph_grows(monkeypatch):
    monkeypatch.setattr(comfy, "WORKFLOWS", WORKFLOWS)
    graph = filled("fx_take", TAKE)
    graph["30"] = {"class_type": "LoadImage", "inputs": {"image": "anchor_1.png"}}
    graph["31"] = {"class_type": "MiniMaxH3AddGuide", "inputs": {"image": ["30", 0], "frame": 0}}
    assert wf.identify(graph, wf.index(WORKFLOWS)) == "fx_take"
    assert wf.identify({"1": {"class_type": "Nothing", "inputs": {}}}, wf.index(WORKFLOWS)) is None


def test_graph_fields_are_every_literal_input_and_the_class_set(monkeypatch):
    monkeypatch.setattr(comfy, "WORKFLOWS", WORKFLOWS)
    fields = wf.graph_fields(filled("fx_take", TAKE))
    assert fields["12.noise_seed"] == 1005 and fields["8.length"] == 24
    assert "8.model" not in fields                                    # a link is not a field
    assert fields["classes"] == wf.classes(filled("fx_take", TAKE))
    diff = wf.field_diff(wf.graph_fields(filled("fx_take", {**TAKE, "seed": 9})), fields)
    assert diff == [{"field": "12.noise_seed", "recorded": 1005, "asked": 9}]


def test_the_index_reads_templates_and_never_changes_them():
    before = {p: (p.stat().st_mtime_ns, sha(p)) for p in WORKFLOWS.rglob("*.json")}
    idx = wf.index(WORKFLOWS)
    assert set(idx) == {"fx_take", "fx_caption", "fx_caption_alt", "fx_tts", "fx_grid"}
    assert {p: (p.stat().st_mtime_ns, sha(p)) for p in WORKFLOWS.rglob("*.json")} == before


@pytest.mark.skipif(not (wf.WORKFLOWS / "image" / "image_qwen3vl_caption.json").exists(),
                    reason="comfy_studio workflows are not on this machine")
def test_a_real_template_named_by_its_file_fingerprints_as_the_client_loads_it():
    template, inject = comfy.load_workflow("image_qwen3vl_caption")
    path = wf.WORKFLOWS / "image" / "image_qwen3vl_caption.json"
    assert wf.fingerprint(*wf.read_template(path)) == wf.fingerprint(template, inject)


# ---- exact, substituted, canned through the real client ---------------------------------

@needs_ffmpeg
def test_an_exact_take_is_the_recorded_bytes_under_the_engines_output_name(rig):
    r = rig()
    rec = take_recording(r.media)
    r.fake.add_recordings([rec])
    out = comfy.run("fx_take", TAKE)
    assert out == [r.box / "comfy" / "output" / "ep_take_05_00001_.mp4"]
    assert sha(out[0]) == sha(Path(rec["path"]))
    row = r.answers()[-1]
    assert row["class"] == "exact" and row["diff"] == [] and row["workflow"] == "fx_take"
    assert row["recording"] == rec["source"] and row["sha"] == sha(out[0])


@needs_ffmpeg
def test_a_second_answer_for_one_prefix_counts_up_like_the_engine(rig):
    r = rig()
    r.fake.add_recordings([take_recording(r.media)])
    comfy.run("fx_take", TAKE)
    assert comfy.run("fx_take", TAKE)[0].name == "ep_take_05_00002_.mp4"


@needs_ffmpeg
def test_a_take_of_the_same_index_and_try_is_substituted_and_trimmed_to_the_asked_frames(rig):
    r = rig()
    r.fake.add_recordings([take_recording(r.media)])
    out = comfy.run("fx_take", {**TAKE, "seed": 2222, "frames": 12})
    row = r.answers()[-1]
    assert row["class"] == "substituted" and row["index"] == 5 and row["tries"] == 0
    assert {d["field"] for d in row["diff"]} == {"12.noise_seed", "8.length"}
    assert fake_comfy.video_info(out[0])[1] == 12


@needs_ffmpeg
def test_a_take_is_looped_up_to_more_frames_than_were_recorded(rig):
    r = rig()
    r.fake.add_recordings([take_recording(r.media)])
    out = comfy.run("fx_take", {**TAKE, "seed": 3, "frames": 40})
    assert r.answers()[-1]["class"] == "substituted" and fake_comfy.video_info(out[0])[1] == 40


@needs_ffmpeg
def test_a_take_at_a_try_count_never_recorded_is_canned_grey(rig):
    r = rig()
    r.fake.add_recordings([take_recording(r.media)])
    comfy.run("fx_take", {**TAKE, "seed": 1})                       # try 0 of index 5: substituted
    out = comfy.run("fx_take", {**TAKE, "seed": 2})                 # try 1: nothing recorded
    row = r.answers()[-1]
    assert row["class"] == "canned" and row["tries"] == 1
    assert fake_comfy.video_info(out[0])[1] == 24 and fake_comfy.grey(out[0])


@needs_ffmpeg
def test_a_tts_line_of_the_same_voice_is_substituted_and_stretched(rig):
    r = rig()
    ref = {"ref_audio": "jekyll_0a1b2c.wav", "ref_text": "I am Henry Jekyll.", "seed": 1,
           "filename_prefix": "line_01", "target_text": "Hyde is near."}
    wav = make_wav(r.media / "line_01.wav", 2.0)
    r.fake.add_recordings([{"kind": "tts_line", "workflow_fp": fp("fx_tts"), "key": {"speaker": "jekyll"},
                            "values": ref, "path": str(wav), "seconds": 9.0, "source": "fixture line 01"}])
    out = comfy.run("fx_tts", {**ref, "target_text": "Hyde is near. Hyde is near"})
    row = r.answers()[-1]
    assert row["class"] == "substituted" and out[0].suffix == ".wav"
    assert 3.5 <= wav_seconds(out[0]) <= 4.5                        # twice the text: half the tempo
    other = comfy.run("fx_tts", {**ref, "ref_audio": "poole_99.wav", "filename_prefix": "line_02"})
    assert r.answers()[-1]["class"] == "canned" and fake_comfy.silent(other[0])


def test_an_unrecorded_picture_is_canned_grey(rig):
    r = rig()
    out = comfy.run("fx_grid", {"prompt": "a lane", "seed": 3, "filename_prefix": "grid_01"})
    assert out[0].name == "grid_01_00001_.png" and fake_comfy.grey(out[0])
    assert r.answers()[-1]["class"] == "canned" and r.answers()[-1]["clock"] is None


def test_a_canned_vl_reply_is_one_every_reader_refuses_and_the_cache_never_keeps(rig):
    from studio import panel_content, picture_read
    from studio.judges import panel_eye
    r = rig()
    values = {"image_1": "frame_aa.png", "prompt": "list the people", "seed": 1}
    text = comfy.cached_text("fx_caption", values, readable=panel_eye.is_json)
    assert text == fake_comfy.CANNED_TEXT
    assert not panel_eye.is_json(text) and not panel_content.readable(text) and not picture_read.readable(text)
    assert not list((r.box / "library" / ".vlm_cache").rglob("*.txt"))
    assert r.answers()[-1]["class"] == "canned" and r.answers()[-1]["kind"] == "vl_text"


def test_a_recorded_vl_reply_is_exact_on_its_values_and_is_cached(rig):
    from studio.judges import panel_eye
    r = rig()
    values = {"image_1": "frame_aa.png", "prompt": "list the people", "seed": 1}
    said = r.media / "reply.txt"
    said.write_text('{"people": 2}', encoding="utf-8")
    r.fake.add_recordings([{"kind": "vl_text", "workflow_fp": fp("fx_caption"), "key": "k", "values": values,
                            "path": str(said), "seconds": 13.2, "source": "fixture vl"}])
    assert comfy.cached_text("fx_caption", values, readable=panel_eye.is_json) == '{"people": 2}'
    assert r.answers()[-1]["class"] == "exact"
    assert len(list((r.box / "library" / ".vlm_cache").rglob("*.txt"))) == 1


# ---- history, queue and the side routes -------------------------------------------------

@needs_ffmpeg
def test_history_spaces_the_run_by_the_recorded_seconds_and_says_so(rig):
    r = rig()
    r.fake.add_recordings([take_recording(r.media, seconds=412.5)])
    record = comfy.wait_record(comfy.submit(filled("fx_take", TAKE)), timeout=10, poll=0.02)
    t0, t1 = take_phases.window(record)
    assert round(t1 - t0, 1) == 412.5 and record["status"]["completed"] is True
    assert record["rehearsal"] == {"clock": "recorded", "match": "exact"}
    assert r.answers()[-1]["clock"] == "recorded" and r.answers()[-1]["seconds"] == 412.5
    assert comfy.outputs_of(record)[0].exists()


def test_the_side_routes_answer_the_engine_ops_and_the_ring(rig):
    r = rig()
    assert engine_ops.alive(base_url=r.host) is True
    assert engine_ops.queue(base_url=r.host)["running_ids"] == [] and comfy.queue_counts() == (0, 0)
    assert engine_ops.free(base_url=r.host) is True
    comfy.free_models()
    comfy.interrupt()
    comfy.run_text("fx_caption", {"image_1": "x.png", "prompt": "p", "seed": 1})
    entries = take_phases.ring()
    assert entries and all({"t", "m"} <= set(e) for e in entries)
    calls = [row["call"] for row in r.log()[1:]]
    assert calls.count("free") == 2 and calls.count("interrupt") == 1 and calls.count("prompt") == 1


def test_the_queue_delete_route_drops_a_pending_job(rig):
    r = rig()
    r.fake.hold(True)
    first = comfy.submit(filled("fx_grid", {"prompt": "a", "seed": 1, "filename_prefix": "g1"}))
    second = comfy.submit(filled("fx_grid", {"prompt": "b", "seed": 2, "filename_prefix": "g2"}))
    assert comfy.running(first) and comfy.pending(second)
    comfy._post("/queue", {"delete": [second]})
    assert not comfy.pending(second) and comfy.running(first)
    r.fake.hold(False)
    assert comfy.wait_record(first, timeout=5, poll=0.02)["status"]["completed"]


@needs_ffmpeg
def test_a_paced_job_runs_for_its_recorded_seconds_before_it_is_in_history(rig):
    r = rig(pace=1.0)
    r.fake.add_recordings([take_recording(r.media, seconds=0.6)])
    pid = comfy.submit(filled("fx_take", TAKE))
    assert comfy.running(pid) and comfy.history(pid) == {}
    assert comfy.wait_record(pid, timeout=5, poll=0.02)["status"]["completed"]


def test_the_engine_log_opens_with_its_shape_header(rig):
    r = rig()
    head = r.log()[0]
    assert head["header"] is True and head["shape"] in ("uncalibrated", "calibrated")
    assert head["url"] == r.host and head["fake"] == "studio.rehearsal.fake_comfy"


def test_a_graph_the_engine_cannot_read_is_a_400_the_client_names():
    with pytest.raises(ValueError):
        fake_comfy.prompt_graph(b"not json")


def test_recordings_load_with_paths_relative_to_their_index(tmp_path):
    (tmp_path / "recordings.json").write_text(json.dumps([{"kind": "grid", "workflow_fp": "x",
                                                           "path": "grids/g.png", "graph": "g.json"}]))
    rec = fake_comfy.load_recordings(tmp_path / "recordings.json")[0]
    assert rec["path"] == str(tmp_path / "grids" / "g.png") and rec["graph"] == str(tmp_path / "g.json")


def test_the_fake_binds_from_a_manifest_on_its_own_port(tmp_path):
    port = fake_comfy.free_port()
    box = manifest_box(tmp_path, port)
    with fake_comfy.FakeComfy.from_manifest(box, workflows=WORKFLOWS) as fake:
        assert fake.url == f"http://127.0.0.1:{port}" and engine_ops.alive(base_url=fake.url)


def test_the_fake_refuses_the_real_engines_port(tmp_path):
    with pytest.raises(ValueError, match="8188"):
        fake_comfy.FakeComfy(tmp_path, workflows=WORKFLOWS, port=8188)


@needs_ffmpeg
def test_inside_an_armed_fence_the_fake_reads_the_real_root_and_trips_nothing(rig):
    from studio.rehearsal import fence
    r = rig()
    rec = take_recording(r.media)                         # made BEFORE the fence: the stand-in real library
    before = sha(Path(rec["path"]))
    r.fake.add_recordings([rec])
    fence.install(fence.Fence.of(roots=(r.media.parent,), sandbox=r.box, repo=settings.REPO, ports=(r.fake.port,)))
    try:
        fitted = comfy.run("fx_take", {**TAKE, "seed": 77, "frames": 12})     # ffmpeg reads the real root
        again = comfy.run("fx_take", {**TAKE, "seed": 77, "frames": 12})      # the same try: substituted again
    finally:
        fence.disarm()
    assert [row["class"] for row in r.answers()] == ["substituted", "substituted"]
    assert again[0].exists() and fake_comfy.video_info(fitted[0])[1] == 12
    assert not (r.box / "tripwire.jsonl").exists() and sha(Path(rec["path"])) == before


# ---- P2's recordings index (studio/rehearsal/recordings.py) joins as it is written -------

def p2():
    return pytest.importorskip("studio.rehearsal.recordings")


def text_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_the_bare_multiset_fingerprint_is_p2s_classes_fp(monkeypatch):
    monkeypatch.setattr(comfy, "WORKFLOWS", WORKFLOWS)
    graph = filled("fx_take", TAKE)
    assert wf.multiset_fp(graph) == p2().classes_fp(graph)


def test_p2s_index_loads_with_paths_relative_to_the_library_root(tmp_path):
    (tmp_path / "idx.json").write_text(json.dumps({"source": "b/episodes/ep01", "entries": [
        {"kind": "take", "workflow_fp": "x", "key": [5, 0], "path": "b/episodes/ep01/takes/r2v/T05.mp4"}]}))
    rec = fake_comfy.load_recordings(tmp_path / "idx.json", root=tmp_path / "lib")[0]
    assert rec["path"] == str(tmp_path / "lib" / "b" / "episodes" / "ep01" / "takes" / "r2v" / "T05.mp4")


@needs_ffmpeg
def test_a_p2_take_entry_is_exact_on_its_section_0_fields_and_substitutes_on_index_and_try(rig):
    rec_mod, r = p2(), rig()
    graph = filled("fx_take", TAKE)
    video = make_video(r.media / "T05.mp4")
    r.fake.add_recordings([rec_mod.entry("take", [5, 0], rec_mod.graph_fields(graph), str(video), 300.0,
                                         "ep01/takes/r2v/T05.graph.json", tries=0,
                                         workflow_fp=rec_mod.classes_fp(graph))])
    comfy.run("fx_take", TAKE)
    comfy.run("fx_take", {**TAKE, "filename_prefix": "ep_take_05", "seed": 1005, "prompt": "Utterson runs"})
    rows = r.answers()
    assert [row["class"] for row in rows] == ["exact", "canned"]           # a new prompt is try 1: none
    assert rows[1]["diff"] == [{"field": "prompts", "recorded": [TAKE["prompt"]], "asked": ["Utterson runs"]}]


def test_a_p2_vl_entry_is_exact_on_the_readers_own_cache_key(rig):
    from studio.judges import panel_eye
    rec_mod, r = p2(), rig()
    values = {"image_1": "panel_ab12cd34.png", "prompt": "who is here", "seed": 11}
    said = r.media / "kk.txt"
    said.write_text('{"people": 1}', encoding="utf-8")
    r.fake.add_recordings([rec_mod.entry("vl_text", comfy.text_key("fx_caption", values),
                                         {"ask": "panel_content", "workflow": "fx_caption"}, str(said), 12.0,
                                         "vlm_calls.jsonl fit")])
    assert comfy.cached_text("fx_caption", values, readable=panel_eye.is_json) == '{"people": 1}'
    assert comfy.run_text("fx_caption", {**values, "seed": 12}) == fake_comfy.CANNED_TEXT
    assert [row["class"] for row in r.answers()] == ["exact", "canned"]


def test_a_p2_grid_entry_is_exact_on_seed_and_prompt_sha_and_substitutes_on_cells(rig):
    rec_mod, r = p2(), rig()
    png = r.media / "grid.png"
    fake_comfy.grey_png(png)
    r.fake.add_recordings([rec_mod.entry("grid", ["S1", 3, text_sha("a lane")], {"cells": None, "name": "g"},
                                         str(png), 95.0, "grids/g.json")])
    comfy.run("fx_grid", {"prompt": "a lane", "seed": 3, "filename_prefix": "grid_01"})
    comfy.run("fx_grid", {"prompt": "a hall", "seed": 4, "filename_prefix": "grid_02"})
    assert [row["class"] for row in r.answers()] == ["exact", "substituted"]


def test_a_p2_tts_entry_needs_the_voice_map_to_be_exact(rig):
    r = rig(voices={"jekyll_0a1b2c.wav": "jekyll"})
    wav = make_wav(r.media / "l1.wav", 1.0)
    p = p2()
    r.fake.add_recordings([p.entry("tts_line", ["jekyll", text_sha("Hyde is near.")], {"text": "Hyde is near."},
                                   str(wav), None, "lines.json")])
    ref = {"ref_audio": "jekyll_0a1b2c.wav", "ref_text": "I am Jekyll.", "seed": 1, "filename_prefix": "l"}
    comfy.run("fx_tts", {**ref, "target_text": "Hyde is near."})
    comfy.run("fx_tts", {**ref, "target_text": "Hyde is near. Hyde is near"})
    comfy.run("fx_tts", {**ref, "ref_audio": "poole_1.wav", "target_text": "Hyde is near."})
    assert [row["class"] for row in r.answers()] == ["exact", "substituted", "substituted"]
    assert r.answers()[2]["speaker"] is None                                # same text, voice unverified


def test_a_p2_refine_crop_is_exact_on_the_staged_source_bytes(rig):
    rec_mod, r = p2(), rig()
    staged = r.box / "comfy" / "input" / "T05_p1_src_ab12cd34.png"
    fake_comfy.grey_png(staged)
    out = r.media / "T05_p1.png"
    fake_comfy.grey_png(out)
    r.fake.add_recordings([rec_mod.entry("refine_crop", sha(staged), {"take": "T05", "workflow": "fx_grid"},
                                         str(out), 40.0, "refine.json")])
    comfy.run("fx_grid", {"prompt": staged.name, "seed": 1, "filename_prefix": "crop"})
    assert r.answers()[-1]["class"] == "exact"
