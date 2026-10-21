"""The fake ComfyUI's replies are held to the REAL engine's shape (2026-10-21_ep02_proof DESIGN
2.2, R12, package P3).

`scripts/proof/record_comfy_transcript.py` is a logging reverse proxy that keeps one
request/reply pair per route plus one `execution_error`.  It is built and tested here ONLY in
front of the fake; recording the real engine is staged run SR-5 and waits for the owner's go.
When `tests/fixtures/proof/comfy_transcript/` exists, the fake's own transcript (recorded by the
same proxy, driven by the real client) must match it key for key and type for type.  Until it
exists, the fake says `shape: uncalibrated` in every engine_log header, and the proof report
caps Q6 at PARTIAL on that word.  SR-5 recorded it on the real engine on 2026-10-21 at 14:45 PDT
(ComfyUI 0.41.2); tests/test_proof_fake_comfy_classes.py holds the fake to each recorded job class."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from scripts.proof import record_comfy_transcript as rct
from studio import comfy, engine_ops, take_phases
from studio.rehearsal import fake_comfy
from tests.test_proof_fake_comfy_routes import filled, rig  # noqa: F401

TRANSCRIPT = Path(__file__).resolve().parent / "fixtures" / "proof" / "comfy_transcript"
GRID = {"prompt": "a lane at night", "seed": 1, "filename_prefix": "grid_01"}


def drive_session(proxy_url: str, monkeypatch) -> None:
    """Every route the studio uses, through the real client, aimed at the proxy."""
    monkeypatch.setattr(comfy, "HOST", proxy_url)
    comfy.run("fx_grid", GRID)                                    # /prompt, /queue, /history
    with pytest.raises(RuntimeError):
        comfy.run("fx_grid", {**GRID, "seed": 2})                 # the fatal fault: an execution_error
    engine_ops.alive(base_url=proxy_url)                          # /system_stats
    engine_ops.free(base_url=proxy_url)                           # /free
    comfy.interrupt()                                             # /interrupt
    assert take_phases.ring()                                     # /internal/logs/raw


def fake_session(rig, tmp_path: Path, monkeypatch):
    """(the fake's transcript folder, its rig): the real client driven through the proxy."""
    r = rig(faults=[{"kind": "exec_fatal", "on": "submit#2", "workflow": "fx_grid"}])
    out = tmp_path / "fake_transcript"
    with rct.Proxy(upstream=r.host, out=out) as proxy:
        drive_session(proxy.url, monkeypatch)
        assert proxy.transcript.missing() == []
    return out, r


def fake_transcript(rig, tmp_path: Path, monkeypatch) -> Path:
    return fake_session(rig, tmp_path, monkeypatch)[0]


# ---- the proxy --------------------------------------------------------------------------

def test_the_proxy_keeps_one_pair_per_route_and_one_execution_error(rig, tmp_path, monkeypatch):
    out = fake_transcript(rig, tmp_path, monkeypatch)
    assert sorted(p.stem for p in out.glob("*.json")) == sorted(fake_comfy.CONTRACT_ROUTES)
    error = json.loads((out / "history_execution_error.json").read_text(encoding="utf-8"))
    assert rct.has_execution_error(error["reply"]) and error["status"] == 200
    prompt = json.loads((out / "post_prompt.json").read_text(encoding="utf-8"))
    assert prompt["method"] == "POST" and "prompt" in prompt["request"] and "prompt_id" in prompt["reply"]


def test_the_proxy_keeps_the_first_pair_and_never_rewrites_it(rig, tmp_path, monkeypatch):
    out, r = fake_session(rig, tmp_path, monkeypatch)
    first = (out / "get_system_stats.json").read_bytes()
    with rct.Proxy(upstream=r.host, out=out) as proxy:
        assert proxy.transcript.saved("get_system_stats")
        assert engine_ops.alive(base_url=proxy.url)
    assert (out / "get_system_stats.json").read_bytes() == first


def test_the_proxy_answers_502_when_the_upstream_is_gone(tmp_path):
    dead = f"http://127.0.0.1:{fake_comfy.free_port()}"
    with rct.Proxy(upstream=dead, out=tmp_path / "t") as proxy:
        with pytest.raises(urllib.error.HTTPError) as got:
            urllib.request.urlopen(f"{proxy.url}/system_stats", timeout=10)
    assert got.value.code == 502 and not (tmp_path / "t" / "get_system_stats.json").exists()


def test_the_proxy_refuses_the_real_engine_without_the_owners_go(tmp_path):
    with pytest.raises(SystemExit) as got:
        rct.main(["--upstream", "http://127.0.0.1:8188", "--out", str(tmp_path / "t")])
    assert got.value.code == 2 and not (tmp_path / "t").exists()
    assert rct.refusal("http://127.0.0.1:8188", owner_go=True) is None
    assert rct.refusal("http://127.0.0.1:18188", owner_go=False) is None


def test_route_keys_name_every_route_the_client_uses():
    assert rct.route_key("GET", "/history/0c1e-77") == "get_history"
    assert rct.route_key("GET", "/internal/logs/raw?x=1") == "get_internal_logs_raw"
    assert rct.route_key("POST", "/prompt") == "post_prompt" and rct.route_key("GET", "/view") is None


# ---- the shape diff ---------------------------------------------------------------------

def test_the_shape_of_a_reply_wildcards_ids_and_keeps_types():
    a = rct.shape({"0c1e9a4f-1111-2222-3333-444455556666": {"outputs": {"9": {"images": [{"filename": "x"}]}}}})
    b = rct.shape({"77aa9a4f-1111-2222-3333-444455556666": {"outputs": {"17": {"images": [{"filename": "y"}]}}}})
    assert a == b
    assert rct.shape({"t": 1}) != rct.shape({"t": 1.5}) and rct.shape([1, "a"]) == ["list", {"anyof": {"int": "int", "str": "str"}}]


def test_the_shape_diff_names_a_missing_key_an_extra_key_and_a_changed_type():
    real = {"prompt_id": "a", "number": 1, "node_errors": {}}
    assert rct.shape_diff(rct.shape(real), rct.shape(real)) == []
    fake = {"prompt_id": "a", "number": "1", "extra": True}
    said = rct.shape_diff(rct.shape(real), rct.shape(fake), "post_prompt")
    assert "post_prompt.node_errors: missing in the fake" in said
    assert "post_prompt.extra: only in the fake" in said
    assert "post_prompt.number: real int, fake str" in said


def test_a_graphs_own_inputs_are_the_graphs_and_never_the_contract():
    """A node's inputs (and an error's current_inputs) are what the client submitted, coerced by the
    engine to each node's types: their names and types are the graph's, so only their kind is compared."""
    real = rct.shape({"p": {"prompt": [1, {"2": {"class_type": "EmptyImage", "inputs": {"width": 8, "cfg": 1.0}}}],
                            "status": {"messages": [["execution_error", {"current_inputs": {"images": ["t"]}}]]}}})
    fake = rct.shape({"p": {"prompt": [1, {"2": {"class_type": "Grid", "inputs": {"seed": 1, "cfg": 1}}}],
                            "status": {"messages": [["execution_error", {"current_inputs": {"prompt": ["x"]}}]]}}})
    assert rct.shape_diff(real, fake, "h") == []
    missing = rct.shape({"p": {"prompt": [1, {"2": {"class_type": "Grid"}}]}})
    assert rct.shape_diff(real, missing, "h") != []


def test_the_rehearsal_label_is_the_one_key_the_fake_may_add():
    real = rct.shape({"0c1e9a4f-1111-2222-3333-444455556666": {"status": {}}})
    fake = rct.shape({"0c1e9a4f-1111-2222-3333-444455556666": {"status": {}, "rehearsal": {"clock": "x"}}})
    assert rct.shape_diff(real, fake, "get_history") == []


# ---- calibration --------------------------------------------------------------------------

def test_the_shape_state_reads_whether_a_full_transcript_exists(rig, tmp_path, monkeypatch):
    assert fake_comfy.shape_state(tmp_path / "absent") == "uncalibrated"
    out = fake_transcript(rig, tmp_path, monkeypatch)
    assert fake_comfy.shape_state(out) == "calibrated"
    (out / "post_free.json").unlink()
    assert fake_comfy.shape_state(out) == "uncalibrated"


@pytest.mark.skipif(TRANSCRIPT.exists(), reason="the SR-5 transcript exists: the contract diff below runs")
def test_without_the_real_transcript_the_fake_says_uncalibrated(rig):
    r = rig()
    assert fake_comfy.TRANSCRIPT == TRANSCRIPT
    assert r.log()[0]["shape"] == "uncalibrated"


@pytest.mark.skipif(not TRANSCRIPT.exists(), reason="no SR-5 transcript yet (needs the owner's go)")
def test_the_fake_matches_the_real_engines_transcript(rig, tmp_path, monkeypatch):
    out = fake_transcript(rig, tmp_path, monkeypatch)
    assert rct.contract_diff(TRANSCRIPT, out) == []
    assert rig().log()[0]["shape"] == "calibrated"


def test_the_contract_diff_of_the_fake_against_itself_is_empty(rig, tmp_path, monkeypatch):
    out = fake_transcript(rig, tmp_path, monkeypatch)
    assert rct.contract_diff(out, out) == []
