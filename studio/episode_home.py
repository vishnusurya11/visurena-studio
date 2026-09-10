"""Where an episode lives inside its book, and nothing else.

    library/<book>/episodes/ep01/
        plan.json        the contract (studio.episode_spec.Episode)
        lines/           one wav per spoken line + lines.json (MEASURED seconds)
        frames/          plates, masters, per-shot start frames + frames.json
        shots/           one take per shot + shots.json
        master.mp4       the delivered 9:16 film
        qc.json          what was measured on the file

Every path an artifact records is book-relative; the absolute root is
resolved here and only here.
"""
from __future__ import annotations

import json
from pathlib import Path

from studio.episode_spec import Episode

LIBRARY = Path(__file__).resolve().parents[1] / "library"


def book_dir(book_id: str) -> Path:
    """The book folder for a 14-digit codex id or a full folder name."""
    hits = sorted(p for p in LIBRARY.iterdir() if p.name.startswith(book_id) or p.name == book_id)
    if not hits:
        raise FileNotFoundError(f"no book matching {book_id!r} under {LIBRARY}")
    return hits[0]


def home(book: Path, number: int) -> Path:
    return Path(book) / "episodes" / f"ep{number:02d}"


def plan_path(book: Path, number: int) -> Path:
    return home(book, number) / "plan.json"


def load_plan(book: Path, number: int) -> Episode:
    """The plan, validated on the way in: a plan that fails here never renders."""
    return Episode.model_validate_json(plan_path(book, number).read_text(encoding="utf-8"))


def lines_dir(book: Path, number: int) -> Path:
    return home(book, number) / "lines"


def frames_dir(book: Path, number: int) -> Path:
    return home(book, number) / "frames"


def shots_dir(book: Path, number: int) -> Path:
    return home(book, number) / "shots"


def master_path(book: Path, number: int) -> Path:
    return home(book, number) / "master.mp4"


def relative(book: Path, path: Path) -> str:
    """How an artifact names a file: relative to the book, posix."""
    return Path(path).resolve().relative_to(Path(book).resolve()).as_posix()


def read_json(path: Path) -> dict | list:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, data) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
