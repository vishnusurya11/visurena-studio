"""The master encode follows the device router (owner 2026-10-18): NVENC at its
highest-quality preset when the GPU is idle, today's x264 byte-for-byte when it is
not.  No test runs an encoder; the argv is the contract."""
from __future__ import annotations

from pathlib import Path

from studio import master_upscale as mu
from studio import video_encoder as ve

ASSEMBLE = ["-c:v", "libx264", "-preset", "fast", "-crf", "17", "-c:a", "aac", "-ar", "48000"]


def pairs(args: list[str]) -> dict:
    return {args[i]: args[i + 1] for i in range(0, len(args) - 1) if args[i].startswith("-")}


def test_the_cpu_route_is_todays_argv_unchanged():
    assert ve.video_args(mu.ENCODE, "cpu") == mu.ENCODE
    assert ve.video_args(ASSEMBLE, "cpu") == ASSEMBLE


def test_the_cpu_route_hands_back_a_copy_not_the_constant():
    got = ve.video_args(mu.ENCODE, "cpu")
    got.append("x")
    assert mu.ENCODE[-1] != "x"


def test_the_cuda_route_is_nvenc_at_p7_constant_quality():
    got = pairs(ve.video_args(mu.ENCODE, "cuda"))
    assert got["-c:v"] == "h264_nvenc" and got["-preset"] == "p7" and got["-tune"] == "hq"
    assert got["-rc"] == "vbr" and got["-b:v"] == "0" and got["-multipass"] == "fullres"
    assert got["-cq"] == str(14 + ve.CQ_OFFSET)
    assert "-crf" not in got


def test_the_cuda_route_keeps_every_other_argument_in_order():
    got = ve.video_args(mu.ENCODE, "cuda")
    tail = ["-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
    assert got[-len(tail):] == tail


def test_args_without_x264_are_left_alone_on_cuda():
    copy = ["-c:v", "copy", "-c:a", "aac"]
    assert ve.video_args(copy, "cuda") == copy


def test_the_master_encode_argv_carries_the_routed_codec(tmp_path):
    cpu = mu.encode_argv(tmp_path / "l.txt", tmp_path / "o.mp4", 3072, 3072, 24)
    gpu = mu.encode_argv(tmp_path / "l.txt", tmp_path / "o.mp4", 3072, 3072, 24, encoder="cuda")
    assert "libx264" in cpu and "h264_nvenc" not in cpu
    assert "h264_nvenc" in gpu and "libx264" not in gpu


def test_the_lanczos_master_carries_the_routed_codec(tmp_path):
    gpu = mu.lanczos_argv(tmp_path / "l.txt", tmp_path / "o.mp4", 768, 768, mu.LANCZOS, encoder="cuda")
    assert "h264_nvenc" in gpu
    assert mu.lanczos_argv(tmp_path / "l.txt", tmp_path / "o.mp4", 768, 768, mu.LANCZOS)[-len(mu.ENCODE) - 1:-1] \
        == mu.ENCODE


def test_the_av3_job_carries_the_encoder_and_defaults_to_cpu(tmp_path):
    job = mu.av3_job(tmp_path / "l.txt", tmp_path / "o.mp4", 64, 64, mu.choice({}), 24, [], [], Path("w.pth"))
    assert job["encoder"] == "cpu"
    job = mu.av3_job(tmp_path / "l.txt", tmp_path / "o.mp4", 64, 64, mu.choice({}), 24, [], [], Path("w.pth"),
                     encoder="cuda")
    assert job["encoder"] == "cuda"


def test_the_encoder_is_asked_of_the_router_under_its_own_name():
    asked = []

    def router(job, need_gb, **kw):
        asked.append((job, need_gb))
        return "cuda"
    assert ve.encoder_for("master encode", route=router) == "cuda"
    assert asked == [("master encode", ve.NVENC_GB)]


def _assemble():
    import importlib.util
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("ep_assemble_enc", root / "scripts" / "episode" / "assemble.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_episode_master_asks_the_router_and_hands_the_answer_to_the_tail(tmp_path, monkeypatch):
    from contextlib import nullcontext

    from studio import episode_clock
    ep, seen = _assemble(), {}
    monkeypatch.setattr(ve, "encoder_for", lambda job, route=None: seen.setdefault("job", job) and "cuda")
    monkeypatch.setattr(episode_clock, "timed", lambda *a, **k: nullcontext())
    monkeypatch.setattr(ep, "tail", lambda *a, **k: seen.setdefault("encoder", k.get("encoder")))
    ep.upscaled_tail(tmp_path, 1, tmp_path / "m.mp4", tmp_path / "t.mp4", tmp_path / "o.mp4", tmp_path,
                     mu.LANCZOS, "")
    assert seen == {"job": "master encode", "encoder": "cuda"}


def test_the_tail_defaults_to_the_cpu_encoder():
    import inspect
    assert inspect.signature(_assemble().tail).parameters["encoder"].default == "cpu"
