"""Item 9: qc reads the DELIVERED master, not the plan's intentions.

The two ffmpeg measurements (scene-detect, loudnorm) and the tracker are
injected, so the default suite runs against a recorded fixture of
scene-detect timestamps and never shells out.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.trailer import qc
from studio.trailer_stage_spec import Metre, QCReport

FIXTURE = Path("tests/fixtures/qc_scene_cuts.json")


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def metre_at(bpm: float, seconds: float, title_hit: float | None = None) -> Metre:
    beat = 60.0 / bpm
    beats = [round(i * beat, 4) for i in range(int(seconds / beat))]
    return Metre(seed=0, rel_path="TRAILER.mp4", seconds=seconds, bpm=bpm, bar=4 * beat,
                 beats=beats, downbeats=beats[::4], bars_in_mode=0.9, grid="metre",
                 fitness=20.0, hits=[30.0, 60.0], stopdowns=[86.5], title_hit=title_hit)


class TestCutLists:
    def test_planned_cuts_are_shot_starts_plus_the_title_card(self):
        plan = {"shots": [{"start": 0.0, "seconds": 2.0}, {"start": 2.0, "seconds": 3.0}]}
        assert qc.planned_cuts(plan) == [2.0, 5.0]

    def test_missing_cuts_are_the_planned_ones_the_picture_lacks(self):
        assert qc.missing_cuts([2.0, 5.0, 9.0], [2.02, 9.0]) == [5.0]

    def test_fraction_on_counts_cuts_within_forty_ms(self):
        assert qc.fraction_on([1.0, 2.03, 3.1], [1.0, 2.0, 3.0]) == pytest.approx(2 / 3)

    def test_on_cap_fraction_counts_shots_at_the_ceiling(self):
        assert qc.on_cap_fraction([4.0, 3.99, 2.0, 1.0], 4.0) == 0.5


class TestLineOverBed:
    """`line_over_bed_lu` was a target (5 LU) that no run ever filled: run 9
    shipped with the field empty and was heard as 'music too loud'.  The mix
    now leaves the ducked bed and the levelled lines beside the master with
    a sheet of where each was laid, and QC reads them.  Measurers are
    injected; nothing here shells out."""

    def write_mix(self, out: Path, lines: list[tuple[float, str]]) -> None:
        out.mkdir(parents=True, exist_ok=True)
        (out / "TRAILER-test.mp4").write_bytes(b"")
        (out / "TRAILER-test.bed-ducked.wav").write_bytes(b"")
        for _, rel in lines:
            (out / rel).write_bytes(b"")
        (out / "lines.level.json").write_text(
            json.dumps([{"at": at, "rel_path": rel} for at, rel in lines]), encoding="utf-8")

    def test_each_line_is_measured_against_the_ducked_bed_under_its_window(self, tmp_path):
        out = tmp_path / "main"
        self.write_mix(out, [(3.0, "line-0.level.wav"), (10.0, "line-1.level.wav")])
        bed = [(t / 10, -30.0 if 3.0 <= t / 10 < 5.0 else -14.0) for t in range(0, 150)]
        levels = {"line-0.level.wav": -21.0, "line-1.level.wav": -12.0}
        lu = qc.line_over_bed(out, momentary=lambda p: bed,
                              integrated=lambda p: levels[p.name], seconds=lambda p: 2.0)
        assert lu == [pytest.approx(9.0), pytest.approx(2.0)]

    def test_a_master_without_lines_measures_nothing(self, tmp_path):
        out = tmp_path / "main"
        out.mkdir()
        (out / "TRAILER-test.mp4").write_bytes(b"")
        assert qc.line_over_bed(out, momentary=lambda p: [], integrated=lambda p: 0.0,
                                seconds=lambda p: 0.0) == []

    def test_the_report_carries_the_measurement_and_flags_a_buried_line(self, tmp_path):
        fixture = load_fixture()
        out = tmp_path / "main"
        self.write_mix(out, [(3.0, "line-0.level.wav")])
        (out / "plan.json").write_text(json.dumps(fixture["plan"]), encoding="utf-8")
        report = qc.qc(out, detect=lambda video, threshold=0.1: fixture["scene_cuts"],
                       measure=lambda video, **_: metre_at(120, 60.0),
                       loud=lambda video: (-14.0, -1.5),
                       lines=lambda out_dir: [2.0])
        assert report.line_over_bed_lu == [2.0]
        assert "line_over_bed_lu" in report.flags
        written = json.loads((out / "qc.json").read_text(encoding="utf-8"))
        assert written["line_over_bed_lu"] == [2.0]


class TestReport:
    def test_qc_reports_manifest_cuts_missing_from_picture(self, tmp_path):
        fixture = load_fixture()
        out = tmp_path / "trailer" / "main"
        out.mkdir(parents=True)
        (out / "plan.json").write_text(json.dumps(fixture["plan"]), encoding="utf-8")
        (out / "TRAILER-test.mp4").write_bytes(b"")
        seen = fixture["scene_cuts"]
        report = qc.qc(out, detect=lambda video, threshold=0.1: seen,
                       track=lambda samples, rate: ([], []),
                       measure=lambda video, **_: metre_at(120, 60.0, title_hit=48.0),
                       loud=lambda video: (-14.0, -1.5))
        assert isinstance(report, QCReport) and report.cuts == len(seen)
        written = json.loads((out / "qc.json").read_text(encoding="utf-8"))
        assert written["missing_cuts"] == fixture["expected_missing"]
        assert report.floor_pass and report.unbound_shots == 0

    def test_a_loud_master_fails_the_floor(self, tmp_path):
        fixture = load_fixture()
        out = tmp_path / "main"
        out.mkdir()
        (out / "plan.json").write_text(json.dumps(fixture["plan"]), encoding="utf-8")
        (out / "TRAILER-test.mp4").write_bytes(b"")
        report = qc.qc(out, detect=lambda video, threshold=0.1: fixture["scene_cuts"],
                       measure=lambda video, **_: metre_at(120, 60.0),
                       loud=lambda video: (-9.0, 0.5))
        assert not report.floor_pass

    def test_cuts_on_beat_reads_the_delivered_picture(self):
        plan = {"shots": [{"start": 0.0, "seconds": 2.0, "cast": [], "char_refs": {}},
                          {"start": 2.0, "seconds": 2.0, "cast": [], "char_refs": {}}]}
        found = metre_at(120, 60.0)
        report = qc.report(plan, found, seen=[2.0, 4.0, 5.2], loud=(-14.0, -2.0))
        assert report.cuts == 3 and report.cuts_on_beat == pytest.approx(2 / 3)
        assert report.title_on_downbeat  # the card at 4.0 is a downbeat at 120 BPM
