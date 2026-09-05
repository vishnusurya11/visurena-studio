"""The line layer: a spoken line at its planned window, the bed out of its way.

Real local ffmpeg on synthetic audio: a band-limited noise bed and a tone
line.  Loudness is READ from ebur128, never assumed from the graph, because
the first duck graph measured a 0.4 dB duck -- the key was quieter than the
compressor's threshold and nothing in the graph text said so.  That is also
why the duck is no longer a compressor: every number the rule asks for is now
written into the envelope, and the test reads back the number that was asked.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from studio import trailer_assemble as ta
from studio.trailer_stage_spec import VoiceLine

SECONDS = 8.0
LINE_AT, LINE_SECONDS = 3.0, 2.0


def lavfi(path: Path, source: str, filters: str, seconds: float, channels: int) -> Path:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", source, "-af", filters,
                    "-t", f"{seconds:.3f}", "-ac", str(channels), "-c:a", "pcm_s16le", str(path)],
                   check=True, capture_output=True)
    return path


@pytest.fixture()
def bed(tmp_path):
    """Pink noise held to 300-2000 Hz: the band a cue's melody lives in."""
    return lavfi(tmp_path / "bed.wav", "anoisesrc=color=pink:seed=7:sample_rate=48000",
                 "highpass=f=300,lowpass=f=2000,volume=-6dB", SECONDS, 2)


@pytest.fixture()
def wide_bed(tmp_path):
    """A bed with a pulse under it and air over it -- the two bands run 10's
    band-split duck left running straight through the line."""
    return lavfi(tmp_path / "wide.wav", "anoisesrc=color=pink:seed=3:sample_rate=48000",
                 "volume=-8dB", SECONDS, 2)


@pytest.fixture()
def line(tmp_path):
    """A tone loud enough to be a key: ffmpeg's sine is 28 dB down by default."""
    return lavfi(tmp_path / "line.wav", "sine=frequency=440:sample_rate=24000",
                 "volume=12dB", LINE_SECONDS, 1)


@pytest.fixture()
def picture(tmp_path):
    out = tmp_path / "picture.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=24",
                    "-t", f"{SECONDS:.3f}", "-pix_fmt", "yuv420p", str(out)], check=True, capture_output=True)
    return out


def loudness_between(path: Path, start: float, end: float) -> float:
    return ta.window_loudness(ta.momentary(path), start, end)


def peak_between(path: Path, start: float, end: float) -> float:
    return ta.window_peak(ta.momentary(path), start, end)


def window(at: float = LINE_AT, seconds: float = LINE_SECONDS,
           depth: float = 12.0) -> tuple[float, float, float]:
    return (at, at + seconds, depth)


class TestDuckEnvelope:
    """The envelope as arithmetic, before any file exists.  Every number in
    the rule -- depth, attack, lookahead, release -- is a number here."""

    def test_the_bed_is_untouched_outside_every_window(self):
        assert ta.duck_db(1.0, [window()]) == 0.0
        assert ta.duck_db(7.0, [window()]) == 0.0

    def test_it_is_already_at_full_depth_when_the_line_starts(self):
        """B: bed_under_line <= -24 LUFS INCLUDING the first 200 ms.  Run 10's
        attack was 160 ms, so the first third of the line played over the bed
        at its own level."""
        assert ta.duck_db(LINE_AT, [window()]) == pytest.approx(-12.0)
        assert ta.duck_db(LINE_AT + 0.2, [window()]) == pytest.approx(-12.0)

    def test_it_opens_a_lookahead_before_the_line_does(self):
        opens = LINE_AT - ta.DUCK_PREDELAY
        assert ta.duck_db(opens - 0.01, [window()]) == 0.0
        assert ta.duck_db(opens + ta.DUCK_ATTACK, [window()]) == pytest.approx(-12.0)

    def test_it_releases_over_the_full_release_and_no_longer(self):
        end = LINE_AT + LINE_SECONDS
        assert ta.duck_db(end + ta.DUCK_RELEASE / 2, [window()]) == pytest.approx(-6.0, abs=0.1)
        assert ta.duck_db(end + ta.DUCK_RELEASE, [window()]) == 0.0

    def test_two_lines_do_not_stack_into_a_hole(self):
        both = [window(3.0, 2.0, 12.0), window(3.5, 2.0, 10.0)]
        assert ta.duck_db(4.0, both) == pytest.approx(-12.0)

    def test_the_depth_is_whatever_reaches_the_floor_a_line_needs(self):
        """A loud bed ducks further than a quiet one; neither ducks less than
        the 10 LU the rule asks for."""
        assert ta.duck_depth(-10.0) == pytest.approx(14.0)
        assert ta.duck_depth(-40.0) == ta.DUCK_DEPTH_DB

    def test_a_line_placed_on_a_hit_does_not_gate_the_bed_away(self):
        """Past DUCK_DEPTH_MAX the bed is gone rather than ducked, and the
        hole is the worse artefact.  QC's bed_under_line_lu names the
        placement instead."""
        assert ta.duck_depth(0.0) == ta.DUCK_DEPTH_MAX

    def test_the_depth_is_sized_against_the_loudest_moment_not_the_mean(self):
        """Run 10's one line sat over a mean of -14.8 LUFS and a PEAK of
        -9.1: it was placed on a bar the cue puts a hit on, and a duck sized
        to the mean leaves that hit above the ceiling the rule sets."""
        readings = [(3.0, -0.4)] + [(round(3.1 + i * 0.1, 2), -30.0) for i in range(19)]
        assert ta.bed_peak(readings, 3.0, 5.0) == -0.4
        assert ta.bed_level(readings, 3.0, 5.0) < -20.0
        assert ta.duck_depth(ta.bed_peak(readings, 3.0, 5.0)) == ta.DUCK_DEPTH_MAX

    def test_a_window_the_bed_is_silent_in_needs_no_duck_beyond_the_minimum(self):
        assert ta.duck_depth(ta.bed_peak([(3.0, float("-inf"))], 3.0, 5.0)) == ta.DUCK_DEPTH_DB

    def test_the_floor_and_the_line_target_are_the_gap_the_norm_asks_for(self):
        assert ta.LINE_TARGET_LUFS - ta.BED_UNDER_LINE == pytest.approx(ta.LINE_OVER_BED)


class TestBedExpression:
    """The same envelope as ffmpeg reads it."""

    def test_the_expression_agrees_with_the_arithmetic(self, tmp_path, bed):
        """Rendered, then measured: the expression is only worth what the file
        it produces measures."""
        shaped = ta.shape_bed(bed, [window()], None, tmp_path / "shaped.wav")
        before = loudness_between(bed, 1.0, 2.5)
        inside = loudness_between(shaped, LINE_AT + 0.3, LINE_AT + LINE_SECONDS)
        assert before - inside == pytest.approx(12.0, abs=1.0)

    def test_a_bed_with_nothing_to_do_is_returned_as_it_is(self, tmp_path, bed):
        assert ta.shape_bed(bed, [], None, tmp_path / "shaped.wav") == bed
        assert not (tmp_path / "shaped.wav").exists()

    def test_every_comma_inside_the_expression_is_escaped(self):
        """An unescaped comma inside a filter argument ends the filter, and
        ffmpeg then errors on a filter nobody wrote."""
        expression = ta.bed_expr([window()], 6.0)
        assert "," not in expression.replace("\\,", "")

    def test_the_gate_is_a_stop_not_a_fade(self):
        assert ta.bed_gain(6.0, [], 6.0) == 0.0
        assert ta.bed_gain(6.0 - ta.HARD_OUT_GATE, [], 6.0) == pytest.approx(1.0)
        assert ta.bed_gain(6.0 - ta.HARD_OUT_GATE / 2, [], 6.0) == pytest.approx(0.5)
        assert ta.HARD_OUT_GATE <= 0.05


class TestHardOut:
    def test_the_bed_stops_dead_and_stays_stopped(self, tmp_path, bed):
        shaped = ta.shape_bed(bed, [], 6.0, tmp_path / "shaped.wav")
        assert loudness_between(shaped, 4.5, 5.5) == pytest.approx(
            loudness_between(bed, 4.5, 5.5), abs=1.0)
        assert peak_between(shaped, 6.5, 7.9) <= -60.0

    def test_it_lands_within_a_frame_of_the_point_it_was_asked_for(self, tmp_path, bed):
        shaped = ta.shape_bed(bed, [], 6.0, tmp_path / "shaped.wav")
        readings = ta.momentary(shaped)
        # M is a 400 ms trailing window, so the first reading fully past the
        # gate is the one that has to be silent.
        assert ta.window_peak(readings, 6.45, 6.6) <= -60.0
        assert ta.window_peak(readings, 5.0, 5.9) >= -30.0

    def test_the_bed_is_peak_safe_before_anything_is_summed_into_it(self, tmp_path, wide_bed):
        """F: pre-limiter TP <= -1 dBTP on the bed.  Run 10 handed the mix a
        bed at +0.4 dBTP and then asked a limiter for 5.5 dB of average."""
        shaped = ta.shape_bed(wide_bed, [], 6.0, tmp_path / "shaped.wav")
        assert ta.true_peak(shaped) <= ta.BED_TP


class TestFullBandDuck:
    def test_the_pulse_and_the_air_duck_too(self, tmp_path, wide_bed):
        """Run 10 ducked 250-4000 Hz only, so under the one line the pulse
        kept hitting.  Measured per band, not per programme."""
        shaped = ta.shape_bed(wide_bed, [window(depth=12.0)], None, tmp_path / "shaped.wav")
        for low, high in ((40, 200), (250, 4000), (6000, 16000)):
            band = f"highpass=f={low},lowpass=f={high}"
            before = ta.window_loudness(ta.momentary(banded(tmp_path, wide_bed, band, "a")), 1.0, 2.5)
            after = ta.window_loudness(ta.momentary(banded(tmp_path, shaped, band, "b")),
                                       LINE_AT + 0.3, LINE_AT + LINE_SECONDS)
            assert before - after >= 10.0, f"{low}-{high} Hz ducked only {before - after:.1f} LU"


def banded(tmp_path: Path, source: Path, filters: str, tag: str) -> Path:
    out = tmp_path / f"band-{tag}.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(source), "-af", filters,
                    "-c:a", "pcm_s16le", str(out)], check=True, capture_output=True)
    return out


class TestMeasure:
    def test_momentary_reads_every_hundred_ms(self, bed):
        readings = ta.momentary(bed)
        assert len(readings) >= 70
        assert all(-60.0 < m < 0.0 for _, m in readings[5:])

    def test_short_term_comes_from_the_same_pass(self, bed):
        assert len(ta.short_term(bed)) == len(ta.momentary(bed))
        assert ta.short_term(bed)[-1][1] > -60.0

    def test_window_loudness_averages_inside_only(self):
        readings = [(0.1, -30.0), (0.2, -30.0), (0.3, -10.0), (0.4, -10.0), (0.5, -50.0)]
        assert ta.window_loudness(readings, 0.3, 0.5) == pytest.approx(-10.0)

    def test_window_loudness_refuses_an_empty_window(self):
        with pytest.raises(ValueError):
            ta.window_loudness([(0.1, -30.0)], 5.0, 6.0)

    def test_window_peak_is_the_loudest_moment_not_the_average(self):
        readings = [(1.0, -40.0), (1.1, -18.0), (1.2, -40.0)]
        assert ta.window_peak(readings, 1.0, 1.3) == -18.0
        assert ta.window_peak(readings, 5.0, 6.0) == float("-inf")


class TestLineWindows:
    def test_a_plan_without_a_lines_field_matches_lines_to_shots(self, tmp_path):
        """Older plans only carry the line text on the shot it plays over."""
        book = tmp_path / "book"
        spoken = VoiceLine(index=0, text="Poison.", speaker="holmes",
                           rel_path="trailer/main/voice/lines/0.wav")
        plan = {"shots": [{"index": 3, "start": 12.5, "line": "Poison.", "speaker": "holmes"},
                          {"index": 4, "start": 14.0, "line": None}]}
        assert ta.line_windows(plan, [spoken], book) == [(12.5, book / "trailer/main/voice/lines/0.wav")]

    def test_a_line_the_plan_dropped_has_no_window(self, tmp_path):
        spoken = VoiceLine(index=2, text="Nobody.", speaker="holmes", rel_path="trailer/main/v/2.wav")
        assert ta.line_windows({"lines": [{"index": 0, "at": 1.0}], "shots": []}, [spoken], tmp_path) == []

    def test_a_card_has_no_file_to_lay(self, tmp_path):
        card = VoiceLine(index=0, text="A study in scarlet.", speaker=None, card=True)
        assert ta.line_windows({"lines": [{"index": 0, "at": 1.0}]}, [card], tmp_path) == []


@pytest.fixture()
def quiet_line(tmp_path):
    """A take 18 dB under the target and 20 under the bed: what a TTS voice
    at its own level can be, and what the duck's key could not hear."""
    return lavfi(tmp_path / "quiet.wav", "sine=frequency=440:sample_rate=24000",
                 "volume=-12dB", LINE_SECONDS, 1)


class TestLevel:
    """A line is levelled to an ABSOLUTE target, through a limiter.  Run 10
    levelled to the bed's own window with plain `volume=` into pcm_s16le:
    +11.8 dB, 3,096 clipped samples, flat factor 24.2, and the loudest point
    of the whole trailer was a piece of dialogue at -8.2 LUFS."""

    def test_the_gain_lands_a_line_on_its_target(self):
        assert ta.line_gain(-28.0) == pytest.approx(12.0)
        assert ta.line_gain(-10.0) == pytest.approx(-6.0)

    def test_the_gain_is_bounded_both_ways(self):
        assert ta.line_gain(-90.0) == ta.GAIN_LIMIT
        assert ta.line_gain(40.0) == -ta.GAIN_LIMIT

    def test_a_quiet_take_is_lifted_to_the_target(self, tmp_path, bed, quiet_line):
        levelled, = ta.level_lines(bed, [(LINE_AT, quiet_line)], tmp_path / "out")
        assert levelled.at == LINE_AT and levelled.path.name == "line-0.level.wav"
        assert ta.integrated(levelled.path) == pytest.approx(ta.LINE_TARGET_LUFS, abs=1.5)

    def test_a_hot_take_is_brought_down_to_the_same_place(self, tmp_path, bed, line):
        levelled, = ta.level_lines(bed, [(LINE_AT, line)], tmp_path / "out")
        assert ta.integrated(levelled.path) == pytest.approx(ta.LINE_TARGET_LUFS, abs=1.5)
        assert ta.integrated(levelled.path) < ta.integrated(line)

    def test_a_levelled_line_never_reaches_the_ceiling(self, tmp_path, line):
        """The whole point: a gain stage with a ceiling at the end of it."""
        hot = ta.level_line(line, 18.0, tmp_path / "hot.wav")
        assert ta.true_peak(hot) <= ta.LINE_TP

    def test_a_levelled_line_is_not_a_square_wave(self, tmp_path, bed, line):
        """B: flat factor 0.  Flat factor counts runs of identical samples --
        run 10's line measured 24.2 of them."""
        levelled, = ta.level_lines(bed, [(LINE_AT, line)], tmp_path / "out")
        peak, flat, _ = ta.line_shape(levelled.path)
        assert flat == 0.0 and peak <= ta.LINE_TP

    def test_a_silent_bed_window_does_not_pull_the_line_to_nothing(self):
        """Momentary readings in a stop-down are -inf; they are not a level
        to duck against."""
        readings = [(3.0, float("-inf")), (3.1, -20.0), (3.2, -20.0), (3.3, float("-inf"))]
        assert ta.bed_level(readings, 3.0, 3.4) == pytest.approx(-20.0)


class TestMixWithLines:
    def test_a_master_carries_the_line_and_gets_the_bed_out_of_its_way(
            self, tmp_path, bed, line, picture):
        out = tmp_path / "master.mp4"
        ta.mix_with_lines(picture, bed, [], [(LINE_AT, line)], out, seconds=SECONDS)
        assert out.exists()
        assert ta.clip_seconds(out) == pytest.approx(SECONDS, abs=0.1)
        ducked = out.with_name("master.bed-ducked.wav")
        assert ducked.exists()
        assert peak_between(ducked, LINE_AT, LINE_AT + LINE_SECONDS) <= ta.BED_UNDER_LINE + 1.0

    def test_the_bed_is_out_of_the_way_in_the_first_two_hundred_ms(
            self, tmp_path, bed, line, picture):
        """The lookahead is the whole reason this is an envelope and not a
        compressor: the duck is already down when the line arrives."""
        out = tmp_path / "master.mp4"
        ta.mix_with_lines(picture, bed, [], [(LINE_AT, line)], out, seconds=SECONDS)
        ducked = out.with_name("master.bed-ducked.wav")
        assert peak_between(ducked, LINE_AT, LINE_AT + 0.25) <= ta.BED_UNDER_LINE + 1.0

    def test_the_mix_writes_down_what_it_did_to_the_bed(self, tmp_path, bed, line, picture):
        """QC measures the duck and the hard out from the sheet beside the
        master, and the mix is the only thing that knows what it chose."""
        out = tmp_path / "master.mp4"
        ta.mix_with_lines(picture, bed, [], [(LINE_AT, line)], out, seconds=SECONDS, hard_out=7.0)
        sheet = json.loads((tmp_path / "lines.level.json").read_text(encoding="utf-8"))
        assert sheet["hard_out"] == 7.0
        row, = sheet["lines"]
        assert row["at"] == LINE_AT and row["rel_path"] == "line-0.level.wav"
        assert row["seconds"] == pytest.approx(LINE_SECONDS, abs=0.05)
        assert row["duck_db"] <= -ta.DUCK_DEPTH_DB
        assert row["bed_floor_lufs"] == pytest.approx(row["bed_peak_lufs"] + row["duck_db"], abs=0.01)

    def test_a_quiet_take_still_clears_the_bed_it_ducked(
            self, tmp_path, bed, quiet_line, picture):
        out = tmp_path / "master.mp4"
        ta.mix_with_lines(picture, bed, [], [(LINE_AT, quiet_line)], out, seconds=SECONDS)
        ducked = out.with_name("master.bed-ducked.wav")
        levelled = out.with_name("line-0.level.wav")
        inside = loudness_between(ducked, LINE_AT + 0.3, LINE_AT + LINE_SECONDS)
        assert ta.integrated(levelled) - inside >= ta.LINE_OVER_BED

    def test_the_hard_out_reaches_the_master(self, tmp_path, bed, line, picture):
        out = tmp_path / "master.mp4"
        ta.mix_with_lines(picture, bed, [], [(LINE_AT, line)], out, seconds=SECONDS, hard_out=6.0)
        ducked = out.with_name("master.bed-ducked.wav")
        assert peak_between(ducked, 6.5, 7.9) <= -60.0

    def test_without_lines_or_a_card_it_is_the_plain_mix(self, tmp_path, bed, picture, monkeypatch):
        seen = []
        monkeypatch.setattr(ta, "mix", lambda *a, **k: seen.append((a, k)) or a[3])
        out = tmp_path / "master.mp4"
        assert ta.mix_with_lines(picture, bed, [], [], out, seconds=SECONDS) == out
        assert seen[0][0][1] == bed


class TestMasteringHeadroom:
    """F: the average is found before the limiter, not inside it."""

    def test_the_limiter_is_a_safety_net_not_the_sound(self):
        assert ta.LIMITING_DB <= 2.0

    def test_every_ceiling_is_asked_for_below_its_true_peak_target(self):
        assert ta.db_to_linear(0.0) == 1.0
        assert ta.limiter(ta.LINE_TP).startswith(
            f"alimiter=limit={ta.db_to_linear(ta.LINE_TP - ta.LIMITER_MARGIN)}")
        assert "level=disabled" in ta.limiter(ta.BED_TP)


class TestBuildWiring:
    def test_build_reads_voice_json_when_present(self, tmp_path):
        """assemble.build hands mix_with_lines the planned windows; no voice.json,
        nothing spoken, and the picture and cue are exactly what they were."""
        from scripts.trailer import assemble as script
        out = tmp_path / "book" / "trailer" / "main"
        out.mkdir(parents=True)
        plan = {"lines": [{"index": 0, "at": 2.0}]}
        (out / "voice.json").write_text(json.dumps([
            {"index": 0, "text": "Poison.", "speaker": "holmes",
             "rel_path": "trailer/main/voice/lines/0.wav", "seconds": 1.2}]), encoding="utf-8")
        assert script.spoken_lines(plan, out) == [(2.0, tmp_path / "book" / "trailer/main/voice/lines/0.wav")]
        (out / "voice.json").unlink()
        assert script.spoken_lines(plan, out) == []
