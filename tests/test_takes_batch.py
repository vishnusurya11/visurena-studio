"""Every take goes to ComfyUI in one go.

Owner, 2026-09-12: "we should do all ref2v videos in one go — doing other jobs
in the middle will do a cold load every time, increasing time."

MEASURED on episode 1 the same morning.  Back to back, the takes ran 407, 502,
583 s.  Once another production's jobs began landing between them, the same
graph took 742, 998 s: every switch evicts the MiniMax weights and the next
take pays to load them again.  Submitting one take, waiting for it, then
submitting the next leaves a gap after every take, and the gap is exactly where
somebody else's job gets in.  Handing over the whole run at once closes it.
"""
from __future__ import annotations

import importlib.util
import sys

import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("takes_r2v", ROOT / "scripts" / "episode" / "takes_r2v.py")
takes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(takes)


@pytest.fixture(autouse=True)
def no_live_hold(tmp_path, monkeypatch):
    """A hold on the real repo is an instruction to the real machine. No test may
    read it or be steered by it -- a live hold failed this file once already."""
    monkeypatch.setattr(takes.approval, "HOLD", tmp_path / "RENDER_HOLD")


def test_every_take_is_submitted_before_any_is_collected(monkeypatch):
    order = []
    monkeypatch.setattr(takes, "submit", lambda graph: (order.append(f"submit {graph['id']}"), graph["id"])[1])
    jobs = [({"index": n, "frames": 100}, {"id": f"g{n}"}) for n in (0, 1, 2)]
    tickets = takes.submit_all(jobs, approved=True)
    assert order == ["submit g0", "submit g1", "submit g2"]
    assert [pid for _, pid in tickets] == ["g0", "g1", "g2"]


def test_the_batch_asks_for_approval_once_per_take_before_anything_is_sent(monkeypatch):
    """A refusal must land before the first job is queued, not halfway through."""
    sent = []
    monkeypatch.setattr(takes, "submit", lambda graph: sent.append(graph) or "x")
    jobs = [({"index": 0, "frames": 10}, {}), ({"index": 1, "frames": 10}, {})]
    try:
        takes.submit_all(jobs, approved=False)
    except Exception as raised:
        assert "REFUSED" in str(raised) or "HELD" in str(raised)
    assert sent == [], "nothing may be queued when the run is not approved"


def test_the_time_reported_is_the_time_comfyui_says_it_ran():
    """Wall time from submit is wrong in a batch: take three's clock would
    include takes one and two. ComfyUI timestamps its own execution."""
    record = {"status": {"messages": [
        ["execution_start", {"timestamp": 1789218000000}],
        ["execution_cached", {"nodes": []}],
        ["execution_success", {"timestamp": 1789218407000}]]}}
    assert takes.ran_for(record) == 407.0


def test_a_record_with_no_timestamps_reports_nothing_rather_than_a_lie():
    assert takes.ran_for({"status": {"messages": []}}) is None
    assert takes.ran_for({}) is None


def test_an_interrupted_take_still_reports_how_long_it_ran():
    record = {"status": {"messages": [
        ["execution_start", {"timestamp": 1789201564000}],
        ["execution_interrupted", {"timestamp": 1789201655000}]]}}
    assert takes.ran_for(record) == 91.0


def test_one_lost_take_does_not_abandon_the_rest_of_the_batch(monkeypatch, tmp_path):
    """T17 was interrupted at 07:13 and the collecting loop died with it, leaving
    takes 18, 20 and 22 executing on ComfyUI with nobody waiting for them. One
    take's misfortune must not cost the three behind it."""
    kept = []

    def collect(c, prompt_id, out):
        if c["index"] == 17:
            raise RuntimeError(f"{prompt_id} failed: unknown error")
        kept.append(c["index"])
        return {**c, "measured_seconds": 1.0, "render_s": 1.0}

    monkeypatch.setattr(takes, "collect", collect)
    tickets = [({"index": n, "frames": 10, "shots": [n]}, f"p{n}") for n in (17, 18, 20, 22)]
    done, lost = takes.collect_all(tickets, lambda c: tmp_path / f"T{c['index']:02d}.mp4")
    assert kept == [18, 20, 22]
    assert [c["index"] for c, _ in lost] == [17]


def test_the_takes_that_were_lost_are_named_so_they_can_be_re_rendered(monkeypatch, tmp_path):
    monkeypatch.setattr(takes, "collect", lambda c, p, o: (_ for _ in ()).throw(RuntimeError("interrupted")))
    tickets = [({"index": 3, "frames": 10, "shots": [3]}, "p3")]
    done, lost = takes.collect_all(tickets, lambda c: tmp_path / "T03.mp4")
    assert done == [] and lost[0][1] == "interrupted" or "interrupted" in str(lost[0][1])


def test_a_retake_never_collides_with_an_attempt_already_on_disk(tmp_path):
    """The retake stage crashed at 07:37 with FileExistsError renaming T02.mp4 to
    T02_fail1.mp4, because T02_fail1.mp4 was already there from an earlier retake:
    the name came from a `tries` counter in the record, not from what is on disk.

    ONE COPY NOW, in `episode_home`.  The renderer and the judge each had their
    own, both globbing the flat take dir while `migrate_layout` had moved the
    displaced rolls into `attempts/` -- so the promise in the name held only by
    the accident of the collision landing in another directory.  Both rooms are
    counted and the new name goes in `attempts/`.
    See tests/test_every_attempt_is_found_and_none_overwritten.py."""
    from studio import episode_home
    for name in ("T02.mp4", "T02_fail1.mp4", "T02_fail2.mp4"):
        (tmp_path / name).write_bytes(b"")
    got = episode_home.next_fail(tmp_path, 2)
    assert got.name == "T02_fail3.mp4" and got.parent.name == "attempts"


def test_the_first_failed_attempt_is_fail1(tmp_path):
    from studio import episode_home
    (tmp_path / "T05.mp4").write_bytes(b"")
    assert episode_home.next_fail(tmp_path, 5).name == "T05_fail1.mp4"
