"""File the owner's board picks on the style cards.

    uv run python -m prism.verdicts <picks.json>     # {style_id: model_id}, from the board's "Copy picks"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from prism.catalog import load_guides, load_styles, write_style


def apply_picks(picks: dict[str, str], folder: Path, models: set[str]) -> list[str]:
    cards = {s.id: s for s in load_styles(folder)}
    for style_id, model_id in picks.items():
        if style_id not in cards or model_id not in models:
            raise KeyError(f"pick {style_id} -> {model_id}: unknown style or model")
    for style_id, model_id in picks.items():
        verdict = cards[style_id].verdict.model_copy(update={"best_model": model_id, "status": "tested"})
        write_style(cards[style_id].model_copy(update={"verdict": verdict}), folder)
    return sorted(picks)


def main(argv: list[str]) -> int:
    picks = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    print(apply_picks(picks, Path("prism/styles"), set(load_guides(Path("prism/models")))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
