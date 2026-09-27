"""The join guard refuses a lost part, not one padded frame.

ep13 (2026-09-27): mixed 3911f + title 107f + black 6f = 4024, the joined
master 4025 -- cfr output padding one frame at a join -- and the guard, written
for a master four frames SHORT (a part the concat demuxer dropped), refused it.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("assemble_join", ROOT / "scripts/episode/assemble.py")
assemble = importlib.util.module_from_spec(_spec)
sys.modules["assemble_join"] = assemble
_spec.loader.exec_module(assemble)


def test_a_part_dropped_is_refused():
    assert assemble.join_lost(got=4020, want=4024)


def test_one_padded_frame_is_not_a_lost_part():
    assert not assemble.join_lost(got=4025, want=4024)


def test_more_than_one_extra_frame_is_refused():
    assert assemble.join_lost(got=4030, want=4024)
