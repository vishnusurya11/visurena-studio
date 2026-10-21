"""What counts as n (2026-10-21_ep02_proof DESIGN 3.3, R13, R14): a sweep tries every take submit
(F1/F9/F10/F13/F16), every distinct write SITE at its first and one mid occurrence (F2/F3) and every
record kind x checkpoint (F18); a point counts toward n only when its recovery TRACE (the executed
lines of the recovery modules, captured by sys.monitoring) is distinct; a sweep past 4 h is sharded
and the untried points are reported, never extrapolated."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from studio import settings
from studio.rehearsal import sweep, trace


def submits(n, workflow="ref2v_take"):
    return [{"call": "prompt", "workflow": workflow, "kind": "take", "prompt_id": f"p{i}"} for i in range(n)]


def test_a_take_fault_is_swept_over_every_take_submit_never_half():
    rows = submits(3) + [{"call": "prompt", "workflow": "qwen_grid", "kind": "grid"}] + [{"call": "history"}]
    points = sweep.take_points("F10", rows)
    assert [p.where["k"] for p in points] == [1, 2, 3]
    assert {p.fault for p in points} == {"F10"} and len({p.id for p in points}) == 3


def test_a_kill_is_swept_over_every_distinct_write_site_at_its_first_and_one_mid_occurrence():
    rows = [{"kind": "takes/r2v/phases.jsonl", "site": "studio/take_phases.py:40", "step": "09"}] * 9
    rows += [{"kind": "takes/r2v/T##.graph.json", "site": "studio/episode_home.py:88", "step": "09"}]
    rows += [{"kind": "cut/master.mp4", "site": "scripts/episode/step_10_edit.py:12", "step": "10"}]
    points = sweep.write_points("F2", rows, step="09")
    got = sorted((p.where["kind"], p.where["occurrence"]) for p in points)
    assert got == [("takes/r2v/T##.graph.json", 1), ("takes/r2v/phases.jsonl", 1), ("takes/r2v/phases.jsonl", 5)]


def test_a_torn_record_is_swept_over_every_kind_and_checkpoint():
    points = sweep.record_points(["attempts.json", "clock.jsonl"], ["after_08", "after_09"])
    assert len(points) == 4 and len({p.id for p in points}) == 4


def test_twenty_positions_that_run_the_same_recovery_lines_are_one_point():
    results = [{"id": f"F1:k={k}", "passed": True, "trace": "aaa"} for k in range(20)]
    results += [{"id": "F1:k=20", "passed": True, "trace": "bbb"}]
    t = sweep.tally(results, planned=21)
    assert t["tried"] == 21 and t["n_distinct"] == 2 and t["passed_distinct"] == 2 and t["untried"] == 0


def test_a_trace_class_passes_only_when_every_point_in_it_passed():
    results = [{"id": "a", "passed": True, "trace": "x"}, {"id": "b", "passed": False, "trace": "x"},
               {"id": "c", "passed": True, "trace": "y"}]
    t = sweep.tally(results, planned=5)
    assert t["n_distinct"] == 2 and t["passed_distinct"] == 1 and t["untried"] == 2
    assert t["failing"] == ["b"]


def test_a_point_with_no_trace_never_counts_toward_n():
    t = sweep.tally([{"id": "a", "passed": True, "trace": None}], planned=1)
    assert t["n_distinct"] == 0 and t["untraced"] == ["a"]


def test_a_sweep_past_its_budget_is_sharded_and_the_untried_points_are_reported():
    points = sweep.take_points("F1", submits(10))
    shards = sweep.shards(points, seconds_per_point=3600.0, budget_s=4 * 3600.0)
    assert [len(s) for s in shards] == [4, 4, 2]
    done = {p.id for p in shards[0]}
    nxt = sweep.next_shard(points, done, seconds_per_point=3600.0, budget_s=4 * 3600.0)
    assert [p.id for p in nxt["run"]] == [p.id for p in shards[1]]
    assert nxt["untried"] == 6


def run_probe(probe: Path, root: Path, args: list) -> set:
    spec = importlib.util.spec_from_file_location(f"probe_{len(args)}_{args[0]}", probe)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with trace.capturing(root=root) as hits:
        for a in args:
            mod.f(a)
    return set(hits)


def test_the_trace_records_each_executed_recovery_line_once(tmp_path):
    probe = tmp_path / "studio" / "comfy.py"
    probe.parent.mkdir()
    probe.write_text("def f(x):\n    if x:\n        return 1\n    return 2\n", encoding="utf-8")
    one, two = run_probe(probe, tmp_path, [True]), run_probe(probe, tmp_path, [False])
    assert ("studio/comfy.py", 3) in one and ("studio/comfy.py", 3) not in two
    assert trace.signature(one) != trace.signature(two)
    assert trace.signature(one) == trace.signature(run_probe(probe, tmp_path, [True, True]))


def test_only_the_recovery_modules_are_traced():
    assert trace.rel(str(settings.REPO / "studio" / "comfy.py")) == "studio/comfy.py"
    assert trace.rel(str(settings.REPO / "studio" / "voice.py")) is None
    assert trace.rel("C:/Python312/Lib/json/__init__.py") is None


def test_a_dump_round_trips_and_a_run_folder_unions_its_processes(tmp_path):
    trace.dump(tmp_path / "traces", "100", {("studio/comfy.py", 3)})
    trace.dump(tmp_path / "traces", "200", {("scripts/episode/drive.py", 9), ("studio/comfy.py", 3)})
    assert trace.read_all(tmp_path / "traces") == {("studio/comfy.py", 3), ("scripts/episode/drive.py", 9)}


def test_a_write_is_named_by_its_file_kind_and_the_code_line_that_made_it(tmp_path):
    book = tmp_path / "library" / "9999_book"
    path = book / "episodes" / "ep02" / "takes" / "r2v" / "T07.graph.json"
    assert trace.kind_of(path, tmp_path) == "episodes/ep##/takes/r2v/T##.graph.json"
    assert trace.kind_of(tmp_path / "tmp" / "x.txt", tmp_path) is None
    assert trace.step_of(["C:/x/scripts/episode/step_09_shoot.py", "9999", "2"]) == "09"
    assert trace.step_of(["scripts/episode/drive.py"]) == "drive"


def test_the_step_is_the_one_the_real_runner_is_in_never_the_process_name():
    from tests.proof_runner_fixture import run_real_steps, step
    seen: list = []
    run_real_steps([step("08", done=True), step("09", lambda ctx: seen.append(trace.current_step()))])
    assert seen == ["09"]
    assert trace.current_step() == trace.step_of(sys.argv)          # outside any runner: the script's own name


def test_a_write_from_a_worker_thread_is_named_by_the_step_the_main_thread_runs():
    import threading
    from tests.proof_runner_fixture import run_real_steps, step
    seen: list = []

    def run(ctx):
        worker = threading.Thread(target=lambda: seen.append(trace.current_step()))
        worker.start()
        worker.join()
    run_real_steps([step("10", run)])
    assert seen == ["10"]


def test_a_step_imported_into_the_episode_process_names_its_writes_by_its_step(tmp_path):
    box = tmp_path / "box"
    (box / "library" / "b" / "episodes").mkdir(parents=True)
    out = str(box / "library" / "b" / "episodes" / "ep02.txt")
    code = ("import sys; sys.path.insert(0, {repo!r}); from studio.rehearsal import trace; "
            "trace.install({{'trace': False, 'record_writes': True}}, box={box!r}); "
            "from tests.proof_runner_fixture import run_real_steps, step; "
            "run_real_steps([step('09', lambda ctx: open({out!r}, 'w').write('x'))])")
    done = subprocess.run([sys.executable, "-c", code.format(repo=str(settings.REPO), box=str(box), out=out)],
                          capture_output=True, text=True, timeout=60, cwd=settings.REPO)
    assert done.returncode == 0, done.stderr
    rows = [json.loads(line) for p in (box / "writes").glob("*.jsonl") for line in p.read_text().splitlines()]
    assert [r["step"] for r in rows if r["kind"] == "episodes/ep##.txt"] == ["09"]
    assert sweep.write_points("F2", rows, step="09")


def test_a_child_process_writes_its_trace_and_its_write_sites(tmp_path):
    box = tmp_path / "box"
    (box / "library" / "b" / "episodes").mkdir(parents=True)
    code = ("import sys; sys.path.insert(0, {repo!r}); from studio.rehearsal import trace; "
            "trace.install({{'trace': True, 'record_writes': True}}, box={box!r}); "
            "from studio import comfy; comfy.transient('HostBuffer'); "
            "open({out!r}, 'w').write('x')")
    out = str(box / "library" / "b" / "episodes" / "ep02.txt")
    done = subprocess.run([sys.executable, "-c", code.format(repo=str(settings.REPO), box=str(box), out=out)],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    assert any(f == "studio/comfy.py" for f, _ in trace.read_all(box / "traces"))
    rows = [json.loads(line) for p in (box / "writes").glob("*.jsonl") for line in p.read_text().splitlines()]
    assert rows and rows[0]["kind"] == "episodes/ep##.txt" and rows[0]["site"] == "<string>:1"
