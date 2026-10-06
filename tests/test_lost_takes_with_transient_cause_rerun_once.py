"""The batched path's one retry: after collect_all, the lost takes whose
cause is transient (comfy.TRANSIENT, or EngineLost's 'vanished') are
resubmitted in ONE second batch and merged; a hard loss is not resubmitted,
and a take that fails transiently twice stays lost -- one retry, never a
loop."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("takes_twice", ROOT / "scripts" / "episode" / "takes_r2v.py")
takes = importlib.util.module_from_spec(_spec)
sys.modules["takes_twice"] = takes
_spec.loader.exec_module(takes)

JOBS = [({"index": 1}, {"g": 1}), ({"index": 2}, {"g": 2}), ({"index": 3}, {"g": 3})]


def fake_engine(monkeypatch, outcomes):
    """outcomes: per collect_all round, {index: 'done' | <lost message>}."""
    rounds, batches = iter(outcomes), []

    def submit_all(jobs, approved=False):
        batches.append([c["index"] for c, _ in jobs])
        return [(c, f"p{c['index']}") for c, _ in jobs]

    def collect_all(tickets, where, on_take=None):
        say = next(rounds)
        done = [c for c, _ in tickets if say[c["index"]] == "done"]
        lost = [(c, say[c["index"]]) for c, _ in tickets if say[c["index"]] != "done"]
        return done, lost
    monkeypatch.setattr(takes, "submit_all", submit_all)
    monkeypatch.setattr(takes, "collect_all", collect_all)
    return batches


def test_a_transient_loss_is_resubmitted_once_and_merged(monkeypatch):
    batches = fake_engine(monkeypatch, [
        {1: "done", 2: "p2 failed: LoadVideo: HostBuffer.read_file_slice", 3: "done"},
        {2: "done"}])
    done, lost = takes.collect_twice(JOBS, lambda c: None)
    assert sorted(c["index"] for c in done) == [1, 2, 3] and lost == []
    assert batches == [[1, 2, 3], [2]]


def test_a_hard_loss_is_not_resubmitted(monkeypatch):
    batches = fake_engine(monkeypatch, [
        {1: "done", 2: "ComfyUI rejected the workflow: bad node", 3: "done"}])
    done, lost = takes.collect_twice(JOBS, lambda c: None)
    assert [c["index"] for c, _ in lost] == [2] and len(batches) == 1


def test_a_vanished_engine_counts_as_transient(monkeypatch):
    batches = fake_engine(monkeypatch, [
        {1: "p1 vanished: the engine restarted", 2: "done", 3: "done"},
        {1: "done"}])
    done, lost = takes.collect_twice(JOBS, lambda c: None)
    assert lost == [] and batches == [[1, 2, 3], [1]]


def test_two_consecutive_transient_failures_stay_lost(monkeypatch):
    batches = fake_engine(monkeypatch, [
        {1: "done", 2: "HostBuffer.read_file_slice", 3: "done"},
        {2: "HostBuffer.read_file_slice again"}])
    done, lost = takes.collect_twice(JOBS, lambda c: None)
    assert [c["index"] for c, _ in lost] == [2]
    assert batches == [[1, 2, 3], [2]]              # no third round, ever


def test_worth_resubmitting_is_the_narrow_class():
    assert takes.worth_resubmitting("LoadVideo: HostBuffer.read_file_slice")
    assert takes.worth_resubmitting("p9 vanished: the engine restarted")
    assert not takes.worth_resubmitting("take 4 produced no video: []")
