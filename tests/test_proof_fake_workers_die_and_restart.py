"""The face detect, anime id and whisper workers are faked at the PROCESS boundary (DESIGN 2.3,
R10, F17; 2026-10-21_ep02_proof P4).

Only each module's pure `worker_argv` is rebound: the REAL spawn, Worker ready handshake, idle
exit, routed_whisper's SPAWNS = 2 restart after a death and anime_id's one fresh retry all run
against a real child process speaking the same JSON line protocol.  The child answers from a
memo keyed by the asked file's bytes (sha256); a miss is canned (an empty detection, an error
for an identity ask, an EMPTY transcript: never the requested text); it exits on line `die_at`."""
from __future__ import annotations

import json
import sys
import time
from contextlib import ExitStack, nullcontext
from pathlib import Path

import numpy as np
import pytest

from studio import anime_id, compute_device, face_detect, routed_whisper, voice_qc
from studio.rehearsal import fake_workers, fakes


@pytest.fixture
def box(tmp_path, monkeypatch):
    monkeypatch.setattr(compute_device, "claim", lambda job, root=None: nullcontext())
    (tmp_path / "memos").mkdir()
    yield tmp_path
    fakes.uninstall()


def install(box: Path, **manifest) -> None:
    fakes.install({"memos": str(box / "memos"), **manifest}, box)


def clip(box: Path, name: str, data: bytes) -> Path:
    path = box / name
    path.write_bytes(data)
    return path


def memo(box: Path, kind: str, answers: dict) -> None:
    (box / "memos" / f"{kind}.json").write_text(json.dumps(answers), encoding="utf-8")


def rows(box: Path) -> list[dict]:
    path = box / "workers.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def test_each_argv_names_the_fake_worker_under_this_python_and_never_minus_i(box):
    install(box, worker_die_at={"whisper": 3})
    for argv, name in ((face_detect.worker_argv(Path("p"), Path("w"), "cpu"), "detect"),
                       (anime_id.worker_argv(Path("p"), Path("r"), "cpu"), "anime"),
                       (routed_whisper.worker_argv(Path("p"), "m", "r"), "whisper")):
        assert argv[0] == sys.executable and "-I" not in argv
        assert Path(argv[1]).name == f"fake_{name}_worker.py" and Path(argv[1]).is_file()
    assert routed_whisper.worker_argv(Path("p"), "m", "r")[3] == "3"


def test_a_whisper_memo_hit_is_the_real_hearing_and_a_miss_hears_nothing(box):
    heard, unheard = clip(box, "a.wav", b"line one"), clip(box, "b.wav", b"line two")
    memo(box, "whisper", {fake_workers.file_key(heard): "the door was locked"})
    install(box)
    worker = routed_whisper.Worker(routed_whisper.spawn_worker(None))
    try:
        assert worker(heard) == "the door was locked" and worker(unheard) == ""
    finally:
        worker.close()
    assert [r["label"] for r in rows(box) if r.get("event") == "answer"] == ["exact", "canned"]


def test_a_worker_that_dies_on_its_line_is_spawned_once_more_then_the_cpu_ear(box):
    wav = clip(box, "a.wav", b"x")
    memo(box, "whisper", {fake_workers.file_key(wav): "heard"})
    install(box, worker_die_at={"whisper": 2})
    cpu = []
    ear = routed_whisper.Routed(lambda: (lambda c: cpu.append(c) or "cpu ear"), routed_whisper.spawn_worker,
                                ExitStack(), busy=lambda: False)
    said = [ear(wav) for _ in range(4)]
    assert said == ["heard", "heard", "cpu ear", "cpu ear"] and ear.spawns == routed_whisper.SPAWNS
    assert sum(r.get("event") == "died" for r in rows(box)) == 2


def test_the_detector_answers_its_memo_and_a_miss_is_an_empty_detection(box):
    take, other = clip(box, "T01.mp4", b"take bytes"), clip(box, "T02.mp4", b"other")
    dets = {"0": [{"box": [1, 2, 30, 40], "score": 0.91}]}
    memo(box, "detect", {fake_workers.detect_key(take, face_detect.EVERY): dets})
    install(box)
    worker = face_detect.Worker(face_detect.spawn("cpu"))
    try:
        assert worker(take) == {0: dets["0"]} and worker(other) == {}
    finally:
        worker.close()


def test_an_idle_worker_exits_and_the_finder_starts_it_again(box):
    take = clip(box, "T01.mp4", b"t")
    install(box, scale=600)
    finder = face_detect.Finder(loose=lambda f: [], route=lambda job, gb: "cpu", busy=lambda: False)
    try:
        assert finder(take, []) == {}
        first = finder.worker.proc.pid
        deadline = time.time() + 10
        while not finder.worker.exited() and time.time() < deadline:
            time.sleep(0.05)
        assert finder.worker.exited()
        finder(take, [])
        assert finder.worker.proc.pid != first and not finder.broken
    finally:
        finder.close()


def test_anime_id_answers_its_memo_and_a_miss_leaves_the_terms_unread(box):
    install(box)
    sheet = np.zeros((4, 4, 3), np.uint8)
    reader = anime_id.Reader(route=lambda job, gb: "cpu", busy=lambda: False)
    try:
        assert reader(sheet, [sheet], [sheet + 1]) is None and reader.broken
    finally:
        reader.close()
    assert sum(r.get("label") == "canned" for r in rows(box)) == 2   # the real one fresh retry


def test_anime_id_memo_keys_on_the_pictures_bytes_in_order(box):
    a, b = clip(box, "sheet.png", b"A"), clip(box, "src0.png", b"B")
    memo(box, "anime", {fake_workers.images_key([a, b]): {"ccip": [[0.0, 0.1]], "clip": [[1.0, 0.9]]}})
    install(box)
    worker = anime_id.Worker(anime_id.spawn("cpu"))
    try:
        ccip, clip_cos = worker([a, b])
    finally:
        worker.close()
    assert ccip.tolist() == [[0.0, 0.1]] and clip_cos.tolist() == [[1.0, 0.9]]
    assert fake_workers.images_key([a, b]) != fake_workers.images_key([b, a])


def test_the_in_process_cpu_ear_reads_the_same_memo(box):
    wav = clip(box, "a.wav", b"y")
    memo(box, "whisper", {fake_workers.file_key(wav): "the same hearing"})
    install(box)
    assert voice_qc.cpu_transcriber()(wav) == "the same hearing"
    assert voice_qc.transcriber()(clip(box, "b.wav", b"z")) == ""


def test_the_vram_read_is_the_manifests_never_nvidia_smi(box):
    install(box, vram_free_mb=1234)
    assert compute_device.smi_free_mb() == 1234
