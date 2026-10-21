"""The seams between the harness (P5) and the fakes (P3's engine, P4's SDK, workers and YouTube),
pinned in the default suite (2026-10-21_ep02_proof DESIGN 3, fix round of 2026-10-21).

Every scenario of the harness table plants its ONE fault into a real sandbox manifest, and the
fake that has to serve it must READ it there: P3's engine parses `faults` (its seven kinds only,
anything else crashed the supervisor at start), P4's SDK reads `sdk_faults`, its workers
`worker_die_at`, its YouTube `youtube`.  Then the supervisor child boots its fake engine with a
fault of every kind planted, and a fenced child pushes one graph through the REAL studio.comfy
client into that engine, so the harness's engine asserts (A-served, A-honest, A-canned,
A-norerender, F10's one resubmission) run on a real engine_log.jsonl."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.proof import rehearse
from studio import settings
from studio.rehearsal import asserts, comfy_faults, fake_publish, fake_sdk, fake_workers, faults, sweep
from tests.proof_sandbox_fixture import tiny_sandbox

WORKFLOWS = Path(__file__).resolve().parent / "fixtures" / "proof" / "fake_comfy" / "workflows"


def manifest(box: Path) -> dict:
    return json.loads((box / "rehearsal.json").read_text(encoding="utf-8"))


def point_of(sc: rehearse.Scenario) -> sweep.Point:
    """A synthetic point of the scenario's sweep (the real list needs a baseline run)."""
    if sc.sweep == "take":
        return sweep.Point(sc.id, {"workflow": "ref2v_take", "k": 2})
    if sc.sweep == "write":
        return sweep.Point(sc.id, {"kind": "episodes/ep##/x.json", "site": "studio/x.py:1", "occurrence": 1,
                                   "step": sc.fault["step"]})
    return sweep.Point(sc.id, {"checkpoint": sc.checkpoint})


def what_reads(doc: dict, box: Path) -> dict:
    """What each fake would see of this manifest: the engine's parsed faults, the SDK's, the workers'
    death lines, YouTube's mode, the harness's own rows.  A row any fake refuses raises here."""
    return {"engine": [f.kind for f in comfy_faults.Faults(doc.get("faults") or ()).faults],
            "sdk": sorted(fake_sdk.Library(box, doc).faults), "youtube": fake_publish.mode(doc),
            "workers": {k: fake_workers.argv(k, doc, box)[3] for k in ("detect", "whisper")},
            "harness": [r["kind"] for r in doc.get("harness_faults") or ()]}


PLANTED = {"F1": ("engine", ["crash"]), "F10": ("engine", ["exec_error"]), "F16": ("engine", ["exec_fatal"]),
           "F2": ("harness", ["kill_at_write"]), "F7": ("harness", ["commit"]), "F15": ("sdk", [1]),
           "F6": ("youtube", "invalid_grant"), "F17": ("workers", {"detect": "0", "whisper": "2"}),
           "F11": ("engine", ["unreadable"] * 3)}


@pytest.mark.parametrize("sid", sorted(PLANTED))
def test_each_scenarios_fault_is_read_by_the_fake_that_serves_it(sid, tmp_path):
    box = tiny_sandbox(tmp_path, run_id=sid)
    sc = rehearse.TABLE[sid]
    rehearse.set_manifest(box, {**faults.CLEAN, "comfy_host": "http://127.0.0.1:1"})
    rehearse.plant(box, box / "library" / "book", sc, point_of(sc))
    key, want = PLANTED[sid]
    assert what_reads(manifest(box), box)[key] == want


def test_every_scenario_in_the_table_plants_a_manifest_every_fake_accepts(tmp_path):
    for sid, sc in rehearse.TABLE.items():
        if sc.fault.get("kind") in ("gaps", "tear", "reboot", "repair_window", "none"):
            continue                                          # a planted FILE, no manifest row
        box = tiny_sandbox(tmp_path / sid, run_id=sid)
        rehearse.set_manifest(box, {**faults.CLEAN, "comfy_host": "http://127.0.0.1:1"})
        rehearse.plant(box, box / "library" / "book", sc, point_of(sc))
        what_reads(manifest(box), box)                        # raises on a row any fake refuses


def test_the_supervisor_child_boots_its_engine_with_a_fault_of_every_kind_planted(tmp_path):
    box = tiny_sandbox(tmp_path, run_id="seams")
    book = rehearse.stage(box, rehearse.SCENARIOS / "smoke")
    rehearse.set_manifest(box, {**faults.CLEAN, "comfy_host": f"http://127.0.0.1:{rehearse.free_port()}"})
    for row in (faults.engine("exec_error", 1, "fx_grid"), faults.rate_limit(1), faults.worker_death("whisper", 2),
                faults.oauth_expired(), faults.kill_at_write("k", "s", 1, "09"), faults.brain_stream(["park"])):
        faults.add(box, row)
    sup = rehearse.launch_supervisor(box, rehearse.TABLE["smoke"], cleared=True, every=0.2, wall=40.0)
    log = (box / "supervisor.log").read_text(encoding="utf-8")
    assert "Traceback" not in log and sup["terminal"] == "HELD_PUBLISH", (sup, log[-1500:])
    assert any(r.get("header") for r in asserts.jsonl(box / "engine_log.jsonl"))      # the engine started
    assert book.is_dir()


CHILD = r"""
import json, sys
from pathlib import Path
box, workflows = Path(sys.argv[1]), Path(sys.argv[2])
from studio import comfy, compute_device, settings      # import studio armed the fence
from studio.rehearsal import supervisor
engine = supervisor.start_engine(box, settings.rehearsal())
comfy.WORKFLOWS, comfy.VLM_CALLS = workflows, None
compute_device.live_claims = lambda **_: []
out = comfy.run("fx_grid", {"prompt": "a", "seed": 1, "filename_prefix": "g"})
print(json.dumps({"out": [str(p) for p in out], "host": comfy.HOST}))
engine.stop()
"""


def test_a_graph_through_the_real_client_in_a_fenced_child_runs_every_engine_assert(tmp_path):
    box = tiny_sandbox(tmp_path, run_id="engine")
    rehearse.set_manifest(box, {**faults.CLEAN, "comfy_host": f"http://127.0.0.1:{rehearse.free_port()}"})
    faults.add(box, faults.engine("exec_error", 1))      # every workflow: the fixture graph is not in the real index
    env = rehearse.child_env(box, cleared=True)
    done = subprocess.run([sys.executable, "-c", CHILD, str(box), str(WORKFLOWS)], cwd=settings.REPO, env=env,
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr[-2000:]
    said = json.loads(done.stdout.strip().splitlines()[-1])
    assert said["host"] == manifest(box)["comfy_host"] and Path(said["out"][0]).is_file()
    engine = asserts.jsonl(box / "engine_log.jsonl")
    assert [r["fault"] for r in engine if r.get("call") == "prompt"] == ["exec_error", None]
    assert asserts.a_served({"kind": "exec_error"}, box, {})["passed"] is True
    assert asserts.specific("F10", box, box / "library" / "book", {})[0]["passed"] is True
    assert asserts.a_honest(engine, [], rehearse.shape_of(engine))["match_classes"]
    assert asserts.a_norerender(engine, {}, *rehearse.fault_moment(engine))["passed"] is True
    assert not (box / "tripwire.jsonl").exists() or not (box / "tripwire.jsonl").read_text().strip()
