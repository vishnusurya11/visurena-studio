"""The GPU ear: openai-whisper on CUDA under ComfyUI's embedded python (the repo venv's
torch is CPU-only), serving one transcript per clip over a line protocol:

    stdout  {"ready": true}                 once the weights are on the card
    stdin   {"clip": "<path>"}              one clip per line
    stdout  {"text": "..."} | {"error": "..."}

It exits on EOF, or after IDLE_S without a clip, so its VRAM is never held long
behind a render (studio/routed_whisper starts it, the device router allows it).

    python -I studio/whisper_worker.py <model> <download_root>
"""
from __future__ import annotations

import json
import queue
import sys
import threading

IDLE_S = 30.0


def answer(engine, clip: str) -> dict:
    try:
        return {"text": str(engine(clip)["text"]).strip()}
    except Exception as failed:
        return {"error": f"{type(failed).__name__}: {failed}"}


def lines(source, idle: float | None):
    """The source's lines, ending at EOF or after `idle` seconds without one."""
    if idle is None:
        yield from source
        return
    got: queue.Queue = queue.Queue()
    threading.Thread(target=lambda: [got.put(l) for l in source] + [got.put(None)], daemon=True).start()
    while (line := got.get(timeout=idle)) is not None:     # queue.Empty after `idle`
        yield line


def serve(source, sink, engine, idle: float | None = None) -> None:
    """One answer line per asked clip."""
    try:
        for line in lines(source, idle):
            if line.strip():
                sink.write(json.dumps(answer(engine, json.loads(line)["clip"])) + "\n")
                sink.flush()
    except queue.Empty:
        return


def load(model: str, root: str):
    import whisper
    loaded = whisper.load_model(model, device="cuda", download_root=root)
    return lambda clip: loaded.transcribe(clip, language="en", fp16=True)


def main(argv: list[str]) -> None:
    engine = load(argv[1], argv[2])
    sys.stdout.write(json.dumps({"ready": True}) + "\n")
    sys.stdout.flush()
    serve(sys.stdin, sys.stdout, engine, IDLE_S)


if __name__ == "__main__":
    main(sys.argv)
