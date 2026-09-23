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


def attempts_of(take_dir: Path, index: int) -> list[Path]:
    """Every roll of one take: the kept file first, then every `T<NN>_*.mp4`.

    IT READS BOTH ROOMS.  `migrate_layout` moved displaced rolls into
    `take_dir/attempts/` and the renderer, written before the move, keeps putting
    them flat -- so episode 3's losers are in `attempts/` and episode 4's are in
    `takes/r2v/`.  Globbing one folder made `take_dq --attempts` report
    "kept T07.mp4 of 1" while four rolls sat one directory down, and a reader of
    that line concludes a best-of-5 was adjudicated."""
    take_dir = Path(take_dir)
    kept = take_dir / f"T{index:02d}.mp4"
    others = sorted(take_dir.glob(f"T{index:02d}_*.mp4"))
    others += sorted((take_dir / "attempts").glob(f"T{index:02d}_*.mp4"))
    return ([kept] if kept.exists() else []) + others


def next_fail(take_dir: Path, index: int) -> Path:
    """The next free `T<NN>_failN.mp4`, in the attempts room, counting BOTH rooms.

    ONE COPY.  `take_dq` and `takes_r2v` each had their own, and the renderer's
    docstring says so: "the renderer had its own, worse, copy of the idea".  Both
    globbed the flat take dir, so with the losers in `attempts/` this returned
    `_fail1` while `attempts/T07_fail1.mp4` already existed -- and the promise in
    its own name, that no displaced attempt is ever overwritten, held only by the
    accident of the collision being in a different directory.

    Read off what is on disk, never off a counter: the renderer once crashed with
    FileExistsError because the name came from `tries` in a record, which a
    re-run does not know about."""
    take_dir = Path(take_dir)
    used = [int(p.stem.rsplit("_fail", 1)[1])
            for room in (take_dir, take_dir / "attempts")
            for p in room.glob(f"T{index:02d}_fail*.mp4")
            if p.stem.rsplit("_fail", 1)[1].isdigit()]
    room = take_dir / "attempts"
    room.mkdir(parents=True, exist_ok=True)
    return room / f"T{index:02d}_fail{max(used, default=0) + 1}.mp4"


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


def episode_arg(argv: list[str]) -> int:
    """The episode number: the second plain (non-flag) argument, or a refusal.

    Twenty CLIs used to fall back to episode 1, and takes_r2v tested
    `isdigit()` on argv[2], so `takes_r2v.py <book> --retake=3` would have
    re-rendered EPISODE ONE's take 3 on the GPU. A default episode is a guess
    about the one thing the command is for (audit 2026-09-22, item 7)."""
    plain = [a for a in argv[1:] if not a.startswith("--")]
    if len(plain) < 2 or not plain[1].isdigit() or int(plain[1]) < 1:
        raise SystemExit(f"say which episode: {argv[0]} <book> <episode> ...  (got {plain[1:2] or 'nothing'})")
    return int(plain[1])


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
