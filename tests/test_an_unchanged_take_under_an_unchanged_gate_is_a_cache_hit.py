"""take_dq serves a verdict on the take's bytes + the gate version, never on the code's hash alone.

Jekyll ep01 repair, run 15 (drive_run03.log, 2026-10-19 12:11): take_dq re-measured all 28
unchanged takes in 1,070 s because measures_sha8 moved c85850eb -> 42a70889 over four commits,
two of which changed no measure (79b8049 adds a gait cure verb; 3d4129e loads the judges
lazily, "no threshold moved").  docs/audit/2026-10-20_deadline_retro/h_diagnosis.md.
The fixture is a copy of ep01's takes/r2v/T00.dq.json (measures_sha8 42a70889, no gate_version).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import take_dq  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "ep01_gate_version" / "T00.dq.json"


def room(tmp_path: Path, **over) -> Path:
    """ep01's T00 record beside a take whose bytes it names, with `over` written into it."""
    take = tmp_path / "T00.mp4"
    take.write_bytes(b"ep01 T00 bytes")
    report = json.loads(FIXTURE.read_text(encoding="utf-8"))
    report |= {"take_sha8": take_dq.take_sha8(take), **over}
    (tmp_path / "T00.dq.json").write_text(json.dumps(report), encoding="utf-8", newline="\n")
    return take


def test_a_refactor_that_moves_the_code_hash_is_still_a_hit(tmp_path):
    take = room(tmp_path, gate_version=take_dq.GATE_VERSION, measures_sha8="c85850eb")
    hit = take_dq.cached(tmp_path, 0, take)
    assert hit is not None and hit["score"] == 49.8


def test_a_bumped_gate_version_is_a_miss(tmp_path):
    take = room(tmp_path, gate_version="0", measures_sha8=take_dq.measures_sha8())
    assert take_dq.cached(tmp_path, 0, take) is None


def test_changed_bytes_are_a_miss(tmp_path):
    take = room(tmp_path, gate_version=take_dq.GATE_VERSION)
    take.write_bytes(b"a retaken T00")
    assert take_dq.cached(tmp_path, 0, take) is None


def test_ep01s_record_from_before_the_gate_version_is_a_hit(tmp_path):
    """Skeptic on 92eacc1: ep01 was measured at 42a70889, the code v1 was pinned from (92eacc1
    changed only the cache), so its 28 takes are not re-measured (about 18 min) on the resume."""
    take = room(tmp_path)
    assert "gate_version" not in json.loads(FIXTURE.read_text(encoding="utf-8"))
    hit = take_dq.cached(tmp_path, 0, take)
    assert hit is not None and hit["measures_sha8"] == "42a70889"


def test_a_record_from_older_measuring_code_is_measured_once(tmp_path):
    take = room(tmp_path, measures_sha8="c85850eb")       # the first delivery's code: warp changed since
    assert take_dq.cached(tmp_path, 0, take) is None


def test_a_record_naming_its_gate_version_is_never_read_by_its_hash(tmp_path):
    take = room(tmp_path, gate_version="0")               # 42a70889 kept, the version says otherwise
    assert take_dq.cached(tmp_path, 0, take) is None


def test_a_deferred_record_still_owes_its_gpu_rows(tmp_path):
    take = room(tmp_path, gate_version=take_dq.GATE_VERSION, deferred=["leak"])
    assert take_dq.cached(tmp_path, 0, take) is None


def test_a_spent_clock_serves_any_gate_version(tmp_path):
    take = room(tmp_path, gate_version="0")
    assert take_dq.cached(tmp_path, 0, take, any_code=True) is not None


def test_every_written_report_names_its_bytes_code_and_gate(tmp_path):
    take = tmp_path / "T03.mp4"
    take.write_bytes(b"three")
    report = take_dq.cache_key({"score": 1}, take)
    assert report == {"score": 1, "take_sha8": take_dq.take_sha8(take),
                      "measures_sha8": take_dq.measures_sha8(), "gate_version": take_dq.GATE_VERSION}
