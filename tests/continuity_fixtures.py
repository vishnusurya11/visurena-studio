"""A tiny book with a look table: the narrator's base suit and a ragged look,
the ragged picture drawn, a borrowed suit not drawn.  Helpers, not tests."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from studio import look_timeline
from studio.continuity_spec import CharacterLooks

PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000040000000808020000005151c952000000144944"
                    "4154789c63aca8a8608001260624405d0e0093180178057263a60000000049454e44ae426082")
CARD = {"base": "day_suit", "body": "Man of 34, slender, grey eyes.",
        "looks": {"day_suit": {"made_by": "base", "layers": {"hair": "Dark brown hair", "top": "grey suit"},
                               "markers": {"hair_colour": "dark", "headwear": "boater"}},
                  "ragged": {"made_by": "fresh", "face_change": True,
                             "layers": {"hair": "Ash-grey hair", "face": "grey-brown beard", "top": "torn shirt"},
                             "markers": {"hair_colour": "grey", "facial_hair": "beard"}},
                  "borrowed": {"made_by": "edit", "layers": {"hair": "Ash-grey hair", "top": "borrowed suit"},
                               "markers": {"hair_colour": "grey"}}},
        "timeline": [{"look": "day_suit", "start": {"chapter": 1}},
                     {"look": "ragged", "start": {"chapter": 22}},
                     {"look": "borrowed", "start": {"chapter": 26, "scene": 2}}]}


def book(tmp_path: Path, row_look: str = "ragged", table: bool = True) -> Path:
    """refs.json bound for chapter 24 with the narrator in `row_look`."""
    root = tmp_path / "book"
    chars = root / "refs" / "characters" / "narrator"
    (chars / "looks").mkdir(parents=True)
    for path in (chars / "sheet.png", chars / "sheet_front.png", chars / "looks" / "ragged.png"):
        path.write_bytes(PNG)
    (root / "refs" / "refs.json").write_text(json.dumps({"chapter": 24, "refs": [
        {"entity_id": "narrator", "kind": "character", "look": row_look, "physical": "Grey beard. Man of 34.",
         "markers": {"hair_colour": "grey", "facial_hair": "beard"}}]}), encoding="utf-8")
    if table:
        look_timeline.write_looks(root, "narrator", CharacterLooks.model_validate(CARD))
    return root


def episode(picks: dict[str, str] | None = None, number: int = 24) -> SimpleNamespace:
    """One setup 's' with the narrator in its only shot; `picks` -> Setup.looks."""
    setup = SimpleNamespace(looks=[SimpleNamespace(who=w, look=l) for w, l in (picks or {}).items()])
    return SimpleNamespace(number=number, setups={"s": setup},
                           shots=[SimpleNamespace(index=0, setup="s", faces=["narrator"])])
