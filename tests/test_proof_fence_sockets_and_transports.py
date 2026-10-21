"""The network and transport fence (DESIGN 2.5; 2026-10-21_ep02_proof P1).

Armed: a connect anywhere but 127.0.0.1 on a manifest fake port trips (the real :8188,
any remote host), a socketpair inside the process passes (asyncio's self-pipe), openai's
clients cannot be built, and a ClaudeSDKClient built without the rehearsal transport trips."""
from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from studio.rehearsal import fence

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def listener():
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    yield srv
    srv.close()


@pytest.fixture
def armed(tmp_path, listener):
    box = tmp_path / "box"
    box.mkdir()
    port = listener.getsockname()[1]
    fence.install(fence.Fence.of(roots=(tmp_path / "real",), sandbox=box, repo=REPO, ports=(port,)))
    yield box, port
    fence.disarm()


def trips(box: Path) -> list[dict]:
    path = box / "tripwire.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def test_the_real_engine_port_trips_before_a_connect(armed):
    box, _ = armed
    with pytest.raises(fence.RehearsalTripwire, match="8188"):
        socket.create_connection(("127.0.0.1", 8188), timeout=1)
    assert trips(box)[-1]["event"] == "socket.connect"


def test_a_remote_host_trips(armed):
    with socket.socket() as sock, pytest.raises(fence.RehearsalTripwire, match="203.0.113.7"):
        sock.connect(("203.0.113.7", 443))     # numeric: no getaddrinfo, so the fence is what refuses


def test_a_manifest_fake_port_and_an_own_socketpair_pass(armed):
    box, port = armed
    socket.create_connection(("127.0.0.1", port), timeout=5).close()
    a, b = socket.socketpair()
    a.close(), b.close()
    assert trips(box) == []


def test_openai_clients_cannot_be_built(armed):
    import openai
    for cls in (openai.OpenAI, openai.AsyncOpenAI):
        with pytest.raises(fence.RehearsalTripwire, match="openai"):
            cls(api_key="sk-rehearsal")
    assert len(trips(armed[0])) == 2


def test_the_sdk_client_needs_the_rehearsal_transport(armed):
    from claude_agent_sdk import ClaudeSDKClient

    class Replay:
        rehearsal = True

    with pytest.raises(fence.RehearsalTripwire, match="rehearsal transport"):
        ClaudeSDKClient()
    assert ClaudeSDKClient(transport=Replay()) is not None
    assert trips(armed[0])[-1]["event"] == "ClaudeSDKClient"


def test_disarmed_the_clients_build_as_before(tmp_path):
    import openai
    from claude_agent_sdk import ClaudeSDKClient
    fence.disarm()
    assert openai.OpenAI(api_key="sk-x") is not None and ClaudeSDKClient() is not None


# ---- asyncio: the Windows proactor connects in C (_overlapped.ConnectEx), no audit event ----

def test_an_asyncio_connect_off_the_fake_ports_trips(armed):
    import asyncio
    box, _ = armed

    async def go():
        await asyncio.open_connection("127.0.0.1", 9)
    with pytest.raises(fence.RehearsalTripwire, match="127.0.0.1:9"):
        asyncio.run(go())
    assert trips(box)[-1]["event"] == "asyncio.connect"


def test_an_asyncio_connect_to_a_fake_port_passes(armed):
    import asyncio
    box, port = armed

    async def go():
        _, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.close()
        await writer.wait_closed()
    asyncio.run(go())
    assert trips(box) == []


def test_an_asyncio_datagram_to_a_remote_host_trips(armed):
    import asyncio

    async def go():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        try:
            await asyncio.get_running_loop().sock_sendto(sock, b"x", ("203.0.113.7", 53))
        finally:
            sock.close()
    with pytest.raises(fence.RehearsalTripwire, match="203.0.113.7"):
        asyncio.run(go())


def test_an_async_http_client_cannot_reach_a_real_port(armed):
    import asyncio
    import httpx
    box, _ = armed

    async def go():
        async with httpx.AsyncClient() as client:
            await client.get("http://127.0.0.1:9/", timeout=3)
    with pytest.raises(BaseException) as caught:
        asyncio.run(go())
    assert "RehearsalTripwire" in repr(caught.value) or isinstance(caught.value, fence.RehearsalTripwire)
    assert trips(box)[-1]["event"] == "asyncio.connect"
