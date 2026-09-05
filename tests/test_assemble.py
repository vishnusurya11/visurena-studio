"""The cut reads THIS run's clips or it refuses.

Run 10 globbed `clips/*.mp4`, filtered by beat id, and never asked whether a
file was the take this run rendered -- so 24% of the delivered picture came
from clips left behind by earlier plans, and those same stale files were read
into the grade calibration.  `takes_for` is where that becomes impossible.
ffmpeg is never run here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.trailer import assemble as script
from studio.clip_cache import fingerprint, record
from studio.trailer_assemble import clip_seconds
from studio.trailer_cut import title_moment

RECIPE = {"prompt": "a man in fog", "seed": 51000}
BEATS = ["B00", "B01", "B02"]


def clip(book: Path, beat_id: str, recipe: dict = RECIPE) -> dict:
    """A promoted clip and the record step 07 wrote for it."""
    video = book / "trailer/main/clips" / f"{beat_id}.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"mp4")
    record(video, recipe)
    return {"beat_id": beat_id, "rel_path": video.relative_to(book).as_posix(),
            "capped": None, "fingerprint": fingerprint(RECIPE)}


def plan(beats: list[str] = BEATS) -> dict:
    return {"shots": [{"beat_id": b, "index": i, "start": 2.0 * i, "seconds": 2.0}
                      for i, b in enumerate(beats)],
            "beats": [{"beat_id": b} for b in beats]}


class TestTakesFor:
    def test_every_shot_reads_its_own_fresh_clip(self, tmp_path):
        clips = {"clips": [clip(tmp_path, b) for b in BEATS]}
        found = script.takes_for(plan(), clips, tmp_path)
        assert [p.stem for p in found.values()] == BEATS

    def test_a_beat_with_no_clip_refuses_the_cut(self, tmp_path):
        clips = {"clips": [clip(tmp_path, b) for b in BEATS[:2]]}
        with pytest.raises(SystemExit, match=r"no fresh clip for beats \['B02'\]"):
            script.takes_for(plan(), clips, tmp_path)

    def test_a_clip_left_over_from_an_earlier_plan_refuses_the_cut(self, tmp_path):
        """The file is there under the right name; its recipe is last plan's."""
        clips = {"clips": [clip(tmp_path, b) for b in BEATS]}
        record(tmp_path / "trailer/main/clips/B01.mp4", {**RECIPE, "prompt": "an old shot"})
        with pytest.raises(SystemExit, match=r"no fresh clip for beats \['B01'\]"):
            script.takes_for(plan(), clips, tmp_path)


class TestClipsDoc:
    def test_a_cut_without_step_07s_record_is_refused(self, tmp_path):
        with pytest.raises(SystemExit, match="no clips.json"):
            script.clips_doc(tmp_path)

    def test_the_record_is_read_from_the_trailer_directory(self, tmp_path):
        doc = {"clips": [], "dropped": []}
        (tmp_path / "clips.json").write_text(json.dumps(doc), encoding="utf-8")
        assert script.clips_doc(tmp_path) == doc


class TestTheDesignedLayer:
    """Run 10's whole designed layer was two cues, both AFTER the music had
    already died: a sub-drop and an impact.  `sfx.riser` was in the tree and
    never called, there was no atmos anywhere, and the pre-title gap was
    digital silence."""

    def layer(self, tmp_path, hard_out=20.0, hit=22.0, seconds=26.5):
        return script.designed_layer(tmp_path, hard_out, hit, seconds)

    def test_the_riser_ends_on_the_hard_out(self, tmp_path):
        (at, path), *_ = self.layer(tmp_path)
        assert at + script.RISER_SECONDS == pytest.approx(20.0)
        assert path.name == "riser.wav" and script.RISER_SECONDS >= 2.0

    def test_the_sub_drop_lands_on_the_stop_not_inside_the_silence(self, tmp_path):
        _, (at, path), _, _ = self.layer(tmp_path)
        assert at + script.SUB_SECONDS == pytest.approx(20.0) and path.name == "sub.wav"

    def test_room_tone_covers_every_second_after_the_bed_stops(self, tmp_path):
        _, _, (at, path), _ = self.layer(tmp_path)
        assert at == pytest.approx(20.0) and path.name == "room.wav"
        assert clip_seconds(path) == pytest.approx(6.5, abs=0.05)

    def test_the_impact_lands_on_the_card_with_a_tail_to_spare(self, tmp_path):
        *_, (at, path) = self.layer(tmp_path)
        assert at == pytest.approx(22.0) and path.name == "hit.wav"
        assert script.IMPACT_SECONDS >= 3.0

    def test_nothing_is_asked_for_before_the_file_starts(self, tmp_path):
        """A picture shorter than the riser would otherwise ask adelay for a
        negative offset, which ffmpeg reads as zero and nobody notices."""
        assert all(at >= 0.0 for at, _ in self.layer(tmp_path, hard_out=1.0, hit=3.0, seconds=7.5))


class TestTheShapeOfTheTail:
    def test_the_bed_stops_where_the_picture_does(self):
        hard_out, hit, card = title_moment(96.4)
        assert hard_out == 96.4 and hit > hard_out and card > hit - hard_out

    def test_the_card_outlasts_the_hit_it_carries(self):
        _, hit, card = title_moment(96.4)
        assert 96.4 + card - hit >= script.IMPACT_SECONDS
