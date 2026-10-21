"""Record the Claude SDK streams a real session answers, in the shape ReplayTransport serves
(2026-10-21_ep02_proof 2.3, staged run SR-2).

    uv run --no-sync python scripts/proof/record_writer.py <streams_dir> <script.py> [args...] --owner-go

RecordingTransport wraps the REAL transport (the bundled claude CLI on the owner's login) and,
for every ask, saves the messages the CLI sent back to <streams_dir>/<schema title>/<prompt sha>.jsonl
(studio.rehearsal.fake_sdk.save_stream).  The script runs with brain.ClaudeSDKClient rebound to a
recording client, so every llm.structured tier and brain turn it makes is recorded.

RUNNING it is one real step-02 session: a subscription turn per Draft part.  It refuses without
--owner-go (DESIGN section 6, SR-2) and is never run by a test; the tests drive it with a fake
inner transport.  It is not a rehearsal transport (`rehearsal` is False): inside an armed
rehearsal the fence refuses it, so SR-2 runs outside one, on a sandbox copy of the book."""
from __future__ import annotations

import json
import runpy
import sys
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from claude_agent_sdk import ClaudeSDKClient  # noqa: E402
from claude_agent_sdk._internal.transport import Transport  # noqa: E402

from studio.rehearsal import fake_sdk  # noqa: E402

GO = "--owner-go"
HANDSHAKE = frozenset({"control_response", "control_request", "control_cancel_request", "keep_alive"})
"""Control-protocol traffic: answered by ReplayTransport itself, never part of a recorded stream."""


class RecordingTransport(Transport):
    """`inner` with every answer to a user message saved as one stream file."""

    rehearsal = False

    def __init__(self, inner: Transport, out: Path, options=None):
        self.inner, self.out, self.options = inner, Path(out), options
        self.ask: dict | None = None
        self.stream: list[dict] = []

    async def connect(self) -> None:
        await self.inner.connect()

    async def write(self, data: str) -> None:
        message = json.loads(data)
        if message.get("type") == "user":
            self.flush()
            self.ask = fake_sdk.ask_of(self.options, message)
        await self.inner.write(data)

    async def read_messages(self) -> AsyncIterator[dict[str, Any]]:
        async for message in self.inner.read_messages():
            if self.ask is not None and message.get("type") not in HANDSHAKE:
                self.stream.append(message)
                if message.get("type") == "result":
                    self.flush()
            yield message

    def flush(self) -> None:
        """Save the stream of the ask in hand (once its result arrived, or a new ask began)."""
        if self.ask is not None and self.stream:
            fake_sdk.save_stream(self.out, self.ask["title"], self.ask["prompt"], self.stream)
        self.ask, self.stream = None, []

    async def close(self) -> None:
        self.flush()
        await self.inner.close()

    def is_ready(self) -> bool:
        return self.inner.is_ready()

    async def end_input(self) -> None:
        await self.inner.end_input()


def real_inner(options) -> Transport:
    """The transport ClaudeSDKClient would build itself: the bundled CLI (staged run SR-2 only)."""
    from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport

    async def nothing():
        return
        yield {}  # noqa: B901 -- an empty async stream, as the SDK's own connect builds
    return SubprocessCLITransport(prompt=nothing(), options=options)


def recording_client(out: Path, inner: Callable[[Any], Transport] = real_inner) -> type:
    """A ClaudeSDKClient whose every session is recorded into `out`."""
    class RecordingClient(ClaudeSDKClient):
        def __init__(self, options=None, transport=None):
            super().__init__(options=options, transport=RecordingTransport(transport or inner(options), out, options))
    return RecordingClient


def main(argv: list[str]) -> int:
    if GO not in argv or len([a for a in argv if a != GO]) < 2:
        sys.stderr.write("record_writer runs one real SDK session per ask: staged run SR-2, which waits for the "
                         f"owner's explicit go.  Pass {GO} with <streams_dir> <script.py> [args...].\n")
        return 2
    out, script, *rest = [a for a in argv if a != GO]
    from studio import brain
    brain.ClaudeSDKClient = recording_client(Path(out))
    sys.argv = [script, *rest]
    runpy.run_path(script, run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
