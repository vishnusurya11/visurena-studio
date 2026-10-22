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
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, voice_ear
from studio.episode_emotion import FEELING_FLOOR_DROP, f0_median
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


def deliveries(home: Path) -> dict[str, str]:
    """Line stem -> its delivery, from lines.json."""
    rows = json.loads((home / "audio" / "lines" / "lines.json").read_text(encoding="utf-8"))
    rows = rows["lines"] if isinstance(rows, dict) else rows
    return {f"l{r['index']:02d}": r.get("delivery") or "calm" for r in rows}


def omitted_stems(book: Path, number: int) -> set[str]:
    """The lines of shots the plan omits from the cut: nobody hears them."""
    ep = episode_home.load_plan(book, number)
    return {f"l{l.index:02d}" for l in ep.lines if l.shot in (ep.omit or [])}


def allowance(pair: tuple[str, str], said: dict[str, str]) -> float:
    return sum(FEELING_FLOOR_DROP for stem in pair if said.get(stem, "calm") != "calm")


REGISTER_ST = 4.0
"""Semitones a short line's median pitch may sit from its speaker's register before it is
flagged.  Not yet calibrated on an owner label (a calm read moves ~2 st, a shout 3; ep01 l11
is the one case): advisory only -- it writes a row, never a revoice, never a seed."""


def register_hz(wavs: list[Path]) -> float:
    """The speaker's register: the median of the median pitch of his measurable lines."""
    got = [hz for hz in (f0_median(w) for w in wavs) if hz > 0]
    return statistics.median(got) if got else 0.0


def offset_st(wav: Path, register: float) -> float | None:
    """How far a clip's median pitch sits from `register`, semitones; None when unvoiced."""
    hz = f0_median(wav)
    return 12.0 * math.log2(hz / register) if hz > 0 and register > 0 else None


def short_register_ok(wav: Path, register: float) -> bool:
    """A short line the pair measure cannot confirm still has to sit at its speaker's register."""
    off = offset_st(wav, register)
    return off is None or abs(off) <= REGISTER_ST


def short_row(wav: Path, row: dict, register: float) -> dict:
    off = offset_st(wav, register)
    return {"line": wav.stem, "speaker": row.get("speaker"), "seconds": row.get("seconds"),
            "register_hz": round(register, 1), "offset_st": None if off is None else round(off, 2),
            "short_register_ok": short_register_ok(wav, register)}


def short_rows(home: Path, rows: list[dict]) -> list[dict]:
    """One row for every line under MEASURABLE_S and every keep_best_far line, against the
    register of the same speaker's other (measurable, unflagged) lines.  CPU, no seed."""
    wav = lambda r: home / "audio" / "lines" / f"l{r['index']:02d}.wav"
    short = lambda r: float(r.get("seconds") or 0) < MEASURABLE_S or r.get("flagged") == "keep_best_far"
    out = []
    for who in sorted({r.get("speaker") for r in rows}):
        mine = [r for r in rows if r.get("speaker") == who and wav(r).exists()]
        register = register_hz([wav(r) for r in mine if not short(r)])
        out += [short_row(wav(r), r, register) for r in mine if short(r)]
    return out


def with_short_lines(report: dict, rows: list[dict]) -> dict:
    """The report with its `short_lines` rows and the stems whose register is off (`short_flagged`)."""
    return report | {"short_lines": rows, "short_flagged": [r["line"] for r in rows if not r["short_register_ok"]]}


def lines_rows(home: Path) -> list[dict]:
    rows = json.loads((home / "audio" / "lines" / "lines.json").read_text(encoding="utf-8"))
    return rows["lines"] if isinstance(rows, dict) else rows


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    home = book / "episodes" / f"ep{number:02d}"
    report, worst_overall = {}, 1.0
    said, gone = deliveries(home), omitted_stems(book, number)
    for who, lines in sorted(lines_by_speaker(home).items()):
        lines = [l for l in lines if l[0] not in gone]
        sims = {(a[0], b[0]): voice_ear.similarity(a[1], b[1])
                for a, b in itertools.combinations(lines, 2)}
        allow = {pair: allowance(pair, said) for pair in sims}
        out = spread(sims, allow=allow)
        under = [list(p) for p, s in sims.items() if s < SAME_SPEAKER_FLOOR - allow[p]]
        report[who] = out | {"lines": len(lines), "under": under,   # step 04's revoice reads these
                             "ruler": voice_ear.RULER}
        mark = "" if out["ok"] else "SPLIT VOICE"
        worst = f"{out['worst']:.2f}" if out["worst"] is not None else "n/a"
        print(f"{who:<34} lines {len(lines):>2}  worst pair {worst} "
              f"{out['worst_pair'] or ''}  {mark}", flush=True)
        if out["worst"] is not None:
            worst_overall = min(worst_overall, out["worst"])
    shorts = [r for r in short_rows(home, lines_rows(home)) if r["line"] not in gone]
    for row in shorts:
        print(f"short {row['line']} {row['speaker']}: {row['offset_st']} st from register"
              f"{'' if row['short_register_ok'] else '  FLAGGED'}", flush=True)
    (home / "review").mkdir(exist_ok=True)
    (home / "review" / "speaker_check.json").write_text(
        json.dumps(with_short_lines(report, shorts), indent=1), encoding="utf-8")
    print(f"floor {SAME_SPEAKER_FLOOR}; worst across the cast {worst_overall:.2f}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
