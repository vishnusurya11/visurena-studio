"""The master eye keeps one read per (take sha8, local frame, slow, plan row, reader model,
prompt) in review/work/eye_reads.json, so a recut that changed one take re-reads only that
take's frames and a crash loses no finished read.  Fake frames and reader, $0."""
from __future__ import annotations

import json

import numpy as np

from studio.judges import master_eye as me

SAID = json.dumps({"landform": "flat", "people": 1, "lookalikes": 0, "text": False, "hour": "day",
                   "framing": "medium", "action": "walks"})


def home_with_two_takes(tmp_path):
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    for i in (1, 2):
        (room / f"T{i:02d}.mp4").write_bytes(f"take {i}".encode())
    (room / "shots.json").write_text(json.dumps(
        [{"index": 1, "shots": [1], "rel_path": "x"}, {"index": 2, "shots": [2], "rel_path": "y"}]), encoding="utf-8")
    placed = {"duration_s": 10.0, "shots": [
        {"index": 1, "t_start": 0.0, "t_end": 5.0, "seconds": 5.0},
        {"index": 2, "t_start": 5.0, "t_end": 10.0, "seconds": 5.0}]}
    plan = {"shots": [{"index": 1, "setup": "a"}, {"index": 2, "setup": "a"}]}
    return placed, plan


class Counter:
    def __init__(self):
        self.reads, self.embeds = 0, 0

    def reader(self, frame):
        self.reads += 1
        return SAID

    def embed(self, frame):
        self.embeds += 1
        return [{"h": 0.2, "vec": np.ones(4)}]


def frames(master, times):
    return [np.full((16, 16, 3), int(t * 10) % 250, np.uint8) for t in times]


def measure(tmp_path, placed, plan, counter, cache):
    return me.measures(tmp_path, tmp_path / "m.mp4", plan, placed, frames=frames, reader=counter.reader,
                       embed=counter.embed, count=10, cache=cache)


def make_cache(tmp_path, reader_id="qwen3vl", prompt="p1"):
    return me.EyeCache(tmp_path, reader_id, prompt)


def test_an_unchanged_master_reads_nothing_the_second_time(tmp_path):
    placed, plan = home_with_two_takes(tmp_path)
    first, second = Counter(), Counter()
    measure(tmp_path, placed, plan, first, make_cache(tmp_path))
    out = measure(tmp_path, placed, plan, second, make_cache(tmp_path))
    assert first.reads == 10 and second.reads == 0 and second.embeds == 0
    assert len(out["reads"]) == 10 and out["reads"][0].seen is not None
    assert out["reads"][0].faces[0]["h"] == 0.2


def test_the_eye_reads_only_the_frames_of_a_changed_take(tmp_path):
    placed, plan = home_with_two_takes(tmp_path)
    measure(tmp_path, placed, plan, Counter(), make_cache(tmp_path))
    (tmp_path / "takes" / "r2v" / "T02.mp4").write_bytes(b"take 2, retaken")
    again = Counter()
    measure(tmp_path, placed, plan, again, make_cache(tmp_path))
    assert again.reads == 5          # shot 2's five sampled frames, not shot 1's


def test_a_changed_reader_or_prompt_reads_everything_again(tmp_path):
    placed, plan = home_with_two_takes(tmp_path)
    measure(tmp_path, placed, plan, Counter(), make_cache(tmp_path))
    for cache in (make_cache(tmp_path, reader_id="other"), make_cache(tmp_path, prompt="p2")):
        c = Counter()
        measure(tmp_path, placed, plan, c, cache)
        assert c.reads == 10


def test_a_changed_plan_row_reads_that_shot_again(tmp_path):
    placed, plan = home_with_two_takes(tmp_path)
    measure(tmp_path, placed, plan, Counter(), make_cache(tmp_path))
    plan["shots"][0]["frame"] = "a new framing"
    c = Counter()
    measure(tmp_path, placed, plan, c, make_cache(tmp_path))
    assert c.reads == 5


def test_the_eye_resumes_after_an_engine_crash(tmp_path):
    placed, plan = home_with_two_takes(tmp_path)

    class Crashes(Counter):
        def reader(self, frame):
            if self.reads == 6:
                raise ConnectionError("the engine went away")
            return super().reader(frame)
    crashed = Crashes()
    try:
        measure(tmp_path, placed, plan, crashed, make_cache(tmp_path))
    except ConnectionError:
        pass
    resumed = Counter()
    measure(tmp_path, placed, plan, resumed, make_cache(tmp_path))
    assert crashed.reads == 6 and resumed.reads == 4


def test_an_unreadable_answer_is_never_kept(tmp_path):
    placed, plan = home_with_two_takes(tmp_path)

    class Garbage(Counter):
        def reader(self, frame):
            self.reads += 1
            return "not json at all"
    measure(tmp_path, placed, plan, Garbage(), make_cache(tmp_path))
    again = Counter()
    measure(tmp_path, placed, plan, again, make_cache(tmp_path))
    assert again.reads == 10


def test_a_dead_cut_changes_where_a_frame_sits_and_so_its_key(tmp_path):
    placed, plan = home_with_two_takes(tmp_path)
    plain = make_cache(tmp_path).key(placed, plan, 7.5)
    (tmp_path / "takes" / "work").mkdir(parents=True)
    (tmp_path / "takes" / "work" / "dead_cuts.json").write_text(
        json.dumps({"cut": [], "seconds": {2: 6.0}}), encoding="utf-8")
    assert make_cache(tmp_path).key(placed, plan, 7.5) != plain


def test_a_time_in_the_tail_has_no_key_and_is_always_read(tmp_path):
    placed, plan = home_with_two_takes(tmp_path)
    assert make_cache(tmp_path).key(placed, plan, 12.0) is None
