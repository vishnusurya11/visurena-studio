"""The Claude seam of a rehearsal is the SDK TRANSPORT (DESIGN 2.3, R9; 2026-10-21_ep02_proof P4).

`fakes` rebinds brain.ClaudeSDKClient to a subclass that always passes ReplayTransport, so the
REAL brain.ask_structured / brain.turn parse every message, build the receipt, raise RateLimited
on a rejected window and BrainFailed on an error result.  A recorded stream answers `exact`; a
miss answers the schema's REFUSING instance (`canned`).  The recorder wraps an inner transport
and saves a stream ReplayTransport serves back unchanged.  $0: no CLI, no network."""
from __future__ import annotations

import json
from pathlib import Path

import anyio
import pytest
from pydantic import BaseModel

from scripts.proof import record_writer
from studio import brain
from studio.rehearsal import fake_sdk, fakes, fence
from tests.test_brain_a_verdict_is_read_from_the_result_never_from_prose import FakeTransport

REPO = Path(__file__).resolve().parents[1]


class Answer(BaseModel):
    title: str
    shots: int


@pytest.fixture
def box(tmp_path):
    (tmp_path / "streams").mkdir()
    yield tmp_path
    fakes.uninstall()


def install(box: Path, **manifest) -> None:
    fakes.install({"sdk_streams": str(box / "streams"), **manifest}, box)


def ask(prompt: str = "Plan it.", schema=Answer):
    async def one():
        return await brain.ask_structured(prompt, schema, model="claude-opus-5-5")
    return anyio.run(one)


def rows(box: Path, name: str = "sdk_log") -> list[dict]:
    path = box / f"{name}.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def record(box: Path, title: str, prompt: str, stream: list[dict]) -> None:
    fake_sdk.save_stream(box / "streams", title, prompt, stream)


def test_the_brain_client_always_carries_the_replay_transport(box):
    install(box)
    assert brain.ClaudeSDKClient.__name__ == "RehearsalClient"
    client = brain.ClaudeSDKClient()
    assert isinstance(client._custom_transport, fake_sdk.ReplayTransport)
    assert client._custom_transport.rehearsal is True
    fakes.uninstall()
    assert brain.ClaudeSDKClient.__name__ == "ClaudeSDKClient"


def test_a_recorded_result_runs_the_real_parse_and_receipt(box):
    install(box)
    record(box, "Answer", "Plan it.", [fake_sdk.result_row({"title": "The Pit", "shots": 12})])
    got, receipt = ask()
    assert got == Answer(title="The Pit", shots=12)
    assert receipt["model_usage"]["claude-rehearsal"] == {"input_tokens": 1000, "output_tokens": 200}
    assert rows(box)[-1]["label"] == "exact" and rows(box)[-1]["title"] == "Answer"


def test_a_rejected_rate_limit_reaches_the_real_rate_limited_path(box):
    install(box, sdk_faults=[{"on": 1, "kind": "rate_limit", "resets_at": 1_800_000_000}])
    with pytest.raises(brain.RateLimited) as caught:
        ask()
    assert caught.value.resets_at == 1_800_000_000
    assert rows(box)[-1]["label"] == "fault"


def test_an_error_result_reaches_the_real_brain_failed_path(box):
    install(box, sdk_faults=[{"on": 1, "kind": "error"}])
    with pytest.raises(brain.BrainFailed, match="error_during_execution"):
        ask()


def test_a_fault_fires_on_its_numbered_ask_only(box):
    install(box, sdk_faults=[{"on": 2, "kind": "error"}])
    record(box, "Answer", "Plan it.", [fake_sdk.result_row({"title": "x", "shots": 1})])
    assert ask()[0].shots == 1
    with pytest.raises(brain.BrainFailed):
        ask()
    assert ask()[0].shots == 1


def test_a_miss_is_canned_and_canned_refuses(box):
    install(box)

    async def one():
        return await brain.turn("why did ep02 park?", brain.triage_options(REPO))
    verdict, _ = anyio.run(one)
    assert verdict.response == "park" and "CANNED" in verdict.reason
    assert rows(box)[-1]["label"] == "canned"


def test_a_schema_with_no_row_is_an_error_result_never_a_guess(box):
    install(box)
    with pytest.raises(brain.BrainFailed):
        ask()
    assert rows(box)[-1]["label"] == "canned" and rows(box)[-1]["row"] is None


def test_the_armed_fence_lets_the_rehearsal_client_through(box):
    install(box)
    record(box, "Answer", "Plan it.", [fake_sdk.result_row({"title": "x", "shots": 2})])
    fence.install(fence.Fence.of(roots=(box / "real",), sandbox=box, repo=REPO))
    try:
        assert ask()[0].shots == 2
    finally:
        fence.disarm()
    assert not (box / "tripwire.jsonl").exists()


def test_the_stream_file_is_keyed_by_title_and_prompt(box):
    path = fake_sdk.save_stream(box / "streams", "Answer", "Plan it.", [fake_sdk.result_row({})])
    assert path.parent.name == "Answer" and path.stem == fake_sdk.prompt_sha("Plan it.")
    assert fake_sdk.load_stream(box / "streams", "Answer", "Plan it.") == [fake_sdk.result_row({})]
    assert fake_sdk.load_stream(box / "streams", "Answer", "other") is None


# ---- the recorder: it wraps an inner transport (here a fake; for real it is staged run SR-2) ----

def test_the_recorder_saves_a_stream_the_replay_serves_back_unchanged(box, monkeypatch):
    stream = [{"type": "rate_limit_event", "uuid": "u", "session_id": "s",
               "rate_limit_info": {"status": "allowed_warning", "resetsAt": 1}},
              fake_sdk.result_row({"title": "Rec", "shots": 3})]
    recording = record_writer.recording_client(box / "streams", inner=lambda options: FakeTransport(stream))
    monkeypatch.setattr(brain, "ClaudeSDKClient", recording)
    got, _ = ask("Record me.")
    assert got.shots == 3
    assert fake_sdk.load_stream(box / "streams", "Answer", "Record me.") == stream
    monkeypatch.undo()
    install(box)
    assert ask("Record me.")[0] == got and rows(box)[-1]["label"] == "exact"


def test_the_recorder_refuses_to_run_without_the_owners_go(capsys):
    assert record_writer.main(["out", "scripts/episode/step_02_plan.py"]) == 2
    assert "SR-2" in capsys.readouterr().err
