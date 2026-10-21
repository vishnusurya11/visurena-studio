"""The fake whisper worker of a rehearsal: studio/rehearsal/workers/__init__.py says the protocol.

    python studio/rehearsal/workers/fake_whisper_worker.py <memo.json> <die_at> <idle_s> <log.jsonl>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from studio.rehearsal.workers import answer_whisper, serve  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(serve("whisper", answer_whisper, sys.argv[1:]))
