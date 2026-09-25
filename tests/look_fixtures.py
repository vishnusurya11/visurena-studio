"""What the LOOK judge's tests share: a book with a pack and real (tiny) PNGs,
the recorded trait cards under tests/fixtures/vlm, the style vectors under
tests/fixtures/measures, and the five injected readers, every one a stub.
Nothing here names a book, a character or an episode; nothing reaches ComfyUI.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from studio import db
from studio.stage_run import StageContext

FIXTURES = Path(__file__).parent / "fixtures"
CARDS = json.loads((FIXTURES / "vlm" / "trait_cards.json").read_text(encoding="utf-8"))
STYLE = np.load(FIXTURES / "measures" / "style_vectors.npy")
"""Rows 0-2 three place pictures, row 3 a sheet in the same style, row 4 the outlier."""

PROMPT = "Character reference sheet. A man wearing a grey coat. Standing, holding a brass lantern."
SEEN = ("a man in a grey coat", "a brass lantern")


def a_book(tmp_path) -> Path:
    book = tmp_path / "book"
    (book / "refs").mkdir(parents=True)
    return book


def a_ctx(tmp_path, book, **tools) -> StageContext:
    """A refs stage context (no budget, no learn: the step equips it), with the
    judge's readers and the ladder's `draw` hung on it the way step 02 hangs `look`."""
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex = db.insert_codex(conn, "Book", codex_id="20260901000001")
    ctx = StageContext(conn, codex, book, "refs", unit="main", logs_root=tmp_path / "logs",
                       busy=lambda: False, hold=tmp_path / "HOLD", launch=lambda cmd: 0)
    ctx.refs_dir = book / "refs"
    ctx.extra = []
    ctx.look_tools = {k: v for k, v in tools.items() if k != "draw"}
    if "draw" in tools:
        ctx.draw = tools["draw"]
    return ctx


SIDE = (512, 384)
"""The OCR fixtures' boxes were recorded at 512 wide; MIN_HEIGHT scales with the width."""


def draw(book: Path, rel: str, colour=(120, 90, 60)) -> Path:
    target = book / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", SIDE, colour).save(target)
    return target


def add_row(book: Path, rel: str, prompt: str = PROMPT, seed: int = 1) -> dict:
    """One pack row, its picture drawn."""
    row = {"path": rel, "workflow": "image_krea2_cinematic_2x", "prompt": prompt, "seed": seed, "seconds": 1.0}
    with (book / "refs" / "pack.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    draw(book, rel)
    return row


def character(book: Path, who: str, prompt: str = PROMPT, silhouette: str = "") -> dict:
    """The analysis row build_pack draws a sheet from, and the pack row of that sheet."""
    folder = book / "analysis" / "characters"
    folder.mkdir(parents=True, exist_ok=True)
    design = {"sheet_prompt": prompt, **({"silhouette": silhouette} if silhouette else {})}
    (folder / f"{who}.json").write_text(json.dumps({"name": who, "profile": {"design": design}}), encoding="utf-8")
    return add_row(book, f"refs/characters/{who}/sheet.png", prompt)


def place(book: Path, where: str) -> dict:
    folder = book / "analysis" / "locations"
    folder.mkdir(parents=True, exist_ok=True)
    view = {"id": "wide_establishing", "prompt": "A wide room at dusk. Bare boards, one window.", "shot_size": "wide"}
    (folder / f"{where}.json").write_text(json.dumps({"name": where, "profile": {"design": {"views": [view]}}}),
                                          encoding="utf-8")
    return add_row(book, f"refs/locations/{where}/wide_establishing.png", view["prompt"])


def name_of(picture) -> str:
    """The entity a picture belongs to: its folder."""
    return Path(picture).parent.name


def reader_of(cards: dict[str, str] | None = None, seen=SEEN, asked: list | None = None,
              answers: dict[str, list] | None = None):
    """A VLM stub: the trait-card question is answered from the fixture card the
    entity is mapped to (d4 -- distinct from everyone -- when unmapped); the
    look-back question from `seen`, or from `answers[entity]` consumed in order."""
    def reader(picture, question):
        if asked is not None:
            asked.append((Path(picture), question))
        if "casting sheet" in question:
            return json.dumps(CARDS[(cards or {}).get(name_of(picture), "d4")])
        listed = answers[name_of(picture)].pop(0) if answers and answers.get(name_of(picture)) else list(seen)
        return json.dumps({"seen": listed, "text": False})
    return reader


def one_hot_faces(picture):
    """Every entity its own face: unit vectors that never read as one man."""
    i = sum(map(ord, name_of(picture))) % 8
    v = np.zeros(8)
    v[i] = 1.0
    return v


def faces_of(vectors: dict[str, np.ndarray]):
    return lambda picture: vectors.get(name_of(picture), one_hot_faces(picture))


def styles_of(rows: dict[str, int] | None = None):
    """DINOv3 stub: each entity's row of the style fixture, the in-style sheet when unmapped."""
    return lambda picture: STYLE[(rows or {}).get(name_of(picture), 3)]


def no_words(_picture):
    return []


def two_wrists(_picture):
    person = [0.5, 0.1, 0.9, 0.5, 0.2, 0.9, 0.4, 0.3, 0.9, 0.3, 0.4, 0.9, 0.6, 0.3, 0.9, 0.7, 0.4, 0.9,
              0.45, 0.5, 0.9, 0.45, 0.7, 0.9, 0.45, 0.9, 0.9, 0.55, 0.5, 0.9, 0.55, 0.7, 0.9, 0.55, 0.9, 0.9,
              0.48, 0.08, 0.9, 0.52, 0.08, 0.9, 0.46, 0.1, 0.9, 0.54, 0.1, 0.9]
    return [{"people": [{"pose_keypoints_2d": person}], "canvas_width": 1, "canvas_height": 1}]


def tools(**override) -> dict:
    """The five readers, all passing unless overridden."""
    base = {"reader": reader_of(), "embed": faces_of({}), "ocr": no_words,
            "keypoints": two_wrists, "style_embed": styles_of()}
    return {**base, **override}


def drawer(drawn: list, book: Path):
    """The ladder's `run`: records the manifest values, draws a fresh picture."""
    def run(workflow, values):
        drawn.append({"workflow": workflow, **values})
        out = book / "work" / f"draw_{len(drawn)}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (64, 48), (20 * len(drawn), 40, 60)).save(out)
        return [out]
    return run


def verdict(book: Path) -> dict:
    return json.loads((book / "refs" / "verdict.json").read_text(encoding="utf-8"))


def logged(tmp_path) -> str:
    return "".join(p.read_text(encoding="utf-8") for p in (tmp_path / "logs").rglob("*.log"))
