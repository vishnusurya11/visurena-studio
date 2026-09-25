"""The LOOK verdict: the owner's one taste signature per (book, style), bound to
the pack it was given on.

refs/pack.jsonl records every picture drawn (path, prompt, seed), so the sha8 of
its bytes is the identity of what was looked at.  refs/verdict.json carries
that sha8; a pack that has grown past it is a pack nobody has looked at whole,
and every format line refuses it until the owner signs again.

    uv run python scripts/refs/sign_look.py <codex_id> "<note>"
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from studio.judges import verdict as jv

PACK = "refs/pack.jsonl"
VERDICT = "refs/verdict.json"
APPROVE = "APPROVE"


def pack_path(book_dir: Path | str) -> Path:
    return Path(book_dir) / PACK


def verdict_path(book_dir: Path | str) -> Path:
    return Path(book_dir) / VERDICT


def pack_sha8(book_dir: Path | str) -> str:
    """The first 8 hex of sha256 over the pack's bytes; a missing pack is the empty pack."""
    path = pack_path(book_dir)
    data = path.read_bytes() if path.exists() else b""
    return hashlib.sha256(data).hexdigest()[:8]


def pack_rows(book_dir: Path | str) -> int:
    path = pack_path(book_dir)
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def read(book_dir: Path | str) -> dict | None:
    """The verdict on disk, whatever pack it signs; None when nobody has signed."""
    path = verdict_path(book_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def current(book_dir: Path | str) -> dict | None:
    """The verdict only if it signs the pack as it stands now."""
    got = read(book_dir)
    if got and got.get("pack_sha8") == pack_sha8(book_dir):
        return got
    return None


def new_rows(book_dir: Path | str) -> int:
    """How many rows the pack has grown by since the last signature."""
    signed = (read(book_dir) or {}).get("rows", 0)
    return max(pack_rows(book_dir) - int(signed), 0)


def sign(book_dir: Path | str, note: str, *, signed_by: str = jv.OWNER,
         faults: list[dict] | None = None) -> Path:
    """Write the APPROVE for the pack as it stands, and return the file.  A
    judge re-judges a stale pack's new rows only and re-signs the same way."""
    body = {"pack_sha8": pack_sha8(book_dir), "verdict": APPROVE, "note": note,
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "rows": pack_rows(book_dir), **jv.signature(signed_by, faults)}
    path = verdict_path(book_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
