"""The line layer: a spoken line at its planned window, the bed ducked under it.

Real local ffmpeg on synthetic audio: a band-limited noise bed and a tone
line.  Loudness is READ from ebur128, never assumed from the graph, because
the first duck graph measured a 0.4 dB duck -- the key was quieter than the
compressor's threshold and nothing in the graph text said so.
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


class TestDuck:
    def test_line_sits_six_lu_over_bed_in_its_window(self, tmp_path, bed, line):
        ducked = ta.duck_bed(bed, [(LINE_AT, line)], tmp_path / "ducked.wav")

        before = loudness_between(bed, 0.8, 2.8)
        inside = loudness_between(ducked, LINE_AT + 0.6, LINE_AT + LINE_SECONDS)
        outside = loudness_between(ducked, 0.8, 2.8)
        spoken = loudness_between(line, 0.6, LINE_SECONDS)
        # Outside the window the bed is the bed; inside, the line clears it by
        # the QC target with room, and the duck itself is at least that deep.
        assert outside == pytest.approx(before, abs=1.0)
        assert spoken - inside >= 5.0
        assert before - inside >= 5.0

    def test_card_window_is_not_ducked(self, tmp_path, bed, line):
        """A card gives the compressor no key, so its window sounds like the bed."""
        card = VoiceLine(index=0, text="A study in scarlet.", speaker=None, card=True)
        spoken = VoiceLine(index=1, text="Poison.", speaker="holmes",
                           rel_path="trailer/main/voice/lines/1.wav")
        book = tmp_path / "book"
        (book / "trailer/main/voice/lines").mkdir(parents=True)
        (book / "trailer/main/voice/lines/1.wav").write_bytes(line.read_bytes())
        plan = {"lines": [{"index": 0, "at": 0.5}, {"index": 1, "at": LINE_AT}]}

        keys = ta.line_windows(plan, [card, spoken], book)
        ducked = ta.duck_bed(bed, keys, tmp_path / "ducked.wav")

        assert keys == [(LINE_AT, book / "trailer/main/voice/lines/1.wav")]
        card_window = loudness_between(ducked, 0.9, 2.5)
        assert card_window == pytest.approx(loudness_between(bed, 0.9, 2.5), abs=1.0)

    def test_the_bed_keeps_its_length_and_is_untouched_without_keys(self, tmp_path, bed):
        assert ta.duck_bed(bed, [], tmp_path / "ducked.wav") == bed
        assert not (tmp_path / "ducked.wav").exists()

    def test_two_lines_chain_two_compressors(self):
        graph = ta.duck_graph([1.0, 4.5])
        assert graph.count("sidechaincompress") == 2
        assert "[mid0][key0]" in graph and "[mid1][key1]" in graph
        assert graph.endswith("[lo][mid2][hi]amix=inputs=3:normalize=0:duration=first[out]")

    def test_a_key_is_delayed_padded_and_conformed(self):
        chain = ta._key_chain(0, 2.345)
        assert chain.startswith("[1:a]")
        assert "adelay=2345:all=1" in chain and chain.endswith(",apad[key0]")
        assert "aresample=48000" in chain and "channel_layouts=stereo" in chain


class TestMeasure:
    def test_momentary_reads_every_hundred_ms(self, bed):
        readings = ta.momentary(bed)
        assert len(readings) >= 70
        assert all(-60.0 < m < 0.0 for _, m in readings[5:])

    def test_window_loudness_averages_inside_only(self):
        readings = [(0.1, -30.0), (0.2, -30.0), (0.3, -10.0), (0.4, -10.0), (0.5, -50.0)]
        assert ta.window_loudness(readings, 0.3, 0.5) == pytest.approx(-10.0)

    def test_window_loudness_refuses_an_empty_window(self):
        with pytest.raises(ValueError):
            ta.window_loudness([(0.1, -30.0)], 5.0, 6.0)


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


@pytest.fixture()
def quiet_line(tmp_path):
    """A line rendered 30 dB under the bed: what a TTS take at its own level
    can be, and what the duck's key cannot hear."""
    return lavfi(tmp_path / "quiet.wav", "sine=frequency=440:sample_rate=24000",
                 "volume=-18dB", LINE_SECONDS, 1)


class TestLevel:
    """A line is LEVELLED to its window before anything else: the bed's
    loudness there plus LINE_OVER_BED, whatever the take came out at.  Run
    9's master was heard as 'music too loud': the bed was normalised to
    -14 LUFS and nothing set a line against it."""

    def test_the_gain_lands_a_line_over_the_bed(self):
        assert ta.line_gain(bed_lu=-30.0, line_lu=-20.0) == pytest.approx(-10.0 + ta.LINE_OVER_BED)
        assert ta.line_gain(bed_lu=-30.0, line_lu=-60.0) == 20.0
        assert ta.line_gain(bed_lu=-60.0, line_lu=-10.0) == -20.0

    def test_a_quiet_take_is_lifted_over_its_window(self, tmp_path, bed, quiet_line):
        (at, levelled), = ta.level_lines(bed, [(LINE_AT, quiet_line)], tmp_path / "out")
        assert at == LINE_AT and levelled.name == "line-0.level.wav"
        window = loudness_between(bed, LINE_AT, LINE_AT + LINE_SECONDS)
        assert ta.integrated(levelled) - window == pytest.approx(ta.LINE_OVER_BED, abs=1.5)

    def test_a_hot_take_is_brought_down_to_the_same_place(self, tmp_path, bed, line):
        (_, levelled), = ta.level_lines(bed, [(LINE_AT, line)], tmp_path / "out")
        window = loudness_between(bed, LINE_AT, LINE_AT + LINE_SECONDS)
        assert ta.integrated(levelled) - window == pytest.approx(ta.LINE_OVER_BED, abs=1.5)
        assert ta.integrated(levelled) < ta.integrated(line)

    def test_a_silent_bed_window_does_not_pull_the_line_to_nothing(self):
        """Momentary readings in a stop-down are -inf; they are not a level
        to sit eight LU over."""
        readings = [(3.0, float("-inf")), (3.1, -20.0), (3.2, -20.0), (3.3, float("-inf"))]
        assert ta.bed_level(readings, 3.0, 3.4) == pytest.approx(-20.0)


class TestMixWithLines:
    def test_a_master_carries_the_line_and_ducks_the_bed(self, tmp_path, bed, line, picture):
        out = tmp_path / "master.mp4"
        ta.mix_with_lines(picture, bed, [], [(LINE_AT, line)], out, seconds=SECONDS)
        assert out.exists()
        assert ta.clip_seconds(out) == pytest.approx(SECONDS, abs=0.1)
        ducked = out.with_name("master.bed-ducked.wav")
        assert ducked.exists()
        assert loudness_between(bed, 0.8, 2.8) - loudness_between(ducked, 3.6, 5.0) >= 5.0

    def test_the_mix_records_where_it_laid_each_levelled_line(self, tmp_path, bed, line, picture):
        """QC measures line-over-bed from the files beside the master, and
        the mix is the one that knows where each levelled line was laid."""
        out = tmp_path / "master.mp4"
        ta.mix_with_lines(picture, bed, [], [(LINE_AT, line)], out, seconds=SECONDS)
        sheet = json.loads((tmp_path / "lines.level.json").read_text(encoding="utf-8"))
        assert sheet == [{"at": LINE_AT, "rel_path": "line-0.level.wav"}]

    def test_a_quiet_take_still_rides_over_the_ducked_bed(self, tmp_path, bed, quiet_line, picture):
        """The quiet take, unlevelled, was 30 dB under the bed and no key to
        the compressor: levelled first, it ducks the bed and clears it."""
        out = tmp_path / "master.mp4"
        ta.mix_with_lines(picture, bed, [], [(LINE_AT, quiet_line)], out, seconds=SECONDS)
        ducked = out.with_name("master.bed-ducked.wav")
        levelled = out.with_name("line-0.level.wav")
        assert levelled.exists()
        inside = loudness_between(ducked, LINE_AT + 0.6, LINE_AT + LINE_SECONDS)
        assert ta.integrated(levelled) - inside >= ta.LINE_OVER_BED

    def test_without_lines_it_is_the_plain_mix(self, tmp_path, bed, picture, monkeypatch):
        seen = []
        monkeypatch.setattr(ta, "mix", lambda *a, **k: seen.append((a, k)) or a[3])
        out = tmp_path / "master.mp4"
        assert ta.mix_with_lines(picture, bed, [], [], out, seconds=SECONDS) == out
        assert seen[0][0][1] == bed


class TestBuildWiring:
    def test_build_reads_voice_json_when_present(self, tmp_path, monkeypatch):
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
