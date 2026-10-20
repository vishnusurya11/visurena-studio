"""Clock honesty (deadline retro 2026-10-20, item 11, package F).

ep01's records could not say where its largest step 09 item went: take renders had no timing row
(84.7 min over 3 render spans, every render figure an estimate); the av3 hang of run 12 left a
`started` mark and 40 min nobody's row covered; the step 04 `lines` wall of 10 min was spent by
the first saying of every line (1,075 s first pass); and the finish line printed "repair 1.83 h
of a 0.63 h cap" -- both repairs summed against the second one's cap.

Fixtures are copies of ep01's own records (tests/fixtures/clock_honesty/): clock.jsonl,
repair.jsonl, and timing.jsonl rows 116-122 (run 12).  No GPU, no ComfyUI, no library read.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from studio import episode_clock as ck
from studio import eta, repair_clock, step_attempts, step_caps, timing_sum
from studio.episode_spec import Line

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).parent / "fixtures" / "clock_honesty"
PDT = timezone(timedelta(hours=-7))
"""ep01's timing.jsonl stamps are naive local ISO, written on the owner's machine in Seattle."""


def _script(name: str, path: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


tr = _script("takes_r2v_clock", "scripts/episode/takes_r2v.py")
say = _script("say_lines_clock", "scripts/episode/say_lines.py")


@pytest.fixture
def book(tmp_path, monkeypatch):
    monkeypatch.setattr(ck.episode_home, "home", lambda b, n: tmp_path / f"ep{n:02d}")
    (tmp_path / "ep01").mkdir()
    return tmp_path


def _ep01(home: Path, timing: bool = True) -> Path:
    shutil.copy(FIX / "ep01_clock.jsonl", home / "clock.jsonl")
    shutil.copy(FIX / "ep01_repair.jsonl", home / "repair.jsonl")
    if timing:
        shutil.copy(FIX / "ep01_timing_run12.jsonl", home / "timing.jsonl")
    return home


def _seattle(monkeypatch):
    monkeypatch.setattr(ck, "local_epoch", lambda stamp: datetime.fromisoformat(stamp).replace(tzinfo=PDT).timestamp())


# ---- (a) a render span writes a take_render row -------------------------------------------

JOBS = [({"index": 3, "frames": 97, "shots": [3]}, {}), ({"index": 5, "frames": 121, "shots": [5, 6]}, {})]


def test_a_render_span_writes_a_take_render_row(book):
    row = tr.stamp_render(book, 1, JOBS, 1_000.0, 1_600.0, lost=[])
    assert (row["stage"], row["span_s"], row["device"], row["within"]) == ("take_render", 600.0, "gpu", "takes")
    assert row["ok"] and ck.indices_in(row["note"]) == [3, 5]
    assert row["detail"] and row["seconds"] == 0.0     # a detail of the takes wall: every summing reader adds 0


def test_nothing_queued_writes_no_render_row(book):
    assert tr.stamp_render(book, 1, [], 1_000.0, 1_600.0, lost=[]) is None
    assert ck.rows(book, 1) == []


def test_a_lost_take_marks_the_span_failed_but_a_boundary_stop_does_not(book):
    assert not tr.stamp_render(book, 1, JOBS, 0.0, 10.0, lost=[(JOBS[0][0], "interrupted")])["ok"]
    assert tr.stamp_render(book, 1, JOBS, 0.0, 10.0, lost=[(JOBS[0][0], tr.BOUNDARY)])["ok"]
    assert not tr.stamp_render(book, 1, JOBS, 0.0, 10.0, lost=None)["ok"]       # collect_twice raised


def test_the_takes_row_and_its_render_are_counted_once(book, monkeypatch):
    clock = iter([1_000.0, 3_000.0])
    monkeypatch.setattr(ck.time, "time", lambda: next(clock))
    with ck.timed(book, 1, "takes"):
        tr.stamp_render(book, 1, JOBS, 1_100.0, 2_900.0, lost=[])
    assert sum(r["seconds"] for r in ck.rows(book, 1)) == 2_000.0
    assert timing_sum.gpu_seconds_of(book / "ep01") == 2_000.0
    assert timing_sum.STAGES["take_render"] == ("09", True) and eta.SUB_STEP["take_render"] == "09"


def test_a_render_under_concurrent_cpu_checks_still_sums_to_the_wall(book, monkeypatch):
    """Skeptic, package F round 1: step 09's CPU lane stamps take_dq rows `within` takes WHILE the GPU
    renders.  ep01 span 1 (timing.jsonl rows 69-75): takes 2,054 s gross, take_dq 1,965 s, renders
    ~1,900 s.  Netting the takes row of both clamped it to 0 and summed 3,865 s against a 2,054 s wall."""
    clock = iter([10_000.0, 12_054.0])
    monkeypatch.setattr(ck.time, "time", lambda: next(clock))
    with ck.timed(book, 1, "takes"):
        ck.stamp(book, 1, "take_dq", 10_080.0, 11_000.0, within="takes")
        tr.stamp_render(book, 1, JOBS, 10_050.0, 11_950.0, lost=[])
        ck.stamp(book, 1, "take_dq", 11_000.0, 12_045.0, within="takes")
    got = ck.rows(book, 1)
    takes = next(r for r in got if r["stage"] == "takes")
    assert sum(r["seconds"] for r in got) == 2_054.0 == timing_sum.gpu_seconds_of(book / "ep01")
    assert takes["seconds"] == 89.0 and not takes.get("overlap_s")             # its own launch and waits
    assert timing_sum.step_seconds_of(book / "ep01")["09"] == 2_054.0
    assert next(r for r in got if r["stage"] == "take_render")["span_s"] == 1_900.0


def test_a_render_row_is_judged_by_its_span_and_a_concurrent_check_is_no_rival():
    cond = {"frames": {3: 97, 5: 121}}
    norm = ck.row_norm({"stage": "take_render", "note": "3 5"}, cond)
    render = {"stage": "take_render", "note": "3 5", "seconds": 0.0, "span_s": 3 * norm, "detail": True,
              "within": "takes", "started": "2026-10-18T10:00:00", "ended": "2026-10-18T11:00:00"}
    dq = {"stage": "take_dq", "seconds": 40.0, "within": "takes",
          "started": "2026-10-18T10:10:00", "ended": "2026-10-18T10:10:40"}
    assert ck.marks(render, [render, dq], cond) == ["SLOW"]
    assert ck.marks(dq, [render, dq], cond) == []


def test_main_stamps_the_render_span_around_the_queue(book, monkeypatch):
    built = [c for c, _ in JOBS]
    clock = itertools.count(10_000.0, 100.0)
    monkeypatch.setattr(tr, "time", SimpleNamespace(time=lambda: next(clock)))
    for name, fake in {"opened": lambda b, n: (book, SimpleNamespace(lines=[])), "cards": lambda *a: built,
                       "refuse_stale_cells": lambda *a: None, "refuse_failed_panels": lambda *a: None,
                       "lint_wall": lambda *a: None, "wants_render": lambda *a: True, "make_room": lambda *a: None,
                       "render_plan": lambda retaken: ("base", None), "graph_for": lambda *a, **k: {},
                       "prior_first_seconds": lambda home: 0.0, "book_first_seconds": lambda *a: None,
                       "first_wall_spent": lambda *a: False,
                       "collect_twice": lambda jobs, *a, **k: ([], [])}.items():
        monkeypatch.setattr(tr, name, fake)
    monkeypatch.setattr(tr.no_last_frame, "take_faults", lambda cards: {})
    monkeypatch.setattr(tr.episode_home, "takes_dir", lambda b, n, e: book / "ep01" / "takes" / e)
    tr.main("x", 1)
    rows = [r for r in ck.rows(book, 1) if r["stage"] == "take_render"]
    assert len(rows) == 1 and rows[0]["span_s"] > 0 and ck.indices_in(rows[0]["note"]) == [3, 5]


def test_the_report_shows_the_render_span_inside_the_takes_wall(book):
    ck.stamp(book, 1, "takes", 10_000.0, 12_000.0)
    tr.stamp_render(book, 1, JOBS, 10_100.0, 11_900.0, lost=[])
    line = next(l for l in ck.report(book, 1).splitlines() if l.startswith("take_render"))
    assert "1800 s inside takes" in line
    total = next(l for l in ck.report(book, 1).splitlines() if l.startswith("TOTAL"))
    assert float(total.split()[1]) == 2_000.0


def test_a_render_row_is_priced_by_the_frames_it_names():
    cond = {"frames": {3: 97, 5: 121, 7: 141}}
    row = {"stage": "take_render", "note": "3 5", "seconds": 1.0}
    assert ck.row_norm(row, cond) == ck.norm_for("takes", frames=[97, 121])


# ---- (b) a killed run's wall shows on the clock --------------------------------------------

def test_run_12s_av3_hang_is_charged_as_killed_not_lost(book, monkeypatch):
    _seattle(monkeypatch)
    _ep01(book / "ep01")
    killed = ck.killed_rows(book, 1)
    run12 = next(r for r in killed if r["run_id"].endswith("20261019041605"))
    assert run12["seconds"] == pytest.approx(2_620.5 - 163.0, abs=1.0)     # 163 s of rows, then the hang
    assert run12["stage"] == "killed" and "step_10" in run12["note"] and run12["killed"]


def test_the_report_lists_the_killed_wall_and_counts_it_in_the_total(book, monkeypatch):
    _seattle(monkeypatch)
    _ep01(book / "ep01")
    out = ck.report(book, 1)
    assert "KILLED" in out and "killed" in out.splitlines()[-1] + out
    total = next(line for line in out.splitlines() if line.startswith("TOTAL"))
    assert float(total.split()[1]) > 2_620.0                                 # the hang is on the clock


def test_a_killed_run_wholly_covered_by_rows_adds_nothing(book):
    home = book / "ep01"
    ck.stamp(book, 1, "take_dq", 1_000.0, 1_060.0)
    (home / "clock.jsonl").write_text(json.dumps({"run_id": "r", "started": 1_000.0, "ended": 1_060.0,
                                                  "seconds": 60.0, "how": "killed"}) + "\n", encoding="utf-8")
    assert ck.killed_rows(book, 1) == []


def test_a_killed_row_contends_with_nothing():
    killed = {"stage": "killed", "killed": True, "started": "2026-10-18T21:16:05",
              "ended": "2026-10-18T21:59:46", "seconds": 2457.5}
    other = {"stage": "take_eye", "started": "2026-10-18T21:17:10", "ended": "2026-10-18T21:18:54", "seconds": 104.3}
    assert not ck.contended(killed, [killed, other]) and not ck.contended(other, [killed, other])


def test_the_finish_line_names_the_killed_hours_and_the_repairs_share(tmp_path):
    home = _ep01(tmp_path, timing=False)
    # a share of the charge and of the repair already on the line, never a third part to add to them
    assert ck.killed_part(home) == " | killed 1.73 h in 4 runs (0.73 h of the charge, 1.00 h of the repair)"
    assert ck.killed_part(tmp_path / "nowhere") == ""


# ---- (c) step 04: the first saying of every line has its own row ---------------------------

def test_the_first_saying_has_its_own_row_beside_the_re_say_wall():
    say_row, lines_row = step_caps.cap("say"), step_caps.cap("lines")
    assert (say_row.step, say_row.read, step_caps.wall_s("say")) == ("04", "step", 900.0)
    assert (lines_row.step, step_caps.wall_s("lines")) == ("04", 600.0)


def _fresh_line(tmp_path, monkeypatch):
    lines = tmp_path / "episodes" / "ep01" / "audio" / "lines"
    lines.mkdir(parents=True)
    plan = SimpleNamespace(number=1, lines=[Line(index=0, kind="narration", speaker="a", text="Gold.", shot=0)])
    monkeypatch.setattr(say.episode_home, "book_dir", lambda _id: tmp_path)
    monkeypatch.setattr(say.episode_home, "load_plan", lambda b, n: plan)
    monkeypatch.setattr(say.voice_qc, "any_transcriber", lambda: (lambda clip: "Gold."))
    monkeypatch.setattr(say, "time", SimpleNamespace(time=iter(range(0, 10_000, 300)).__next__))
    monkeypatch.setattr(say, "render", lambda book, ep, line, out, attempt, records: {
        "index": line.index, "speaker": "a", "text": line.text, "seconds": 1.0, "tries": attempt + 1})
    monkeypatch.setattr(say, "listen_all", lambda recs, *a, **k: [r.update(
        passed=True, error_rate=0.0, similarity=0.9, floor=0.65, why="ok", heard="Gold.") for r in recs] and [])
    return tmp_path / "episodes" / "ep01"


def test_the_first_saying_spends_the_say_row_not_the_lines_wall(tmp_path, monkeypatch):
    home = _fresh_line(tmp_path, monkeypatch)
    say.main("x", 1)
    assert step_attempts.seconds(home, "say") == 300.0 and step_attempts.seconds(home, "lines") == 0.0


def test_a_re_say_of_a_line_heard_wrong_spends_the_lines_wall(tmp_path, monkeypatch):
    home = _fresh_line(tmp_path, monkeypatch)
    heard_wrong = {"index": 0, "speaker": "a", "text": "Gold.", "seconds": 1.0, "tries": 1, "passed": False,
                   "rel_path": "episodes/ep01/audio/lines/l00.wav"}
    (home / "audio" / "lines" / "l00.wav").write_bytes(b"RIFF")
    (home / "audio" / "lines" / "lines.json").write_text(json.dumps([heard_wrong]), encoding="utf-8")
    say.main("x", 1)
    assert step_attempts.seconds(home, "lines") == 300.0 and step_attempts.seconds(home, "say") == 0.0


def test_the_round_bucket_reads_whether_any_line_was_listened_to():
    fresh, heard = {}, {0: {"passed": False}}
    assert say.round_bucket(0, [], fresh, [0]) == "say"
    assert say.round_bucket(1, [], fresh, [0]) == "lines"
    assert say.round_bucket(0, [0], fresh, [0]) == "lines"
    assert say.round_bucket(0, [], heard, [0]) == "lines"


# ---- the finish line: killed hours beside the repair's own part ----------------------------
# (each repair against its own cap is package A's fix in studio/repair_clock.finish_part)

def test_ep01s_finish_line_names_the_killed_hours_before_the_repairs(tmp_path):
    from tests.test_gpu_ledger import load
    home = _ep01(tmp_path, timing=False)
    line = load().finish_line(home)
    assert line == ("charged 6.02 h | wall 30.85 h | dead 23.00 h"
                    " | killed 1.73 h in 4 runs (0.73 h of the charge, 1.00 h of the repair)"
                    + repair_clock.finish_part(home))
