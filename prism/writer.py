"""File one model's writer output on the library: style blocks and recaps on the cards, subject forms on the set.

    uv run python -m prism.writer <writer.json> [...]

A writer (an agent following the model guide's `system_prompt`) writes each part once:
the style block and recap per style, the style-neutral subject form per subject.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from prism.catalog import ModelWords, load_styles, load_subjects, write_style


def checked(said: dict, cards: dict, subject_ids: set[str]) -> None:
    strays = set(said["styles"]) - set(cards)
    if strays or set(said["subjects"]) != subject_ids:
        raise KeyError(f"writer names unheld styles {sorted(strays)} or not exactly the subjects {sorted(subject_ids)}")


def apply_writing(said: dict, styles: Path, subjects_path: Path) -> None:
    model, cards, held = said["model"], {s.id: s for s in load_styles(styles)}, load_subjects(subjects_path)
    checked(said, cards, {s.id for s in held.subjects})
    for style_id, parts in said["styles"].items():
        card = cards[style_id]
        write_style(card.model_copy(update={"models": {**card.models, model: ModelWords(**parts)}}), styles)
    rows = [s.model_copy(update={"forms": {**s.forms, model: said["subjects"][s.id]}}) for s in held.subjects]
    subjects_path.write_text(json.dumps(held.model_copy(update={"subjects": rows}).model_dump(), indent=2,
                                        ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    from prism.render import SUBJECTS
    for path in argv:
        apply_writing(json.loads(Path(path).read_text(encoding="utf-8")), Path("prism/styles"), SUBJECTS)
        print("filed", path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
