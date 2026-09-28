#!/usr/bin/env python
"""One speaker, one voice: measure each part's lines against EACH OTHER.

    uv run python scripts/episode/speaker_check.py <book_id> <episode>

say_lines scores a render against the character's DESIGN clip; nobody scores a
character's lines against one another, so a part can pass twice and be two men
(WotW ep05: 0.58 between the neighbour's two lines, both passing).  Free, CPU.
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, voice_ear
from studio.speaker_spread import SAME_SPEAKER_FLOOR, spread


MEASURABLE_S = 2.0
"""say_lines.SIM_MEASURABLE_S: under 2 s a voice embedding scores one man's own
slices 0.07-0.58 (finding 40); ep13's two "split voices" were "Listen!" and
"What are we?"."""


def long_enough(wav: Path) -> bool:
    import soundfile
    return soundfile.info(str(wav)).duration >= MEASURABLE_S


def lines_by_speaker(home: Path) -> dict[str, list[tuple[str, Path]]]:
    rows = json.loads((home / "audio" / "lines" / "lines.json").read_text(encoding="utf-8"))
    rows = rows["lines"] if isinstance(rows, dict) else rows
    out: dict[str, list[tuple[str, Path]]] = {}
    for row in rows:
        who = row.get("who") or row.get("speaker") or "narration"
        wav = home / "audio" / "lines" / (row.get("file") or f"l{row['index']:02d}.wav")
        if wav.exists() and long_enough(wav):
            out.setdefault(who, []).append((wav.stem, wav))
    return out


def main(book_id: str, number: int) -> None:
    home = episode_home.book_dir(book_id) / "episodes" / f"ep{number:02d}"
    report, worst_overall = {}, 1.0
    for who, lines in sorted(lines_by_speaker(home).items()):
        sims = {(a[0], b[0]): voice_ear.similarity(a[1], b[1])
                for a, b in itertools.combinations(lines, 2)}
        out = spread(sims)
        report[who] = out | {"lines": len(lines)}
        mark = "" if out["ok"] else "SPLIT VOICE"
        worst = f"{out['worst']:.2f}" if out["worst"] is not None else "n/a"
        print(f"{who:<34} lines {len(lines):>2}  worst pair {worst} "
              f"{out['worst_pair'] or ''}  {mark}", flush=True)
        if out["worst"] is not None:
            worst_overall = min(worst_overall, out["worst"])
    (home / "review").mkdir(exist_ok=True)
    (home / "review" / "speaker_check.json").write_text(
        json.dumps(report, indent=1), encoding="utf-8")
    print(f"floor {SAME_SPEAKER_FLOOR}; worst across the cast {worst_overall:.2f}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
