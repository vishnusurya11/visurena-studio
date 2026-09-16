#!/usr/bin/env python
"""G-EYE: the contact sheet a person looks at, and the rubric they fill, before
`--watched=<sha8>` means anything.

    uv run python scripts/episode/eye_review.py <codex_id> <n> [--engine=r2v]

Writes, beside the master it describes:

    episodes/epNN/review/contact_<sha8>.png   5x6 grid, one frame every 5 s, 256 px cells
    episodes/epNN/review/eye_<sha8>.json      the rubric, blank, for a person to fill

WHY (ten reviewers, 2026-09-16, `docs/analysis/ep08_ep09_why_worse.md`).
Episode 9 passed 28/28 takes at 100.0 -- the best DQ in the series -- while
62 % of its frames were off their storyboard cell, its 5th-percentile luma was
16.5 against 4-7 for episodes 5-7, and its first dialogue came at 87.6 s.  Every
gate was built for one fault and found its own fault absent.  The publish
ladder asked for `--watched=<sha8>` and was satisfied by an agent that had
looked at six frames.

So the eye review is a STAGE with an ARTEFACT: the whole master at a glance,
and five questions, each one of ep09's faults, answered `y` or `n` by name.
Every question is written so that `y` is the good answer; an `n` passes only
with a `waived_because` the owner would sign, and the waiver is recorded in the
upload ledger beside the video id.  `youtube_upload.py --watched=<sha8>`
refuses without this file, and refuses a file that reviewed a different cut.

A passing gate proves only the absence of the fault it was built for.  This is
the gate for the faults the other gates cannot see.  Free, no GPU, no network.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, frames, script_qc, youtube_publish as yp  # noqa: E402

COLS, ROWS, CELL = 5, 6, 256
EVERY_S = 5.0
"""One frame every five seconds: a 2-3 minute master is 24-36 frames, and the
5x6 grid holds thirty, so a long master widens the step to fit (recorded in the
rubric as `frames_every_s`)."""

RUBRIC = (
    ("shadow", "Is there a true black somewhere in most frames? "
               "(ep09: 5th-percentile luma 16.5 against 4-7 for ep05-07; the histogram "
               "lifted off the floor and 94 % of its colour was one orange)"),
    ("faces", "In the closes, is the face readable at a quarter of the frame height? "
              "(ep09: three medium_close shots written 'two-shot' and drawn at 0.15-0.23)"),
    ("board", "Does each frame still resemble its storyboard cell? "
              "(ep09: 62 % of frames off-board; last frame vs own cell 0.075)"),
    ("repeats", "Is every picture drawn once -- no wide repeated, no close of the same face "
                "with the same list? (ep09: 9 of 30 shots the same close of Lucy; "
                "14 of 44 panels 'the same moment as panel k')"),
    ("story", "Does the turn land as an ACTION on screen? (ep09: the rescue -- a hand "
              "catching the horse by the curb -- is not in the episode; it cuts from the "
              "danger to 'You're not hurt, I hope, miss')"),
)
"""Field -> question.  `y` is always the good answer."""

ANSWERS = ("y", "n")


# ---- the paths ---------------------------------------------------------------

def review_dir(home: Path) -> Path:
    return Path(home) / "review"


def contact_path(home: Path, digest: str) -> Path:
    return review_dir(home) / f"contact_{digest}.png"


def rubric_path(home: Path, digest: str) -> Path:
    return review_dir(home) / f"eye_{digest}.json"


# ---- the contact sheet -------------------------------------------------------

def seconds_of(master: Path) -> float:
    """The master's length off ffmpeg's own report: ffprobe is not on this box.

    `ffmpeg -i <file>` with no output exits non-zero and still prints the
    `Duration:` line, which is all we need; decoding the whole master to find
    it (`script_qc.seconds_of`) costs seconds a review does not have to."""
    proc = subprocess.run(["ffmpeg", "-v", "info", "-i", str(master)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    return script_qc._from_stderr(proc.stderr)


def sample_times(seconds: float, every: float = EVERY_S, cells: int = COLS * ROWS) -> list[float]:
    """Frame times: every `every` seconds while the grid holds them, else the
    step that fits the whole master into the grid.  Never past the end."""
    step = every if seconds / every <= cells else seconds / cells
    return [round(i * step, 3) for i in range(cells) if i * step < seconds]


def grab(master: Path, times: list[float], work: Path) -> list[Path]:
    """One PNG per sample time, via ffmpeg."""
    work.mkdir(parents=True, exist_ok=True)
    return [frames.frame_at(master, t, work / f"f{i:02d}.png") for i, t in enumerate(times)]


def fitted(image, cell: int):
    """The frame scaled to fit inside a square cell, aspect kept."""
    scale = cell / max(image.width, image.height)
    return image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))))


def grid(stills: list[Path], times: list[float], dest: Path,
         cols: int = COLS, rows: int = ROWS, cell: int = CELL) -> Path:
    """The stills on a cols x rows grid of `cell` px squares, each stamped with
    its time, so a reviewer can name the second a fault lives at."""
    from PIL import Image, ImageDraw

    sheet = Image.new("RGB", (cols * cell, rows * cell), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    for i, (still, at) in enumerate(zip(stills, times)):
        image = fitted(Image.open(still).convert("RGB"), cell)
        x, y = (i % cols) * cell, (i // cols) * cell
        sheet.paste(image, (x + (cell - image.width) // 2, y + (cell - image.height) // 2))
        draw.text((x + 4, y + 4), f"{int(at // 60):02d}:{at % 60:04.1f}", fill=(255, 255, 0))
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest)
    return dest


# ---- the rubric ----------------------------------------------------------------

def blank_rubric(digest: str, master: str, contact: str, every: float, count: int) -> dict:
    """The file a person fills.  Every answer is empty on purpose: a rubric
    that arrives pre-filled is the six-frame glance with a signature."""
    return {"sha8": digest, "master": master, "contact": contact,
            "frames_every_s": every, "frames": count,
            "how": "answer each field y or n; y is always the good answer; an n passes only "
                   "with a waived_because the owner would sign; notes may not be empty",
            "rubric": {field: {"question": question, "answer": "", "waived_because": ""}
                       for field, question in RUBRIC},
            "notes": "", "reviewed_by": "", "reviewed_at": ""}


def write_blank(path: Path, rubric: dict) -> Path:
    """Write the blank rubric ONLY where none exists: a filled review of this
    same cut is never blanked by re-running the builder."""
    if path.exists():
        return path
    return episode_home.write_json(path, rubric)


def unanswered(rubric: dict) -> list[str]:
    """Every field with no y/n, and `notes` when it says nothing."""
    fields = rubric.get("rubric", {})
    out = [field for field, _q in RUBRIC
           if str(fields.get(field, {}).get("answer", "")).strip().lower() not in ANSWERS]
    if not str(rubric.get("notes", "")).strip():
        out.append("notes")
    return out


def unwaived(rubric: dict) -> list[str]:
    """Every field answered n with no reason written beside it."""
    fields = rubric.get("rubric", {})
    return [field for field, _q in RUBRIC
            if str(fields.get(field, {}).get("answer", "")).strip().lower() == "n"
            and not str(fields.get(field, {}).get("waived_because", "")).strip()]


def waivers(rubric: dict) -> dict[str, str]:
    """{field: reason} for every n that carries one -- what the ledger records."""
    fields = rubric.get("rubric", {})
    return {field: str(fields[field]["waived_because"]).strip()
            for field, _q in RUBRIC
            if str(fields.get(field, {}).get("answer", "")).strip().lower() == "n"
            and str(fields.get(field, {}).get("waived_because", "")).strip()}


def refusals(rubric: dict, digest: str, path: Path) -> list[str]:
    """Every reason this rubric does not clear `--watched`.  Empty means go."""
    out = []
    if rubric.get("sha8") != digest:
        out.append(f"{path} reviewed sha8 {rubric.get('sha8') or '(none)'}, this cut is {digest}; "
                   f"rebuild the contact sheet and look at THIS file")
    if missing := unanswered(rubric):
        out.append(f"{path} leaves {', '.join(missing)} unanswered; look at the contact sheet "
                   f"and answer every field")
    if bare := unwaived(rubric):
        out.append(f"{path} answers n on {', '.join(bare)} with no waived_because; "
                   f"fix the cut or write the reason the owner would sign")
    return out


def verdict(home: Path, watched: str, digest: str) -> tuple[list[str], dict]:
    """(refusals, the rubric) for `--watched=<watched>` against a master at `digest`.

    The file is looked up by the sha the caller CLAIMS to have watched; its
    contents are judged against the sha of the file being uploaded."""
    path = rubric_path(home, watched)
    if not path.exists():
        want = rubric_path(home, digest)
        return [f"no eye review at {want}; run eye_review.py, look at "
                f"{contact_path(home, digest)}, and fill it"], {}
    rubric = episode_home.read_json(path)
    return refusals(rubric, digest, path), rubric


# ---- the stage -----------------------------------------------------------------

def build(home: Path, master: Path, digest: str, every: float = EVERY_S) -> tuple[Path, Path]:
    """The contact sheet and the (blank) rubric for this master."""
    times = sample_times(seconds_of(master), every)
    stills = grab(master, times, review_dir(home) / "work" / digest)
    contact = grid(stills, times, contact_path(home, digest))
    rubric = blank_rubric(digest, master.name, contact.name, every, len(times))
    return contact, write_blank(rubric_path(home, digest), rubric)


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    book = episode_home.book_dir(args[0])
    home = episode_home.home(book, int(args[1]))
    engine = next((a.split("=", 1)[1] for a in argv if a.startswith("--engine=")), "")
    _engine, master, _qc = yp.deliverable(home, engine)
    digest = yp.sha8(master)
    contact, rubric = build(home, master, digest)
    print(f"master   {master}   sha8 {digest}")
    print(f"look at  {contact}")
    print(f"fill     {rubric}")
    print(f"then     youtube_upload.py {args[0]} {args[1]} --watched={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
