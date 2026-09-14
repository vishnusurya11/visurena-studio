"""Where an episode lives inside its book, and nothing else.

    library/<book>/episodes/ep04/
        plan.json        the contract (studio.episode_spec.Episode)
        story.md         what was decided and why
        youtube.json     the owner's declaration to the platform
        audio/           the music bed
          lines/         one wav per spoken line + lines.json (MEASURED seconds)
        boards/
          plates/        one empty plate per setup
          sheets/        the drawn sheets, their prompts and their dq reports
          cells/         the cut cells the takes are pinned to
          panels/        single-panel redraws and the drafts they replaced
        takes/
          <engine>/      one take per index + shots.json + prompts.json
            attempts/    the rolls that lost
          work/          scratch: the composited guide audio, the strips
        cut/             master.mp4 and every master_iterN.mp4
        reports/         qc.json and the html pages

ONE FOLDER PER STAGE, in pipeline order (owner, 2026-09-13).  Episode 3 kept
100+ files under `frames/` alone -- plates, sheets, prompts, dq reports, cells,
END cells, superseded `.before.png` drafts and redraw working files -- with the
stage encoded only in a filename prefix, and the engine in folder SUFFIXES
(`shots_r2v`, `work_r2v`).  At one episode that is untidy; at fourteen it stops
you doing the thing this pipeline does most, which is RE-ROLL one stage and
leave the rest alone.

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


def audio_dir(book: Path, number: int) -> Path:
    """Everything the ear gets: the bed, and `lines/` under it."""
    return home(book, number) / "audio"


def lines_dir(book: Path, number: int) -> Path:
    return audio_dir(book, number) / "lines"


def boards_dir(book: Path, number: int) -> Path:
    return home(book, number) / "boards"


def plates_dir(book: Path, number: int) -> Path:
    """One empty plate per setup: the place, with nobody in it."""
    return boards_dir(book, number) / "plates"


def sheets_dir(book: Path, number: int) -> Path:
    """The drawn sheets, their prompts and their dq reports -- the PAID artefacts."""
    return boards_dir(book, number) / "sheets"


def cells_dir(book: Path, number: int) -> Path:
    """The cells cut out of the sheets; these are what a take is pinned to."""
    return boards_dir(book, number) / "cells"


def panels_dir(book: Path, number: int) -> Path:
    """Single-panel redraws and the drafts they replaced.

    Kept apart from `cells/` deliberately: a superseded `.before.png` sitting
    beside the cells was read as another shot's picture and cost episode 3 ten
    of its eighteen foreign-frame flags."""
    return boards_dir(book, number) / "panels"


def takes_root(book: Path, number: int) -> Path:
    return home(book, number) / "takes"


def takes_under(home_dir: Path, engine: str = "i2v") -> Path:
    """One engine's takes, addressed from the EPISODE HOME rather than from
    (book, number).  Some readers -- a per-take HTML card, say -- are handed the
    home and never see the number, and without this they spell the room out by
    hand -- which is how a hand-written join to the pre-split takes folder
    outlived the folder it named, in three separate report scripts."""
    return Path(home_dir) / "takes" / engine


def takes_dir(book: Path, number: int, engine: str = "i2v") -> Path:
    """One engine's takes. The engine is a FOLDER, not a filename suffix."""
    return takes_root(book, number) / engine


def attempts_dir(book: Path, number: int, engine: str = "i2v") -> Path:
    """The rolls that lost, kept so best-of-N can be re-judged and so a
    superseded take is never mistaken for the current one."""
    return takes_dir(book, number, engine) / "attempts"


def work_dir(book: Path, number: int, engine: str = "i2v") -> Path:
    """Scratch for a render: composited guide audio, reference strips."""
    return takes_root(book, number) / "work"


def cut_dir(book: Path, number: int) -> Path:
    """Every master: the delivered one and every numbered iteration."""
    return home(book, number) / "cut"


def make_rooms(book: Path, number: int) -> None:
    """Make the episode's output rooms, before the work that fills them.

    `master_path` returns `<home>/cut/...` and nothing created `cut/`.  Episodes
    1 to 3 have one only because `migrate_layout.py` made it while moving their
    masters in; a NEW episode never got one, so the first assemble reached
    ffmpeg and died on "No such file or directory" AFTER the cut, the mix and
    the bed had been paid for.  `reports_dir` had the same shape.

    A room is free and the work in front of it is not, so they are made at the
    start of the step, not at the moment of writing."""
    for room in (cut_dir(book, number), reports_dir(book, number)):
        room.mkdir(parents=True, exist_ok=True)


def master_path(book: Path, number: int, engine: str = "i2v") -> Path:
    return cut_dir(book, number) / ("master.mp4" if engine == "i2v" else f"master_{engine}.mp4")


def reports_dir(book: Path, number: int) -> Path:
    """What was MEASURED, and the pages a human reads. Never mixed with the film."""
    return home(book, number) / "reports"


def qc_path(book: Path, number: int, engine: str = "i2v") -> Path:
    return reports_dir(book, number) / ("qc.json" if engine == "i2v" else f"qc_{engine}.json")


def engine_arg(argv: list[str]) -> str:
    return next((a.split("=", 1)[1] for a in argv if a.startswith("--engine=")), "i2v")


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
