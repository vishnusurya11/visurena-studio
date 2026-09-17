"""Whisper runs IN-PROCESS on the CPU, so a listen never enters ComfyUI's queue.

MEASURED on episode 10 (analyst F, time): every take_dq and every qc listen went
through `comfy_transcriber`, which is one more job in the same single queue the
takes render in -- so a DQ waited on a render and a render waited on a DQ, and
the skill grew a rule ("never a DQ while takes are in flight") to work around
its own tool.  The repo venv had no whisper because the GPU torch lived only in
ComfyUI's python; but the ear does not need the GPU.  `openai-whisper` installs
against the venv's CPU torch, and a 5 s line on `large-v3-turbo` is seconds.

So the in-process CPU ear is the default and the ComfyUI ear is the fallback,
which is the reverse of what `any_transcriber` did.
"""
from studio import voice_qc


def test_the_default_device_is_the_cpu():
    assert voice_qc.DEVICE == "cpu"


def test_the_cpu_never_asks_for_half_precision():
    """fp16 on a CPU is a warning per call and a silent fallback; ask for what runs."""
    assert voice_qc.whisper_options("cpu")["fp16"] is False
    assert voice_qc.whisper_options("cuda")["fp16"] is True
    assert voice_qc.whisper_options("cpu")["language"] == "en"


def test_the_engine_is_cached_per_model_and_device(monkeypatch):
    loads = []

    class Engine:
        def transcribe(self, path, **kw):
            return {"text": " heard "}

    import types
    fake = types.SimpleNamespace(load_model=lambda m, device="", download_root="": (loads.append((m, device)), Engine())[1])
    monkeypatch.setitem(__import__("sys").modules, "whisper", fake)
    voice_qc._HEARD.clear()
    listen = voice_qc.transcriber("tiny", device="cpu")
    listen2 = voice_qc.transcriber("tiny", device="cpu")
    assert loads == [("tiny", "cpu")]
    assert listen("x.wav") == "heard" and listen2("x.wav") == "heard"
    voice_qc._HEARD.clear()


def test_whisper_is_importable_in_this_venv():
    """The dependency is pinned in pyproject; if this fails, `uv sync --all-groups`."""
    import whisper  # noqa: F401
