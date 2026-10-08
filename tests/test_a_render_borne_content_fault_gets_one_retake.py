"""ep21 (2026-10-08 14:10Z): the take eye found content faults on T05, T06,
T14 and T31 and the ladder retook none -- 'content' is INPUT_BORNE, so every
one went to the terminal, a still of its panel.  The panels say otherwise:
panel_content.json passed shots 6 and 14 (T06 drew a second, fair-haired
man; T14 stood a man the shot asks low), so those faults came from the
RENDER, and one seed retake is their cure.  Shots 5 and 31 carry the same
fault in their panels: input-borne, the terminal's.

And the take DQ cache served T27 and T30 their old letterbox refusals after
the letterbox measure was fixed ('cached, bytes unchanged'): a cached verdict
holds only while the measuring code is the code that wrote it."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from studio import take_ladder
from studio.judges.verdict import Fault, Verdict

ROOT = Path(__file__).resolve().parents[1]


def content(where: str, note: str, repeated: bool = False) -> Fault:
    return Fault(kind="content", where=where, note=note, evidence={"hard": True, "repeated": repeated})


def home_with_panels(tmp_path: Path) -> Path:
    home = tmp_path / "ep21"
    (home / "storyboard").mkdir(parents=True)
    (home / "takes" / "r2v").mkdir(parents=True)
    rows = [{"shot": 5, "passed": False, "faults": ["text or lettering in the picture"]},
            {"shot": 6, "passed": True, "faults": []},
            {"shot": 14, "passed": True, "faults": []},
            {"shot": 31, "passed": False, "faults": ["posture 'sitting': the shot asks for lying"]}]
    (home / "storyboard" / "panel_content.json").write_text(json.dumps(rows), encoding="utf-8")
    return home


def test_a_content_fault_on_a_clean_panel_routes_to_a_seed(tmp_path):
    home = home_with_panels(tmp_path)
    verdict = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, faults=[
        content("T05", "text or lettering in the picture"),
        content("T06", "blonde hair where the row says otherwise"),
        content("T14", "posture 'standing': the shot asks for low"),
        content("T31", "posture 'sitting': the shot asks for lying")])
    routed = take_ladder.route(verdict, home / "takes" / "r2v")
    assert sorted(routed.get("seed", {})) == [6, 14]


def test_a_content_fault_the_panel_carries_stays_with_the_terminal():
    assert take_ladder.cure_of([content("T05", "text")], panel_clean=False) == ""
    assert take_ladder.cure_of([content("T05", "text")]) == ""          # unknown panel: as before


def test_a_render_borne_fault_a_fresh_seed_reproduced_goes_to_the_terminal():
    assert take_ladder.cure_of([content("T06", "hair", repeated=True)], panel_clean=True) == ""


def test_a_cached_take_verdict_lapses_when_the_measures_change(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("take_dq_mod", ROOT / "scripts" / "episode" / "take_dq.py")
    dq = importlib.util.module_from_spec(spec)
    sys.modules["take_dq_mod"] = dq
    spec.loader.exec_module(dq)
    kept = tmp_path / "T27.mp4"
    kept.write_bytes(b"take bytes")
    report = {"score": 31.9, "take_sha8": dq.take_sha8(kept), "measures_sha8": dq.measures_sha8()}
    (tmp_path / "T27.dq.json").write_text(json.dumps(report), encoding="utf-8")
    assert dq.cached(tmp_path, 27, kept) is not None
    monkeypatch.setattr(dq, "measures_sha8", lambda: "deadbeef")
    assert dq.cached(tmp_path, 27, kept) is None
    old = {"score": 31.9, "take_sha8": dq.take_sha8(kept)}                  # written before the key existed
    (tmp_path / "T27.dq.json").write_text(json.dumps(old), encoding="utf-8")
    assert dq.cached(tmp_path, 27, kept) is None
