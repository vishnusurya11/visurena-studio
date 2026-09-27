"""The last gain spends the peak headroom toward -14 and never past the ceiling."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_assemble", ROOT / "scripts" / "episode" / "assemble.py")
assemble = importlib.util.module_from_spec(spec)
sys.modules["ep_assemble"] = assemble
spec.loader.exec_module(assemble)


def test_a_quiet_master_is_lifted_to_the_target_the_limiter_catching_the_peaks():
    """ep13 master_iter2 (2026-09-27): -15.86 LUFS with 0.7 dB of peak headroom
    -- the gun and the shouts -- and QC's floor is -15.5.  The limiter after the
    gain exists for those transients; it may take up to LIMIT_DB off them."""
    assert assemble.final_gain(-15.8, -1.7) == 1.8
    assert assemble.final_gain(-17.0, -1.7) == 3.0
    assert assemble.final_gain(-15.8, -1.0) == 1.8


def test_the_limiter_never_takes_more_than_its_share():
    assert assemble.final_gain(-20.0, -1.2) == round(assemble.TP_CEILING - 0.1 + 1.2 + assemble.LIMIT_DB, 2)


def test_a_master_in_band_is_left_alone():
    assert assemble.final_gain(-14.9, -1.7) == 0.0
