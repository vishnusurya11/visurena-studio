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


def fixture_beats(out_dir: Path) -> list[str]:
    """The fixture plan's own beats, as if every clip were freshly rendered."""
    return [shot["beat_id"] for shot in load_fixture()["plan"]["shots"]]


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

    def test_a_cut_on_a_stopdown_or_hit_is_on_the_music(self):
        """Run 10: the walk cuts on every L0 event, the tracker puts them
        between beats, and QC graded 8 of them off-beat."""
        found = metre_at(120, 60.0).model_copy(update={"stopdowns": [10.25], "hits": [20.75]})
        assert qc.on_music(found) == sorted(set(found.beats) | {10.25, 20.75})
        assert qc.fraction_on([10.25, 20.75, 30.0], qc.on_music(found)) == 1.0

    def test_cuts_where_the_grid_has_no_pulse_are_not_graded(self):
        """Before the first beat and after the last there is nothing to be
        on: an intro shot and the card over the tail are not off-beat."""
        found = metre_at(120, 60.0)
        found = found.model_copy(update={"beats": found.beats[10:]})  # the pulse starts at 5.0
        assert qc.graded([0.3, 5.0, 59.5, 61.0, 70.0], found) == [5.0, 59.5]
        assert qc.graded([1.0], found.model_copy(update={"beats": []})) == []

    def test_on_cap_fraction_counts_shots_at_the_ceiling(self):
        assert qc.on_cap_fraction([4.0, 3.99, 2.0, 1.0], 4.0) == 0.5

    def test_an_act_one_shot_is_measured_against_its_own_act_s_cap(self):
        """At 92 BPM act 1 may run two bars (5.2 s); `max_shot` says 4.0.  A
        4.0 s act-1 shot is inside its ceiling, an act-3 one is on it."""
        bar = 240.0 / 92.0
        shots = [{"start": 0.0, "seconds": 4.0}, {"start": 4.0, "seconds": 2.0},
                 {"start": 6.0, "seconds": 2.0}, {"start": 8.0, "seconds": 2.0},
                 {"start": 10.0, "seconds": 4.0}]
        assert qc.on_cap_fraction(qc.act_caps_of(shots, bar), bar) == 0.2


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
                       lines=lambda out_dir: [2.0], fresh=fixture_beats)
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
                       loud=lambda video: (-14.0, -1.5), fresh=fixture_beats)
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
                       loud=lambda video: (-9.0, 0.5), fresh=fixture_beats)
        assert not report.floor_pass

    def test_cuts_on_beat_reads_the_delivered_picture(self):
        plan = {"shots": [{"start": 0.0, "seconds": 2.0, "cast": [], "char_refs": {}},
                          {"start": 2.0, "seconds": 2.0, "cast": [], "char_refs": {}}]}
        found = metre_at(120, 60.0)
        report = qc.report(plan, found, seen=[2.0, 4.0, 5.2], loud=(-14.0, -2.0))
        assert report.cuts == 3 and report.cuts_on_beat == pytest.approx(2 / 3)
        assert report.title_on_downbeat  # the card at 4.0 is a downbeat at 120 BPM

    def test_the_report_grades_on_the_music_over_the_pulse_it_has(self):
        """Run 10's shape in small: a cut in the intro before the pulse, one
        on a stopdown between beats, one off, and the card over the tail."""
        plan = {"shots": [{"start": 0.0, "seconds": 2.0, "cast": [], "char_refs": {}}]}
        found = metre_at(120, 20.0).model_copy(update={"beats": [round(0.5 * i, 4) for i in range(6, 40)],
                                                       "downbeats": [round(2.0 * i, 4) for i in range(2, 10)],
                                                       "stopdowns": [10.25], "hits": []})
        report = qc.report(plan, found, seen=[1.0, 4.0, 10.25, 12.3, 25.0], loud=(-14.0, -2.0))
        assert report.cuts == 5
        assert report.cuts_on_beat == pytest.approx(2 / 3)
        assert report.cuts_on_downbeat == pytest.approx(2 / 3)


class TestNoTakePlaysTwice:
    """The owner's rule, measured on the master: a rendered take is never
    seen twice, and no shot is cut from a clip of an earlier plan."""

    def plan(self, beat_ids):
        return {"shots": [{"beat_id": b, "start": 2.0 * i, "seconds": 2.0,
                           "cast": [], "char_refs": {}}
                          for i, b in enumerate(beat_ids)]}

    def report_of(self, beat_ids, fresh=None):
        return qc.report(self.plan(beat_ids), metre_at(120, 60.0), seen=[2.0],
                         loud=(-14.0, -1.5), fresh=fresh)

    def test_a_take_played_twice_is_counted(self):
        assert self.report_of(["B0", "B1", "B0"]).reused_shots == 1
        assert self.report_of(["B0", "B1", "B2"]).reused_shots == 0

    def test_a_shot_cut_from_a_clip_no_longer_fresh_is_counted(self):
        found = self.report_of(["B0", "B1", "B2"], fresh=["B0", "B2"])
        assert found.stale_shots == 1

    def test_without_a_freshness_reading_nothing_is_called_stale(self):
        assert self.report_of(["B0", "B1"]).stale_shots == 0

    def test_a_trailer_with_no_clips_json_has_no_fresh_clip_at_all(self, tmp_path):
        assert qc.fresh_shots(tmp_path) == []

    def test_fresh_shots_reads_the_run_s_own_record(self, tmp_path):
        from studio.clip_cache import fingerprint, record
        book = tmp_path / "book"
        out = book / "trailer" / "main"
        out.mkdir(parents=True)
        video = out / "clips" / "B0.mp4"
        video.parent.mkdir()
        video.write_bytes(b"mp4")
        recipe = {"prompt": "p", "seed": 1}
        record(video, recipe)
        (out / "clips.json").write_text(json.dumps({"clips": [
            {"beat_id": "B0", "rel_path": video.relative_to(book).as_posix(),
             "fingerprint": fingerprint(recipe)}]}), encoding="utf-8")
        assert qc.fresh_shots(out) == ["B0"]

def flat(level: float, start: float, end: float, step: float = 0.1) -> list[tuple[float, float]]:
    """Momentary readings holding one level across a span."""
    return [(round(start + i * step, 2), level)
            for i in range(int(round((end - start) / step)))]


class TestLayers:
    """A: how much of the runtime is music with nothing over it.  Run 10 was
    92% music-only with two stretches of 27 and 40 seconds, and QC -- which
    measured integrated loudness, true peak and a fraction of cuts -- had no
    field that could say so."""

    def readings(self):
        return flat(-14.0, 0.0, 30.0)

    def test_a_line_window_is_not_music_only(self):
        runs = qc.music_only_runs(self.readings(), [(10.0, 14.0)], 30.0)
        assert runs == [(0.0, 9.9), (14.0, 29.9)]

    def test_silence_is_not_music_only_either(self):
        quiet = flat(-14.0, 0.0, 10.0) + flat(-60.0, 10.0, 14.0) + flat(-14.0, 14.0, 20.0)
        assert qc.music_only_runs(quiet, [], 20.0) == [(0.0, 9.9), (14.0, 19.9)]

    def test_the_fraction_is_the_share_of_the_picture(self):
        runs = qc.music_only_runs(self.readings(), [(10.0, 14.0)], 30.0)
        assert qc.music_only_fraction(runs, 30.0) == pytest.approx(0.86, abs=0.02)

    def test_the_final_montage_is_measured_apart_from_the_rest(self):
        """The norm allows ONE long music-only stretch, at the end."""
        runs = [(0.0, 6.0), (10.0, 30.0)]
        assert qc.longest_music_only(runs) == 6.0
        assert qc.final_music_only(runs) == 20.0

    def test_a_single_stretch_is_the_final_montage(self):
        assert qc.longest_music_only([(0.0, 20.0)]) == 0.0
        assert qc.final_music_only([(0.0, 20.0)]) == 20.0

    def test_nothing_measured_is_nothing_claimed(self):
        assert qc.music_only_fraction([], 30.0) == 0.0
        assert qc.final_music_only([]) == 0.0


class TestSpeechOccupancy:
    def test_it_is_the_share_of_the_picture_with_a_voice_on_it(self):
        assert qc.speech_occupancy([(2.0, 4.0), (10.0, 13.0)], 25.0) == pytest.approx(0.2)

    def test_a_line_running_past_the_card_only_counts_to_the_card(self):
        assert qc.speech_occupancy([(20.0, 30.0)], 25.0) == pytest.approx(0.2)

    def test_a_short_trailer_is_asked_for_three_real_lines_not_a_ratio(self):
        """Three lines of the 1.5-4 s the norm gives them is 0.22 of 30 s and
        cannot be the 0.30 a 90-150 s trailer is measured against."""
        assert qc.speech_target(25.0) == 0.22
        assert qc.speech_target(30.0) == 0.22

    def test_the_full_norm_applies_once_the_trailer_is_long_enough(self):
        assert qc.speech_target(60.0) == 0.30
        assert qc.speech_target(105.0) == 0.30
        assert 0.22 < qc.speech_target(45.0) < 0.30


class TestShape:
    """C and D: where the loudest moment sits and how the trailer ends."""

    def test_the_peak_position_is_a_fraction_of_the_picture(self):
        short = flat(-20.0, 0.0, 20.0) + flat(-10.0, 20.0, 22.0) + flat(-18.0, 22.0, 25.0)
        assert qc.peak_position(short, 25.0) == pytest.approx(0.8)

    def test_the_undefined_head_of_the_short_term_window_is_dropped(self):
        """ebur128 reports about -120 until its 3 s window fills, and a
        reading at t=0 louder than everything would otherwise win."""
        short = [(0.0, 0.0), (1.0, 0.0)] + flat(-20.0, 3.0, 10.0) + flat(-10.0, 10.0, 12.0)
        assert qc.peak_position(short, 12.0) >= 0.8

    def test_the_acts_are_thirds_of_the_picture_not_of_the_file(self):
        assert qc.act_bounds(30.0) == [(0.0, 10.0), (10.0, 20.0), (20.0, 30.0)]

    def test_act_three_is_measured_against_act_two(self):
        readings = flat(-20.0, 0.0, 10.0) + flat(-18.0, 10.0, 20.0) + flat(-13.0, 20.0, 30.0)
        assert qc.act_over_act(readings, qc.act_bounds(30.0)) == pytest.approx(5.0)

    def test_a_trailer_that_sinks_into_its_third_act_reads_negative(self):
        """Run 10: act 3 was 1-3 LU QUIETER than act 2."""
        readings = flat(-20.0, 0.0, 10.0) + flat(-12.0, 10.0, 20.0) + flat(-15.0, 20.0, 30.0)
        assert qc.act_over_act(readings, qc.act_bounds(30.0)) == pytest.approx(-3.0)


class TestTheButton:
    def test_the_held_breath_is_the_longest_stretch_under_the_ceiling(self):
        readings = flat(-14.0, 0.0, 20.0) + flat(-45.0, 20.0, 22.0) + flat(-10.0, 22.0, 26.0)
        assert qc.longest_under(readings, 20.0, 22.0, -35.0) == pytest.approx(1.9, abs=0.05)

    def test_a_fade_is_not_a_hard_out(self):
        """Run 10 faded over 3 s.  The gate asks that the bed was PLAYING and
        then was not, within one momentary window."""
        fade = [(round(20.0 + i * 0.1, 2), -14.0 - i) for i in range(30)]
        assert not qc.hard_out_ok(flat(-14.0, 19.0, 20.0) + fade, 20.0)

    def test_a_stop_is(self):
        readings = flat(-14.0, 19.0, 20.0) + flat(-45.0, 20.0, 22.0)
        assert qc.hard_out_ok(readings, 20.0)

    def test_a_bed_that_was_never_playing_did_not_stop(self):
        assert not qc.hard_out_ok(flat(-50.0, 19.0, 22.0), 20.0)

    def test_the_hit_is_read_where_the_card_is_struck(self):
        readings = flat(-45.0, 20.0, 22.0) + flat(-9.0, 22.0, 25.0)
        assert qc.title_hit_lu(readings, 22.0) == -9.0

    def test_a_card_struck_over_nothing_reads_dead(self):
        """Run 10's cue had faded to -46 LUFS by the time the card arrived."""
        assert qc.title_hit_lu(flat(-46.0, 22.0, 25.0), 22.0) == -46.0


class TestBedUnderLine:
    def test_it_is_the_loudest_moment_of_the_window_not_the_average(self):
        """A mean says the bed was mostly out of the way; run 10's bed was
        mostly out of the way of a line it opened over at -9 LUFS."""
        bed = flat(-30.0, 3.0, 4.0) + [(4.0, -9.0)] + flat(-30.0, 4.1, 5.0)
        assert qc.bed_under_lines(bed, [(3.0, 5.0)]) == [-9.0]

    def test_the_smeared_onset_is_not_read_as_the_bed_under_the_line(self):
        """ebur128 integrates 400 ms, so the reading at a line's onset is
        mostly the bed from BEFORE the duck opened."""
        bed = [(3.0, -9.0), (3.1, -14.0), (3.2, -20.0)] + flat(-30.0, 3.4, 5.0)
        assert qc.bed_under_lines(bed, [(3.0, 5.0)]) == [-30.0]

    def test_a_window_the_bed_has_no_reading_in_measures_nothing_loud(self):
        assert qc.bed_under_lines([], [(3.0, 5.0)]) == [-70.0]


class TestPerActBeatLock:
    """G: one on-beat number for the whole trailer forces a music video."""

    def test_each_act_is_graded_on_its_own(self):
        grid = [round(0.5 * i, 2) for i in range(60)]
        cuts = [1.3, 2.7, 10.0, 10.5, 21.0, 21.5, 22.0]
        assert qc.on_beat_by_act(cuts, grid, qc.act_bounds(30.0)) == [0.0, 1.0, 1.0]

    def test_an_act_with_no_cuts_in_it_reads_zero(self):
        assert qc.on_beat_by_act([], [0.0], qc.act_bounds(30.0)) == [0.0, 0.0, 0.0]


class TestTheCueCut:
    """The cut against the cue it was cut to: qc reads music/plan.json and
    grades the detected cuts against the plan's spans."""

    def plan_json(self) -> str:
        from tests.test_cue_qc import build_plan
        return build_plan().model_copy(update={"rel_path": "m/cue-1.flac"}).model_dump_json()

    def write_cue(self, out: Path, takes: list[dict]) -> None:
        (out / "music").mkdir(parents=True, exist_ok=True)
        (out / "music/plan.json").write_text(self.plan_json(), encoding="utf-8")
        (out / "clips.json").write_text(json.dumps({"takes": takes}), encoding="utf-8")
        (out / "lines.level.json").write_text(json.dumps(
            {"hard_out": 24.0, "lines": [{"at": 16.5, "seconds": 2.5, "rel_path": "l.wav"}]}),
            encoding="utf-8")

    def test_the_report_counts_frames_rendered_against_frames_played(self, tmp_path):
        self.write_cue(tmp_path, [{"frames": 121}, {"frames": 243}])
        cuts = [4.0, 6.0, 8.0, 10.0, 10.5, 14.5, 16.0, 20.0, 22.0]
        cut = qc.measure_cue(tmp_path, cuts)
        assert cut.frames_rendered == 364 and cut.frames_played == 576
        assert cut.floor_misses() == [] and cut.lines_in_troughs == 1.0

    def test_a_cut_inside_a_sustain_fails_the_floor(self, tmp_path):
        self.write_cue(tmp_path, [])
        cut = qc.measure_cue(tmp_path, [2.0, 4.0, 8.0, 20.0])
        assert "cuts_inside_sustain" in cut.floor_misses()

    def test_the_chosen_seeds_own_cut_map_supplies_the_events(self, tmp_path):
        """Named after the cue that plays, so a settled cue (row 53) is graded
        against its own moved map, never the unsettled seed's."""
        self.write_cue(tmp_path, [])
        events = [{"t": 4.0, "rank": 3}, {"t": 12.0, "rank": 2}, {"t": 5.0, "rank": 1}]
        (tmp_path / "music/cutmap-1.json").write_text(json.dumps({"events": events}), encoding="utf-8")
        assert qc.measure_cue(tmp_path, [4.0, 12.0, 5.0]).cuts_on_events == pytest.approx(2 / 3)

    def test_a_trailer_cut_before_the_plan_existed_is_unmeasured(self, tmp_path):
        assert qc.measure_cue(tmp_path, [2.0]) is None

    def test_qc_carries_the_cue_cut_into_the_report(self, tmp_path):
        fixture = load_fixture()
        out = tmp_path / "main"
        out.mkdir()
        (out / "TRAILER-x.mp4").write_bytes(b"")
        (out / "plan.json").write_text(json.dumps(fixture["plan"]), encoding="utf-8")
        self.write_cue(out, [{"frames": 100}])
        report = qc.qc(out, detect=lambda video, threshold=0.1: [4.0, 8.0, 12.0, 20.0],
                       measure=lambda video, **_: metre_at(120, 60.0),
                       loud=lambda video: (-14.0, -1.5), lines=lambda out_dir: [],
                       fresh=fixture_beats, shape=None)
        assert report.cue_cut is not None and report.cue_cut.frames_rendered == 100
        assert "cue_cut" not in report.flags and "cuts_inside_sustain" in report.flags


class TestTheLevelSheet:
    def test_the_mixs_own_sheet_carries_the_hard_out_and_every_duck(self, tmp_path):
        (tmp_path / "lines.level.json").write_text(json.dumps({
            "hard_out": 96.4, "lines": [{"at": 12.0, "seconds": 2.5,
                                         "rel_path": "line-0.level.wav", "duck_db": -11.2,
                                         "bed_peak_lufs": -12.8, "bed_floor_lufs": -24.0}]}),
            encoding="utf-8")
        sheet = qc.level_sheet(tmp_path)
        assert sheet["hard_out"] == 96.4
        assert qc.sheet_windows(sheet) == [(12.0, 14.5)]

    def test_run_tens_bare_list_still_reads(self, tmp_path):
        """The one master this pipeline can measure before and after."""
        (tmp_path / "lines.level.json").write_text(
            json.dumps([{"at": 29.755, "rel_path": "line-0.level.wav"}]), encoding="utf-8")
        sheet = qc.level_sheet(tmp_path)
        assert sheet["hard_out"] is None and len(sheet["lines"]) == 1
        assert qc.sheet_windows(sheet, seconds=lambda p: 2.23) == [(29.755, 31.985)]

    def test_a_mix_that_laid_no_lines_has_no_sheet_and_claims_nothing(self, tmp_path):
        assert qc.level_sheet(tmp_path) == {"hard_out": None, "lines": []}


class TestShapeReachesTheReport:
    def plan(self):
        return {"shots": [{"start": 0.0, "seconds": 2.0, "cast": [], "char_refs": {}}]}

    def test_the_report_carries_a_measured_shape_and_flags_what_it_missed(self):
        shape = {"music_only_fraction": 0.92, "longest_music_only_s": 40.0,
                 "speech_occupancy": 0.021, "speech_target": 0.30,
                 "peak_position": 0.53, "act3_over_act2_lu": -2.0,
                 "pre_title_silence_s": 0.0, "hard_out": False, "title_hit_lu": -46.0,
                 "cuts_on_beat_by_act": [0.9, 0.8, 0.5]}
        report = qc.report(self.plan(), metre_at(120, 60.0), seen=[2.0],
                           loud=(-14.0, -1.5), shape=shape)
        assert set(report.flags) >= {"music_only_fraction", "longest_music_only_s",
                                     "speech_occupancy", "peak_position",
                                     "act3_over_act2_lu", "pre_title_silence_s",
                                     "title_hit_lu", "cuts_on_beat_act3"}
        assert "cuts_on_beat_act1" not in report.flags  # it graded the walk; the walk is gone
        assert not report.floor_pass  # the bed never stopped

    def test_a_report_with_no_shape_claims_nothing_and_still_passes(self):
        report = qc.report(self.plan(), metre_at(120, 60.0), seen=[2.0], loud=(-14.0, -1.5))
        assert report.floor_pass and "music_only_fraction" not in report.flags

    def test_a_clipped_line_fails_the_floor_rather_than_flagging(self):
        """B, as safety: run 10's only line had 3,096 samples at full scale
        and flat factor 24.2, and every gate passed it."""
        clipped = qc.report(self.plan(), metre_at(120, 60.0), seen=[2.0], loud=(-14.0, -1.5),
                            shape={"line_tp": [0.0], "line_flat_factor": [24.2]})
        assert not clipped.floor_pass and not clipped.lines_are_clean
        clean = qc.report(self.plan(), metre_at(120, 60.0), seen=[2.0], loud=(-14.0, -1.5),
                          shape={"line_tp": [-3.4], "line_flat_factor": [0.0]})
        assert clean.floor_pass

    def test_a_bed_left_on_a_line_is_flagged(self):
        buried = qc.report(self.plan(), metre_at(120, 60.0), seen=[2.0], loud=(-14.0, -1.5),
                           shape={"bed_under_line_lu": [-9.0], "line_crest_db": [2.58]})
        assert "bed_under_line_lu" in buried.flags and "line_crest_db" in buried.flags

    def test_the_whole_trailer_beat_lock_is_no_longer_a_target(self):
        """It is the target that forced a music video."""
        from studio.trailer_stage_spec import QC_TARGETS
        assert "cuts_on_beat" not in QC_TARGETS
