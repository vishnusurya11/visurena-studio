"""The research loop's two ends: a brief of what the library holds, and a merge of what a run found.

The web research itself is done by agents (the `prism` skill); this module is
what makes a re-run add only NEW styles:

    uv run python -m prism.research brief            # prints the brief for the agents
    uv run python -m prism.research merge <inbox>    # validates, refuses duplicates, files the new
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from prism.catalog import Style, load_styles, read_style, write_style

STYLES = Path("prism/styles")


def counts(styles: list[Style]) -> str:
    held = Counter(s.family for s in styles)
    return ", ".join(f"{family}: {held[family]}" for family in ("anime", "live_action"))


def brief(styles: list[Style], run: str) -> str:
    """What a research agent must know: the run id, the held styles (never redo them), the card shape."""
    rows = "\n".join(f"- {s.id} | {s.name} | {', '.join(s.lineage.titles[:2])}" for s in styles)
    schema = json.dumps(Style.model_json_schema(), indent=1)
    return (f"# Prism research brief, run {run}\n\nHeld ({counts(styles)}). Do NOT research these again:\n"
            f"{rows or '- (none)'}\n\nWrite one card per NEW style, `run` = \"{run}\", "
            f"to the inbox folder you were given. Card schema:\n```json\n{schema}\n```\n")


def name_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def duplicate_of(card: Style, styles: list[Style]) -> str | None:
    """The held style this card repeats, by id or by name; None when it is new."""
    for held in styles:
        if held.id == card.id or name_key(held.name) == name_key(card.name):
            return held.id
    return None


def merge(inbox: Path, folder: Path) -> tuple[list[str], dict[str, str]]:
    """File every valid new card from `inbox` into `folder`; (added ids, refused file -> reason)."""
    held, added, refused = load_styles(folder), [], {}
    for path in sorted(Path(inbox).glob("*.json")):
        try:
            card = read_style(path)
        except (ValidationError, ValueError) as fault:
            refused[path.name] = str(fault).splitlines()[0]
            continue
        if repeat := duplicate_of(card, held):
            refused[path.name] = f"repeats {repeat}"
            continue
        write_style(card, folder)
        held.append(card)
        added.append(card.id)
    return added, refused


def next_run(styles: list[Style]) -> str:
    runs = [int(s.run[1:]) for s in styles if re.fullmatch(r"r\d+", s.run)]
    return f"r{max(runs, default=0) + 1:03d}"


def main(argv: list[str]) -> int:
    styles = load_styles(STYLES)
    if argv[:1] == ["brief"]:
        print(brief(styles, next_run(styles)))
        return 0
    if argv[:1] == ["merge"] and len(argv) == 2:
        added, refused = merge(Path(argv[1]), STYLES)
        print(json.dumps({"added": added, "refused": refused}, indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
