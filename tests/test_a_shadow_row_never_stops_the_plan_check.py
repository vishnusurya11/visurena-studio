"""Wave 1 review finding 1: a shadow row reports, it never refuses (craft ruling 2026-10-21).

`plan_check.craft_shadow_gate` sits before G-ASPECT, G-CROWD and the other HARD gates in `main`.  A
shadow detector that raised (a malformed `series_map.json` raises a pydantic ValidationError in
`series_map.load`) stopped step 02 on a row that only prints, and the HARD gates after it never ran.
Wave 0 already caught this class in `qc.words_rows` and `takes_r2v.craft_census`.  The gate now says
"not measured" and counts 0.  Fixtures: tests/fixtures/craft (Jekyll ep01 plan.json, ch_01, ch_02).
No render, no network, no spend."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from studio import episode_spec

CRAFT = Path(__file__).parent / "fixtures" / "craft"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import plan_check  # noqa: E402


def episode() -> episode_spec.Episode:
    return episode_spec.Episode(**json.loads((CRAFT / "episodes" / "ep01" / "plan.json").read_text(encoding="utf-8")))


def book_with_a_broken_map(tmp_path: Path) -> Path:
    shutil.copytree(CRAFT / "source", tmp_path / "source")
    (tmp_path / "series_map.json").write_text('{"reveals": [{"entity": "hyde"}]}', encoding="utf-8")
    return tmp_path


def test_a_malformed_series_map_is_not_measured_and_counts_nothing(tmp_path, capsys):
    assert plan_check.craft_shadow_gate(episode(), book_with_a_broken_map(tmp_path), 1) == 0
    said = capsys.readouterr().out
    assert said.startswith("CRAFT SHADOW : not measured (") and "ValidationError" in said


def test_any_detector_fault_is_not_measured(monkeypatch, capsys):
    def broken(*_):
        raise KeyError("lines")
    monkeypatch.setattr(plan_check, "shadow_rows", broken)
    assert plan_check.craft_shadow_gate(episode(), CRAFT, 1) == 0
    assert "CRAFT SHADOW : not measured (KeyError: 'lines')" in capsys.readouterr().out


def test_a_readable_plan_still_prints_its_rows(capsys):
    assert plan_check.craft_shadow_gate(episode(), CRAFT, 1) == 0
    said = capsys.readouterr().out
    assert said.startswith("CRAFT SHADOW : ") and "advisory: G-MUTE shot 13" in said
