#!/usr/bin/env python
"""The book's cast pictures: one identity BUST per character, one wardrobe CARD
per wardrobe state.

    uv run python scripts/episode/cast_cards.py <codex_id> --check     # free
    uv run python scripts/episode/cast_cards.py <codex_id> --prompts   # free
    uv run python scripts/episode/cast_cards.py <codex_id> --draw <who> <bust|indoor|outdoor> --approved

`--check` is free, model-free and runs every time (`studio/cast_agree.py`).
`--prompts` writes every picture's prompt to disk as text for the owner to
read; it draws nothing.  `--draw` is the ESCALATE gate: it spends, so it
refuses unless the owner's `--approved` is on the command line.

This replaces `cast_variants.py`, which drew one variant per SETUP from a
change typed on the command line.  Two faults, both measured: four of the
Watson "variants" on disk are byte-identical (md5 6021ad83...), because six
setups have only two wardrobe states between them; and a hand-typed prompt is
how `char-sherlock_holmes_lab.prompt.txt` came to freeze an outdoor muffler
round his throat in a heated laboratory.  The prompt is built from
`refs.json`, never typed.
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import cast_agree, cast_refs, episode_home, image_spend as spend
from studio.llm import _load_dotenv

MODEL, SIZE, QUALITY = cast_refs.MODEL, cast_refs.SIZE, cast_refs.QUALITY
PLANNED_USD, CEILING_USD = 0.64, 1.28
"""Eight pictures at $0.08, and one redraw each if the gate refuses one.  The
run stops and asks at the ceiling rather than retrying a third time."""
SUPERSEDED = ".superseded"


def check_all(book: Path, cast: list[str]) -> dict[str, list[str]]:
    """Every complaint about every character, by name.  Free: no model, no call."""
    out: dict[str, list[str]] = {}
    for who in cast:
        try:
            said = cast_agree.check(book, who)
        except KeyError as missing:
            said = [str(missing).strip('"')]
        if said:
            out[who] = said
    return out


def prompt_file(book: Path, stem: str) -> Path:
    return cast_refs.characters(book) / f"{stem}.prompt.txt"


def write_prompts(book: Path, cast: list[str]) -> list[Path]:
    """Every picture's prompt, on disk beside the picture, for the owner to read.

    Costs nothing and draws nothing: a prompt the owner has not read is a
    picture nobody agreed to pay for."""
    made = []
    for who in cast:
        row = cast_refs.row(book, who)
        if missing := cast_refs.sheet_missing(row):
            # NOT SILENCE.  This was `continue`, and the three Utah leads went
            # to the drawer with no prompt on disk and nobody told.
            print(f"  {who}: no prompt written -- the row is missing {', '.join(missing)}",
                  flush=True)
            continue
        for stem, said in cast_refs.sheet_prompts(row).items():
            path = prompt_file(book, stem)
            path.write_text(_record(stem, said, cast_refs.bust(book, who).name),
                            encoding="utf-8")
            made.append(path)
    return made


def _record(stem: str, said: str, reference: str) -> str:
    """One prompt as the owner reads it: what is drawn, from what, at what price."""
    kind = "identity BUST" if "_" not in stem.replace("char-", "") else "wardrobe CARD"
    return (f"{stem}.png -- {kind}\n"
            f"model: {MODEL}  size: {SIZE}  quality: {QUALITY}  n: 1\n"
            f"call: images.edit  reference: {reference}\n"
            f"estimate: ${spend.estimate_usd(MODEL, SIZE, QUALITY):.2f}\n\n{said}\n")


def supersede(path: Path) -> Path | None:
    """Keep the picture being replaced, free and on disk, before replacing it."""
    if not path.exists():
        return None
    kept = path.parent / SUPERSEDED / f"{path.stem}.{time.strftime('%Y%m%dT%H%M%S')}.png"
    kept.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, kept)
    return kept


def draw(book: Path, who: str, kind: str, approved: bool = False) -> Path:
    """PAID: one gpt-image edit, $0.08.  Refuses without the owner's go.

    The default gate policy for any credit-spending step is ESCALATE, so the
    refusal is the behaviour and the drawing is the exception."""
    if not approved:
        raise SystemExit(f"cast_cards --draw {who} {kind} spends "
                         f"${spend.estimate_usd(MODEL, SIZE, QUALITY):.2f}: "
                         f"pass --approved once the owner has approved the prompt")
    row = cast_refs.row(book, who)
    stem = row["ref_id"] if kind == "bust" else f"{row['ref_id']}_{kind}"
    try:
        said = cast_refs.sheet_prompts(row)[stem]
    except ValueError as thin:
        raise SystemExit(f"cast_cards --draw refuses before spending: {thin}")
    out = cast_refs.characters(book) / f"{stem}.png"
    supersede(out)
    source = cast_refs.bust(book, who)
    drawn = _edit(source, out, said, book, stem)
    remember(book, stem, said, source)
    return drawn


def remember(book: Path, stem: str, said: str, source: Path) -> Path:
    """The prompt beside the card, EVERY time it is drawn.

    Episode 9's six Utah cards had no prompt on disk: `--prompts` skipped rows
    without `sheet`, and `--draw` never wrote one.  A picture with no record of
    what asked for it cannot be checked against anything."""
    record = prompt_file(book, stem)
    record.write_text(_record(stem, said, source.name), encoding="utf-8")
    return record


def _edit(source: Path, out: Path, said: str, book: Path, stem: str) -> Path:
    """The one call that costs money, and the ledger line that records it."""
    import base64
    import os

    _load_dotenv()
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    with open(source, "rb") as handle:
        got = client.images.edit(model=MODEL, image=[handle], prompt=said,
                                 size=SIZE, quality=QUALITY, n=1)
    out.write_bytes(base64.b64decode(got.data[0].b64_json))
    spend.record(book, MODEL, SIZE, QUALITY, 1, f"cast sheet {stem}")
    return out


def cast_of(book: Path) -> list[str]:
    """Every character the book has bound, in refs.json order."""
    return [row["entity_id"] for row in cast_refs.load(book).get("refs", [])
            if row.get("kind") == "character"]


def named(argv: list[str], book: Path) -> list[str]:
    """The characters asked for on the command line, or the whole bound cast."""
    asked = [word for word in argv[2:] if not word.startswith("--")
             and word not in ("bust",) + cast_refs.STATES]
    return asked or cast_of(book)


def main(argv: list[str]) -> None:
    book = episode_home.book_dir(argv[1])
    cast = named(argv, book)
    if "--prompts" in argv:
        for path in write_prompts(book, cast):
            print(f"  {path}", flush=True)
    if "--draw" in argv:
        at = argv.index("--draw")
        print(draw(book, argv[at + 1], argv[at + 2], "--approved" in argv))
    for who, said in check_all(book, cast).items():
        print(f"{who}:", flush=True)
        for line in said:
            print(f"    {line}", flush=True)


if __name__ == "__main__":
    main(sys.argv)
