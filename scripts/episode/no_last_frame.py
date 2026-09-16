"""THE CHECK THE OWNER ASKED FOR (2026-09-16): run it AFTER the prompts are
generated and after the sheets are drawn, and it says whether a last frame got
in anywhere.

    uv run python scripts/episode/no_last_frame.py <codex_id> <n>

A last frame in a ref2v take makes the model race to that picture and hold it:
near, the segment freezes; far, the background dissolves into the other picture.
That is the warping (`docs/calibration/end_frames.md`).

The rule has now been broken twice while written down, each time on an artefact
nobody was looking at -- once through the reference list, once through the prompt
text. So this reads the ARTEFACTS ON DISK, not the flags:

    SHEET PROMPTS   seq_*.prompt.txt      no END panel asked for
    CELLS           cells/Q??_?E.png      no END cell drawn
    TAKE PROMPTS    prompts.json / shots.json
                                          no "<Picture N> is the last frame"
                                          no "*E.png" staged as a reference

Exit 0 clean, exit 1 with every offender named. Free, reads only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home  # noqa: E402

DECLARED = re.compile(r"<Picture (\d+)> is the last frame")
RETAINED = re.compile(r"<Picture (\d+)> \(([^)]*last frame[^)]*)\)")
ASKED = re.compile(r"\bEND panel\b|\blast frame of panel\b", re.I)


def sheet_prompts(boards: Path) -> list[str]:
    """Every sheet prompt that asks a drawer for an END panel."""
    return [p.name for p in sorted(boards.glob("*.prompt.txt"))
            if ASKED.search(p.read_text(encoding="utf-8", errors="replace"))]


def end_cells_drawn(boards: Path) -> list[str]:
    """Every END cell sitting on disk. Not a failure on an OLD episode -- it is a
    failure on a new one, because nothing draws them any more."""
    return [p.name for p in sorted((boards / "cells").glob("Q*E.png"))]


def prompt_faults(card: dict) -> list[str]:
    """What is wrong with ONE take's prompt and reference list."""
    text = card.get("prompt", "")
    out = [f"declares <Picture {n}> the last frame" for n in DECLARED.findall(text)]
    out += [f"retains <Picture {n}> as a last frame" for n, _ in RETAINED.findall(text)]
    out += [f"stages the END cell {r}" for r in card.get("refs", []) if str(r).endswith("E.png")]
    return out


def take_faults(records: list[dict]) -> dict[int, list[str]]:
    """{take index -> its faults}, only the takes that have some."""
    return {c["index"]: said for c in records if (said := prompt_faults(c))}


def read_takes(book: Path, number: int) -> tuple[str, list[dict]]:
    """The take records to judge: the RENDERED ones if they exist, else the
    dry-built prompts. Both are artefacts; neither is a flag."""
    room = episode_home.takes_dir(book, number, "r2v")
    for name in ("shots.json", "prompts.json"):
        if (p := room / name).exists():
            return name, json.loads(p.read_text(encoding="utf-8"))
    return "", []


def report(book: Path, number: int) -> int:
    boards = episode_home.boards_dir(book, number)
    bad = 0

    asked = sheet_prompts(boards) if boards.exists() else []
    print(f"sheet prompts asking for an END panel : {len(asked)}")
    for name in asked:
        print(f"    {name}")
    bad += len(asked)

    drawn = end_cells_drawn(boards) if (boards / "cells").exists() else []
    print(f"END cells drawn on disk               : {len(drawn)}")
    for name in drawn[:10]:
        print(f"    {name}")
    bad += len(drawn)

    where, records = read_takes(book, number)
    faults = take_faults(records)
    print(f"take prompts read ({where or 'none found'}): {len(records)}")
    print(f"take prompts with a last frame        : {len(faults)}")
    for index, said in sorted(faults.items()):
        print(f"    T{index:02d}: " + "; ".join(said))
    bad += len(faults)

    print()
    print("CLEAN: no last frame anywhere" if not bad else f"REFUSED: {bad} places make a last frame")
    return 0 if not bad else 1


def main(book_id: str, number: int) -> int:
    return report(episode_home.book_dir(book_id), number)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], int(sys.argv[2])))
