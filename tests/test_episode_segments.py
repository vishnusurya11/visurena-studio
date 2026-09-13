import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_assemble", ROOT / "scripts" / "episode" / "assemble.py")
assemble = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assemble)

PLACED = {"shots": [{"index": 0, "seconds": 3.0}, {"index": 1, "seconds": 5.0}, {"index": 2, "seconds": 4.0}]}


def test_per_shot_takes_cut_one_segment_per_shot():
    takes = {i: assemble.TakePath(f"T{i}.mp4") for i in range(3)}
    assert assemble.segments_of(PLACED, takes) == [(0, 3.0), (1, 5.0), (2, 4.0)]


def test_run_takes_cut_one_segment_per_run_summing_its_shots():
    takes = {0: assemble.TakePath("T0.mp4", [0, 1]), 2: assemble.TakePath("T2.mp4", [2])}
    assert assemble.segments_of(PLACED, takes) == [(0, 8.0), (2, 4.0)]
