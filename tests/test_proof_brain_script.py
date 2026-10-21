"""The brain's scripted stream (2026-10-21_ep02_proof DESIGN 3: "brain = the real brain over
ReplayTransport with a scripted stream per scenario (relaunch, redo:<step>, park)").

The manifest's `brain_stream` answers the REAL brain.turn, one verdict per session, through P4's
ReplayTransport: the brain's own Verdict parsing and clamp run on it.  Every scripted answer is a
<sandbox>/sdk_log.jsonl row labelled `scripted`; past the end of the stream, and for any ask that
is not the brain's verdict, the answer falls through to P4's source (recorded, then canned)."""
from __future__ import annotations

import json
from pathlib import Path

import anyio
import pytest
from pydantic import BaseModel

from studio import brain
from studio.rehearsal import brain_script, fakes

REPO = Path(__file__).resolve().parents[1]


class Other(BaseModel):
    title: str


@pytest.fixture
def box(tmp_path):
    yield tmp_path
    fakes.uninstall()


def arm(box: Path, stream: list[str]) -> None:
    manifest = {"sdk_streams": str(box / "streams"), "brain_stream": stream}
    fakes.install(manifest, box)
    brain_script.install(manifest, box)


def turn():
    async def one():
        return await brain.turn("why did ep01 stop?", brain.triage_options(REPO))
    return anyio.run(one)[0]


def labels(box: Path) -> list[str]:
    return [json.loads(x)["label"] for x in (box / "sdk_log.jsonl").read_text(encoding="utf-8").splitlines()]


def test_each_session_takes_the_next_scripted_verdict_then_the_canned_one(box):
    arm(box, ["relaunch", "redo:09", "park"])
    got = [turn() for _ in range(4)]
    assert [v.response for v in got] == ["relaunch", "cure", "park", "park"]
    assert got[1].order == {"kind": "redo", "step_id": "09"}
    assert "CANNED" in got[3].reason and labels(box) == ["scripted", "scripted", "scripted", "canned"]


def test_a_scripted_redo_passes_through_the_brains_own_clamp(box):
    arm(box, ["redo:99"])
    verdict = brain.allowed(turn(), brain.episode_step_ids())
    assert verdict.response == "park" and "99" in verdict.reason


def test_an_ask_that_is_not_the_brains_verdict_is_never_scripted(box):
    arm(box, ["relaunch"])

    async def one():
        return await brain.ask_structured("Plan it.", Other, model="claude-opus-5-5")
    with pytest.raises(brain.BrainFailed):
        anyio.run(one)
    assert labels(box) == ["canned"] and turn().response == "relaunch"


def test_an_unknown_word_in_the_stream_is_refused():
    with pytest.raises(ValueError, match="relaunch"):
        brain_script.verdict_of("shrug")


def test_no_stream_installs_nothing(box):
    fakes.install({"sdk_streams": str(box / "streams")}, box)
    assert brain_script.install({}, box) is False
    assert turn().response == "park" and labels(box) == ["canned"]
