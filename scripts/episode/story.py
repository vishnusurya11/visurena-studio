#!/usr/bin/env python
"""`story.md`: what this episode is, where it got to, what was decided.

    uv run python scripts/episode/story.py <codex_id> <episode>
    uv run python scripts/episode/story.py <codex_id> <episode> --say
    uv run python scripts/episode/story.py <codex_id> <episode> \\
        --decide "MAX_FACES 2 -> 4" --because "faces says whose face must READ"
    uv run python scripts/episode/story.py <codex_id> <episode> --next "cut and QC"

The facts are read off disk every run, because they go stale the moment
anything renders.  The judgement -- what was settled, why, what is next -- is
kept verbatim, because nothing on disk can reconstruct it.  Read it first when
picking an episode up; `--say` prints the three sentences to say back.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import episode_home, story_bible as sb, story_layer


def stage_of(home: Path, takes: list, plan_exists: bool, total: int = 0) -> str:
    """The furthest stage with something on disk to show for it.

    Takes outstanding beat every later artefact: a master and a report from the
    PREVIOUS iteration sit on disk all through the next one, and the first
    version of this read them and called an episode "delivered" with five takes
    still unrendered.  A status line that flatters is worse than none."""
    if total and len(takes) < total:
        return "8 takes"
    if (home / "report_final.html").exists() and any(home.glob("master_iter*.mp4")):
        return "10 pages — delivered"
    if any(home.glob("master_iter*.mp4")):
        return "9 cut and QC"
    if takes:
        return "8 takes"
    if list((home / "frames").glob("Q??_?.png")):
        return "6 storyboards drawn"
    if list((home / "frames").glob("plate_*.png")):
        return "3 plates"
    if (home / "placed.json").exists():
        return "2 timeline"
    if (home / "lines").exists():
        return "1 lines"
    return "0 the plan" if plan_exists else "0 no plan yet"


def planned_takes(book: Path, episode, number: int, fallback: int) -> int:
    """How many takes this episode WILL have, not how many exist.  Read from the
    take cards if they have been written, else built from the plan, because
    "15 of 15" while four are still queued is the same flattering lie."""
    prompts = episode_home.takes_dir(book, number, "r2v") / "prompts.json"
    if prompts.exists():
        return len(episode_home.read_json(prompts))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("takes_r2v", Path(__file__).with_name("takes_r2v.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return len(module.cards(book, episode, number))
    except Exception:
        return fallback


def facts(book_id: str, number: int) -> dict:
    book = episode_home.book_dir(book_id)
    home = episode_home.home(book, number)
    episode = episode_home.load_plan(book, number)
    takes_sheet = episode_home.takes_dir(book, number, "r2v") / "shots.json"
    takes = episode_home.read_json(takes_sheet) if takes_sheet.exists() else []
    placed = episode_home.read_json(home / "placed.json") if (home / "placed.json").exists() else {}
    masters = sorted(home.glob("master_iter*.mp4"))
    planned = planned_takes(book, episode, number, len(takes))
    return {
        "title": f"{episode.title} — episode {number}",
        "question": episode.question,
        "shots": len(episode.shots), "lines": len(episode.lines),
        "seconds": float(placed.get("duration_s", 0.0)),
        "stage": stage_of(home, takes, plan_exists=True, total=planned),
        "takes_done": len(takes), "takes_total": max(planned, len(takes)),
        "master": str(masters[-1]) if masters else "",
        "pages": [p.name for p in sorted(home.glob("*.html"))],
        "story": story_layer.report(episode.question, episode.shots)["says"],
    }


def page(book_id: str, number: int) -> Path:
    home = episode_home.home(episode_home.book_dir(book_id), number)
    return home / "story.md"


def write(book_id: str, number: int, edit=None) -> Path:
    out = page(book_id, number)
    known = facts(book_id, number)
    text = sb.merge(out.read_text(encoding="utf-8"), known) if out.exists() else sb.render(known)
    if edit:
        text = edit(text)
    out.write_text(text, encoding="utf-8")
    return out


def flag(argv: list[str], name: str) -> str | None:
    for arg in argv:
        if arg.startswith(f"--{name}="):
            return arg.split("=", 1)[1]
    if f"--{name}" in argv:
        at = argv.index(f"--{name}") + 1
        if at < len(argv) and not argv[at].startswith("--"):
            return argv[at]
    return None


def main(argv: list[str]) -> None:
    book_id, number = argv[1], int(argv[2]) if len(argv) > 2 and argv[2].isdigit() else 1
    what, why, nxt = flag(argv, "decide"), flag(argv, "because"), flag(argv, "next")
    edit = None
    if what:
        if not why:
            raise SystemExit("a decision without its reason is a rule the next window cannot evaluate; "
                             'add --because "<why>"')
        edit = lambda text: sb.decide(text, date.today().isoformat(), what, why)
    elif nxt:
        edit = lambda text: sb.render(sb._read_facts(text) | {"title": text.splitlines()[0][2:]},
                                      sb.parse(text) | {sb.NEXT: f"- {nxt}"})
    out = write(book_id, number, edit)
    if "--say" in argv:
        print(sb.restate(out.read_text(encoding="utf-8")))
    print(f"story -> {out}", flush=True)


if __name__ == "__main__":
    main(sys.argv)
