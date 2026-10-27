"""G-CAST on a real cast (local: loads facenet on the CPU, reads one book's base
sheets, writes nothing under library/).  Prints every pair's cosine against the
master's wall; the Jekyll cast measured 2026-10-27: Jekyll-Utterson 0.550, the
highest pair Utterson-Enfield 0.712, nothing at the wall of 0.75."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import cast_faces

BOOK = Path(__file__).resolve().parents[1] / "library" / "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"


def bound(book: Path) -> set[str]:
    rows = json.loads((book / "refs" / "refs.json").read_text(encoding="utf-8")).get("refs", [])
    return {r["entity_id"] for r in rows if r.get("kind") in ("character", "characters")}


@pytest.mark.local
def test_the_jekyll_cast_is_scored_pair_by_pair(tmp_path):
    if not (BOOK / "refs" / "refs.json").exists():
        pytest.skip("the Jekyll book is not on this machine")
    sheets = cast_faces.base_sheets(BOOK, bound(BOOK))
    vecs = cast_faces.vectors(BOOK, sheets, cast_faces.default_embed(), {})
    pairs = cast_faces.pair_scores(vecs)
    for p in pairs:
        print(f"{p['cosine']:.3f} {p['a']}+{p['b']}" + ("  COLLAPSE" if p["cosine"] >= cast_faces.WALL else ""))
    print("no face:", sorted(set(sheets) - set(vecs)))
    jekyll = next(p for p in pairs if {p["a"], p["b"]} == {"gabriel_john_utterson", "henry_jekyll"})
    assert 0.0 < jekyll["cosine"] < 1.0
