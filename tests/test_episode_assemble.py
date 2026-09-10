"""The last gain spends the peak headroom toward -14 and never past the ceiling."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_assemble", ROOT / "scripts" / "episode" / "assemble.py")
assemble = importlib.util.module_from_spec(spec)
sys.modules["ep_assemble"] = assemble
spec.loader.exec_module(assemble)


def test_a_quiet_master_is_lifted_within_the_peak_headroom():
    assert assemble.final_gain(-15.8, -1.7) == 0.6
    assert assemble.final_gain(-17.0, -1.7) == 0.6


def test_a_master_in_band_is_left_alone():
    assert assemble.final_gain(-14.9, -1.7) == 0.0
    assert assemble.final_gain(-15.8, -1.0) == 0.0
