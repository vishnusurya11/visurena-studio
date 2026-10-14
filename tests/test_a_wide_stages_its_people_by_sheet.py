"""A wide stages its people by their one-figure sheet, like every other size.

OWNER 2026-10-14 (Jekyll ep01 HEL): "the first shot doesn't have the actual
characters in the scene, so in the second shot the character magically appears."
Shot 0 was a wide naming the lawyer and Mr. Enfield in `faces`; `wide_only` drew
both from wardrobe words, and the panel holds two strangers (a blond man, a man
in a brown greatcoat) where the sheets have a grey-haired lawyer and a grey frock
coat.  Shot 1's grid staged Enfield's sheet, so he "appears".  The same rule drew
shot 7's Hyde bearded from his row's words; the setup's later grids chained on
that panel as their room, and shot 9 drew both Hydes.

`wide_only` (2026-10-02 09:39) answered ep16 shot 19, where the WHOLE four-pose
turnaround was drawn as four women.  Three hours later (7ad14e6) grids began
staging the sheet's one-figure crop, which removed that cause at every size; the
wide exemption was never taken back.  So the ceiling now picks by visibility
(`scene_cast.pick`) and size no longer exempts anyone."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("grids", ROOT / "scripts" / "episode" / "grids.py")
grids = importlib.util.module_from_spec(spec)
sys.modules["grids"] = grids
spec.loader.exec_module(grids)

CAST = ("utterson", "enfield", "hyde")


def book_with_sheets(tmp_path: Path) -> Path:
    rows = [{"entity_id": w, "kind": "character", "name": f"Mr. {w.title()}", "display": f"Mr. {w.title()}",
             "physical": f"{w} coat", "gender": "male"} for w in CAST]
    (tmp_path / "refs").mkdir()
    (tmp_path / "refs" / "refs.json").write_text(json.dumps({"refs": rows}), encoding="utf-8")
    for w in CAST:
        folder = tmp_path / "refs" / "characters" / w
        folder.mkdir(parents=True)
        Image.new("RGB", (8, 8)).save(folder / "sheet.png")
        Image.new("RGB", (4, 8)).save(folder / "sheet_front.png")
    return tmp_path


def shot(i, size, faces, frame=""):
    return SimpleNamespace(index=i, size=size, faces=list(faces), cuts=[], frame=frame, at_rest="", end="")


def test_a_wide_stages_both_men_by_sheet(tmp_path):
    book = book_with_sheets(tmp_path)
    people, slots = grids.cast_of(book, [shot(0, "wide", ["utterson", "enfield"])], reserve=1)
    assert [p["ref"] for p in people] == [1, 2]
    assert sorted(Path(p).parent.name for p in slots.values()) == ["enfield", "utterson"]


def test_over_the_ceiling_the_speck_in_the_wide_goes_to_words(tmp_path):
    """Two slots (the place and the room keep one): Hyde is a speck in the wide
    and a big face in the close; the lawyer is only in the wide."""
    book = book_with_sheets(tmp_path)
    shots = [shot(7, "wide", ["utterson", "hyde"]), shot(8, "close", ["hyde"])]
    people, slots = grids.cast_of(book, shots, reserve=2)
    by = {p["entity"]: p["ref"] for p in people}
    assert by == {"utterson": None, "hyde": 1}


def test_a_person_the_picture_names_is_staged_with_the_faces(tmp_path):
    """An over-the-shoulder holds the shoulder's owner: his sheet goes in too."""
    book = book_with_sheets(tmp_path)
    s = shot(2, "medium_close", ["utterson"], frame="Medium close over Mr. Enfield's near shoulder")
    people, _ = grids.cast_of(book, [s], reserve=1)
    assert [p["entity"] for p in people] == ["utterson", "enfield"]
