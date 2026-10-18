"""A vendor's prompt upsampler as a Prism model: FLUX 3 Klein's PUP writes one whole caption per
(style, subject) from the request a person would type.

    uv run python -m prism.upsample requests <out.json> <style_id> [...]   # what the upsampler is asked
    <ComfyUI python> prism/scripts/pup_captions.py <requests.json> <captions.json> <pup dir>
    uv run python -m prism.upsample file <captions.json> <model_id>          # files them on the cards
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from prism.catalog import ModelWords, Style, Subject, SubjectSet, load_styles, write_style


def request(style: Style, subject: Subject) -> str:
    return re.sub(r"\s+", " ", f"{style.style_words} {subject.prose} {subject.camera}").strip()


def requests(styles: list[Style], subjects: SubjectSet, wanted: list[str]) -> list[dict]:
    return [{"style": s.id, "subject": subject.id, "request": request(s, subject)}
            for s in styles if s.id in wanted for subject in subjects.subjects]


def file_captions(rows: list[dict], folder: Path, model_id: str) -> None:
    cards = {s.id: s for s in load_styles(folder)}
    for row in rows:
        card = cards[row["style"]]
        own = card.models.get(model_id) or ModelWords(style="")
        own = own.model_copy(update={"captions": {**own.captions, row["subject"]: row["caption"]}})
        cards[row["style"]] = card.model_copy(update={"models": {**card.models, model_id: own}})
    for card_id in {row["style"] for row in rows}:
        write_style(cards[card_id], folder)


def main(argv: list[str]) -> int:
    from prism.catalog import load_subjects
    from prism.render import SUBJECTS
    styles = Path("prism/styles")
    if argv[:1] == ["requests"]:
        rows = requests(load_styles(styles), load_subjects(SUBJECTS), argv[2:])
        Path(argv[1]).write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{len(rows)} requests -> {Path(argv[1]).resolve()}")
        return 0
    if argv[:1] == ["file"]:
        file_captions(json.loads(Path(argv[1]).read_text(encoding="utf-8")), styles, argv[2])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
