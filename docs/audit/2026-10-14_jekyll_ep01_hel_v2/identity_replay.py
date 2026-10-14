"""Replay the take identity row WITH the cast sheets handed in (decision 3, 2026-10-14).

Since 4c5f14c (2026-09-25) `take_verdict.measure` never handed `sheets_of` to
`identity_gate.identity_dq`, so the row read "not measured" on every take.  This
replays the armed judge, sheets in, over shipped takes and writes one JSON row per
take: what the HARD rule (STRANGER / DRIFT) would have refused on work that shipped.

    uv run python docs/audit/2026-10-14_jekyll_ep01_hel_v2/identity_replay.py <out.jsonl> <episode_dir>...

$0, CPU, read-only.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from studio import identity_gate, take_verdict as tv  # noqa: E402
from studio.measure import faces  # noqa: E402


def records(ep: Path) -> list[dict]:
    path = ep / "takes" / "r2v" / "shots.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def scarlet_sheets(rec: dict, book: Path) -> dict:
    """Early Scarlet records name a sheet by basename: char-<who>[_look].png under refs/characters."""
    return {who: book / "refs" / "characters" / ref for who in rec.get("faces") or []
            for ref in rec.get("refs") or [] if Path(ref).name.startswith(f"char-{who}")}


def replay(ep: Path, detect, embed, out) -> None:
    book = ep.parents[1]
    for rec in records(ep):
        video = ep / "takes" / "r2v" / f"T{rec['index']:02d}.mp4"
        sheets = tv.sheets_of(rec, book) or scarlet_sheets(rec, book)
        sheets = {w: p for w, p in sheets.items() if p.exists()}
        if not video.exists() or not sheets:
            continue
        t0 = time.time()
        rep = identity_gate.identity_dq(video, [0], rec.get("faces", []), rec.get("refs", []),
                                        sheets=sheets, detect=detect, embed=embed)
        row = {"episode": f"{book.name[:14]}/{ep.name}", "take": rec["index"], "faces": rec.get("faces", []),
               "sheets": sorted(sheets), "measured": rep["measured"], "hard": rep["hard"],
               "flags": rep["flags"], "present": rep["present"], "note": rep.get("note", ""),
               "s": round(time.time() - t0, 1)}
        out.write(json.dumps(row) + "\n")
        out.flush()
        print(row["episode"], row["take"], "HARD" if row["hard"] else "ok", row["hard"][:2], flush=True)


def main(target: str, eps: list[str]) -> None:
    detect, embed = faces.embedder()
    with open(target, "a", encoding="utf-8") as out:
        for ep in eps:
            replay(Path(ep), detect, embed, out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
