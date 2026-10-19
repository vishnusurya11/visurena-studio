"""The device router: the owner's rule for every heavy non-render job (2026-10-18):
"if the GPU is rendering, do this on the CPU; if the GPU is empty, do it on the GPU."

`device_for(job, need_gb)` says "cuda" only when the ComfyUI queue is empty (twice,
SETTLE_S apart: the gap between two submissions of one render step is not idle), no
GPU claim of ours is live (the av3 master pass, the whisper worker), and enough VRAM
is free after the engine was asked to free its models.  Every decision is logged
with its reason.  Every probe is injected: no test reaches ComfyUI or nvidia-smi."""
from __future__ import annotations

import json
import os
import time

from studio import compute_device as cd


class Box:
    """A probe whose answers a test sets; it records the /free posts."""

    def __init__(self, queues=((0, 0), (0, 0)), free=20000, claims=(), env=None):
        self.queues, self.free, self.held, self.env = list(queues), free, list(claims), env or {}
        self.freed, self.slept = 0, []

    def probe(self) -> cd.Probe:
        return cd.Probe(queue=self.queue, free_mb=lambda: self.free, free_models=self.post_free,
                        claims=lambda: self.held, sleep=self.slept.append, env=self.env)

    def queue(self):
        return self.queues.pop(0) if len(self.queues) > 1 else self.queues[0]

    def post_free(self):
        self.freed += 1


def routed(box: Box, need_gb: float = 4.0, log=None):
    seen = []
    device = cd.device_for("whisper", need_gb, probe=box.probe(), log=log or seen.append)
    return device, seen


# -- the decision ----------------------------------------------------------------------

def test_an_idle_gpu_routes_to_cuda_and_says_so():
    device, seen = routed(Box())
    assert device == "cuda"
    assert seen[0].device == "cuda" and seen[0].reason == "GPU idle" and seen[0].job == "whisper"


def test_a_running_render_routes_to_cpu_without_freeing_anything():
    box = Box(queues=[(1, 0)])
    device, seen = routed(box)
    assert device == "cpu" and "render running" in seen[0].reason
    assert box.freed == 0


def test_a_pending_render_routes_to_cpu():
    device, seen = routed(Box(queues=[(0, 2)]))
    assert device == "cpu" and "render queued" in seen[0].reason


def test_a_render_submitted_inside_the_settle_gap_routes_to_cpu():
    box = Box(queues=[(0, 0), (1, 0)])
    device, seen = routed(box)
    assert device == "cpu" and "render running" in seen[0].reason
    assert box.slept == [cd.SETTLE_S] and box.freed == 0


def test_a_live_gpu_claim_routes_to_cpu():
    box = Box(claims=[{"job": "av3 master", "pid": 1, "at": time.time()}])
    device, seen = routed(box)
    assert device == "cpu" and "av3 master" in seen[0].reason


def test_no_free_when_vram_enough():
    box = Box(free=20000)
    assert routed(box)[0] == "cuda" and box.freed == 0


def test_one_free_when_short():
    box = Box(free=1000)
    routed(box, need_gb=4.0)
    assert box.freed == 1


def test_a_busy_queue_never_frees():
    box = Box(queues=[(1, 0)], free=1000)
    routed(box)
    assert box.freed == 0


def test_a_down_engine_gives_a_cpu_decision_with_that_reason():
    def down():
        raise ConnectionError("refused")
    probe = Box().probe()
    probe = cd.Probe(queue=down, free_mb=probe.free_mb, free_models=probe.free_models,
                     claims=probe.claims, sleep=probe.sleep, env={})
    seen = []
    assert cd.device_for("x", 1, probe=probe, log=seen.append) == "cpu"
    assert seen[0].reason == "engine unreachable"


def test_too_little_vram_after_the_free_routes_to_cpu():
    device, seen = routed(Box(free=3000), need_gb=4.0)
    assert device == "cpu" and "VRAM" in seen[0].reason and "4" in seen[0].reason


def test_an_unreadable_nvidia_smi_routes_to_cpu():
    device, seen = routed(Box(free=None))
    assert device == "cpu" and "nvidia-smi" in seen[0].reason


def test_the_kill_switch_forces_cpu_before_any_probe():
    box = Box(env={cd.SETTING: "cpu"})
    device, seen = routed(box)
    assert device == "cpu" and cd.SETTING in seen[0].reason and box.freed == 0


def test_a_probe_that_raises_routes_to_cpu_with_its_error():
    def broken():
        raise OSError("engine gone")
    probe = Box().probe()
    probe = cd.Probe(queue=broken, free_mb=probe.free_mb, free_models=probe.free_models,
                     claims=probe.claims, sleep=probe.sleep, env={})
    seen = []
    assert cd.device_for("x", 1, probe=probe, log=seen.append) == "cpu"
    assert "router error" in seen[0].reason and "engine gone" in seen[0].reason


def test_freed_vram_is_waited_for_a_few_polls():
    reads = iter([1000, 1000, 9000])
    box = Box()
    probe = box.probe()
    probe = cd.Probe(queue=probe.queue, free_mb=lambda: next(reads), free_models=probe.free_models,
                     claims=probe.claims, sleep=probe.sleep, env={})
    assert cd.device_for("x", 4, probe=probe, log=lambda d: None) == "cuda"


# -- the parts -------------------------------------------------------------------------

def test_nvidia_smi_free_memory_is_parsed_in_mib():
    assert cd.parse_free_mb("14375\n") == 14375
    assert cd.parse_free_mb("14375\n2000\n") == 14375      # the first GPU
    assert cd.parse_free_mb("") is None and cd.parse_free_mb("N/A") is None


def test_a_claim_is_live_while_held_and_gone_after(tmp_path):
    with cd.claim("av3 master", root=tmp_path):
        live = cd.live_claims(root=tmp_path)
        assert [c["job"] for c in live] == ["av3 master"]
    assert cd.live_claims(root=tmp_path) == []


def test_a_stale_claim_is_ignored(tmp_path):
    (tmp_path / "old_1.json").write_text(json.dumps({"job": "old", "pid": 1, "at": 0}), encoding="utf-8")
    assert cd.live_claims(root=tmp_path, now=cd.STALE_S + 10) == []


def test_a_garbled_claim_is_ignored(tmp_path):
    (tmp_path / "bad_1.json").write_text("{not json", encoding="utf-8")
    assert cd.live_claims(root=tmp_path) == []


def test_a_decision_line_names_job_device_and_reason():
    line = cd.Decision("panel_eye", "cpu", "render running (1 running, 0 pending)").line()
    assert line == "DEVICE panel_eye -> cpu: render running (1 running, 0 pending)"


def test_decisions_are_appended_to_the_log_file(tmp_path):
    path = tmp_path / "decisions.jsonl"
    cd.write_decision(cd.Decision("whisper", "cuda", "GPU idle"), path)
    cd.write_decision(cd.Decision("encode", "cpu", "render running"), path)
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]
    assert [r["device"] for r in rows] == ["cuda", "cpu"] and rows[0]["job"] == "whisper"


# -- claim liveness ---------------------------------------------------------------------

def put(folder, name, pid, at):
    (folder / f"{name}.json").write_text(json.dumps({"job": name, "pid": pid, "at": at}), encoding="utf-8")


def test_dead_pid_claim_ignored(tmp_path):
    put(tmp_path, "gone", 111, time.time())
    put(tmp_path, "alive", 222, time.time())
    live = cd.live_claims(root=tmp_path, alive=lambda pid: pid == 222)
    assert [c["job"] for c in live] == ["alive"]


def test_own_pid_claim_ignored(tmp_path):
    put(tmp_path, "mine", 333, time.time())
    put(tmp_path, "theirs", 444, time.time())
    live = cd.live_claims(root=tmp_path, own_pid=333, alive=lambda pid: True)
    assert [c["job"] for c in live] == ["theirs"]


def test_stale_heartbeat_dropped(tmp_path):
    put(tmp_path, "silent", 555, 1000.0)
    assert cd.live_claims(root=tmp_path, now=1000.0 + cd.STALE_S + 1, alive=lambda pid: True) == []
    assert cd.STALE_S == 600.0


def test_a_beat_refreshes_the_claim_time(tmp_path):
    put(tmp_path, "held", 666, 1000.0)
    cd.beat(tmp_path / "held.json", now=5000.0)
    assert json.loads((tmp_path / "held.json").read_text(encoding="utf-8"))["at"] == 5000.0


def test_a_missing_pid_is_not_alive():
    assert cd.pid_alive(os.getpid()) is True and cd.pid_alive(0) is False
