"""G-TAKELINT also runs studio.prompt_lint's card rules (P1-P18) on the dry-built cards.

Jekyll ep03: the built cards for T03/T16 read "with <Subject 1> leans now in frame"; P9 refused
them at step 06, after the voices were recorded.  The same check now runs at step 02."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, "scripts/episode")

from studio.episode_spec import Line, Setup, Shot  # noqa: E402

GARBLE = "detailed_description:" + chr(10) + "At the first frame, the lane lies grey, with <Subject 1> leans now in frame."
NARR = "Then we walked on together down the lane and the morning opened wide."


def fixture(tmp_path):
    book = tmp_path / "book"
    (book / "refs").mkdir(parents=True)
    rows = [{"ref_id": "char-watson", "kind": "character", "entity_id": "watson", "name": "John Watson",
             "display": "Dr. Watson", "gender": "male", "physical": "A lean man of thirty, dark hair."}]
    (book / "refs" / "refs.json").write_text(json.dumps({"refs": rows}), encoding="utf-8")
    shot = Shot(index=3, section="friction", setup="lane", size="wide", faces=[],
                frame="A hillside lane under a grey sky.",
                motion="The camera pushes in toward the gate across the whole shot",
                at_rest="The gate sits at the LEFT of the frame.")
    setup = Setup(described="A hillside lane in grey daylight from the LEFT.", cast=["watson"])
    ep = SimpleNamespace(shots=[shot], lines=[Line(index=0, kind="narration", speaker="watson", text=NARR, shot=3)],
                         setups={"lane": setup}, aspect="1:1", where="", light="", look="")
    ep.shot = lambda i: shot
    return book, ep, [{"index": 3, "seconds": 6.0, "setup": "lane", "cuts": []}]


def test_a_garbled_dry_card_is_a_takelint_row(tmp_path, monkeypatch):
    import plan_check, takes_r2v
    book, ep, rows = fixture(tmp_path)
    monkeypatch.setattr(takes_r2v, "dry_prompt", lambda *a, **k: GARBLE)
    got = plan_check.card_lint_rows(book, ep, 3, rows, 3.0)
    assert got and got[0].startswith("G-TAKELINT card T03: P9"), got


def test_a_clean_dry_card_adds_no_row(tmp_path, monkeypatch):
    import plan_check, takes_r2v
    book, ep, rows = fixture(tmp_path)
    monkeypatch.setattr(takes_r2v, "dry_prompt", lambda *a, **k: "detailed_description:" + chr(10) + "At the first frame, the lane lies grey.")
    assert plan_check.card_lint_rows(book, ep, 3, rows, 3.0) == []


def test_the_gate_counts_the_card_rows_hard(tmp_path, monkeypatch, capsys):
    import plan_check, takes_r2v
    book, ep, rows = fixture(tmp_path)
    monkeypatch.setattr(takes_r2v, "dry_prompt", lambda *a, **k: GARBLE)
    monkeypatch.setattr(takes_r2v, "dry_faults", lambda *a, **k: [])
    monkeypatch.setattr(plan_check, "projected", lambda *a, **k: rows)
    assert plan_check.take_lint_gate(book, ep, 3, 3.0) == 1
    assert "G-TAKELINT card T03: P9" in capsys.readouterr().out
