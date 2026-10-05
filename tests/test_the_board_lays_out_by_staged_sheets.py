"""Step 07 hands the layout rule what each shot must stage: its faces and the
setup props its own prose names (the rule grids.py stages props by), so a
machine shot never shares a grid whose slots people have filled.  $0: the prop
lookup is replaced; nothing is drawn."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))

import step_07_board  # noqa: E402
from studio import pack_refs  # noqa: E402


def test_needs_are_faces_plus_the_props_the_prose_names(monkeypatch):
    monkeypatch.setattr(pack_refs, "props_named",
                        lambda book, pids, text: [("sheet", (p, "")) for p in pids if p.split("_")[0] in text])
    doc = {"setups": {"deck": {"props": ["fighting_machine", "ram"]}},
           "shots": [{"index": 13, "setup": "deck", "faces": ["captain"], "frame": "the captain at the rail"},
                     {"index": 14, "setup": "deck", "faces": [], "frame": "a fighting-machine wades"}]}
    needs = step_07_board.needs_of(Path("book"), doc)
    assert needs == {13: {"captain"}, 14: {"fighting_machine"}}
