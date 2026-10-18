"""Prism renders only on the owner's go, never over a busy GPU, and times every image."""
from __future__ import annotations

import json

import pytest

from prism import render
from prism.plan import jobs
from tests.prism_fixtures import guide, style, subjects


def planned():
    return jobs([style()], subjects(), {"krea2": guide("krea2"), "flux3_klein": guide("flux3_klein")})


class Runner:
    def __init__(self, tmp_path):
        self.calls, self.tmp = [], tmp_path

    def __call__(self, workflow, values):
        self.calls.append((workflow, values))
        made = self.tmp / f"comfy_{len(self.calls)}.png"
        made.write_bytes(b"png")
        return [made]


def test_without_the_go_nothing_renders(tmp_path):
    runner = Runner(tmp_path)
    with pytest.raises(render.NoGo):
        render.render_all(planned(), tmp_path / "run", runner, go=False, busy=lambda: False)
    assert runner.calls == []


def test_a_busy_gpu_refuses_the_run(tmp_path):
    runner = Runner(tmp_path)
    with pytest.raises(render.GpuBusy):
        render.render_all(planned(), tmp_path / "run", runner, go=True, busy=lambda: True)
    assert runner.calls == []


def test_each_job_lands_at_its_relative_out_and_is_timed(tmp_path):
    root = tmp_path / "run"
    rows = render.render_all(planned(), root, Runner(tmp_path), go=True, busy=lambda: False)
    assert len(rows) == 10 and all((root / r["out"]).exists() for r in rows)
    logged = [json.loads(line) for line in (root / "timings.jsonl").read_text().splitlines()]
    assert logged == rows and {"seconds", "model", "style", "subject"} <= set(rows[0])


def test_the_first_job_of_each_model_is_marked_cold(tmp_path):
    rows = render.render_all(planned(), tmp_path / "run", Runner(tmp_path), go=True, busy=lambda: False)
    assert [r["cold"] for r in rows] == [True] + [False] * 4 + [True] + [False] * 4


def test_a_failed_job_is_logged_and_the_run_goes_on(tmp_path):
    root, runner = tmp_path / "run", Runner(tmp_path)

    def flaky(workflow, values):
        if len(runner.calls) == 1:
            runner.calls.append("boom")
            raise RuntimeError("HostBuffer.read_file_slice failed")
        return runner(workflow, values)

    rows = render.render_all(planned(), root, flaky, go=True, busy=lambda: False)
    assert len(rows) == 10 and rows[1]["error"].startswith("RuntimeError")
    assert not (root / rows[1]["out"]).exists() and (root / rows[2]["out"]).exists()


def test_a_rerun_renders_only_the_missing(tmp_path):
    root, runner = tmp_path / "run", Runner(tmp_path)
    render.render_all(planned(), root, runner, go=True, busy=lambda: False)
    (root / planned()[3].out).unlink()
    again = render.render_all(planned(), root, runner, go=True, busy=lambda: False)
    assert [r["out"] for r in again] == [planned()[3].out]
